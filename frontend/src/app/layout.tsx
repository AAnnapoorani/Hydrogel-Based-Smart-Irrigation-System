import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Providers } from "@/components/Providers";
import Navbar from "@/components/Navbar";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "IrrigateWise – Smart Irrigation Platform",
  description: "AI-powered soil analysis, crop recommendation & water optimization for Tamil Nadu farmers.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <link
          href="https://fonts.googleapis.com/css2?family=Fraunces:ital,wght@0,400;0,600;0,700;1,400&family=DM+Sans:wght@300;400;500;600&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className={inter.className} style={{ fontFamily: "'DM Sans', sans-serif" }}>
        <Providers>
          <Navbar />
          <div className="min-h-screen bg-[#f8faf5]">{children}</div>
        </Providers>
      </body>
    </html>
  );
}
