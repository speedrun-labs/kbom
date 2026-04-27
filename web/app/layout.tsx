import type { Metadata } from "next";
import type { ReactNode } from "react";

import { QueryProvider } from "@/components/providers/QueryProvider";
import { CommandPalette } from "@/components/CommandPalette";

import "./globals.css";

export const metadata: Metadata = {
  title: "KBOM",
  description: "Kitchen BOM extraction from blueprints",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="min-h-full">
        <QueryProvider>
          <CommandPalette />
          {children}
        </QueryProvider>
      </body>
    </html>
  );
}
