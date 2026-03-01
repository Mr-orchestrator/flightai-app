'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import AnimatedBackground from '@/components/AnimatedBackground';
import Navbar from '@/components/Navbar';
import AutoPackageSection from '@/components/AutoPackageSection';
import { getAirports } from '@/lib/api';
import type { Airport } from '@/lib/api';
import { isAuthenticated, getCurrentUser, logout as doLogout } from '@/lib/auth';

export default function Home() {
  const [airports, setAirports] = useState<Airport[]>([]);

  // Auth state
  const [isAuthed, setIsAuthed] = useState(false);
  const [userName, setUserName] = useState<string | null>(null);

  useEffect(() => {
    // Load airports on mount
    getAirports()
      .then(setAirports)
      .catch((err) => {
        console.error('Failed to load airports:', err);
      });

    // Check auth state
    const authed = isAuthenticated();
    setIsAuthed(authed);
    if (authed) {
      const user = getCurrentUser();
      setUserName(user?.name || null);
    }
  }, []);

  const handleLogout = () => {
    doLogout();
    setIsAuthed(false);
    setUserName(null);
  };

  return (
    <main className="min-h-screen">
      <AnimatedBackground />
      <Navbar
        isAuthenticated={isAuthed}
        userName={userName}
        onLogout={handleLogout}
      />

      {/* Hero Section */}
      <section className="relative min-h-screen flex items-center justify-center px-6 pt-32">
        <div className="max-w-7xl mx-auto w-full">
          <motion.div
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 1, ease: [0.6, 0.01, 0.05, 0.9] }}
            className="text-center mb-16"
          >
            <motion.div
              className="inline-block mb-6"
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ duration: 0.6, delay: 0.2, type: 'spring' }}
            >
              <div className="px-6 py-3 rounded-full bg-gradient-gold/10 border border-gold-500/30">
                <span className="text-gold-400 font-bold text-sm tracking-wider">
                  AI-POWERED LUXURY BOOKING
                </span>
              </div>
            </motion.div>

            <h1 className="text-6xl md:text-7xl lg:text-8xl font-display font-black mb-6">
              <span className="block text-white">Your Next</span>
              <span className="block text-gradient-gold">Adventure Awaits</span>
            </h1>

            <p className="text-xl md:text-2xl text-premium-mist/70 max-w-3xl mx-auto">
              Real-time flights, hotels & activities powered by Amadeus + AI curation
            </p>
          </motion.div>

          {/* AI Auto Package Section — primary feature */}
          <div id="packages">
            <AutoPackageSection
              originIata=""
              airports={airports}
              isAuthenticated={isAuthed}
            />
          </div>
        </div>
      </section>
    </main>
  );
}
