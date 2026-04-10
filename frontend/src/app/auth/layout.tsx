/**
 * @module AuthLayout
 * @description Layout wrapper for authentication pages (login, register, forgot/reset password).
 */
import Navbar from "@/components/layout/navbar";
import Footer from "@/components/layout/footer";

/**
 * Wraps auth pages with the shared Navbar and Footer.
 * @param props.children - The auth page content.
 * @returns The auth layout element.
 */
export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <Navbar />
      <main className="flex-1">{children}</main>
      <Footer />
    </>
  );
}
