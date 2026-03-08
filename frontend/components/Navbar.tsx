/**
 * Premium Navbar Component
 * Lufthansa-inspired navigation with glow intro + auth UI
 */

'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { navbarSlide } from '@/lib/motion';
import { FiUser, FiPhone, FiMap, FiPackage, FiLogOut, FiMenu, FiX } from 'react-icons/fi';

interface NavbarProps {
  isAuthenticated?: boolean;
  userName?: string | null;
  onLogout?: () => void;
}

export default function Navbar({ isAuthenticated = false, userName, onLogout }: NavbarProps) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

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
          <motion.a
            href="/"
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
          </motion.a>

          {/* Navigation Links */}
          <motion.div
            className="hidden md:flex items-center gap-6"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.8, delay: 0.3 }}
          >
            <NavLink icon={<FiMap />} label="My Trips" href="/trips" />
            <NavLink icon={<FiPackage />} label="Packages" href="/#packages" />
            <NavLink icon={<FiPhone />} label="Support" href="#" />

            {isAuthenticated ? (
              <div className="flex items-center gap-3">
                <div className="text-sm text-premium-mist/70">
                  Hi, <span className="text-gold-400 font-semibold">{userName || 'Traveler'}</span>
                </div>
                <motion.button
                  onClick={onLogout}
                  className="flex items-center gap-2 px-4 py-2 rounded-xl bg-premium-surface/50 border border-premium-border text-premium-mist/70 font-medium hover:text-red-400 hover:border-red-500/30 transition-all duration-300"
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                >
                  <FiLogOut className="w-4 h-4" />
                  <span>Logout</span>
                </motion.button>
              </div>
            ) : (
              <div className="flex items-center gap-3">
                <motion.a
                  href="/auth"
                  className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-gold-500/20 to-gold-600/20 border border-gold-500/30 text-gold-400 font-semibold hover:shadow-glow transition-all duration-300"
                  whileHover={{ scale: 1.05, y: -2 }}
                  whileTap={{ scale: 0.95 }}
                >
                  <FiUser className="w-4 h-4" />
                  <span>Sign In</span>
                </motion.a>
              </div>
            )}
          </motion.div>

          {/* Mobile hamburger button */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden flex items-center justify-center w-10 h-10 rounded-xl bg-premium-surface/50 border border-premium-border text-premium-mist/70 hover:text-gold-400 transition-colors"
            aria-label="Toggle menu"
          >
            {mobileMenuOpen ? <FiX className="w-5 h-5" /> : <FiMenu className="w-5 h-5" />}
          </button>
        </div>

        {/* Mobile menu dropdown */}
        <AnimatePresence>
          {mobileMenuOpen && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.2 }}
              className="md:hidden overflow-hidden"
            >
              <div className="py-4 space-y-2 border-t border-premium-border/30 mt-2">
                <MobileNavLink icon={<FiMap />} label="My Trips" href="/trips" onClick={() => setMobileMenuOpen(false)} />
                <MobileNavLink icon={<FiPackage />} label="Packages" href="/#packages" onClick={() => setMobileMenuOpen(false)} />
                <MobileNavLink icon={<FiPhone />} label="Support" href="#" onClick={() => setMobileMenuOpen(false)} />

                {isAuthenticated ? (
                  <div className="pt-2 border-t border-premium-border/20 mt-2 space-y-2">
                    <div className="text-sm text-premium-mist/70 px-3">
                      Hi, <span className="text-gold-400 font-semibold">{userName || 'Traveler'}</span>
                    </div>
                    <button
                      onClick={() => { setMobileMenuOpen(false); onLogout?.(); }}
                      className="flex items-center gap-2 w-full px-3 py-2 rounded-xl text-premium-mist/70 hover:text-red-400 transition-colors"
                    >
                      <FiLogOut className="w-4 h-4" />
                      <span>Logout</span>
                    </button>
                  </div>
                ) : (
                  <div className="pt-2 border-t border-premium-border/20 mt-2">
                    <a
                      href="/auth"
                      onClick={() => setMobileMenuOpen(false)}
                      className="flex items-center gap-2 px-3 py-2 rounded-xl text-gold-400 font-semibold"
                    >
                      <FiUser className="w-4 h-4" />
                      <span>Sign In</span>
                    </a>
                  </div>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
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
  href: string;
}

function NavLink({ icon, label, href }: NavLinkProps) {
  return (
    <motion.a
      href={href}
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

// Mobile Navigation Link Component
function MobileNavLink({ icon, label, href, onClick }: NavLinkProps & { onClick: () => void }) {
  return (
    <a
      href={href}
      onClick={onClick}
      className="flex items-center gap-3 px-3 py-2.5 rounded-xl text-premium-mist/70 hover:text-gold-400 hover:bg-premium-surface/30 transition-colors"
    >
      <span className="text-lg">{icon}</span>
      <span className="font-medium">{label}</span>
    </a>
  );
}
