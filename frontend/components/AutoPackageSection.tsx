'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { staggerContainer, staggerItem } from '@/lib/motion';
import {
  FiPackage, FiStar, FiMapPin, FiCalendar,
  FiChevronDown, FiChevronUp, FiSun, FiCamera,
  FiHeart, FiDollarSign, FiClock, FiCheck,
  FiSearch, FiUsers, FiHome, FiZap, FiDatabase,
  FiX,
} from 'react-icons/fi';
import {
  fetchAutoPackages, fetchAutoPackagesStream, getOnboardingStatus, savePreferences,
  bookPackage, trackEngagement,
} from '@/lib/api';
import type {
  TravelPackage, AutoPackageResponse, ProgressEvent,
  BookPackageRequest, TrackEngagementRequest,
} from '@/lib/api';

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
  { id: 'nightlife', label: 'Nightlife', icon: <FiZap className="w-4 h-4" /> },
  { id: 'history', label: 'History', icon: <FiSearch className="w-4 h-4" /> },
];

const COMPANION_OPTIONS = [
  { id: 'solo', label: 'Solo' },
  { id: 'couple', label: 'Couple' },
  { id: 'family', label: 'Family' },
  { id: 'friends', label: 'Friends' },
];

const ACCOMMODATION_OPTIONS = [
  { id: 'hotel', label: 'Hotel' },
  { id: 'resort', label: 'Resort' },
  { id: 'hostel', label: 'Hostel' },
];

const FREQUENCY_OPTIONS = [
  { id: 'rarely', label: 'Rarely (0-1/year)' },
  { id: 'sometimes', label: 'Sometimes (2-3/year)' },
  { id: 'often', label: 'Often (4+/year)' },
];

const AIRLINE_OPTIONS = [
  { id: 'AI', label: 'Air India' },
  { id: '6E', label: 'IndiGo' },
  { id: 'UK', label: 'Vistara' },
  { id: 'EK', label: 'Emirates' },
  { id: 'QR', label: 'Qatar Airways' },
  { id: 'SQ', label: 'Singapore Airlines' },
  { id: 'BA', label: 'British Airways' },
  { id: 'LH', label: 'Lufthansa' },
];

const ONBOARDING_STEPS = 5;

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

function DataSourceBadge({ source }: { source?: string }) {
  if (source === 'amadeus') {
    return (
      <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
        <FiDatabase className="w-2.5 h-2.5" /> LIVE
      </span>
    );
  }
  if (source === 'amadeus_list') {
    return (
      <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-bold bg-sky-500/20 text-sky-400 border border-sky-500/30">
        <FiDatabase className="w-2.5 h-2.5" /> LISTED
      </span>
    );
  }
  if (source === 'estimated' || source === 'suggested') {
    return (
      <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-bold bg-amber-500/20 text-amber-400 border border-amber-500/30">
        AI EST.
      </span>
    );
  }
  return null;
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
  const [dataQuality, setDataQuality] = useState<string | null>(null);
  const [amadeusStats, setAmadeusStats] = useState<{ flights_found: number; hotels_found: number; activities_found: number } | null>(null);

  // Profile intelligence metadata
  const [bookingCount, setBookingCount] = useState(0);
  const [resolvedOrigin, setResolvedOrigin] = useState<{ iata: string; source: string } | null>(null);

  // Save trip state
  const [savingTier, setSavingTier] = useState<string | null>(null);
  const [savedTiers, setSavedTiers] = useState<Set<string>>(new Set());

  // Progress tracking
  const [progressPercent, setProgressPercent] = useState(0);
  const [progressMessage, setProgressMessage] = useState('');
  const [progressStep, setProgressStep] = useState('');
  const [abortStream, setAbortStream] = useState<(() => void) | null>(null);

  // Natural language input
  const [nlQuery, setNlQuery] = useState('');
  const [useNL, setUseNL] = useState(true);

  // Onboarding
  const [showOnboarding, setShowOnboarding] = useState(false);
  const [onboardingChecked, setOnboardingChecked] = useState(false);
  const [onboardingStep, setOnboardingStep] = useState(1);
  const [autoGenerateAfterOnboarding, setAutoGenerateAfterOnboarding] = useState(false);
  const [profileReady, setProfileReady] = useState(false); // returning user with prefs
  const [companions, setCompanions] = useState('');
  const [accommodation, setAccommodation] = useState('hotel');
  const [dreamDestinations, setDreamDestinations] = useState('');
  const [budgetMin, setBudgetMin] = useState(20000);
  const [budgetMax, setBudgetMax] = useState(100000);
  const [travelFrequency, setTravelFrequency] = useState('');
  const [preferredAirlines, setPreferredAirlines] = useState<string[]>([]);
  const [dietaryNeeds, setDietaryNeeds] = useState('');
  const [accessibilityNeeds, setAccessibilityNeeds] = useState('');

  // Check onboarding status on mount
  useEffect(() => {
    if (isAuth && !onboardingChecked) {
      getOnboardingStatus()
        .then((status) => {
          if (!status.onboarding_completed) {
            setShowOnboarding(true);
          } else if (status.has_preferences) {
            // Returning user with completed profile — mark ready for auto-suggest
            setProfileReady(true);
          }
          setOnboardingChecked(true);
        })
        .catch(() => setOnboardingChecked(true));
    }
  }, [isAuth, onboardingChecked]);

  // Auto-generate after onboarding completes
  useEffect(() => {
    if (autoGenerateAfterOnboarding && !isLoading) {
      setAutoGenerateAfterOnboarding(false);
      handleGenerate();
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [autoGenerateAfterOnboarding]);

  const toggleInterest = (id: string) => {
    setSelectedInterests((prev) =>
      prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id]
    );
  };

  const toggleAirline = (id: string) => {
    setPreferredAirlines((prev) =>
      prev.includes(id) ? prev.filter((a) => a !== id) : [...prev, id]
    );
  };

  const handleSaveOnboarding = async () => {
    try {
      await savePreferences({
        interests: selectedInterests,
        budget_level: budgetLevel,
        travel_style: 'mixed',
        preferred_destinations: dreamDestinations ? dreamDestinations.split(',').map(d => d.trim()) : [],
        travel_companions: companions || undefined,
        accommodation_preference: accommodation,
        budget_range_min: budgetMin,
        budget_range_max: budgetMax,
        travel_frequency: travelFrequency || undefined,
        preferred_airlines: preferredAirlines.length > 0 ? preferredAirlines : undefined,
        dietary_needs: dietaryNeeds ? dietaryNeeds.split(',').map(d => d.trim()) : undefined,
        accessibility_needs: accessibilityNeeds ? accessibilityNeeds.split(',').map(d => d.trim()) : undefined,
        onboarding_step: ONBOARDING_STEPS,
      });
      setShowOnboarding(false);
      setOnboardingStep(1);
      // Auto-generate personalized packages based on saved preferences
      setAutoGenerateAfterOnboarding(true);
    } catch {
      setShowOnboarding(false);
      setOnboardingStep(1);
    }
  };

  const handleGenerate = () => {
    // Cancel any in-flight stream
    if (abortStream) abortStream();

    setIsLoading(true);
    setError(null);
    setPackages([]);
    setNote('');
    setDataQuality(null);
    setAmadeusStats(null);
    setProgressPercent(0);
    setProgressMessage('Starting...');
    setProgressStep('');

    const requestPayload = {
      destination: destination || undefined,
      duration_days: duration,
      natural_language_query: useNL && nlQuery ? nlQuery : undefined,
      preferences: {
        interests: selectedInterests.length > 0 ? selectedInterests : undefined,
        budget_level: budgetLevel,
        travel_style: 'mixed' as const,
      },
    };

    const cancel = fetchAutoPackagesStream(
      requestPayload,
      // onProgress
      (event: ProgressEvent) => {
        setProgressPercent(event.percent);
        setProgressMessage(event.message);
        setProgressStep(event.step);
      },
      // onComplete
      (result: AutoPackageResponse) => {
        if (result.success && result.packages.length > 0) {
          setPackages(result.packages);
          setNote(result.personalization_note);
          setModelUsed(result.model_used);
          setDataQuality(result.data_quality);
          setAmadeusStats(result.amadeus_data || null);
          setBookingCount(result.booking_count || 0);
          setResolvedOrigin(result.resolved_origin || null);
          setSavedTiers(new Set()); // Reset for new packages
        } else {
          setError(result.error || 'No packages generated');
        }
        setIsLoading(false);
        setAbortStream(null);
      },
      // onError
      (errorMsg: string) => {
        setError(errorMsg);
        setIsLoading(false);
        setAbortStream(null);
      },
    );

    setAbortStream(() => cancel);
  };

  const filteredPackages = activeTierFilter
    ? packages.filter((p) => p.tier === activeTierFilter)
    : packages;

  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.8, delay: 0.3 }}
      className="mt-16 max-w-7xl mx-auto"
    >
      {/* Multi-Step Onboarding Wizard */}
      <AnimatePresence>
        {showOnboarding && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4"
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="bg-navy-900 border border-gold-500/20 rounded-2xl shadow-2xl max-w-lg w-full p-8 relative"
            >
              <button
                onClick={() => { setShowOnboarding(false); setOnboardingStep(1); }}
                className="absolute top-4 right-4 text-premium-mist/40 hover:text-white"
              >
                <FiX className="w-5 h-5" />
              </button>

              {/* Step indicator */}
              <div className="flex items-center gap-1 mb-6">
                {Array.from({ length: ONBOARDING_STEPS }).map((_, i) => (
                  <div key={i} className="flex-1 flex items-center">
                    <div className={`h-1.5 w-full rounded-full transition-all duration-300 ${
                      i + 1 <= onboardingStep ? 'bg-gold-400' : 'bg-premium-surface/50'
                    }`} />
                  </div>
                ))}
              </div>

              <div className="text-center mb-6">
                <FiUsers className="w-10 h-10 text-gold-400 mx-auto mb-3" />
                <h3 className="text-xl font-display font-bold text-white">
                  {onboardingStep === 1 && 'What interests you?'}
                  {onboardingStep === 2 && 'Budget & Travel Companions'}
                  {onboardingStep === 3 && 'Travel Habits & Airlines'}
                  {onboardingStep === 4 && 'Special Needs'}
                  {onboardingStep === 5 && 'Dream Destinations'}
                </h3>
                <p className="text-premium-mist/60 text-sm mt-1">Step {onboardingStep} of {ONBOARDING_STEPS}</p>
              </div>

              {/* Step 1: Interests */}
              {onboardingStep === 1 && (
                <div className="mb-6">
                  <div className="flex flex-wrap gap-2">
                    {INTEREST_OPTIONS.map((opt) => (
                      <button
                        key={opt.id}
                        type="button"
                        onClick={() => toggleInterest(opt.id)}
                        className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full border text-xs font-medium transition-all ${
                          selectedInterests.includes(opt.id)
                            ? 'bg-gold-500/20 border-gold-500/50 text-gold-400'
                            : 'bg-premium-surface/30 border-premium-border/50 text-premium-mist/60 hover:border-gold-500/30'
                        }`}
                      >
                        {opt.icon} {opt.label}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Step 2: Budget + Companions */}
              {onboardingStep === 2 && (
                <div className="space-y-5 mb-6">
                  <div>
                    <label className="block text-sm font-semibold text-premium-mist/80 mb-2">
                      <FiDollarSign className="inline mr-1" /> Budget Range (INR)
                    </label>
                    <div className="flex items-center gap-3">
                      <input
                        type="number"
                        value={budgetMin}
                        onChange={(e) => setBudgetMin(parseInt(e.target.value) || 0)}
                        placeholder="Min"
                        className="flex-1 px-3 py-2.5 bg-premium-surface/50 border border-premium-border rounded-xl text-white text-sm placeholder-premium-mist/40 focus:border-gold-500 focus:ring-2 focus:ring-gold-500/20 transition-all outline-none"
                      />
                      <span className="text-premium-mist/40">to</span>
                      <input
                        type="number"
                        value={budgetMax}
                        onChange={(e) => setBudgetMax(parseInt(e.target.value) || 0)}
                        placeholder="Max"
                        className="flex-1 px-3 py-2.5 bg-premium-surface/50 border border-premium-border rounded-xl text-white text-sm placeholder-premium-mist/40 focus:border-gold-500 focus:ring-2 focus:ring-gold-500/20 transition-all outline-none"
                      />
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-semibold text-premium-mist/80 mb-2">
                      <FiUsers className="inline mr-1" /> Who do you travel with?
                    </label>
                    <div className="flex gap-2">
                      {COMPANION_OPTIONS.map((opt) => (
                        <button
                          key={opt.id}
                          type="button"
                          onClick={() => setCompanions(opt.id)}
                          className={`px-4 py-2 rounded-lg border text-sm font-medium transition-all ${
                            companions === opt.id
                              ? 'bg-gold-500/20 border-gold-500/50 text-gold-400'
                              : 'bg-premium-surface/30 border-premium-border/50 text-premium-mist/60 hover:border-gold-500/30'
                          }`}
                        >
                          {opt.label}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* Step 3: Travel frequency + Preferred airlines */}
              {onboardingStep === 3 && (
                <div className="space-y-5 mb-6">
                  <div>
                    <label className="block text-sm font-semibold text-premium-mist/80 mb-2">
                      <FiCalendar className="inline mr-1" /> How often do you travel?
                    </label>
                    <div className="flex gap-2">
                      {FREQUENCY_OPTIONS.map((opt) => (
                        <button
                          key={opt.id}
                          type="button"
                          onClick={() => setTravelFrequency(opt.id)}
                          className={`px-3 py-2 rounded-lg border text-xs font-medium transition-all ${
                            travelFrequency === opt.id
                              ? 'bg-gold-500/20 border-gold-500/50 text-gold-400'
                              : 'bg-premium-surface/30 border-premium-border/50 text-premium-mist/60 hover:border-gold-500/30'
                          }`}
                        >
                          {opt.label}
                        </button>
                      ))}
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-semibold text-premium-mist/80 mb-2">Preferred Airlines</label>
                    <div className="flex flex-wrap gap-2">
                      {AIRLINE_OPTIONS.map((opt) => (
                        <button
                          key={opt.id}
                          type="button"
                          onClick={() => toggleAirline(opt.id)}
                          className={`px-3 py-1.5 rounded-full border text-xs font-medium transition-all ${
                            preferredAirlines.includes(opt.id)
                              ? 'bg-gold-500/20 border-gold-500/50 text-gold-400'
                              : 'bg-premium-surface/30 border-premium-border/50 text-premium-mist/60 hover:border-gold-500/30'
                          }`}
                        >
                          {opt.label}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* Step 4: Dietary + Accessibility */}
              {onboardingStep === 4 && (
                <div className="space-y-5 mb-6">
                  <div>
                    <label className="block text-sm font-semibold text-premium-mist/80 mb-2">Dietary Needs (comma-separated, optional)</label>
                    <input
                      type="text"
                      value={dietaryNeeds}
                      onChange={(e) => setDietaryNeeds(e.target.value)}
                      placeholder="e.g. Vegetarian, Vegan, Halal, Gluten-free"
                      className="w-full px-4 py-2.5 bg-premium-surface/50 border border-premium-border rounded-xl text-white text-sm placeholder-premium-mist/40 focus:border-gold-500 focus:ring-2 focus:ring-gold-500/20 transition-all outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-semibold text-premium-mist/80 mb-2">Accessibility Needs (comma-separated, optional)</label>
                    <input
                      type="text"
                      value={accessibilityNeeds}
                      onChange={(e) => setAccessibilityNeeds(e.target.value)}
                      placeholder="e.g. Wheelchair access, Elevator required"
                      className="w-full px-4 py-2.5 bg-premium-surface/50 border border-premium-border rounded-xl text-white text-sm placeholder-premium-mist/40 focus:border-gold-500 focus:ring-2 focus:ring-gold-500/20 transition-all outline-none"
                    />
                  </div>
                </div>
              )}

              {/* Step 5: Dream destinations + Accommodation */}
              {onboardingStep === 5 && (
                <div className="space-y-5 mb-6">
                  <div>
                    <label className="block text-sm font-semibold text-premium-mist/80 mb-2">
                      <FiMapPin className="inline mr-1" /> Dream destinations (comma-separated)
                    </label>
                    <input
                      type="text"
                      value={dreamDestinations}
                      onChange={(e) => setDreamDestinations(e.target.value)}
                      placeholder="e.g. Paris, Tokyo, Bali"
                      className="w-full px-4 py-2.5 bg-premium-surface/50 border border-premium-border rounded-xl text-white text-sm placeholder-premium-mist/40 focus:border-gold-500 focus:ring-2 focus:ring-gold-500/20 transition-all outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-semibold text-premium-mist/80 mb-2">
                      <FiHome className="inline mr-1" /> Preferred accommodation
                    </label>
                    <div className="flex gap-2">
                      {ACCOMMODATION_OPTIONS.map((opt) => (
                        <button
                          key={opt.id}
                          type="button"
                          onClick={() => setAccommodation(opt.id)}
                          className={`px-4 py-2 rounded-lg border text-sm font-medium transition-all ${
                            accommodation === opt.id
                              ? 'bg-gold-500/20 border-gold-500/50 text-gold-400'
                              : 'bg-premium-surface/30 border-premium-border/50 text-premium-mist/60 hover:border-gold-500/30'
                          }`}
                        >
                          {opt.label}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* Navigation buttons */}
              <div className="flex gap-3">
                {onboardingStep > 1 && (
                  <button
                    onClick={() => setOnboardingStep(s => s - 1)}
                    className="flex-1 px-6 py-3 border border-premium-border rounded-xl font-display font-bold text-premium-mist/70 hover:text-white hover:border-gold-500/30 transition-all"
                  >
                    Back
                  </button>
                )}
                {onboardingStep < ONBOARDING_STEPS ? (
                  <button
                    onClick={() => setOnboardingStep(s => s + 1)}
                    className="flex-1 px-6 py-3 bg-gradient-gold rounded-xl font-display font-bold text-navy-950 hover:scale-[1.02] transition-transform"
                  >
                    Next
                  </button>
                ) : (
                  <button
                    onClick={handleSaveOnboarding}
                    className="flex-1 px-6 py-3 bg-gradient-gold rounded-xl font-display font-bold text-navy-950 hover:scale-[1.02] transition-transform"
                  >
                    Save & Start Exploring
                  </button>
                )}
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

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
          <div className="flex items-center justify-between mb-8">
            <div className="flex items-center gap-3">
              <div className="p-3 rounded-xl bg-gold-500/10 border border-gold-500/20">
                <FiPackage className="w-6 h-6 text-gold-400" />
              </div>
              <div>
                <h2 className="text-3xl font-display font-bold text-white">
                  AI Travel Packages
                </h2>
                <p className="text-premium-mist/60 mt-1">
                  Real-time flights & hotels powered by Amadeus + AI curation
                </p>
              </div>
            </div>
            {isAuth && (
              <button
                onClick={() => setShowOnboarding(true)}
                className="flex items-center gap-2 px-4 py-2 rounded-xl border border-gold-500/30 bg-gold-500/10 text-gold-400 text-sm font-semibold hover:bg-gold-500/20 transition-all"
              >
                <FiUsers className="w-4 h-4" />
                Personalize
              </button>
            )}
          </div>

          {/* Sign-in prompt for unauthenticated users */}
          {!isAuth && (
            <div className="mb-6 p-4 bg-gold-500/5 border border-gold-500/20 rounded-xl flex items-center justify-between">
              <div className="flex items-center gap-3">
                <FiUsers className="w-5 h-5 text-gold-400" />
                <p className="text-sm text-premium-mist/70">
                  <a href="/auth" className="text-gold-400 font-semibold hover:text-gold-300 transition-colors">Sign in</a>
                  {' '}for personalized recommendations based on your travel history & preferences
                </p>
              </div>
            </div>
          )}

          {/* Profile-ready banner for returning authenticated users */}
          {isAuth && profileReady && packages.length === 0 && !isLoading && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="mb-6 p-4 bg-emerald-500/5 border border-emerald-500/20 rounded-xl flex items-center justify-between"
            >
              <div className="flex items-center gap-3">
                <FiStar className="w-5 h-5 text-emerald-400" />
                <p className="text-sm text-premium-mist/70">
                  Your profile is set up! Hit <span className="text-emerald-400 font-semibold">Generate</span> for personalized packages based on your preferences, or type a specific trip below.
                </p>
              </div>
              <button
                onClick={handleGenerate}
                className="ml-4 px-4 py-2 bg-emerald-500/20 border border-emerald-500/30 rounded-lg text-emerald-400 text-sm font-bold hover:bg-emerald-500/30 transition-all whitespace-nowrap"
              >
                Suggest for me
              </button>
            </motion.div>
          )}

          {/* Natural Language Input */}
          <div className="mb-6">
            <div className="flex items-center gap-2 mb-3">
              <button
                onClick={() => setUseNL(true)}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                  useNL ? 'bg-gold-500/20 text-gold-400 border border-gold-500/30' : 'text-premium-mist/50 hover:text-white'
                }`}
              >
                Describe your trip
              </button>
              <button
                onClick={() => setUseNL(false)}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                  !useNL ? 'bg-gold-500/20 text-gold-400 border border-gold-500/30' : 'text-premium-mist/50 hover:text-white'
                }`}
              >
                Use form
              </button>
            </div>

            {useNL && (
              <div className="relative">
                <FiSearch className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gold-400" />
                <input
                  type="text"
                  value={nlQuery}
                  onChange={(e) => setNlQuery(e.target.value)}
                  placeholder="e.g. I want a relaxing beach vacation in Goa for a week under 50k..."
                  className="w-full pl-12 pr-4 py-4 bg-premium-surface/50 border-2 border-premium-border rounded-xl text-white font-medium placeholder-premium-mist/40 focus:border-gold-500 focus:ring-4 focus:ring-gold-500/20 transition-all duration-300 outline-none text-lg"
                />
              </div>
            )}
          </div>

          {/* Structured Form (shown when "Use form" is selected or alongside NL) */}
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
            {!useNL && (
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
            )}
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
                  {progressMessage || 'Generating packages...'}
                </>
              ) : (
                <>
                  <FiZap className="w-5 h-5" />
                  Generate Real-Time AI Packages
                </>
              )}
            </span>
          </motion.button>

          {/* Progress bar */}
          <AnimatePresence>
            {isLoading && progressPercent > 0 && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="mt-4"
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs text-premium-mist/60 font-medium">{progressMessage}</span>
                  <span className="text-xs text-gold-400 font-bold">{progressPercent}%</span>
                </div>
                <div className="h-2 bg-premium-surface/50 rounded-full overflow-hidden border border-premium-border/30">
                  <motion.div
                    className="h-full bg-gradient-gold rounded-full"
                    initial={{ width: 0 }}
                    animate={{ width: `${progressPercent}%` }}
                    transition={{ duration: 0.5, ease: 'easeOut' }}
                  />
                </div>
                <div className="flex justify-between mt-2 text-[10px] text-premium-mist/40">
                  <span className={progressStep === 'nlp' || progressStep === 'profile' ? 'text-gold-400 font-bold' : ''}>
                    Parse & Profile
                  </span>
                  <span className={progressStep === 'flights' || progressStep === 'hotels' || progressStep === 'activities' ? 'text-gold-400 font-bold' : ''}>
                    Amadeus Data
                  </span>
                  <span className={progressStep === 'ai' || progressStep === 'validate' ? 'text-gold-400 font-bold' : ''}>
                    AI Curation
                  </span>
                  <span className={progressStep === 'done' ? 'text-gold-400 font-bold' : ''}>
                    Done
                  </span>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

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

          {/* Data quality indicator */}
          {dataQuality && amadeusStats && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="mt-6 flex flex-wrap items-center gap-3"
            >
              <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-bold border ${
                dataQuality === 'full_realtime'
                  ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                  : dataQuality === 'partial_realtime'
                  ? 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                  : 'bg-gray-500/10 text-gray-400 border-gray-500/30'
              }`}>
                <FiDatabase className="w-3.5 h-3.5" />
                {dataQuality === 'full_realtime' ? 'Full Real-Time Data' :
                 dataQuality === 'partial_realtime' ? 'Partial Real-Time Data' :
                 'Estimated Data'}
              </div>
              <span className="text-xs text-premium-mist/40">
                {amadeusStats.flights_found} flights &middot; {amadeusStats.hotels_found} hotels &middot; {amadeusStats.activities_found} activities from Amadeus
              </span>
            </motion.div>
          )}

          {/* Results */}
          {packages.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
              className="mt-10"
            >
              {/* Profile intelligence banner */}
              {(bookingCount > 0 || resolvedOrigin) && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="mb-6 p-3 bg-gold-500/5 border border-gold-500/15 rounded-xl flex items-center gap-3 text-sm"
                >
                  <span className="text-gold-400 text-base">&#10022;</span>
                  <span className="text-premium-mist/70">
                    {bookingCount > 0
                      ? `Personalized based on ${bookingCount} past booking${bookingCount !== 1 ? 's' : ''}`
                      : 'Personalized from your preferences'}
                    {resolvedOrigin && (
                      <> &middot; Departing from <span className="text-white font-semibold">{resolvedOrigin.iata}</span>
                        <span className="text-premium-mist/40"> ({resolvedOrigin.source})</span>
                      </>
                    )}
                  </span>
                </motion.div>
              )}

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
                {filteredPackages.map((pkg) => {
                  const styles = TIER_STYLES[pkg.tier] || TIER_STYLES.standard;
                  const isExpanded = expandedTier === pkg.tier;
                  const flightPrice = pkg.flights.price_inr || pkg.flights.estimated_price_inr || 0;

                  return (
                    <motion.div
                      key={pkg.tier}
                      variants={staggerItem}
                      className={`relative bg-premium-surface/30 backdrop-blur-xl rounded-2xl border ${styles.border} ${styles.glow} transition-all duration-300 overflow-hidden`}
                    >
                      {/* Tier badge */}
                      <div className="p-6">
                        <div className="flex items-center justify-between mb-4">
                          <div className={`inline-block px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider border ${styles.badge}`}>
                            {pkg.tier}
                          </div>
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

                        {/* Flight info */}
                        <div className="p-3 bg-premium-surface/40 rounded-xl mb-3">
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-sm font-semibold text-white">
                              {pkg.flights.airline_name || pkg.flights.travel_class.replace('_', ' ')}
                            </span>
                            <DataSourceBadge source={pkg.flights.data_source} />
                          </div>
                          <div className="flex items-center justify-between text-xs text-premium-mist/50">
                            <span>
                              {pkg.flights.flight_number && `${pkg.flights.flight_number} · `}
                              {pkg.flights.travel_class.replace('_', ' ')}
                              {pkg.flights.stops !== undefined && ` · ${pkg.flights.stops} stop${pkg.flights.stops !== 1 ? 's' : ''}`}
                            </span>
                            <span>~INR {formatINR(flightPrice)}</span>
                          </div>
                        </div>

                        {/* Hotel info */}
                        <div className="p-3 bg-premium-surface/40 rounded-xl mb-3">
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-sm font-semibold text-white">{pkg.hotel.name}</span>
                            <DataSourceBadge source={pkg.hotel.data_source} />
                          </div>
                          <div className="flex items-center justify-between">
                            <div className="flex">
                              {pkg.hotel.star_rating && Array.from({ length: pkg.hotel.star_rating }).map((_, i) => (
                                <FiStar key={i} className="w-3 h-3 text-gold-400 fill-gold-400" />
                              ))}
                            </div>
                            <div className="text-xs text-premium-mist/50">
                              {pkg.hotel.area && `${pkg.hotel.area} · `}INR {formatINR(pkg.hotel.price_per_night_inr)}/night
                            </div>
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

                        {/* Personalization reasons badges */}
                        {pkg.personalization_reasons && pkg.personalization_reasons.length > 0 && (
                          <div className="flex flex-wrap gap-1.5 mb-3">
                            {pkg.personalization_reasons.map((reason, i) => (
                              <span
                                key={i}
                                className="inline-flex items-center gap-1 text-[11px] px-2 py-0.5 bg-gold-500/10 text-gold-400 border border-gold-500/20 rounded-full"
                              >
                                <span className="text-gold-400">&#10022;</span>
                                {reason}
                              </span>
                            ))}
                          </div>
                        )}

                        {/* Expand itinerary button */}
                        <button
                          onClick={() => {
                            const newTier = isExpanded ? null : pkg.tier;
                            setExpandedTier(newTier);
                            // Track engagement when expanding (not collapsing)
                            if (newTier && isAuth) {
                              trackEngagement({
                                signal_type: 'tier_expand',
                                destination_iata: pkg.destination_iata,
                                tier: pkg.tier,
                                cabin_class: pkg.flights.travel_class,
                                hotel_star_rating: pkg.hotel.star_rating,
                              });
                            }
                          }}
                          className="w-full flex items-center justify-center gap-2 py-2 text-sm font-semibold text-gold-400 hover:text-gold-300 transition-colors"
                        >
                          {isExpanded ? (
                            <>Hide Itinerary <FiChevronUp /></>
                          ) : (
                            <>View {pkg.duration_days}-Day Itinerary <FiChevronDown /></>
                          )}
                        </button>

                        {/* Save Trip button */}
                        {isAuth && (
                          <button
                            onClick={async () => {
                              if (savedTiers.has(pkg.tier) || savingTier === pkg.tier) return;
                              setSavingTier(pkg.tier);
                              try {
                                await bookPackage({
                                  tier: pkg.tier,
                                  origin_iata: resolvedOrigin?.iata || originIata,
                                  destination_iata: pkg.destination_iata,
                                  destination_city: pkg.destination_city,
                                  duration_days: pkg.duration_days,
                                  cabin_class: pkg.flights.travel_class,
                                  hotel_star_rating: pkg.hotel.star_rating,
                                  carrier_codes: pkg.flights.flight_number ? [pkg.flights.flight_number.substring(0, 2)] : undefined,
                                  hotel_name: pkg.hotel.name,
                                  total_price_inr: pkg.estimated_total_inr,
                                });
                                setSavedTiers(prev => new Set(prev).add(pkg.tier));
                              } catch (err) {
                                console.error('Failed to save trip:', err);
                              } finally {
                                setSavingTier(null);
                              }
                            }}
                            disabled={savedTiers.has(pkg.tier) || savingTier === pkg.tier}
                            className={`w-full mt-2 flex items-center justify-center gap-2 py-2.5 rounded-xl text-sm font-bold transition-all ${
                              savedTiers.has(pkg.tier)
                                ? 'bg-green-500/20 text-green-400 border border-green-500/30 cursor-default'
                                : savingTier === pkg.tier
                                ? 'bg-gold-500/10 text-gold-400/50 border border-gold-500/20 cursor-wait'
                                : 'bg-gold-500/20 text-gold-400 border border-gold-500/30 hover:bg-gold-500/30 hover:scale-[1.02]'
                            }`}
                          >
                            {savedTiers.has(pkg.tier) ? (
                              <><FiCheck className="w-4 h-4" /> Trip Saved</>
                            ) : savingTier === pkg.tier ? (
                              <>Saving...</>
                            ) : (
                              <><FiHeart className="w-4 h-4" /> Save Trip</>
                            )}
                          </button>
                        )}
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
                                        <div className="flex-1">
                                          <span className="text-premium-mist/50 capitalize">{act.time}: </span>
                                          <span className="text-premium-mist/80">{act.activity}</span>
                                          {act.estimated_cost_inr > 0 && (
                                            <span className="text-premium-mist/40 ml-1">
                                              (INR {formatINR(act.estimated_cost_inr)})
                                            </span>
                                          )}
                                        </div>
                                        <DataSourceBadge source={act.data_source} />
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
