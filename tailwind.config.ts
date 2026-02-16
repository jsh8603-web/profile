import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        apple: {
          bg: '#FAFAFA',
          white: '#FFFFFF',
          gray: {
            50: '#F5F5F7',
            100: '#E8E8ED',
            200: '#D2D2D7',
            300: '#B0B0B5',
            400: '#86868B',
            500: '#6E6E73',
            600: '#424245',
            700: '#333336',
            800: '#1D1D1F',
          },
          blue: '#0071E3',
          'blue-hover': '#0077ED',
          'blue-light': '#EBF5FF',
        },
      },
      fontFamily: {
        sans: ['Plus Jakarta Sans', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
      },
      borderRadius: {
        'apple': '12px',
        'apple-lg': '16px',
        'apple-xl': '20px',
      },
      boxShadow: {
        'apple-sm': '0 1px 2px rgba(0,0,0,0.04)',
        'apple': '0 4px 12px rgba(0,0,0,0.06)',
        'apple-lg': '0 8px 30px rgba(0,0,0,0.08)',
        'apple-xl': '0 20px 60px rgba(0,0,0,0.1)',
      },
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
  ],
};
export default config;
