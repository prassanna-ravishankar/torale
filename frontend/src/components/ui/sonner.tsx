"use client";

import { Toaster as Sonner, ToasterProps } from "sonner";

const Toaster = ({ ...props }: ToasterProps) => {
  return (
    <Sonner
      theme="light"
      className="toaster group"
      position="bottom-right"
      expand={false}
      visibleToasts={3}
      closeButton
      richColors
      toastOptions={{
        classNames: {
          toast: "bg-white border-2 border-zinc-900 shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] font-sans",
          title: "font-grotesk font-bold text-zinc-900",
          description: "font-sans text-sm text-zinc-600",
          actionButton: "bg-zinc-900 text-white font-bold border-2 border-zinc-900 hover:bg-[hsl(10,90%,55%)]",
          cancelButton: "bg-white text-zinc-900 border-2 border-zinc-900",
          closeButton: "bg-white border-2 border-zinc-900 hover:bg-zinc-100",
          error: "border-red-600 bg-red-50",
          success: "border-emerald-600 bg-emerald-50",
          warning: "border-amber-600 bg-amber-50",
          info: "border-blue-600 bg-blue-50",
        },
      }}
      style={
        {
          "--normal-bg": "var(--popover)",
          "--normal-text": "var(--popover-foreground)",
          "--normal-border": "var(--border)",
        } as React.CSSProperties
      }
      {...props}
    />
  );
};

export { Toaster };
