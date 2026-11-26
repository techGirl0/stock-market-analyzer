import type { Metadata } from "next";
import "./globals.css";
import { Header } from "@/components/layout/Header";

export const metadata: Metadata = {
  title: "WolfStreet Signal",
  description: "Market intelligence platform for retail investors and fintech learners.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <Header />
        <main className="main-content">{children}</main>
      </body>
    </html>
  );
}
