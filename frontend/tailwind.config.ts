import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // Premium Aviation Palette
        navy: {
          50: '#E8EAF6',
          100: '#C5CAE9',
          200: '#9FA8DA',
          300: '#7986CB',
          400: '#5C6BC0',
          500: '#3F51B5',
          600: '#3949AB',
          700: '#303F9F',
          800: '#283593',
          900: '#1A237E',
          950: '#05164D', // Primary Navy
        },
        gold: {
          50: '#FFF8E1',
          100: '#FFECB3',
          200: '#FFE082',
          300: '#FFD54F',
          400: '#FFCA28',
          500: '#FFC107',
          600: '#FFB300',
          700: '#FFA000',
          800: '#FF8F00',
          900: '#FF6F00',
          950: '#F9B233', // Accent Gold
        },
        premium: {
          bg: '#0A0E27',
          card: '#0F1335',
          surface: '#161B42',
          border: '#1E2555',
          mist: '#E8F0FF',
        }
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'gradient-conic': 'conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))',
        'gradient-luxury': 'linear-gradient(135deg, #05164D 0%, #0A0E27 50%, #1A1F45 100%)',
        'gradient-gold': 'linear-gradient(135deg, #F9B233 0%, #FBBF24 50%, #FCD34D 100%)',
        'gradient-glass': 'linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%)',
        'aviation-hero': 'linear-gradient(180deg, rgba(5,22,77,0.95) 0%, rgba(10,14,39,0.98) 100%)',
      },
      boxShadow: {
        'luxury': '0 20px 60px -15px rgba(0, 0, 0, 0.6)',
        'luxury-lg': '0 30px 80px -20px rgba(0, 0, 0, 0.7)',
        'glow': '0 0 20px rgba(249, 178, 51, 0.5)',
        'glow-lg': '0 0 40px rgba(249, 178, 51, 0.6)',
        'inner-glow': 'inset 0 0 20px rgba(249, 178, 51, 0.2)',
        'glass': '0 8px 32px 0 rgba(31, 38, 135, 0.37)',
        'elevation-1': '0 2px 8px rgba(0,0,0,0.12)',
        'elevation-2': '0 4px 16px rgba(0,0,0,0.16)',
        'elevation-3': '0 8px 32px rgba(0,0,0,0.20)',
        'elevation-4': '0 16px 48px rgba(0,0,0,0.24)',
      },
      backdropBlur: {
        xs: '2px',
      },
      animation: {
        'fade-in': 'fadeIn 0.6s ease-out',
        'fade-in-up': 'fadeInUp 0.8s ease-out',
        'scale-in': 'scaleIn 0.5s ease-out',
        'slide-in-right': 'slideInRight 0.6s ease-out',
        'slide-in-left': 'slideInLeft 0.6s ease-out',
        'glow-pulse': 'glowPulse 2s ease-in-out infinite',
        'float': 'float 6s ease-in-out infinite',
        'shimmer': 'shimmer 2.5s linear infinite',
        'orbit': 'orbit 3s linear infinite',
        'scan': 'scan 2s ease-in-out infinite',
        'reveal': 'reveal 1s ease-out',
        'card-entrance': 'cardEntrance 0.6s ease-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        fadeInUp: {
          '0%': { opacity: '0', transform: 'translateY(30px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        scaleIn: {
          '0%': { opacity: '0', transform: 'scale(0.9)' },
          '100%': { opacity: '1', transform: 'scale(1)' },
        },
        slideInRight: {
          '0%': { opacity: '0', transform: 'translateX(-30px)' },
          '100%': { opacity: '1', transform: 'translateX(0)' },
        },
        slideInLeft: {
          '0%': { opacity: '0', transform: 'translateX(30px)' },
          '100%': { opacity: '1', transform: 'translateX(0)' },
        },
        glowPulse: {
          '0%, 100%': { boxShadow: '0 0 20px rgba(249, 178, 51, 0.5)' },
          '50%': { boxShadow: '0 0 40px rgba(249, 178, 51, 0.8)' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-20px)' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-1000px 0' },
          '100%': { backgroundPosition: '1000px 0' },
        },
        orbit: {
          '0%': { transform: 'rotate(0deg) translateX(50px) rotate(0deg)' },
          '100%': { transform: 'rotate(360deg) translateX(50px) rotate(-360deg)' },
        },
        scan: {
          '0%, 100%': { transform: 'translateY(-100%) scaleY(0)' },
          '50%': { transform: 'translateY(0%) scaleY(1)' },
        },
        reveal: {
          '0%': { clipPath: 'inset(0 100% 0 0)' },
          '100%': { clipPath: 'inset(0 0 0 0)' },
        },
        cardEntrance: {
          '0%': { 
            opacity: '0', 
            transform: 'translateY(40px) scale(0.95)',
            filter: 'blur(10px)'
          },
          '100%': { 
            opacity: '1', 
            transform: 'translateY(0) scale(1)',
            filter: 'blur(0px)'
          },
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        display: ['Poppins', 'system-ui', 'sans-serif'],
      },
      fontSize: {
        'hero': ['4.5rem', { lineHeight: '1.1', letterSpacing: '-0.02em' }],
        'display': ['3.5rem', { lineHeight: '1.2', letterSpacing: '-0.02em' }],
      },
      borderRadius: {
        'luxury': '20px',
        'card': '16px',
      },
      spacing: {
        '18': '4.5rem',
        '88': '22rem',
        '100': '25rem',
        '112': '28rem',
        '128': '32rem',
      },
    },
  },
  plugins: [],
}

export default config
