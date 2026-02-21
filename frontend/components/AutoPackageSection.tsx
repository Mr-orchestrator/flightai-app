'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { staggerContainer, staggerItem } from '@/lib/motion';
import {
  FiPackage, FiStar, FiMapPin, FiCalendar,
  FiChevronDown, FiChevronUp, FiSun, FiCamera,
  FiHeart, FiDollarSign, FiClock, FiCheck,
} from 'react-icons/fi';
import { fetchAutoPackages } from '@/lib/api';
import type { TravelPackage } from '@/lib/api';

interface AutoPackageSectionProps {
  originIata: string;
  airports: Array<{ iata: string; city: string }>;
  isAuthenticated: boolean;
}

const INTEREST_OPTIONS = [
  { id: 'beach', label: 'Beach', icon: <FiSun className="w-4 h-4" /> },
  { id: 'culture', label: 'Culture', icon: <FiCamera className="w-4 h-4" /> },
  { id: 'adventure', label: 'Adventure', icon: <FiMapPin className="w-4 h-4" /> },
  { id: 'food', label: 'Food & Dining', icon: <FiHeart className="w-4 h-4" /> },
  { id: 'shopping', label: 'Shopping', icon: <FiPackage className="w-4 h-4" /> },
  { id: 'nature', label: 'Nature', icon: <FiStar className="w-4 h-4" /> },
];

const TIER_STYLES: Record<string, { border: string; badge: string; glow: string; accent: string }> = {
  budget: {
    border: 'border-green-500/30',
    badge: 'bg-green-500/20 text-green-400 border-green-500/30',
    glow: 'hover:shadow-[0_0_30px_rgba(34,197,94,0.15)]',
    accent: 'text-green-400',
  },
  standard: {
    border: 'border-gold-500/30',
    badge: 'bg-gold-500/20 text-gold-400 border-gold-500/30',
    glow: 'hover:shadow-[0_0_30px_rgba(249,178,51,0.15)]',
    accent: 'text-gold-400',
  },
  premium: {
    border: 'border-purple-500/30',
    badge: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
    glow: 'hover:shadow-[0_0_30px_rgba(168,85,247,0.15)]',
    accent: 'text-purple-400',
  },
};

function formatINR(amount: number): string {
  return new Intl.NumberFormat('en-IN', { maximumFractionDigits: 0 }).format(amount);
}

export default function AutoPackageSection({ originIata, airports, isAuthenticated: isAuth }: AutoPackageSectionProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [packages, setPackages] = useState<TravelPackage[]>([]);
  const [note, setNote] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [selectedInterests, setSelectedInterests] = useState<string[]>([]);
  const [budgetLevel, setBudgetLevel] = useState('moderate');
  const [destination, setDestination] = useState('');
  const [duration, setDuration] = useState(7);
  const [expandedTier, setExpandedTier] = useState<string | null>(null);
  const [activeTierFilter, setActiveTierFilter] = useState<string | null>(null);
  const [modelUsed, setModelUsed] = useState<string | null>(null);

  const toggleInterest = (id: string) => {
    setSelectedInterests((prev) =>
      prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id]
    );
  };

  const handleGenerate = async () => {
    setIsLoading(true);
    setError(null);
    setPackages([]);
    setNote('');

    try {
      const result = await fetchAutoPackages({
        destination: destination || undefined,
        duration_days: duration,
        preferences: {
          interests: selectedInterests.length > 0 ? selectedInterests : undefined,
          budget_level: budgetLevel,
          travel_style: 'mixed',
        },
      });

      if (result.success && result.packages.length > 0) {
        setPackages(result.packages);
        setNote(result.personalization_note);
        setModelUsed(result.model_used);
      } else {
        setError(result.error || 'No packages generated');
      }
    } catch (err: any) {
      setError(err.message || 'Failed to generate packages');
    } finally {
      setIsLoading(false);
    }
  };

  const filteredPackages = activeTierFilter
    ? packages.filter((p) => p.tier === activeTierFilter)
    : packages;

  // Not authenticated — show prompt
  if (!isAuth) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, delay: 0.3 }}
        className="mt-16 max-w-4xl mx-auto"
      >
        <div className="bg-gradient-glass backdrop-blur-2xl rounded-luxury border border-gold-500/20 shadow-luxury p-10 text-center">
          <FiPackage className="w-12 h-12 text-gold-400 mx-auto mb-4" />
          <h3 className="text-2xl font-display font-bold text-white mb-3">
            AI Travel Packages
          </h3>
          <p className="text-premium-mist/60 mb-6 max-w-md mx-auto">
            Sign in to unlock personalized travel packages powered by AI.
            We&apos;ll learn from your searches to create perfect itineraries.
          </p>
          <a
            href="/auth"
            className="inline-block px-8 py-3 bg-gradient-gold rounded-xl font-display font-bold text-navy-950 shadow-glow hover:scale-105 transition-transform"
          >
            Sign In to Get Started
          </a>
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.8, delay: 0.3 }}
      className="mt-16 max-w-7xl mx-auto"
    >
      <div className="bg-gradient-glass backdrop-blur-2xl rounded-luxury border border-gold-500/20 shadow-luxury overflow-hidden">
        {/* Gold top border */}
        <motion.div
          className="h-1 bg-gradient-gold"
          initial={{ scaleX: 0 }}
          animate={{ scaleX: 1 }}
          transition={{ duration: 1.2, ease: 'easeOut' }}
        />

        <div className="p-8 md:p-10">
          {/* Header */}
          <div className="flex items-center gap-3 mb-8">
            <div className="p-3 rounded-xl bg-gold-500/10 border border-gold-500/20">
              <FiPackage className="w-6 h-6 text-gold-400" />
            </div>
            <div>
              <h2 className="text-3xl font-display font-bold text-white">
                AI Travel Packages
              </h2>
              <p className="text-premium-mist/60 mt-1">
                Personalized itineraries crafted from your travel history
              </p>
            </div>
          </div>

          {/* Preferences */}
          <div className="space-y-6 mb-8">
            {/* Interests */}
            <div>
              <label className="block text-sm font-semibold text-premium-mist/80 mb-3 uppercase tracking-wide">
                Your Interests
              </label>
              <div className="flex flex-wrap gap-2">
                {INTEREST_OPTIONS.map((opt) => (
                  <motion.button
                    key={opt.id}
                    type="button"
                    onClick={() => toggleInterest(opt.id)}
                    className={`flex items-center gap-2 px-4 py-2 rounded-full border font-medium text-sm transition-all duration-200 ${
                      selectedInterests.includes(opt.id)
                        ? 'bg-gold-500/20 border-gold-500/50 text-gold-400'
                        : 'bg-premium-surface/30 border-premium-border/50 text-premium-mist/60 hover:border-gold-500/30 hover:text-gold-400/80'
                    }`}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                  >
                    {opt.icon}
                    {opt.label}
                  </motion.button>
                ))}
              </div>
            </div>

            {/* Destination + Duration + Budget row */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-semibold text-premium-mist/80 mb-2 uppercase tracking-wide">
                  <FiMapPin className="inline mr-1" /> Destination (Optional)
                </label>
                <input
                  type="text"
                  value={destination}
                  onChange={(e) => setDestination(e.target.value)}
                  placeholder="e.g. Dubai, Paris, Tokyo"
                  className="w-full px-4 py-3 bg-premium-surface/50 border-2 border-premium-border rounded-xl text-white font-medium placeholder-premium-mist/40 focus:border-gold-500 focus:ring-4 focus:ring-gold-500/20 transition-all duration-300 outline-none"
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-premium-mist/80 mb-2 uppercase tracking-wide">
                  <FiCalendar className="inline mr-1" /> Duration (days)
                </label>
                <input
                  type="number"
                  min={2}
                  max={30}
                  value={duration}
                  onChange={(e) => setDuration(parseInt(e.target.value) || 7)}
                  className="w-full px-4 py-3 bg-premium-surface/50 border-2 border-premium-border rounded-xl text-white font-medium focus:border-gold-500 focus:ring-4 focus:ring-gold-500/20 transition-all duration-300 outline-none"
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-premium-mist/80 mb-2 uppercase tracking-wide">
                  <FiDollarSign className="inline mr-1" /> Budget Level
                </label>
                <select
                  value={budgetLevel}
                  onChange={(e) => setBudgetLevel(e.target.value)}
                  className="w-full px-4 py-3 bg-premium-surface/50 border-2 border-premium-border rounded-xl text-white font-medium focus:border-gold-500 focus:ring-4 focus:ring-gold-500/20 transition-all duration-300 outline-none appearance-none cursor-pointer"
                >
                  <option value="budget">Budget</option>
                  <option value="moderate">Moderate</option>
                  <option value="luxury">Luxury</option>
                </select>
              </div>
            </div>
          </div>

          {/* Generate button */}
          <motion.button
            onClick={handleGenerate}
            disabled={isLoading}
            className="relative w-full px-8 py-4 bg-gradient-gold rounded-xl font-display font-bold text-lg text-navy-950 shadow-glow disabled:opacity-50 disabled:cursor-not-allowed overflow-hidden"
            whileHover={{ scale: isLoading ? 1 : 1.02, y: isLoading ? 0 : -2 }}
            whileTap={{ scale: isLoading ? 1 : 0.98 }}
          >
            <motion.div
              className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent"
              animate={{ x: ['-200%', '200%'] }}
              transition={{ duration: 2, repeat: Infinity, repeatDelay: 1 }}
            />
            <span className="relative flex items-center justify-center gap-3">
              {isLoading ? (
                <>
                  <motion.div
                    className="w-5 h-5 border-3 border-navy-950/30 border-t-navy-950 rounded-full"
                    animate={{ rotate: 360 }}
                    transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                  />
                  Generating packages with AI...
                </>
              ) : (
                <>
                  <FiPackage className="w-5 h-5" />
                  Generate AI Packages
                </>
              )}
            </span>
          </motion.button>

          {/* Error */}
          <AnimatePresence>
            {error && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                className="mt-6 p-4 bg-red-500/10 border border-red-500/30 rounded-xl"
              >
                <p className="text-red-400 text-center text-sm">{error}</p>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Results */}
          {packages.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
              className="mt-10"
            >
              {/* Tier filter tabs */}
              <div className="flex gap-2 mb-8">
                {[
                  { key: null, label: 'All' },
                  { key: 'budget', label: 'Budget' },
                  { key: 'standard', label: 'Standard' },
                  { key: 'premium', label: 'Premium' },
                ].map((tab) => (
                  <button
                    key={tab.label}
                    onClick={() => setActiveTierFilter(tab.key)}
                    className={`px-4 py-2 rounded-lg font-semibold text-sm transition-all ${
                      activeTierFilter === tab.key
                        ? 'bg-gold-500/20 text-gold-400 border border-gold-500/30'
                        : 'text-premium-mist/60 hover:text-white bg-premium-surface/30 border border-transparent'
                    }`}
                  >
                    {tab.label}
                  </button>
                ))}
              </div>

              {/* Package cards */}
              <motion.div
                className="grid grid-cols-1 lg:grid-cols-3 gap-6"
                variants={staggerContainer}
                initial="hidden"
                animate="visible"
              >
                {filteredPackages.map((pkg, index) => {
                  const styles = TIER_STYLES[pkg.tier] || TIER_STYLES.standard;
                  const isExpanded = expandedTier === pkg.tier;

                  return (
                    <motion.div
                      key={pkg.tier}
                      variants={staggerItem}
                      className={`relative bg-premium-surface/30 backdrop-blur-xl rounded-2xl border ${styles.border} ${styles.glow} transition-all duration-300 overflow-hidden`}
                    >
                      {/* Tier badge */}
                      <div className="p-6">
                        <div className={`inline-block px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider border ${styles.badge} mb-4`}>
                          {pkg.tier}
                        </div>

                        <h3 className="text-xl font-display font-bold text-white mb-1">
                          {pkg.name}
                        </h3>
                        <p className="text-premium-mist/60 text-sm mb-4">
                          {pkg.tagline}
                        </p>

                        {/* Price */}
                        <div className="mb-4">
                          <div className="text-xs text-premium-mist/50 uppercase tracking-wider mb-1">
                            Estimated Total
                          </div>
                          <div className={`text-3xl font-display font-black ${styles.accent}`}>
                            INR {formatINR(pkg.estimated_total_inr)}
                          </div>
                        </div>

                        {/* Hotel */}
                        <div className="p-3 bg-premium-surface/40 rounded-xl mb-3">
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-sm font-semibold text-white">{pkg.hotel.name}</span>
                            <div className="flex">
                              {Array.from({ length: pkg.hotel.star_rating }).map((_, i) => (
                                <FiStar key={i} className="w-3 h-3 text-gold-400 fill-gold-400" />
                              ))}
                            </div>
                          </div>
                          <div className="text-xs text-premium-mist/50">
                            {pkg.hotel.area} &middot; INR {formatINR(pkg.hotel.price_per_night_inr)}/night
                          </div>
                        </div>

                        {/* Flight class */}
                        <div className="p-3 bg-premium-surface/40 rounded-xl mb-3">
                          <div className="flex items-center justify-between">
                            <span className="text-sm text-white">
                              {pkg.flights.travel_class.replace('_', ' ')}
                            </span>
                            <span className="text-xs text-premium-mist/50">
                              ~INR {formatINR(pkg.flights.estimated_price_inr)}
                            </span>
                          </div>
                        </div>

                        {/* Highlights */}
                        {pkg.highlights && pkg.highlights.length > 0 && (
                          <div className="flex flex-wrap gap-1.5 mb-4">
                            {pkg.highlights.slice(0, 3).map((h, i) => (
                              <span
                                key={i}
                                className="text-xs px-2 py-1 bg-premium-surface/40 rounded-md text-premium-mist/70"
                              >
                                {h}
                              </span>
                            ))}
                          </div>
                        )}

                        {/* Inclusions */}
                        {pkg.inclusions && pkg.inclusions.length > 0 && (
                          <div className="space-y-1 mb-4">
                            {pkg.inclusions.map((inc, i) => (
                              <div key={i} className="flex items-center gap-2 text-xs text-premium-mist/60">
                                <FiCheck className="w-3 h-3 text-green-400 flex-shrink-0" />
                                {inc}
                              </div>
                            ))}
                          </div>
                        )}

                        {/* Expand itinerary button */}
                        <button
                          onClick={() => setExpandedTier(isExpanded ? null : pkg.tier)}
                          className="w-full flex items-center justify-center gap-2 py-2 text-sm font-semibold text-gold-400 hover:text-gold-300 transition-colors"
                        >
                          {isExpanded ? (
                            <>Hide Itinerary <FiChevronUp /></>
                          ) : (
                            <>View {pkg.duration_days}-Day Itinerary <FiChevronDown /></>
                          )}
                        </button>
                      </div>

                      {/* Expandable itinerary */}
                      <AnimatePresence>
                        {isExpanded && pkg.daily_itinerary && (
                          <motion.div
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: 'auto', opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                            transition={{ duration: 0.3 }}
                            className="overflow-hidden"
                          >
                            <div className="px-6 pb-6 space-y-3">
                              <div className="h-px bg-premium-border/50" />
                              {pkg.daily_itinerary.map((day) => (
                                <div
                                  key={day.day}
                                  className="p-3 bg-premium-surface/20 rounded-xl"
                                >
                                  <div className="text-sm font-semibold text-white mb-2">
                                    Day {day.day}: {day.title}
                                  </div>
                                  <div className="space-y-1.5">
                                    {day.activities.map((act, ai) => (
                                      <div key={ai} className="flex items-start gap-2 text-xs">
                                        <FiClock className="w-3 h-3 text-gold-400 mt-0.5 flex-shrink-0" />
                                        <div>
                                          <span className="text-premium-mist/50 capitalize">{act.time}: </span>
                                          <span className="text-premium-mist/80">{act.activity}</span>
                                          {act.estimated_cost_inr > 0 && (
                                            <span className="text-premium-mist/40 ml-1">
                                              (INR {formatINR(act.estimated_cost_inr)})
                                            </span>
                                          )}
                                        </div>
                                      </div>
                                    ))}
                                  </div>
                                </div>
                              ))}
                            </div>
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </motion.div>
                  );
                })}
              </motion.div>

              {/* Personalization note */}
              {note && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 0.5 }}
                  className="mt-8 p-4 bg-gold-500/5 border border-gold-500/20 rounded-xl"
                >
                  <div className="flex items-start gap-3">
                    <FiStar className="w-5 h-5 text-gold-400 mt-0.5 flex-shrink-0" />
                    <div>
                      <div className="text-sm font-semibold text-gold-400 mb-1">AI Personalization Note</div>
                      <p className="text-sm text-premium-mist/70">{note}</p>
                      {modelUsed && (
                        <p className="text-xs text-premium-mist/40 mt-2">Powered by {modelUsed}</p>
                      )}
                    </div>
                  </div>
                </motion.div>
              )}
            </motion.div>
          )}
        </div>
      </div>
    </motion.div>
  );
}
