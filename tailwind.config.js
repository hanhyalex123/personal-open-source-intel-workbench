/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      fontFamily: {
        display: ['"Space Grotesk"', "ui-sans-serif", "sans-serif"],
        body: ['"Sora"', "ui-sans-serif", "sans-serif"]
      },
      colors: {
        ink: "#e7f4ef",
        panel: "#0f1b1f",
        panelSoft: "#15262d",
        accent: "#21d4b5"
      },
      boxShadow: {
        glow: "0 20px 45px -20px rgba(33, 212, 181, 0.45)"
      },
      keyframes: {
        "fade-up": {
          "0%": { opacity: "0", transform: "translateY(14px)" },
          "100%": { opacity: "1", transform: "translateY(0)" }
        },
        "pulse-dot": {
          "0%, 100%": { transform: "scale(1)", opacity: "0.65" },
          "50%": { transform: "scale(1.35)", opacity: "1" }
        }
      },
      animation: {
        "fade-up": "fade-up 500ms ease-out both",
        "pulse-dot": "pulse-dot 1.6s ease-in-out infinite"
      }
    }
  },
  plugins: []
};