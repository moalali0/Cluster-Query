/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#f5f5f5",
        mist: "#2a2a2a",
        signal: "#ea580c",
        warn: "#fb923c",
        panel: "#1e1e1e",
        surface: "#141414",
        "surface-light": "#262626",
        accent: "#ea580c",
        "accent-light": "#fb923c",
        "accent-dim": "#9a3412",
        subtle: "#a3a3a3",
      },
      boxShadow: {
        card: "0 16px 40px -24px rgba(0, 0, 0, 0.6)",
      },
    },
  },
  plugins: [],
};
