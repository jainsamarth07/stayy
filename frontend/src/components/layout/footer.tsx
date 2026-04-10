import Link from "next/link";
import { Globe } from "lucide-react";

const footerSections = {
  Support: [
    { label: "Help Center", href: "#" },
    { label: "Get help with a safety issue", href: "#" },
    { label: "Cancellation options", href: "#" },
    { label: "Accessibility", href: "#" },
    { label: "Report a concern", href: "#" },
  ],
  Hosting: [
    { label: "Become a Host", href: "/auth/register?role=host" },
    { label: "Host resources", href: "#" },
    { label: "Community forum", href: "#" },
    { label: "Hosting responsibly", href: "#" },
    { label: "How it works", href: "#" },
  ],
  StayNest: [
    { label: "About", href: "#" },
    { label: "Newsroom", href: "#" },
    { label: "Careers", href: "#" },
    { label: "Investors", href: "#" },
    { label: "Zero commissions", href: "#" },
  ],
};

export default function Footer() {
  return (
    <footer className="bg-neutral-100 border-t">
      {/* Links grid */}
      <div className="mx-auto max-w-container px-4 sm:px-8 md:px-10 xl:px-20 py-12">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {Object.entries(footerSections).map(([title, links]) => (
            <div key={title}>
              <h3 className="text-sm font-bold mb-4">{title}</h3>
              <ul className="space-y-3">
                {links.map((link) => (
                  <li key={link.href + link.label}>
                    <Link
                      href={link.href}
                      className="text-sm text-neutral-600 hover:underline hover:text-neutral-900 transition-colors"
                    >
                      {link.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>

      {/* Bottom bar */}
      <div className="border-t">
        <div className="mx-auto max-w-container px-4 sm:px-8 md:px-10 xl:px-20 py-6">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex flex-wrap items-center gap-2 text-sm text-neutral-600">
              <span>&copy; {new Date().getFullYear()} StayNest, Inc.</span>
              <span className="hidden sm:inline">·</span>
              <Link href="#" className="hover:underline">Terms</Link>
              <span>·</span>
              <Link href="#" className="hover:underline">Privacy</Link>
              <span>·</span>
              <Link href="#" className="hover:underline">Sitemap</Link>
            </div>
            <div className="flex items-center gap-4 text-sm">
              <button className="flex items-center gap-2 font-semibold hover:underline">
                <Globe className="h-4 w-4" />
                English (US)
              </button>
              <span className="font-semibold">₹ INR</span>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
}
