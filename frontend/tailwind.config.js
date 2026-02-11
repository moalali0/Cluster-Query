/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
      colors: {
        brand: {
          50: "#fff7ed",
          100: "#ffedd5",
          200: "#fed7aa",
          300: "#fdba74",
          400: "#fb923c",
          500: "#f97316",
          600: "#ea580c",
          700: "#c2410c",
          800: "#9a3412",
          900: "#7c2d12",
          950: "#431407",
        },
        surface: {
          0: "#000000",
          50: "#0a0a0a",
          100: "#0f0f0f",
          200: "#141414",
          300: "#1a1a1a",
          400: "#222222",
          500: "#2a2a2a",
          600: "#333333",
          700: "#444444",
          800: "#666666",
          900: "#999999",
        },
      },
      boxShadow: {
        glow: "0 0 20px -4px rgba(249, 115, 22, 0.15)",
        "glow-lg": "0 0 40px -8px rgba(249, 115, 22, 0.2)",
        card: "0 1px 3px rgba(0, 0, 0, 0.4), 0 8px 24px -8px rgba(0, 0, 0, 0.5)",
      },
      animation: {
        "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "fade-in": "fadeIn 0.3s ease-out",
        "slide-up": "slideUp 0.3s ease-out",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        slideUp: {
          "0%": { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
      },
    },
  },
  plugins: [],
};
