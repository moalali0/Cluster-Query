/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#0f172a",
        mist: "#e2e8f0",
        signal: "#0f766e",
        warn: "#92400e",
        panel: "#ffffff",
      },
      boxShadow: {
        card: "0 16px 40px -24px rgba(15, 23, 42, 0.45)",
      },
    },
  },
  plugins: [],
};
