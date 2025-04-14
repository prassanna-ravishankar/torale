import { cookies } from "next/headers";
import { NextResponse } from "next/server";
import { createServerClient, type CookieOptions } from "@supabase/ssr";
import { Database } from "@/types/supabase";

// This ensures the route handler is treated as dynamic, preventing potential caching issues
export const dynamic = "force-dynamic";

/**
 * Route handler for the Supabase authentication callback.
 * It exchanges the authentication code received from Supabase for a user session,
 * setting the necessary authentication cookies for subsequent requests.
 * Relies on `@supabase/ssr` library to handle cookie management.
 */
export async function GET(request: Request) {
  const { searchParams, origin } = new URL(request.url);
  const code = searchParams.get("code");
  const error = searchParams.get("error");
  const errorDescription = searchParams.get("error_description");

  console.log("[Auth Callback] Processing request...");

  // Redirect back to auth page if there's an error in the callback parameters
  if (error) {
    console.error("[Auth Callback] Error in callback params:", {
      error,
      errorDescription,
    });
    const redirectUrl = new URL("/auth", origin);
    redirectUrl.searchParams.set("error", error);
    if (errorDescription) {
      redirectUrl.searchParams.set("error_description", errorDescription);
    }
    return NextResponse.redirect(redirectUrl);
  }

  // Redirect back to auth page if no code is provided
  if (!code) {
    console.error("[Auth Callback] No code found, redirecting to auth page.");
    return NextResponse.redirect(new URL("/auth?error=no_code_found", origin));
  }

  console.log("[Auth Callback] Auth code found, attempting exchange...");

  // Await the cookies() promise to get the cookie store for the request
  const cookieStore = await cookies();

  // Create a Supabase client configured for server-side operations (Route Handlers)
  // It requires access to the request cookies to manage the session.
  const supabase = createServerClient<Database>(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        // Provide the necessary methods for the Supabase client to interact with cookies
        get(name: string) {
          return cookieStore.get(name)?.value;
        },
        set(name: string, value: string, options: CookieOptions) {
          // The `set` method is called by the Supabase client library to persist session details.
          // We update the cookie store provided by Next.js.
          try {
            cookieStore.set({ name, value, ...options });
          } catch (error) {
            console.error(
              `[Auth Callback] Error setting cookie in store: ${name}`,
              error,
            );
          }
        },
        remove(name: string, options: CookieOptions) {
          // The `remove` method is called by the Supabase client library (e.g., on sign out).
          // We update the cookie store to remove the session cookie.
          try {
            // Attempt to remove cookie by setting value to empty and maxAge to 0
            cookieStore.set({ name, value: "", ...options, maxAge: 0 });
          } catch (error) {
            console.error(
              `[Auth Callback] Error removing cookie in store: ${name}`,
              error,
            );
          }
        },
      },
    },
  );

  try {
    // Attempt to exchange the received code for a user session
    const { error: exchangeError } =
      await supabase.auth.exchangeCodeForSession(code);

    // If the exchange fails, redirect back to the auth page with an error
    if (exchangeError) {
      console.error(
        "[Auth Callback] Error exchanging code:",
        exchangeError.message,
      );
      const redirectUrl = new URL("/auth", origin);
      redirectUrl.searchParams.set("error", exchangeError.message);
      return NextResponse.redirect(redirectUrl);
    }

    // If the exchange is successful, the Supabase client (via the cookie methods above)
    // should have set the necessary auth cookies.
    // Redirect the user to the intended destination (e.g., dashboard).
    console.log(
      "[Auth Callback] Code exchange successful. Redirecting to dashboard.",
    );
    return NextResponse.redirect(`${origin}/dashboard`);
  } catch (err) {
    // Catch any unexpected errors during the process
    console.error("[Auth Callback] Unhandled error during code exchange:", err);
    const redirectUrl = new URL("/auth", origin);
    redirectUrl.searchParams.set("error", "server_error");
    const description =
      err instanceof Error ? err.message : "Unknown server error";
    redirectUrl.searchParams.set("error_description", description);
    return NextResponse.redirect(redirectUrl);
  }
}
