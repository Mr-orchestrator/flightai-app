'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import { motion } from 'framer-motion';
import {
  FiArrowLeft, FiMapPin, FiCalendar, FiStar,
  FiClock, FiChevronDown, FiChevronUp,
} from 'react-icons/fi';
import AnimatedBackground from '@/components/AnimatedBackground';
import Navbar from '@/components/Navbar';
import { getTripDetail } from '@/lib/api';
import type { TripDetail, TravelPackage } from '@/lib/api';
import { isAuthenticated, getCurrentUser, logout as doLogout } from '@/lib/auth';

function formatINR(amount: number): string {
  return new Intl.NumberFormat('en-IN', { maximumFractionDigits: 0 }).format(amount);
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return '';
  const d = new Date(dateStr + 'T00:00:00');
  return d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });
}

function formatDuration(iso: string): string {
  if (!iso) return '';
  const match = iso.match(/PT(?:(\d+)H)?(?:(\d+)M)?/);
  if (!match) return iso;
  const h = match[1] ? `${match[1]}h` : '';
  const m = match[2] ? ` ${match[2]}m` : '';
  return `${h}${m}`.trim();
}

function formatFlightTime(iso: string): string {
  if (!iso) return '';
  const timePart = iso.includes('T') ? iso.split('T')[1] : iso;
  return timePart?.substring(0, 5) || '';
}

const TIER_COLORS: Record<string, { border: string; badge: string; accent: string }> = {
  budget: {
    border: 'border-green-500/30',
    badge: 'bg-green-500/20 text-green-400 border-green-500/30',
    accent: 'text-green-400',
  },
  standard: {
    border: 'border-gold-500/30',
    badge: 'bg-gold-500/20 text-gold-400 border-gold-500/30',
    accent: 'text-gold-400',
  },
  premium: {
    border: 'border-purple-500/30',
    badge: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
    accent: 'text-purple-400',
  },
};

export default function TripDetailPage() {
  const params = useParams();
  const tripId = params.id as string;

  const [trip, setTrip] = useState<TripDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [isAuthed, setIsAuthed] = useState(false);
  const [userName, setUserName] = useState<string | null>(null);
  const [expandedDays, setExpandedDays] = useState<Set<number>>(new Set([1]));

  useEffect(() => {
    const authed = isAuthenticated();
    setIsAuthed(authed);
    if (authed) {
      const user = getCurrentUser();
      setUserName(user?.name || null);
      getTripDetail(tripId)
        .then(setTrip)
        .catch(console.error)
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, [tripId]);

  const handleLogout = () => {
    doLogout();
    setIsAuthed(false);
    setUserName(null);
  };

  const toggleDay = (day: number) => {
    setExpandedDays(prev => {
      const next = new Set(prev);
      if (next.has(day)) next.delete(day);
      else next.add(day);
      return next;
    });
  };

  const pkg: TravelPackage | null = trip?.package || null;
  const style = TIER_COLORS[trip?.tier || 'standard'] || TIER_COLORS.standard;

  return (
    <main className="min-h-screen">
      <AnimatedBackground />
      <Navbar isAuthenticated={isAuthed} userName={userName} onLogout={handleLogout} />

      <section className="relative px-6 pt-32 pb-20">
        <div className="max-w-4xl mx-auto">
          {/* Back link */}
          <a href="/trips" className="inline-flex items-center gap-2 text-premium-mist/60 hover:text-gold-400 transition-colors mb-6">
            <FiArrowLeft className="w-4 h-4" /> Back to My Trips
          </a>

          {loading ? (
            <div className="text-center py-20">
              <div className="w-8 h-8 border-2 border-gold-400 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
              <p className="text-premium-mist/60">Loading trip details...</p>
            </div>
          ) : !trip || !pkg ? (
            <div className="text-center py-20">
              <p className="text-premium-mist/60">Trip not found or no detail available.</p>
            </div>
          ) : (
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
              {/* Header */}
              <div className="mb-8">
                <div className="flex items-center gap-3 mb-2">
                  <span className={`px-3 py-1 rounded-full border text-xs font-bold uppercase ${style.badge}`}>
                    {trip.tier}
                  </span>
                  {pkg.name && <span className="text-premium-mist/50 text-sm">{pkg.name}</span>}
                </div>
                <h1 className="text-4xl font-display font-black text-white mb-2">
                  {trip.destination_city || trip.destination_iata}
                </h1>
                {trip.departure_date && (
                  <p className="text-premium-mist/60 flex items-center gap-2">
                    <FiCalendar className="w-4 h-4" />
                    {formatDate(trip.departure_date)} — {formatDate(trip.return_date)}
                    {pkg.duration_days && <span>· {pkg.duration_days} days</span>}
                  </p>
                )}
              </div>

              {/* Flight info */}
              <div className={`bg-gradient-glass backdrop-blur-xl rounded-2xl border ${style.border} p-6 mb-4`}>
                <h2 className="text-sm font-bold text-premium-mist/50 uppercase tracking-wider mb-4">Flights</h2>
                <div className="grid md:grid-cols-2 gap-6">
                  {/* Outbound */}
                  <div>
                    <p className="text-xs text-premium-mist/40 mb-1">OUTBOUND</p>
                    <p className="text-white font-semibold">
                      {pkg.flights?.airline_name || pkg.flights?.travel_class || 'Flight'}
                      {pkg.flights?.flight_number && ` ${pkg.flights.flight_number}`}
                    </p>
                    <p className="text-premium-mist/60 text-sm">
                      {pkg.flights?.departure_time && formatFlightTime(pkg.flights.departure_time)}
                      {pkg.flights?.duration && ` · ${formatDuration(pkg.flights.duration)}`}
                      {pkg.flights?.arrival_time && ` → ${formatFlightTime(pkg.flights.arrival_time)}`}
                    </p>
                    {pkg.flights?.stops !== undefined && (
                      <p className="text-premium-mist/40 text-xs mt-1">
                        {pkg.flights.stops === 0 ? 'Non-stop' : `${pkg.flights.stops} stop${pkg.flights.stops > 1 ? 's' : ''}`}
                      </p>
                    )}
                  </div>
                  {/* Return */}
                  {pkg.flights?.return_airline_name && (
                    <div>
                      <p className="text-xs text-premium-mist/40 mb-1">RETURN</p>
                      <p className="text-white font-semibold">
                        {pkg.flights.return_airline_name}
                        {pkg.flights.return_flight_number && ` ${pkg.flights.return_flight_number}`}
                      </p>
                      <p className="text-premium-mist/60 text-sm">
                        {pkg.flights.return_departure_time && formatFlightTime(pkg.flights.return_departure_time)}
                        {pkg.flights.return_duration && ` · ${formatDuration(pkg.flights.return_duration)}`}
                        {pkg.flights.return_arrival_time && ` → ${formatFlightTime(pkg.flights.return_arrival_time)}`}
                      </p>
                      {pkg.flights.return_stops !== undefined && (
                        <p className="text-premium-mist/40 text-xs mt-1">
                          {pkg.flights.return_stops === 0 ? 'Non-stop' : `${pkg.flights.return_stops} stop${pkg.flights.return_stops > 1 ? 's' : ''}`}
                        </p>
                      )}
                    </div>
                  )}
                </div>
                {(pkg.flights?.estimated_price_inr || pkg.flights?.price_inr) && (
                  <p className={`mt-4 text-sm font-semibold ${style.accent}`}>
                    Flight: INR {formatINR(pkg.flights.price_inr || pkg.flights.estimated_price_inr || 0)}
                  </p>
                )}
              </div>

              {/* Hotel info */}
              <div className={`bg-gradient-glass backdrop-blur-xl rounded-2xl border ${style.border} p-6 mb-4`}>
                <h2 className="text-sm font-bold text-premium-mist/50 uppercase tracking-wider mb-4">Hotel</h2>
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-white font-semibold text-lg">{pkg.hotel?.name || 'Hotel'}</p>
                    <div className="flex items-center gap-2 mt-1">
                      {pkg.hotel?.star_rating && (
                        <span className="flex items-center gap-0.5 text-gold-400 text-sm">
                          {Array.from({ length: pkg.hotel.star_rating }).map((_, i) => (
                            <FiStar key={i} className="w-3.5 h-3.5 fill-current" />
                          ))}
                        </span>
                      )}
                      {pkg.hotel?.area && <span className="text-premium-mist/50 text-sm">{pkg.hotel.area}</span>}
                    </div>
                  </div>
                  <div className="text-right">
                    {pkg.hotel?.price_per_night_inr && (
                      <>
                        <p className={`font-semibold ${style.accent}`}>
                          INR {formatINR(pkg.hotel.price_per_night_inr)}/night
                        </p>
                        {pkg.duration_days && (
                          <p className="text-premium-mist/50 text-xs">
                            {pkg.duration_days} nights = INR {formatINR(pkg.hotel.price_per_night_inr * pkg.duration_days)}
                          </p>
                        )}
                      </>
                    )}
                  </div>
                </div>
              </div>

              {/* Daily Itinerary */}
              {pkg.daily_itinerary && pkg.daily_itinerary.length > 0 && (
                <div className={`bg-gradient-glass backdrop-blur-xl rounded-2xl border ${style.border} p-6 mb-4`}>
                  <h2 className="text-sm font-bold text-premium-mist/50 uppercase tracking-wider mb-4">Daily Itinerary</h2>
                  <div className="space-y-2">
                    {pkg.daily_itinerary.map((day) => (
                      <div key={day.day} className="border border-premium-border/30 rounded-xl overflow-hidden">
                        <button
                          onClick={() => toggleDay(day.day)}
                          className="w-full flex items-center justify-between px-4 py-3 hover:bg-premium-surface/20 transition-colors"
                        >
                          <span className="font-semibold text-white">
                            Day {day.day}: {day.title}
                          </span>
                          {expandedDays.has(day.day) ? (
                            <FiChevronUp className="w-4 h-4 text-premium-mist/50" />
                          ) : (
                            <FiChevronDown className="w-4 h-4 text-premium-mist/50" />
                          )}
                        </button>
                        {expandedDays.has(day.day) && day.activities && (
                          <div className="px-4 pb-3 space-y-2">
                            {day.activities.map((act, j) => (
                              <div key={j} className="flex items-start justify-between text-sm">
                                <div className="flex items-start gap-2">
                                  <FiClock className="w-3.5 h-3.5 text-premium-mist/40 mt-0.5" />
                                  <div>
                                    <span className="text-premium-mist/40">{act.time}</span>
                                    <span className="text-white ml-2">{act.activity}</span>
                                  </div>
                                </div>
                                {act.estimated_cost_inr > 0 && (
                                  <span className="text-premium-mist/50 whitespace-nowrap">
                                    INR {formatINR(act.estimated_cost_inr)}
                                  </span>
                                )}
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Total */}
              <div className={`bg-gradient-glass backdrop-blur-xl rounded-2xl border ${style.border} p-6`}>
                <div className="flex items-center justify-between">
                  <span className="text-premium-mist/60 font-semibold">Total Package</span>
                  <span className="text-3xl font-display font-black text-gold-400">
                    INR {formatINR(pkg.estimated_total_inr || trip.total_package_inr || 0)}
                  </span>
                </div>
              </div>
            </motion.div>
          )}
        </div>
      </section>
    </main>
  );
}
