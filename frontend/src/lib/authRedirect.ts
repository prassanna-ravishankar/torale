export function getSignInRedirect(pathname: string, search: string): string {
  const returnPath = search ? `${pathname}?${search}` : pathname
  return `/sign-in?redirect_url=${encodeURIComponent(returnPath)}`
}
