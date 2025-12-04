/**
 * Premium Floating Search Card
 * CRED-style glassmorphism with elevation and glow
 */

'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { searchCardFloat, staggerContainer, staggerItem } from '@/lib/motion';
import { FiSearch, FiMapPin } from 'react-icons/fi';

interface SearchCardProps {
  airports: Array<{ iata: string; city: string; name: string }>;
  onSearch: (origin: string, query: string) => void;
  isLoading?: boolean;
}

export default function SearchCard({ airports, onSearch, isLoading = false }: SearchCardProps) {
  const [origin, setOrigin] = useState('');
  const [query, setQuery] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (origin && query) {
      onSearch(origin, query);
    }
  };

  return (
    <motion.div
      className="relative max-w-4xl mx-auto"
      variants={searchCardFloat}
      initial="initial"
      animate="animate"
    >
      {/* Glassmorphism Card with Premium Styling */}
      <motion.div
        className="relative bg-gradient-glass backdrop-blur-2xl rounded-luxury border border-gold-500/20 shadow-luxury overflow-hidden"
        variants={staggerContainer}
        initial="hidden"
        animate="visible"
      >
        {/* Gold top border animation */}
        <motion.div
          className="absolute top-0 left-0 right-0 h-1 bg-gradient-gold"
          initial={{ scaleX: 0 }}
          animate={{ scaleX: 1 }}
          transition={{ duration: 1.2, ease: 'easeOut' }}
        />

        {/* Inner glow effect */}
        <div className="absolute inset-0 bg-gradient-to-b from-gold-500/5 to-transparent pointer-events-none" />

        <div className="relative p-10">
          {/* Header */}
          <motion.div className="mb-8" variants={staggerItem}>
            <motion.div
              className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-gold-500/10 border border-gold-500/20 mb-4"
              whileHover={{ scale: 1.05 }}
            >
              <span className="w-2 h-2 rounded-full bg-gold-500 animate-pulse" />
              <span className="text-sm font-semibold text-gold-400 uppercase tracking-wider">
                AI-Powered Search
              </span>
            </motion.div>

            <h2 className="text-4xl md:text-5xl font-display font-black text-white mb-3">
              Where to next?
            </h2>
            <p className="text-lg text-premium-mist/60">
              Describe your trip naturally — let AI handle the rest
            </p>
          </motion.div>

          {/* Search Form */}
          <form onSubmit={handleSubmit}>
            <motion.div className="space-y-6" variants={staggerContainer}>
              {/* Origin Selection */}
              <motion.div variants={staggerItem}>
                <label className="block text-sm font-semibold text-premium-mist/80 mb-3 uppercase tracking-wide">
                  <FiMapPin className="inline mr-2" />
                  Departure From
                </label>
                <div className="relative group">
                  <select
                    value={origin}
                    onChange={(e) => setOrigin(e.target.value)}
                    className="w-full px-6 py-4 bg-premium-surface/50 border-2 border-premium-border rounded-2xl text-white font-medium placeholder-premium-mist/40 focus:border-gold-500 focus:ring-4 focus:ring-gold-500/20 transition-all duration-300 outline-none backdrop-blur-xl appearance-none cursor-pointer"
                    required
                  >
                    <option value="">Select your departure city...</option>
                    {airports.map((airport) => (
                      <option key={airport.iata} value={airport.iata}>
                        {airport.iata} - {airport.city}
                      </option>
                    ))}
                  </select>
                  {/* Custom dropdown arrow */}
                  <div className="absolute right-6 top-1/2 -translate-y-1/2 pointer-events-none">
                    <svg className="w-5 h-5 text-gold-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </div>

                  {/* Glow effect on focus */}
                  <div className="absolute inset-0 rounded-2xl bg-gold-500/10 opacity-0 group-focus-within:opacity-100 transition-opacity duration-300 -z-10 blur-xl" />
                </div>
              </motion.div>

              {/* Trip Description */}
              <motion.div variants={staggerItem}>
                <label className="block text-sm font-semibold text-premium-mist/80 mb-3 uppercase tracking-wide">
                  <FiSearch className="inline mr-2" />
                  Describe Your Trip
                </label>
                <div className="relative group">
                  <textarea
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="e.g., 7 days in Dubai, weekend trip to Paris, 2 weeks in Switzerland..."
                    rows={4}
                    className="w-full px-6 py-4 bg-premium-surface/50 border-2 border-premium-border rounded-2xl text-white font-medium placeholder-premium-mist/40 focus:border-gold-500 focus:ring-4 focus:ring-gold-500/20 transition-all duration-300 outline-none backdrop-blur-xl resize-none"
                    required
                  />

                  {/* Glow effect on focus */}
                  <div className="absolute inset-0 rounded-2xl bg-gold-500/10 opacity-0 group-focus-within:opacity-100 transition-opacity duration-300 -z-10 blur-xl" />
                </div>

                {/* AI suggestion chips */}
                <div className="flex flex-wrap gap-2 mt-3">
                  {['7 days in Dubai', 'Weekend in Goa', '2 weeks in Europe'].map((suggestion) => (
                    <motion.button
                      key={suggestion}
                      type="button"
                      onClick={() => setQuery(suggestion)}
                      className="px-3 py-1.5 text-xs font-medium text-gold-400/70 bg-gold-500/5 border border-gold-500/20 rounded-full hover:bg-gold-500/10 hover:text-gold-400 transition-colors duration-200"
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                    >
                      {suggestion}
                    </motion.button>
                  ))}
                </div>
              </motion.div>

              {/* Submit Button with Premium Animation */}
              <motion.div variants={staggerItem}>
                <motion.button
                  type="submit"
                  disabled={isLoading || !origin || !query}
                  className="relative w-full px-8 py-5 bg-gradient-gold rounded-2xl font-display font-bold text-lg text-navy-950 shadow-glow disabled:opacity-50 disabled:cursor-not-allowed overflow-hidden group"
                  whileHover={{ scale: isLoading ? 1 : 1.02, y: isLoading ? 0 : -2 }}
                  whileTap={{ scale: isLoading ? 1 : 0.98 }}
                >
                  {/* Shimmer effect */}
                  <motion.div
                    className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent"
                    animate={{
                      x: ['-200%', '200%'],
                    }}
                    transition={{
                      duration: 2,
                      repeat: Infinity,
                      repeatDelay: 1,
                    }}
                  />

                  <span className="relative flex items-center justify-center gap-3">
                    {isLoading ? (
                      <>
                        <motion.div
                          className="w-5 h-5 border-3 border-navy-950/30 border-t-navy-950 rounded-full"
                          animate={{ rotate: 360 }}
                          transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                        />
                        Extracting Trip Details...
                      </>
                    ) : (
                      <>
                        <FiSearch className="w-6 h-6" />
                        Extract Trip Details with AI
                      </>
                    )}
                  </span>

                  {/* Ripple effect on click */}
                  <AnimatePresence>
                    {!isLoading && (
                      <motion.div
                        className="absolute inset-0 bg-white/20 rounded-2xl"
                        initial={{ scale: 0, opacity: 1 }}
                        whileTap={{ scale: 2, opacity: 0 }}
                        transition={{ duration: 0.6 }}
                      />
                    )}
                  </AnimatePresence>
                </motion.button>
              </motion.div>
            </motion.div>
          </form>

          {/* Decorative elements */}
          <div className="absolute -bottom-10 -right-10 w-40 h-40 bg-gold-500/10 rounded-full blur-3xl pointer-events-none" />
          <div className="absolute -top-10 -left-10 w-40 h-40 bg-navy-500/10 rounded-full blur-3xl pointer-events-none" />
        </div>
      </motion.div>

      {/* Floating particles around card */}
      <motion.div
        className="absolute -top-4 -right-4 w-3 h-3 rounded-full bg-gold-500"
        animate={{
          y: [-10, 10, -10],
          opacity: [0.5, 1, 0.5],
        }}
        transition={{
          duration: 3,
          repeat: Infinity,
          ease: 'easeInOut',
        }}
      />
      <motion.div
        className="absolute -bottom-4 -left-4 w-2 h-2 rounded-full bg-gold-400"
        animate={{
          y: [10, -10, 10],
          opacity: [0.3, 0.8, 0.3],
        }}
        transition={{
          duration: 4,
          repeat: Infinity,
          ease: 'easeInOut',
          delay: 1,
        }}
      />
    </motion.div>
  );
}
