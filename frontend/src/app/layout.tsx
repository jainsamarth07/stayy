import type { Metadata } from "next";
import { Plus_Jakarta_Sans } from "next/font/google";
import "./globals.css";
import { ClientProviders } from "./client-providers";

const jakarta = Plus_Jakarta_Sans({
  subsets: ["latin"],
  variable: "--font-jakarta",
});

export const metadata: Metadata = {
  title: "StayNest — Commission-Free Rentals",
  description:
    "Find your perfect stay. Hosts keep 100% of their booking revenue.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={`${jakarta.variable} font-sans min-h-screen antialiased`}>
        <ClientProviders>{children}</ClientProviders>
      </body>
    </html>
  );
}
