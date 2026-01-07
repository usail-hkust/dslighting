import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "DSLighting Interactive",
  description: "Web interface for dslighting data science agents",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
