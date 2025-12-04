/**
 * Motion System Configuration
 * CRED-level animation presets and Framer Motion variants
 */

import { Variants, Transition } from 'framer-motion';

// ==================== EASING CURVES ====================

export const easings = {
  // CRED-style smooth easings
  credEase: [0.25, 0.1, 0.25, 1],
  appleEase: [0.4, 0, 0.2, 1],
  luxury: [0.6, 0.01, 0.05, 0.9],
  bounce: [0.68, -0.55, 0.265, 1.55],
  snappy: [0.25, 0.46, 0.45, 0.94],
} as const;

// ==================== TRANSITION PRESETS ====================

export const transitions = {
  default: {
    type: 'spring',
    stiffness: 300,
    damping: 30,
  } as Transition,
  
  smooth: {
    type: 'spring',
    stiffness: 100,
    damping: 20,
  } as Transition,
  
  bouncy: {
    type: 'spring',
    stiffness: 400,
    damping: 25,
    mass: 0.8,
  } as Transition,
  
  slow: {
    type: 'spring',
    stiffness: 60,
    damping: 20,
  } as Transition,
  
  tween: (duration: number = 0.6) => ({
    type: 'tween',
    duration,
    ease: easings.credEase,
  } as Transition),
};

// ==================== ANIMATION VARIANTS ====================

// Hero Section Entrance
export const heroVariants: Variants = {
  hidden: {
    opacity: 0,
    y: 60,
    scale: 0.95,
    filter: 'blur(10px)',
  },
  visible: {
    opacity: 1,
    y: 0,
    scale: 1,
    filter: 'blur(0px)',
    transition: {
      duration: 1.2,
      ease: easings.luxury,
      staggerChildren: 0.2,
    },
  },
};

// Staggered children reveal (CRED-style)
export const staggerContainer: Variants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
      delayChildren: 0.2,
    },
  },
};

export const staggerItem: Variants = {
  hidden: {
    opacity: 0,
    y: 30,
    filter: 'blur(8px)',
  },
  visible: {
    opacity: 1,
    y: 0,
    filter: 'blur(0px)',
    transition: {
      duration: 0.6,
      ease: easings.credEase,
    },
  },
};

// Card entrance (boarding pass swipe-in)
export const cardEntrance: Variants = {
  hidden: {
    opacity: 0,
    x: -100,
    rotateY: -15,
    scale: 0.9,
  },
  visible: {
    opacity: 1,
    x: 0,
    rotateY: 0,
    scale: 1,
    transition: {
      duration: 0.8,
      ease: easings.luxury,
    },
  },
};

// Flight card hover effect
export const flightCardHover = {
  rest: {
    scale: 1,
    y: 0,
    boxShadow: '0 8px 32px rgba(0,0,0,0.2)',
    borderColor: 'rgba(30, 37, 85, 1)',
  },
  hover: {
    scale: 1.02,
    y: -8,
    boxShadow: '0 20px 60px rgba(249, 178, 51, 0.3)',
    borderColor: 'rgba(249, 178, 51, 0.8)',
    transition: {
      duration: 0.3,
      ease: easings.snappy,
    },
  },
  tap: {
    scale: 0.98,
  },
};

// Button glow pulse
export const buttonGlow: Variants = {
  rest: {
    boxShadow: '0 0 20px rgba(249, 178, 51, 0.3)',
  },
  hover: {
    boxShadow: [
      '0 0 20px rgba(249, 178, 51, 0.3)',
      '0 0 40px rgba(249, 178, 51, 0.6)',
      '0 0 20px rgba(249, 178, 51, 0.3)',
    ],
    transition: {
      duration: 1.5,
      repeat: Infinity,
      ease: 'easeInOut',
    },
  },
  tap: {
    scale: 0.95,
    boxShadow: '0 0 50px rgba(249, 178, 51, 0.8)',
  },
};

// Ripple effect on click
export const ripple: Variants = {
  initial: {
    scale: 0,
    opacity: 1,
  },
  animate: {
    scale: 2.5,
    opacity: 0,
    transition: {
      duration: 0.6,
      ease: 'easeOut',
    },
  },
};

// Route arrow animation
export const routeArrow: Variants = {
  initial: {
    x: 0,
  },
  animate: {
    x: [0, 10, 0],
    transition: {
      duration: 2,
      repeat: Infinity,
      ease: 'easeInOut',
    },
  },
};

// Seat badge pulse (dynamic based on availability)
export const seatBadgePulse: Variants = {
  low: {
    scale: [1, 1.05, 1],
    boxShadow: [
      '0 0 0 0 rgba(239, 68, 68, 0.7)',
      '0 0 0 10px rgba(239, 68, 68, 0)',
      '0 0 0 0 rgba(239, 68, 68, 0)',
    ],
    transition: {
      duration: 1.5,
      repeat: Infinity,
    },
  },
  medium: {
    scale: 1,
  },
  high: {
    scale: 1,
  },
};

// Price tag reveal
export const priceReveal: Variants = {
  hidden: {
    opacity: 0,
    scale: 0.8,
    rotateX: -90,
  },
  visible: {
    opacity: 1,
    scale: 1,
    rotateX: 0,
    transition: {
      duration: 0.8,
      ease: easings.bounce,
      delay: 0.3,
    },
  },
};

// Loading state - CRED scanning orbit
export const scanningOrbit: Variants = {
  animate: {
    rotate: 360,
    transition: {
      duration: 3,
      repeat: Infinity,
      ease: 'linear',
    },
  },
};

// Confidence badge pop
export const badgePop: Variants = {
  hidden: {
    scale: 0,
    opacity: 0,
  },
  visible: {
    scale: 1,
    opacity: 1,
    transition: {
      type: 'spring',
      stiffness: 500,
      damping: 15,
      delay: 0.5,
    },
  },
};

// Glassmorphism layer float
export const glassFloat: Variants = {
  initial: {
    y: 0,
  },
  animate: {
    y: [-10, 10, -10],
    transition: {
      duration: 6,
      repeat: Infinity,
      ease: 'easeInOut',
    },
  },
};

// Navbar entrance
export const navbarSlide: Variants = {
  hidden: {
    y: -100,
    opacity: 0,
  },
  visible: {
    y: 0,
    opacity: 1,
    transition: {
      duration: 0.6,
      ease: easings.credEase,
    },
  },
};

// Search card float and glow
export const searchCardFloat: Variants = {
  initial: {
    y: 0,
    boxShadow: '0 8px 32px rgba(31, 38, 135, 0.37)',
  },
  animate: {
    y: [-5, 5, -5],
    boxShadow: [
      '0 8px 32px rgba(31, 38, 135, 0.37)',
      '0 12px 48px rgba(249, 178, 51, 0.2)',
      '0 8px 32px rgba(31, 38, 135, 0.37)',
    ],
    transition: {
      duration: 4,
      repeat: Infinity,
      ease: 'easeInOut',
    },
  },
};

// Shimmer text effect
export const shimmerText: Variants = {
  animate: {
    backgroundPosition: ['0% 50%', '100% 50%', '0% 50%'],
    transition: {
      duration: 3,
      repeat: Infinity,
      ease: 'linear',
    },
  },
};

// Modal/Overlay backdrop
export const backdropFade: Variants = {
  hidden: {
    opacity: 0,
  },
  visible: {
    opacity: 1,
    transition: {
      duration: 0.3,
    },
  },
};

// Modal content
export const modalSlide: Variants = {
  hidden: {
    opacity: 0,
    y: 100,
    scale: 0.9,
  },
  visible: {
    opacity: 1,
    y: 0,
    scale: 1,
    transition: {
      duration: 0.4,
      ease: easings.credEase,
    },
  },
  exit: {
    opacity: 0,
    y: 100,
    scale: 0.9,
    transition: {
      duration: 0.3,
    },
  },
};

// ==================== UTILITY FUNCTIONS ====================

/**
 * Generate stagger animation with custom delay
 */
export const generateStagger = (childCount: number, baseDelay: number = 0.1) => ({
  visible: {
    transition: {
      staggerChildren: baseDelay,
      delayChildren: 0.2,
    },
  },
});

/**
 * Create custom hover animation
 */
export const createHover = (
  scale: number = 1.05,
  y: number = -5,
  shadowColor: string = 'rgba(249, 178, 51, 0.3)'
) => ({
  rest: {
    scale: 1,
    y: 0,
  },
  hover: {
    scale,
    y,
    boxShadow: `0 20px 60px ${shadowColor}`,
    transition: {
      duration: 0.3,
      ease: easings.snappy,
    },
  },
});

/**
 * Page transition wrapper
 */
export const pageTransition: Variants = {
  initial: {
    opacity: 0,
    y: 20,
  },
  animate: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.6,
      ease: easings.credEase,
    },
  },
  exit: {
    opacity: 0,
    y: -20,
    transition: {
      duration: 0.4,
    },
  },
};
