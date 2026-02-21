'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { FiMail, FiLock, FiUser, FiMapPin, FiArrowLeft } from 'react-icons/fi';
import { signup, login, isAuthenticated } from '@/lib/auth';
import { getAirports } from '@/lib/api';
import type { Airport } from '@/lib/api';
import { useRouter } from 'next/navigation';
import AnimatedBackground from '@/components/AnimatedBackground';

type Tab = 'login' | 'signup';

export default function AuthPage() {
  const router = useRouter();
  const [tab, setTab] = useState<Tab>('login');
  const [airports, setAirports] = useState<Airport[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Form state
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [homeAirport, setHomeAirport] = useState('');

  useEffect(() => {
    if (isAuthenticated()) {
      router.push('/');
    }
    getAirports().then(setAirports).catch(() => {});
  }, [router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      if (tab === 'signup') {
        await signup({ email, password, name, home_airport: homeAirport || undefined });
      } else {
        await login({ email, password });
      }
      router.push('/');
    } catch (err: any) {
      const msg = err?.response?.data?.detail || err?.message || 'Something went wrong';
      setError(msg);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main className="min-h-screen relative flex items-center justify-center px-6">
      <AnimatedBackground />

      <motion.div
        initial={{ opacity: 0, y: 30, scale: 0.95 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ duration: 0.8, ease: [0.6, 0.01, 0.05, 0.9] }}
        className="relative w-full max-w-md"
      >
        {/* Back button */}
        <motion.button
          onClick={() => router.push('/')}
          className="mb-6 flex items-center gap-2 text-premium-mist/60 hover:text-gold-400 transition-colors"
          whileHover={{ x: -4 }}
        >
          <FiArrowLeft /> Back to search
        </motion.button>

        {/* Glass card */}
        <div className="relative bg-gradient-glass backdrop-blur-2xl rounded-luxury border border-gold-500/20 shadow-luxury overflow-hidden">
          {/* Gold top border */}
          <motion.div
            className="absolute top-0 left-0 right-0 h-1 bg-gradient-gold"
            initial={{ scaleX: 0 }}
            animate={{ scaleX: 1 }}
            transition={{ duration: 1.2, ease: 'easeOut' }}
          />

          <div className="p-8">
            {/* Header */}
            <div className="text-center mb-8">
              <h1 className="text-3xl font-display font-black text-white mb-2">
                {tab === 'login' ? 'Welcome Back' : 'Join FlightAI'}
              </h1>
              <p className="text-premium-mist/60">
                {tab === 'login'
                  ? 'Sign in to access personalized packages'
                  : 'Create an account for AI-powered travel'}
              </p>
            </div>

            {/* Tab switcher */}
            <div className="flex mb-8 bg-premium-surface/50 rounded-xl p-1">
              {(['login', 'signup'] as Tab[]).map((t) => (
                <button
                  key={t}
                  onClick={() => { setTab(t); setError(null); }}
                  className={`flex-1 py-3 rounded-lg font-semibold text-sm uppercase tracking-wider transition-all duration-300 ${
                    tab === t
                      ? 'bg-gradient-gold text-navy-950 shadow-glow'
                      : 'text-premium-mist/60 hover:text-white'
                  }`}
                >
                  {t === 'login' ? 'Sign In' : 'Sign Up'}
                </button>
              ))}
            </div>

            {/* Error */}
            <AnimatePresence>
              {error && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  className="mb-6 p-4 bg-red-500/10 border border-red-500/30 rounded-xl"
                >
                  <p className="text-red-400 text-sm text-center">{error}</p>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Form */}
            <form onSubmit={handleSubmit} className="space-y-5">
              <AnimatePresence mode="wait">
                {tab === 'signup' && (
                  <motion.div
                    key="name-field"
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    transition={{ duration: 0.3 }}
                  >
                    <label className="block text-sm font-semibold text-premium-mist/80 mb-2 uppercase tracking-wide">
                      <FiUser className="inline mr-2" /> Full Name
                    </label>
                    <input
                      type="text"
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      placeholder="Your full name"
                      required={tab === 'signup'}
                      className="w-full px-5 py-3.5 bg-premium-surface/50 border-2 border-premium-border rounded-xl text-white font-medium placeholder-premium-mist/40 focus:border-gold-500 focus:ring-4 focus:ring-gold-500/20 transition-all duration-300 outline-none"
                    />
                  </motion.div>
                )}
              </AnimatePresence>

              <div>
                <label className="block text-sm font-semibold text-premium-mist/80 mb-2 uppercase tracking-wide">
                  <FiMail className="inline mr-2" /> Email
                </label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  required
                  className="w-full px-5 py-3.5 bg-premium-surface/50 border-2 border-premium-border rounded-xl text-white font-medium placeholder-premium-mist/40 focus:border-gold-500 focus:ring-4 focus:ring-gold-500/20 transition-all duration-300 outline-none"
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-premium-mist/80 mb-2 uppercase tracking-wide">
                  <FiLock className="inline mr-2" /> Password
                </label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Min 6 characters"
                  required
                  minLength={6}
                  className="w-full px-5 py-3.5 bg-premium-surface/50 border-2 border-premium-border rounded-xl text-white font-medium placeholder-premium-mist/40 focus:border-gold-500 focus:ring-4 focus:ring-gold-500/20 transition-all duration-300 outline-none"
                />
              </div>

              <AnimatePresence mode="wait">
                {tab === 'signup' && (
                  <motion.div
                    key="airport-field"
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    transition={{ duration: 0.3 }}
                  >
                    <label className="block text-sm font-semibold text-premium-mist/80 mb-2 uppercase tracking-wide">
                      <FiMapPin className="inline mr-2" /> Home Airport (Optional)
                    </label>
                    <select
                      value={homeAirport}
                      onChange={(e) => setHomeAirport(e.target.value)}
                      className="w-full px-5 py-3.5 bg-premium-surface/50 border-2 border-premium-border rounded-xl text-white font-medium focus:border-gold-500 focus:ring-4 focus:ring-gold-500/20 transition-all duration-300 outline-none appearance-none cursor-pointer"
                    >
                      <option value="">Select your home airport...</option>
                      {airports.map((airport) => (
                        <option key={airport.iata} value={airport.iata}>
                          {airport.iata} - {airport.city}
                        </option>
                      ))}
                    </select>
                  </motion.div>
                )}
              </AnimatePresence>

              {/* Submit button */}
              <motion.button
                type="submit"
                disabled={isLoading}
                className="relative w-full px-8 py-4 bg-gradient-gold rounded-xl font-display font-bold text-lg text-navy-950 shadow-glow disabled:opacity-50 disabled:cursor-not-allowed overflow-hidden"
                whileHover={{ scale: isLoading ? 1 : 1.02, y: isLoading ? 0 : -2 }}
                whileTap={{ scale: isLoading ? 1 : 0.98 }}
              >
                {/* Shimmer */}
                <motion.div
                  className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent"
                  animate={{ x: ['-200%', '200%'] }}
                  transition={{ duration: 2, repeat: Infinity, repeatDelay: 1 }}
                />
                <span className="relative flex items-center justify-center gap-2">
                  {isLoading ? (
                    <>
                      <motion.div
                        className="w-5 h-5 border-3 border-navy-950/30 border-t-navy-950 rounded-full"
                        animate={{ rotate: 360 }}
                        transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                      />
                      {tab === 'login' ? 'Signing in...' : 'Creating account...'}
                    </>
                  ) : (
                    tab === 'login' ? 'Sign In' : 'Create Account'
                  )}
                </span>
              </motion.button>
            </form>
          </div>
        </div>
      </motion.div>
    </main>
  );
}
