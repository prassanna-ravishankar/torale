import { SignIn } from '@clerk/nextjs'

export default function SignInRoutePage() {
  return (
    <SignIn
      routing="path"
      path="/sign-in"
      signUpUrl="/sign-up"
      fallbackRedirectUrl="/dashboard"
    />
  )
}
