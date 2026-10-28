"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { ApiService } from "@/lib/api";
import { Menu, X, Wifi, WifiOff } from "lucide-react";

interface NavLink {
  href: string;
  label: string;
}

const links: NavLink[] = [
  { href: "/dashboard",        label: "Dashboard" },
  { href: "/plants",           label: "Terrace Garden" },
  { href: "/diagnosis",        label: "Plant Health" },
  { href: "/soil",             label: "Soil Analysis" },
  { href: "/irrigation",       label: "Irrigation & Automation" },
  { href: "/model-evaluation", label: "Model Evaluation" },
  { href: "/metrics",          label: "ML Metrics" },
  { href: "/reports",          label: "Reports" },
];

export default function Navbar() {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [toggling, setToggling] = useState(false);
  const queryClient = useQueryClient();

  const { data: nodeStatus } = useQuery({
    queryKey: ["node-status"],
    queryFn: ApiService.getNodeStatus,
    refetchInterval: 3000,
  });

  const isOnline = Boolean(nodeStatus?.is_online);

  const handleToggleConnection = async () => {
    try {
      setToggling(true);
      if (isOnline) {
        await ApiService.disconnectNode();
      } else {
        await ApiService.simulatePacket();
      }
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["node-status"] }),
        queryClient.invalidateQueries({ queryKey: ["latest-sensor"] }),
        queryClient.invalidateQueries({ queryKey: ["predictive-decision"] }),
      ]);
    } catch (err) {
      console.error("Failed to toggle ESP32 node:", err);
    } finally {
      setToggling(false);
    }
  };

  return (
    <header className="sticky top-0 z-50 bg-white/95 backdrop-blur-sm border-b border-slate-200/80 transition-colors">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between gap-4">
        {/* Brand Logo */}
        <Link href="/" className="flex items-center gap-2.5 group">
          <div className="w-9 h-9 rounded-full overflow-hidden bg-white border border-emerald-600/30 shadow-soft flex items-center justify-center p-0.5 group-hover:scale-105 transition-transform">
            <img
              src="/logo.png"
              alt="IrrigateWise Crest Logo"
              className="w-full h-full object-contain"
            />
          </div>
          <div className="flex flex-col">
            <span className="font-bold text-slate-900 text-lg leading-tight tracking-tight">
              IrrigateWise
            </span>
            <span className="text-[10px] text-slate-500 font-medium -mt-0.5 tracking-wide">
              Smart Precision Ag
            </span>
          </div>
        </Link>

        {/* Desktop Navigation Links */}
        <nav className="hidden lg:flex items-center gap-1">
          {links.map((l) => {
            const active = pathname === l.href || pathname.startsWith(l.href + "/");
            return (
              <Link
                key={l.href}
                href={l.href}
                className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
                  active
                    ? "bg-emerald-50 text-emerald-800 font-semibold"
                    : "text-slate-600 hover:text-slate-900 hover:bg-slate-100/70"
                }`}
              >
                {l.label}
              </Link>
            );
          })}
        </nav>

        {/* Right Section: Node Status Pill + Action Button + Mobile Toggle */}
        <div className="flex items-center gap-2.5">
          {/* Professional Node Connectivity Pill */}
          <div className="hidden sm:flex items-center">
            {isOnline ? (
              <div className="flex items-center gap-2 bg-emerald-50/90 border border-emerald-200/80 rounded-lg px-2.5 py-1 text-xs text-emerald-900 shadow-soft">
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                </span>
                <span className="font-medium">Node Live</span>
                <button
                  onClick={handleToggleConnection}
                  disabled={toggling}
                  className="ml-1 text-[11px] font-semibold text-emerald-700 hover:text-rose-700 px-1.5 py-0.5 rounded hover:bg-emerald-100/70 transition-colors disabled:opacity-50"
                  title="Disconnect live simulation"
                >
                  {toggling ? "…" : "Disconnect"}
                </button>
              </div>
            ) : (
              <div className="flex items-center gap-2 bg-slate-100/80 border border-slate-200 rounded-lg px-2.5 py-1 text-xs text-slate-700">
                <span className="h-2 w-2 rounded-full bg-slate-400"></span>
                <span className="font-medium">Node Standby</span>
                <button
                  onClick={handleToggleConnection}
                  disabled={toggling}
                  className="ml-1 text-[11px] font-semibold text-emerald-700 hover:text-emerald-800 px-1.5 py-0.5 rounded hover:bg-slate-200 transition-colors disabled:opacity-50"
                  title="Simulate live sensor transmission"
                >
                  {toggling ? "…" : "Connect Demo"}
                </button>
              </div>
            )}
          </div>

          <Link
            href="/dashboard"
            className="hidden md:inline-flex items-center text-xs font-semibold px-3.5 py-1.5 rounded-lg bg-emerald-700 text-white hover:bg-emerald-800 transition-colors shadow-soft"
          >
            Dashboard
          </Link>

          {/* Mobile Menu Toggle Button */}
          <button
            className="lg:hidden p-2 rounded-lg text-slate-600 hover:text-slate-900 hover:bg-slate-100 transition-colors"
            onClick={() => setMobileOpen((v) => !v)}
            aria-label="Toggle navigation menu"
          >
            {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {/* Mobile Drawer */}
      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="lg:hidden border-t border-slate-200/80 bg-white overflow-hidden shadow-card"
          >
            <div className="px-4 py-3 space-y-1">
              {/* Mobile Node Switcher */}
              <div className="p-2.5 mb-2 bg-slate-50 border border-slate-200/80 rounded-xl flex items-center justify-between text-xs">
                <span className="font-medium text-slate-800 flex items-center gap-2">
                  <span className={`w-2 h-2 rounded-full ${isOnline ? "bg-emerald-500 animate-pulse" : "bg-slate-400"}`}></span>
                  ESP32 Status: {isOnline ? "Live Online" : "Standby"}
                </span>
                <button
                  onClick={handleToggleConnection}
                  disabled={toggling}
                  className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-all ${
                    isOnline
                      ? "bg-slate-200 hover:bg-slate-300 text-slate-800"
                      : "bg-emerald-700 hover:bg-emerald-800 text-white"
                  }`}
                >
                  {toggling ? "…" : isOnline ? "Disconnect" : "Connect Demo"}
                </button>
              </div>

              {links.map((l) => {
                const active = pathname === l.href;
                return (
                  <Link
                    key={l.href}
                    href={l.href}
                    onClick={() => setMobileOpen(false)}
                    className={`block px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                      active
                        ? "bg-emerald-50 text-emerald-800 font-semibold"
                        : "text-slate-600 hover:text-slate-900 hover:bg-slate-50"
                    }`}
                  >
                    {l.label}
                  </Link>
                );
              })}

              <Link
                href="/dashboard"
                onClick={() => setMobileOpen(false)}
                className="block mt-2 text-center bg-emerald-700 text-white py-2 rounded-lg text-sm font-semibold hover:bg-emerald-800 transition-colors"
              >
                Open Dashboard
              </Link>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </header>
  );
}
