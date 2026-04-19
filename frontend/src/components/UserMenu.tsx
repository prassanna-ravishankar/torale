import { UserButton } from '@clerk/clerk-react'

export default function UserMenu() {
  return <UserButton afterSignOutUrl="/sign-in" />
}
