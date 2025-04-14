import { createServerClient, type CookieOptions } from "@supabase/ssr";
import { NextResponse, type NextRequest } from "next/server";

/**
 * Middleware function to handle session management and protected routes.
 * Uses `@supabase/ssr` to create a server client that interacts with cookies.
 * It checks for a valid user session based on cookies and redirects:
 * - Unauthenticated users trying to access protected routes to the /auth page.
 * - Authenticated users trying to access the /auth page to the /dashboard.
 * It also refreshes the session cookie if necessary.
 */
export async function updateSession(request: NextRequest) {
  // This response object will be modified by the Supabase client
  // if the session needs to be refreshed or cookies updated.
  let response = NextResponse.next({
    request: {
      headers: request.headers,
    },
  });

  // Create a Supabase client configured for middleware
  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        // Provide methods for the client to read/write cookies from the request/response
        get(name: string) {
          return request.cookies.get(name)?.value;
        },
        set(name: string, value: string, options: CookieOptions) {
          // If the client needs to set a cookie (e.g., session refreshed),
          // it updates the request cookies and the response cookies.
          request.cookies.set({
            name,
            value,
            ...options,
          });
          // Ensure the response object is up-to-date if cookies are set/modified
          response = NextResponse.next({
            request: {
              headers: request.headers,
            },
          });
          response.cookies.set({
            name,
            value,
            ...options,
          });
        },
        remove(name: string, options: CookieOptions) {
          // If the client needs to remove a cookie (e.g., sign out),
          // it updates the request cookies and the response cookies.
          request.cookies.set({
            name,
            value: "",
            ...options,
          });
          response = NextResponse.next({
            request: {
              headers: request.headers,
            },
          });
          response.cookies.set({
            name,
            value: "",
            ...options,
          });
        },
      },
    },
  );

  // Check if a user session exists based on the cookies.
  // IMPORTANT: Avoid calling supabase.auth.getUser() here unless absolutely necessary for logic
  // that runs *before* the protected route check. getUser() makes an external network request
  // and can slow down every request. For basic protection, getSession() is sufficient.
  const {
    data: { session },
  } = await supabase.auth.getSession();

  // Define protected routes
  const protectedPaths = ["/dashboard", "/profile", "/settings", "/alerts"];
  const isProtectedPath = protectedPaths.some(
    (path) =>
      request.nextUrl.pathname === path ||
      request.nextUrl.pathname.startsWith(`${path}/`),
  );
  const isAuthPage = request.nextUrl.pathname === "/auth";

  // --- Redirect Logic ---
  // If trying to access a protected route without a valid session, redirect to /auth
  if (isProtectedPath && !session) {
    console.log(
      `[Middleware] No session, redirecting protected path: ${request.nextUrl.pathname} to /auth`,
    );
    return NextResponse.redirect(new URL("/auth", request.url));
  }

  // If trying to access the /auth page with a valid session, redirect to /dashboard
  if (isAuthPage && session) {
    console.log(
      `[Middleware] Session found, redirecting from /auth to /dashboard`,
    );
    return NextResponse.redirect(new URL("/dashboard", request.url));
  }

  // If no redirection is needed, continue with the request/response cycle.
  // The response object might have updated cookies if the session was refreshed.
  return response;
}

// Middleware entry point: Called for every request matching the config.matcher
export async function middleware(request: NextRequest) {
  console.log(
    `[Middleware] Request: ${request.method} ${request.nextUrl.pathname}`,
  );
  // Calls the session handling logic
  return await updateSession(request);
}

// Configures which paths the middleware should run on.
export const config = {
  matcher: [
    // Match all request paths except for static assets, images, favicon, and API routes.
    // This ensures middleware runs on page navigations (/auth, /dashboard, etc.)
    // but avoids unnecessary checks on asset requests.
    "/((?!_next/static|_next/image|favicon.ico|api/|.*.(?:svg|png|jpg|jpeg|gif|webp)$).*)",
  ],
};
