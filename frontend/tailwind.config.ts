/**
 * Tailwind CSS configuration.
 * StayNest design system — warm terracotta palette with sage accents.
 * @type {import('tailwindcss').Config}
 */
module.exports = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        primary: {
          50: "#FDF4EF",
          100: "#FAE5D8",
          200: "#F5C9AD",
          300: "#EDA97E",
          400: "#E2854E",
          500: "#C06B3E",
          600: "#A35530",
          700: "#843F24",
          800: "#6B321D",
          900: "#502618",
        },
        accent: {
          50: "#F0F5F1",
          100: "#DCE8DE",
          200: "#B8D1BC",
          300: "#8FB596",
          400: "#6E9A76",
          500: "#5E7A63",
          600: "#4A6350",
          700: "#3B4F40",
          800: "#2D3D32",
          900: "#1F2B23",
        },
      },
      maxWidth: {
        container: "1440px",
      },
      screens: {
        "2xl": "1536px",
      },
      fontFamily: {
        sans: ["var(--font-jakarta)", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};
