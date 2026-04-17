"use client";

import React from "react";
import { AuthProvider } from "@/components/providers/auth-provider";
import { ToastContainer } from "@/components/ui/toast";
import Navbar from "@/components/layout/navbar";
import Footer from "@/components/layout/footer";
import AiAgentChat from "@/components/AiAgent/AiAgentChat";
import { usePathname } from "next/navigation";

const noShellRoutes = ["/auth", "/dashboard", "/admin"];

export function ClientProviders({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const hideShell = noShellRoutes.some((r) => pathname.startsWith(r));

  return (
    <AuthProvider>
      {hideShell ? (
        children
      ) : (
        <>
          <Navbar />
          <main>{children}</main>
          <Footer />
        </>
      )}
      <ToastContainer />
      <AiAgentChat />
    </AuthProvider>
  );
}
