'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { FiChevronDown, FiChevronUp, FiClock, FiMapPin, FiInfo, FiExternalLink } from 'react-icons/fi';
import type { Flight, FlightSegment } from '@/lib/api';

interface FlightCardProps {
  flight: Flight;
  index: number;
  isBestPrice?: boolean;
}

export default function FlightCard({ flight, index, isBestPrice }: FlightCardProps) {
  const [isExpanded, setIsExpanded] = useState(index === 0); // First flight expanded by default

  const formatDuration = (minutes: number | string) => {
    const totalMinutes = typeof minutes === 'string' ? parseInt(minutes, 10) : minutes;
    const hours = Math.floor(totalMinutes / 60);
    const mins = totalMinutes % 60;
    return `${hours}h ${mins}m`;
  };

  const formatDateTime = (isoString: string) => {
    const date = new Date(isoString);
    return date.toLocaleString('en-IN', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getSeatStatusClass = (seats: number | string) => {
    if (typeof seats === 'string') return 'text-gray-400';
    if (seats <= 3) return 'text-red-500';
    if (seats <= 7) return 'text-yellow-500';
    return 'text-green-500';
  };

  const generateBookingUrl = (type: 'google' | 'kayak' | 'skyscanner') => {
    const origin = flight.outbound.departure.iata;
    const dest = flight.outbound.arrival.iata;
    const date = flight.outbound.departure.time.split('T')[0];

    switch (type) {
      case 'google':
        return `https://www.google.com/travel/flights?q=flights+from+${origin}+to+${dest}+on+${date}`;
      case 'kayak':
        return `https://www.kayak.com/flights/${origin}-${dest}/${date}`;
      case 'skyscanner':
        return `https://www.skyscanner.com/transport/flights/${origin.toLowerCase()}/${dest.toLowerCase()}/${date.replace(/-/g, '')}`;
      default:
        return '';
    }
  };

  const renderSegment = (segment: FlightSegment, segIndex: number) => (
    <div key={segIndex} className="mb-6 pb-6 border-b border-white/10 last:border-0">
      <div className="flex items-center justify-between mb-4">
        <h5 className="text-sm font-bold text-gold-400">
          Leg {segIndex + 1}: {segment.departure.iata} → {segment.arrival.iata}
        </h5>
        <span className="text-xs text-premium-mist/60">{formatDuration(segment.duration)}</span>
      </div>

      <div className="grid grid-cols-3 gap-4">
        {/* Departure */}
        <div>
          <p className="text-xs font-semibold text-premium-mist/60 mb-2">DEPARTURE</p>
          <div className="space-y-1">
            <p className="text-lg font-bold text-white">{segment.departure.iata}</p>
            <p className="text-sm text-premium-mist">{formatDateTime(segment.departure.time)}</p>
            {segment.departure.terminal && (
              <p className="text-xs text-premium-mist/60">Terminal {segment.departure.terminal}</p>
            )}
          </div>
        </div>

        {/* Flight Details */}
        <div className="text-center">
          <p className="text-xs font-semibold text-premium-mist/60 mb-2">FLIGHT</p>
          <div className="space-y-1">
            <p className="text-sm font-bold text-gold-400">{segment.carrier}</p>
            <p className="text-sm text-premium-mist">{segment.carrier}{segment.flight_number}</p>
            <p className="text-xs text-premium-mist/60">{segment.aircraft || 'Aircraft N/A'}</p>
          </div>
        </div>

        {/* Arrival */}
        <div className="text-right">
          <p className="text-xs font-semibold text-premium-mist/60 mb-2">ARRIVAL</p>
          <div className="space-y-1">
            <p className="text-lg font-bold text-white">{segment.arrival.iata}</p>
            <p className="text-sm text-premium-mist">{formatDateTime(segment.arrival.time)}</p>
            {segment.arrival.terminal && (
              <p className="text-xs text-premium-mist/60">Terminal {segment.arrival.terminal}</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.1 }}
      className="mb-4"
    >
      {/* Collapsed Header */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full glass rounded-2xl p-6 transition-all duration-300 hover:border-gold-500/50 text-left"
      >
        <div className="flex items-center justify-between">
          {/* Left: Price and Route */}
          <div className="flex-1">
            <div className="flex items-center gap-4">
              <div>
                <div className="text-2xl font-bold text-gold-400">
                  {flight.price.currency} {flight.price.total.toLocaleString()}
                </div>
                {isBestPrice && (
                  <span className="inline-block mt-1 px-3 py-1 bg-gold-500/20 text-gold-400 text-xs font-bold rounded-full">
                    🏆 BEST PRICE
                  </span>
                )}
              </div>
              
              <div className="text-premium-mist/80">
                <div className="flex items-center gap-2 text-sm">
                  <span className="font-bold">{flight.outbound.departure.iata}</span>
                  <span>→</span>
                  <span className="font-bold">{flight.outbound.arrival.iata}</span>
                </div>
                <div className="text-xs mt-1">
                  {flight.outbound.carrier_name || flight.validating_airline} • {flight.outbound.stops} stop{flight.outbound.stops !== 1 ? 's' : ''}
                </div>
              </div>
            </div>
          </div>

          {/* Right: Seats and Expand */}
          <div className="flex items-center gap-4">
            <div className={`text-sm font-semibold ${getSeatStatusClass(flight.seats_available)}`}>
              {typeof flight.seats_available === 'number' ? `${flight.seats_available} seats` : flight.seats_available}
            </div>
            <div className="text-gold-400">
              {isExpanded ? <FiChevronUp size={24} /> : <FiChevronDown size={24} />}
            </div>
          </div>
        </div>
      </button>

      {/* Expanded Details */}
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="overflow-hidden"
          >
            <div className="glass rounded-2xl mt-2 p-6 space-y-6">
              {/* Price Breakdown */}
              <div className="flex justify-between items-center pb-6 border-b border-white/10">
                <div>
                  <p className="text-xs font-semibold text-premium-mist/60 uppercase tracking-wider mb-2">Total Price</p>
                  <p className="text-3xl font-bold text-gold-400">{flight.price.currency} {flight.price.total.toLocaleString()}</p>
                  {flight.price.base && (
                    <p className="text-sm text-premium-mist/80 mt-1">Base Fare: {flight.price.currency} {flight.price.base.toLocaleString()}</p>
                  )}
                </div>
                <div className="text-right">
                  <div className={`text-lg font-bold ${getSeatStatusClass(flight.seats_available)}`}>
                    {typeof flight.seats_available === 'number' ? `${flight.seats_available} SEATS` : flight.seats_available}
                  </div>
                  {isBestPrice && (
                    <span className="inline-block mt-2 px-4 py-2 bg-gold-500/20 text-gold-400 text-sm font-bold rounded-full">
                      🏆 BEST PRICE
                    </span>
                  )}
                </div>
              </div>

              {/* Overview Metrics */}
              <div className="grid grid-cols-4 gap-4">
                <div>
                  <p className="text-xs font-semibold text-premium-mist/60 mb-1">AIRLINE</p>
                  <p className="text-sm font-bold text-white">{flight.outbound.carrier_name || flight.validating_airline}</p>
                </div>
                <div>
                  <p className="text-xs font-semibold text-premium-mist/60 mb-1">CABIN</p>
                  <p className="text-sm font-bold text-white">Economy</p>
                </div>
                <div>
                  <p className="text-xs font-semibold text-premium-mist/60 mb-1">STOPS</p>
                  <p className="text-sm font-bold text-white">{flight.outbound.stops} stop{flight.outbound.stops !== 1 ? 's' : ''}</p>
                </div>
                <div>
                  <p className="text-xs font-semibold text-premium-mist/60 mb-1">DURATION</p>
                  <p className="text-sm font-bold text-white">{formatDuration(flight.outbound.duration)}</p>
                </div>
              </div>

              {/* Booking Links */}
              <div className="space-y-3">
                <p className="text-sm font-semibold text-premium-mist/80">🔗 Book This Flight:</p>
                <div className="grid grid-cols-3 gap-3">
                  <a
                    href={generateBookingUrl('google')}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center justify-center gap-2 px-4 py-3 bg-gold-500/10 hover:bg-gold-500/20 border border-gold-500/30 rounded-xl text-sm font-semibold text-gold-400 transition-all"
                  >
                    <FiExternalLink size={16} />
                    Google Flights
                  </a>
                  <a
                    href={generateBookingUrl('kayak')}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center justify-center gap-2 px-4 py-3 bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl text-sm font-semibold text-white transition-all"
                  >
                    <FiExternalLink size={16} />
                    Kayak
                  </a>
                  <a
                    href={generateBookingUrl('skyscanner')}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center justify-center gap-2 px-4 py-3 bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl text-sm font-semibold text-white transition-all"
                  >
                    <FiExternalLink size={16} />
                    Skyscanner
                  </a>
                </div>
              </div>

              {/* Outbound Flight Details */}
              <div>
                <h4 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                  <span>🛫</span> Outbound Flight
                </h4>
                <div className="space-y-4">
                  {flight.outbound.segments.map((segment, idx) => renderSegment(segment, idx))}
                </div>
              </div>

              {/* Return Flight Details */}
              {flight.return && (
                <div>
                  <h4 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                    <span>🛬</span> Return Flight
                  </h4>
                  <div className="space-y-4">
                    {flight.return.segments.map((segment, idx) => renderSegment(segment, idx))}
                  </div>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
