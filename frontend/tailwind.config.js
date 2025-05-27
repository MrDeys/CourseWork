/** @type {import('tailwindcss').Config} */

function hexToRgba(hex, alpha) {
  const hexValue = hex.replace("#", "");
  const r = parseInt(hexValue.substring(0, 2), 16);
  const g = parseInt(hexValue.substring(2, 4), 16);
  const b = parseInt(hexValue.substring(4, 6), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

module.exports = {
  content: ["./src/**/*.{js,jsx,ts,tsx}", "./public/index.html"],
  theme: {
    extend: {
      colors: {
        "color-bg": "#121212",
        "color-surface": "#1E1E1E",
        "color-card-border": "#333333",

        "color-gradient-red-start": "#D90429",
        "color-gradient-red-mid": "#EF233C",
        "color-gradient-orange": "#F97316",
        "color-gradient-yellow-end": "#FFD700",

        "color-primary-red": "#CC0000",
        "color-primary-yellow": "#FFD700",

        "color-text-white": "#FFFFFF",
        "color-text-second": "#9CA3AF",

        "color-button-active-bg": "#CC0000",
        "color-button-active-text": "#FFD700",

        "color-button-inactive-bg": "#374151",
        "color-button-inactive-text": "#FFD700",

        "color-button-hover-bg": "#4B5563",
        "color-button-hover-text": "#FFED00",
      },
      backgroundImage: (theme) => ({
        "card-bg-gradient": `linear-gradient(to right, ${theme(
          "colors.color-surface"
        )}, ${theme("colors.color-surface")} 80%, ${theme(
          "colors.color-bg"
        )} 100%)`,
      }),
      boxShadow: {
        "red-button": `0 0 12px 3px ${hexToRgba("#CC0000", 0.6)}`,
        "card-hover": `0 0 15px 5px ${hexToRgba("#ff3333", 0.35)}`,
      },
    },
  },
  plugins: [
    function ({ addUtilities, theme, e }) {
      const newUtilities = {};
      const textGradients = {
        "neuro-title": `linear-gradient(to right, ${theme(
          "colors.color-gradient-red-start"
        )} 0%, ${theme("colors.color-gradient-red-mid")} 45%, ${theme(
          "colors.color-gradient-orange"
        )} 75%, ${theme("colors.color-gradient-yellow-end")} 100%)`,
      };
      Object.entries(textGradients).forEach(([name, backgroundImageValue]) => {
        newUtilities[`.text-gradient-${e(name)}`] = {
          backgroundImage: backgroundImageValue,
          "-webkit-background-clip": "text",
          "-webkit-text-fill-color": "transparent",
          "background-clip": "text",
          "text-fill-color": "transparent",
        };
      });
      addUtilities(newUtilities);
    },
  ],
};
