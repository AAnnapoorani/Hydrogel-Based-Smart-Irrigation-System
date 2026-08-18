/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans:  ["DM Sans", "sans-serif"],
        serif: ["Fraunces", "Georgia", "serif"],
        mono:  ["JetBrains Mono", "monospace"],
      },
      colors: {
        green: {
          50:  "#eaf3de",
          100: "#c0dd97",
          200: "#97c459",
          300: "#7db53a",
          400: "#639922",
          500: "#4d7d18",
          600: "#3b6d11",
          700: "#2f580d",
          800: "#27500a",
          900: "#173404",
          950: "#0d1f02",
        },
        teal: {
          50:  "#e1f5ee",
          100: "#9fe1cb",
          400: "#1d9e75",
          600: "#0f6e56",
          700: "#0a5240",
          900: "#04342c",
        },
        amber: {
          50:  "#faeeda",
          100: "#fac775",
          400: "#ba7517",
          600: "#854f0b",
        },
      },
      borderRadius: {
        "2xl": "1rem",
        "3xl": "1.25rem",
      },
      boxShadow: {
        soft: "0 2px 12px rgba(40,80,10,0.08)",
        md:   "0 4px 20px rgba(40,80,10,0.10)",
        lg:   "0 8px 32px rgba(40,80,10,0.12)",
      },
    },
  },
  plugins: [],
};
