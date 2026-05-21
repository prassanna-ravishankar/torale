import { UserButton } from '@clerk/nextjs'

export default function UserMenu() {
  return <UserButton afterSignOutUrl="/sign-in" />
}
