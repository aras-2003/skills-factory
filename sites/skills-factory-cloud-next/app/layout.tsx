import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Skills Factory Cloud",
  description: "Testowy, read/compute-only cloud runtime zgodny z Skills Factory Lab.",
  other: {
    "codex-preview": "development",
  },
  icons: {
    icon: "/favicon.svg",
    shortcut: "/favicon.svg",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pl">
      <body className="antialiased">{children}</body>
    </html>
  );
}
