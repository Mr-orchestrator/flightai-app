/**
 * Premium Navbar Component
 * Lufthansa-inspired navigation with glow intro
 */

'use client';

import { motion } from 'framer-motion';
import { navbarSlide } from '@/lib/motion';
import { FiUser, FiPhone, FiMap } from 'react-icons/fi';

export default function Navbar() {
  return (
    <motion.nav
      className="fixed top-0 left-0 right-0 z-50 bg-gradient-to-b from-premium-bg/95 to-transparent backdrop-blur-xl border-b border-premium-border/50"
      variants={navbarSlide}
      initial="hidden"
      animate="visible"
    >
      <div className="max-w-7xl mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          {/* Logo Section */}
          <motion.div
            className="flex items-center gap-4"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.8, delay: 0.2 }}
          >
            {/* Logo Icon with Glow */}
            <motion.div
              className="relative w-14 h-14 rounded-2xl bg-gradient-gold flex items-center justify-center shadow-glow"
              whileHover={{ scale: 1.05, rotate: 5 }}
              transition={{ type: 'spring', stiffness: 400, damping: 10 }}
            >
              <span className="text-3xl">✈️</span>
              
              {/* Animated glow ring */}
              <motion.div
                className="absolute inset-0 rounded-2xl border-2 border-gold-500"
                animate={{
                  scale: [1, 1.2, 1],
                  opacity: [0.8, 0.3, 0.8],
                }}
                transition={{
                  duration: 2,
                  repeat: Infinity,
                  ease: 'easeInOut',
                }}
              />
            </motion.div>

            {/* Brand Name */}
            <div>
              <motion.h1
                className="text-2xl font-display font-black text-transparent bg-clip-text bg-gradient-to-r from-gold-400 to-gold-600"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 1, delay: 0.4 }}
              >
                FlightAI
              </motion.h1>
              <motion.p
                className="text-xs text-gold-500/80 font-semibold tracking-wider uppercase"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 1, delay: 0.6 }}
              >
                Premium Booking
              </motion.p>
            </div>
          </motion.div>

          {/* Navigation Links */}
          <motion.div
            className="hidden md:flex items-center gap-8"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.8, delay: 0.3 }}
          >
            <NavLink icon={<FiMap />} label="My Trips" />
            <NavLink icon={<FiPhone />} label="Support" />
            
            {/* Profile Button with Premium Styling */}
            <motion.button
              className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-gold-500/20 to-gold-600/20 border border-gold-500/30 text-gold-400 font-semibold hover:shadow-glow transition-all duration-300"
              whileHover={{ scale: 1.05, y: -2 }}
              whileTap={{ scale: 0.95 }}
            >
              <FiUser className="w-4 h-4" />
              <span>Profile</span>
            </motion.button>
          </motion.div>
        </div>
      </div>

      {/* Bottom glow line */}
      <motion.div
        className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-gold-500/50 to-transparent"
        initial={{ scaleX: 0 }}
        animate={{ scaleX: 1 }}
        transition={{ duration: 1.5, delay: 0.5 }}
      />
    </motion.nav>
  );
}

// Navigation Link Component
interface NavLinkProps {
  icon: React.ReactNode;
  label: string;
}

function NavLink({ icon, label }: NavLinkProps) {
  return (
    <motion.a
      href="#"
      className="group relative flex items-center gap-2 text-premium-mist/70 hover:text-gold-400 transition-colors duration-300 py-2"
      whileHover={{ y: -2 }}
    >
      <span className="text-lg">{icon}</span>
      <span className="font-medium">{label}</span>
      
      {/* Underline animation */}
      <motion.div
        className="absolute bottom-0 left-0 right-0 h-0.5 bg-gradient-to-r from-gold-500 to-gold-600"
        initial={{ scaleX: 0 }}
        whileHover={{ scaleX: 1 }}
        transition={{ duration: 0.3 }}
      />
    </motion.a>
  );
}
