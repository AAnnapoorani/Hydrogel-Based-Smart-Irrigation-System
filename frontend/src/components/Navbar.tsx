"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

const links = [
  { href: "/dashboard",  label: "Dashboard"   },
  { href: "/soil",       label: "Soil Analysis" },
  { href: "/irrigation", label: "Irrigation"  },
  { href: "/reports",    label: "Reports"     },
];

export default function Navbar() {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <nav className="bg-white border-b border-green-100 sticky top-0 z-50">
      <div className="max-w-6xl mx-auto px-4 h-14 flex items-center justify-between">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2.5 group">
          <div className="w-8 h-8 bg-green-700 rounded-lg flex items-center justify-center text-white text-xs font-bold group-hover:bg-green-900 transition-colors">
            IW
          </div>
          <span
            className="font-bold text-green-900 text-lg"
            style={{ fontFamily: "'Fraunces', serif" }}
          >
            IrrigateWise
          </span>
        </Link>

        {/* Desktop links */}
        <div className="hidden md:flex items-center gap-1">
          {links.map((l) => {
            const active = pathname === l.href || pathname.startsWith(l.href + "/");
            return (
              <Link
                key={l.href}
                href={l.href}
                className={`px-3.5 py-1.5 rounded-lg text-sm font-medium transition-all ${
                  active
                    ? "bg-green-50 text-green-700"
                    : "text-green-600 hover:bg-green-50 hover:text-green-700"
                }`}
              >
                {l.label}
              </Link>
            );
          })}
        </div>

        {/* CTA + hamburger */}
        <div className="flex items-center gap-2">
          <Link
            href="/dashboard"
            className="hidden md:block bg-green-700 hover:bg-green-900 text-white text-sm font-semibold px-4 py-2 rounded-lg transition-all"
          >
            Open Dashboard
          </Link>
          <button
            className="md:hidden p-2 rounded-lg hover:bg-green-50 text-green-700 transition-colors"
            onClick={() => setMobileOpen((v) => !v)}
            aria-label="Toggle menu"
          >
            <svg width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              {mobileOpen
                ? <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                : <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h16" />
              }
            </svg>
          </button>
        </div>
      </div>

      {/* Mobile drawer */}
      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="md:hidden border-t border-green-100 bg-white overflow-hidden"
          >
            <div className="px-4 py-3 space-y-1">
              {links.map((l) => {
                const active = pathname === l.href;
                return (
                  <Link
                    key={l.href}
                    href={l.href}
                    onClick={() => setMobileOpen(false)}
                    className={`block px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                      active ? "bg-green-50 text-green-700" : "text-green-600 hover:bg-green-50"
                    }`}
                  >
                    {l.label}
                  </Link>
                );
              })}
              <Link
                href="/dashboard"
                onClick={() => setMobileOpen(false)}
                className="block mt-2 text-center bg-green-700 text-white py-2.5 rounded-lg text-sm font-semibold"
              >
                Open Dashboard
              </Link>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </nav>
  );
}
