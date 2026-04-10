/**
 * Tailwind CSS configuration.
 * Airbnb-inspired design system with rose palette and extended breakpoints.
 * @type {import('tailwindcss').Config}
 */
module.exports = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        primary: {
          50: "#fff1f2",
          100: "#ffe4e6",
          200: "#fecdd3",
          300: "#fda4af",
          400: "#fb7185",
          500: "#f43f5e",
          600: "#e11d48",
          700: "#be123c",
          800: "#9f1239",
          900: "#881337",
        },
      },
      maxWidth: {
        container: "2520px",
      },
      screens: {
        "2xl": "1536px",
      },
      fontFamily: {
        sans: ["var(--font-nunito)", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};
