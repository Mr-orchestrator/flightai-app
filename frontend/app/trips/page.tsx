'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { FiMapPin, FiCalendar, FiArrowRight, FiPackage } from 'react-icons/fi';
import AnimatedBackground from '@/components/AnimatedBackground';
import Navbar from '@/components/Navbar';
import { getMyTrips } from '@/lib/api';
import type { SavedTrip } from '@/lib/api';
import { isAuthenticated, getCurrentUser, logout as doLogout } from '@/lib/auth';

function formatINR(amount: number): string {
  return new Intl.NumberFormat('en-IN', { maximumFractionDigits: 0 }).format(amount);
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return '';
  const d = new Date(dateStr + 'T00:00:00');
  return d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });
}

const TIER_COLORS: Record<string, string> = {
  budget: 'bg-green-500/20 text-green-400 border-green-500/30',
  standard: 'bg-gold-500/20 text-gold-400 border-gold-500/30',
  premium: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
};

export default function TripsPage() {
  const [trips, setTrips] = useState<SavedTrip[]>([]);
  const [loading, setLoading] = useState(true);
  const [isAuthed, setIsAuthed] = useState(false);
  const [userName, setUserName] = useState<string | null>(null);

  useEffect(() => {
    const authed = isAuthenticated();
    setIsAuthed(authed);
    if (authed) {
      const user = getCurrentUser();
      setUserName(user?.name || null);
      getMyTrips()
        .then(setTrips)
        .catch(console.error)
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
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
      <Navbar isAuthenticated={isAuthed} userName={userName} onLogout={handleLogout} />

      <section className="relative px-6 pt-32 pb-20">
        <div className="max-w-5xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <h1 className="text-4xl font-display font-black text-white mb-2">My Trips</h1>
            <p className="text-premium-mist/60 mb-8">Your saved travel packages</p>
          </motion.div>

          {!isAuthed ? (
            <div className="text-center py-20">
              <FiPackage className="w-12 h-12 text-premium-mist/30 mx-auto mb-4" />
              <p className="text-premium-mist/60 mb-4">Sign in to view your saved trips</p>
              <a
                href="/auth"
                className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-gold rounded-xl font-display font-bold text-navy-950"
              >
                Sign In
              </a>
            </div>
          ) : loading ? (
            <div className="text-center py-20">
              <div className="w-8 h-8 border-2 border-gold-400 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
              <p className="text-premium-mist/60">Loading your trips...</p>
            </div>
          ) : trips.length === 0 ? (
            <div className="text-center py-20">
              <FiMapPin className="w-12 h-12 text-premium-mist/30 mx-auto mb-4" />
              <p className="text-premium-mist/60 mb-4">No saved trips yet</p>
              <a
                href="/#packages"
                className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-gold rounded-xl font-display font-bold text-navy-950"
              >
                Generate Your First Package
              </a>
            </div>
          ) : (
            <div className="grid gap-4">
              {trips.map((trip, i) => (
                <motion.a
                  key={trip.id}
                  href={`/trips/${trip.id}`}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.05 }}
                  className="group block bg-gradient-glass backdrop-blur-xl rounded-2xl border border-premium-border/50 p-6 hover:border-gold-500/30 transition-all"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 rounded-xl bg-gold-500/10 flex items-center justify-center text-2xl">
                        {trip.destination_city?.slice(0, 2) === 'Du' ? '🏙️' :
                         trip.destination_city?.slice(0, 2) === 'Ba' ? '🏖️' :
                         trip.destination_city?.slice(0, 2) === 'To' ? '🗼' : '✈️'}
                      </div>
                      <div>
                        <h3 className="text-lg font-display font-bold text-white group-hover:text-gold-400 transition-colors">
                          {trip.destination_city || trip.destination_iata}
                        </h3>
                        <div className="flex items-center gap-3 text-sm text-premium-mist/60">
                          {trip.departure_date && (
                            <span className="flex items-center gap-1">
                              <FiCalendar className="w-3.5 h-3.5" />
                              {formatDate(trip.departure_date)} — {formatDate(trip.return_date)}
                            </span>
                          )}
                          <span className={`px-2 py-0.5 rounded-full border text-xs font-semibold ${TIER_COLORS[trip.tier] || TIER_COLORS.standard}`}>
                            {trip.tier}
                          </span>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      {trip.total_package_inr && (
                        <span className="text-lg font-display font-bold text-gold-400">
                          INR {formatINR(trip.total_package_inr)}
                        </span>
                      )}
                      <FiArrowRight className="w-5 h-5 text-premium-mist/40 group-hover:text-gold-400 transition-colors" />
                    </div>
                  </div>
                </motion.a>
              ))}
            </div>
          )}
        </div>
      </section>
    </main>
  );
}
