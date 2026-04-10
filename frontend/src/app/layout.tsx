import type { Metadata } from "next";
import { Nunito } from "next/font/google";
import "./globals.css";
import { ClientProviders } from "./client-providers";

const nunito = Nunito({
  subsets: ["latin"],
  variable: "--font-nunito",
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
      <body className={`${nunito.variable} font-sans min-h-screen antialiased`}>
        <ClientProviders>{children}</ClientProviders>
      </body>
    </html>
  );
}
