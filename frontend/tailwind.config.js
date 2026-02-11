/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#fb923c",
        panel: "#111111",
        surface: "#181818",
        accent: "#ea580c",
        "accent-light": "#fb923c",
        "accent-bright": "#fdba74",
        dim: "#78350f",
      },
      boxShadow: {
        card: "0 16px 40px -24px rgba(234, 88, 12, 0.15)",
      },
    },
  },
  plugins: [],
};
