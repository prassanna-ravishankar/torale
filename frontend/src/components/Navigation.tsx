"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const navigation = [
  { name: "Dashboard", href: "/" },
  { name: "Alerts", href: "/alerts" },
  { name: "Settings", href: "/settings" },
];

export default function Navigation() {
  const pathname = usePathname();

  return (
    <nav className="flex space-x-4">
      {navigation.map((item) => {
        const isActive = pathname === item.href;
        return (
          <Link
            key={item.name}
            href={item.href}
            className={`px-3 py-2 rounded-md text-sm font-medium ${
              isActive
                ? "bg-gray-900 text-white"
                : "text-gray-300 hover:bg-gray-700 hover:text-white"
            }`}
          >
            {item.name}
          </Link>
        );
      })}
    </nav>
  );
}
