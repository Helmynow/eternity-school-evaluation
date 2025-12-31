/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Language Division (Blues)
        'ese-lang': {
          900: '#094773',
          800: '#23547B',
          700: '#485D7B',
          500: '#2D7EA1',
          300: '#67A1BA',
          200: '#9DC6E1',
          soft: '#869FC9',
        },
        // International Division (Greens)
        'ese-int': {
          900: '#2C5B4C',
          700: '#5D7D60',
          600: '#487557',
          500: '#7CA48A',
          300: '#8EB49B',
          50: '#E5F6DF',
          accent: '#86C997',
          neutral: '#D1DCCD',
        },
        // Accent Colors
        'ese-accent': {
          terracotta: '#C88167',
          mustard: '#E4A740',
          olive: '#B8AD7E',
          beige: '#EBE1DB',
          'deep-teal': '#29544C',
          sage: '#7CA48A',
          blue: '#619FC5',
          'light-blue': '#A7C9D8',
          'pale-sage': '#D1DDCD',
        },
        // Ink Colors
        'ese-ink': {
          white: '#F8F8F8',
          offwhite: '#F8F0E8',
          navy: '#204088',
          blue: '#486898',
          green: '#285848',
        },
      },
      fontFamily: {
        sans: ['Plus Jakarta Sans', 'system-ui', 'sans-serif'],
        heading: ['Fraunces', 'Georgia', 'serif'],
        mono: ['JetBrains Mono', 'ui-monospace', 'monospace'],
        arabic: ['Noto Sans Arabic', 'Segoe UI', 'system-ui', 'sans-serif'],
      },
      borderRadius: {
        'ese-pill': '0.875rem',
        'ese-tile': '1.125rem',
        'ese-card': '1.125rem',
        'ese-neumorphic': '1.25rem',
      },
      boxShadow: {
        'ese-drop': '0 0.625rem 1rem rgba(0, 0, 0, 0.12)',
        'ese-step': '0 0.25rem 0 rgba(0, 0, 0, 0.1)',
        'ese-inner-top': 'inset 0 0.0625rem 0 rgba(255, 255, 255, 0.55)',
        'ese-inner-bottom': 'inset 0 -0.0625rem 0 rgba(0, 0, 0, 0.08)',
        'ese-card-embossed': '0 0.25rem 0 rgba(0, 0, 0, 0.1), 0 0.625rem 1rem rgba(0, 0, 0, 0.12), inset 0 0.0625rem 0 rgba(255, 255, 255, 0.55), inset 0 -0.0625rem 0 rgba(0, 0, 0, 0.08)',
      },
    },
  },
  plugins: [],
}

