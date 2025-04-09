/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.{html,js}",
    "./static/**/*.{html,js}",
    "./*.{html,js}"
  ],
  theme: {
    extend: {
      fontFamily: {
        'sans': ['Roboto', 'sans-serif'],
      }
    },
    colors: {
      'dark-purple': '#301934',
    },
  },
  plugins: [],
}