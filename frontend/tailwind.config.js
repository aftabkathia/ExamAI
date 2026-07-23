/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        ink: {
          950: "#071018",
          900: "#0c1a24",
          800: "#132736",
          700: "#1c3648",
          600: "#2a4d63",
        },
        jade: {
          300: "#6fd4b0",
          400: "#3cbc8f",
          500: "#1f9a73",
          600: "#167a5b",
        },
        sand: {
          50: "#f7f4ef",
          100: "#efe8dc",
          200: "#e2d5c2",
        },
        ember: {
          400: "#e8a04a",
          500: "#d4842a",
        },
      },
      fontFamily: {
        display: ["var(--font-display)", "Georgia", "serif"],
        sans: ["var(--font-sans)", "system-ui", "sans-serif"],
      },
      backgroundImage: {
        "mesh":
          "radial-gradient(ellipse 80% 50% at 20% -10%, rgba(31,154,115,0.25), transparent), radial-gradient(ellipse 60% 40% at 90% 10%, rgba(232,160,74,0.12), transparent), radial-gradient(ellipse 50% 30% at 50% 100%, rgba(31,154,115,0.08), transparent)",
        "grid":
          "linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px)",
      },
      backgroundSize: {
        grid: "48px 48px",
      },
      boxShadow: {
        glow: "0 0 40px rgba(31,154,115,0.15)",
      },
      keyframes: {
        "fade-up": {
          "0%": { opacity: "0", transform: "translateY(16px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
        pulseSoft: {
          "0%, 100%": { opacity: "0.6" },
          "50%": { opacity: "1" },
        },
      },
      animation: {
        "fade-up": "fade-up 0.6s ease-out both",
        shimmer: "shimmer 2s linear infinite",
        "pulse-soft": "pulseSoft 2.5s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};
