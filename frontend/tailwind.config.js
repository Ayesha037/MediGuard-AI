/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        canvas: "#F7FAFC",
        surface: "#FFFFFF",
        ink: {
          900: "#0F172A",
          600: "#334155",
          400: "#64748B",
          200: "#CBD5E1",
        },
        clinical: {
          DEFAULT: "#0A5C7A",
          dark: "#083F54",
          light: "#E4F0F4",
        },
        teal: {
          DEFAULT: "#0D9488",
          light: "#CCFBF1",
        },
        status: {
          healthy: "#059669",
          healthyBg: "#ECFDF5",
          warning: "#D97706",
          warningBg: "#FFFBEB",
          critical: "#DC2626",
          criticalBg: "#FEF2F2",
          offline: "#64748B",
          offlineBg: "#F1F5F9",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["'IBM Plex Mono'", "ui-monospace", "monospace"],
      },
      borderRadius: {
        card: "10px",
      },
      boxShadow: {
        card: "0 1px 2px 0 rgba(15, 23, 42, 0.04), 0 1px 3px 0 rgba(15, 23, 42, 0.06)",
        elevated: "0 4px 12px -2px rgba(15, 23, 42, 0.08)",
      },
    },
  },
  plugins: [],
};
