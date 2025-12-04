'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import AnimatedBackground from '@/components/AnimatedBackground';
import Navbar from '@/components/Navbar';
import SearchCard from '@/components/SearchCard';
import FlightCard from '@/components/FlightCard';
import { getAirports, extractTrip, searchFlights } from '@/lib/api';
import type { Airport, TripExtractionResponse, FlightSearchResponse } from '@/lib/api';

export default function Home() {
  const [airports, setAirports] = useState<Airport[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [tripData, setTripData] = useState<TripExtractionResponse | null>(null);
  const [flightsData, setFlightsData] = useState<FlightSearchResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Load airports on mount
    getAirports()
      .then(setAirports)
      .catch((err) => {
        console.error('Failed to load airports:', err);
        setError('Failed to load airports. Please check if the backend API is running.');
      });
  }, []);

  const handleSearch = async (origin: string, query: string) => {
    setIsLoading(true);
    setError(null);
    setTripData(null);
    setFlightsData(null);

    try {
      // Extract trip details
      const tripResult = await extractTrip({
        origin_iata: origin,
        user_query: query,
        fallback_days: 7,
      });

      console.log('Trip extracted:', tripResult);
      setTripData(tripResult);

      // Search flights if extraction was successful
      if (tripResult.success && tripResult.destination_iata) {
        const flightsResult = await searchFlights({
          origin: tripResult.origin_iata,
          destination: tripResult.destination_iata,
          departure_date: tripResult.departure_date,
          return_date: tripResult.return_date,
          adults: 1,
          max_results: 10,
          currency: 'INR',
        });

        console.log('Flights found:', flightsResult);
        setFlightsData(flightsResult);
      } else {
        setError(tripResult.error || 'Could not extract trip details from your query.');
      }
    } catch (err: any) {
      console.error('Search error:', err);
      setError(err.message || 'An error occurred during search. Please check if the backend API is running.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main className="min-h-screen">
      <AnimatedBackground />
      <Navbar />
      
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
                  ✨ AI-POWERED LUXURY BOOKING
                </span>
              </div>
            </motion.div>

            <h1 className="text-6xl md:text-7xl lg:text-8xl font-display font-black mb-6">
              <span className="block text-white">Your Next</span>
              <span className="block text-gradient-gold">Adventure Awaits</span>
            </h1>

            <p className="text-xl md:text-2xl text-premium-mist/70 max-w-3xl mx-auto">
              Experience the future of flight booking with cinematic visuals,
              intelligent AI, and premium design
            </p>
          </motion.div>

          <SearchCard 
            airports={airports}
            onSearch={handleSearch}
            isLoading={isLoading}
          />

          {/* Error Display */}
          {error && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="mt-8 max-w-4xl mx-auto p-6 bg-red-500/10 border border-red-500/30 rounded-2xl backdrop-blur-xl"
            >
              <p className="text-red-400 text-center">
                ⚠️ {error}
              </p>
            </motion.div>
          )}

          {/* Trip Summary Display */}
          {tripData && tripData.success && (
            <motion.div
              initial={{ opacity: 0, y: 40, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              transition={{ duration: 0.8, ease: [0.6, 0.01, 0.05, 0.9] }}
              className="mt-12 max-w-4xl mx-auto"
            >
              <div className="bg-gradient-glass backdrop-blur-2xl rounded-luxury border border-gold-500/20 shadow-luxury p-8">
                <h2 className="text-3xl font-display font-bold text-white mb-6">
                  ✈️ Your Journey
                </h2>

                {/* Route Display */}
                <div className="grid grid-cols-3 gap-4 mb-6">
                  <div className="text-center p-6 bg-premium-surface/50 rounded-2xl border border-premium-border">
                    <div className="text-sm text-premium-mist/60 uppercase tracking-wider mb-2">Departure</div>
                    <div className="text-4xl font-display font-black text-white mb-1">{tripData.origin_iata}</div>
                    <div className="text-lg text-gold-400">{tripData.origin_city}</div>
                  </div>

                  <div className="flex items-center justify-center">
                    <motion.div
                      animate={{ x: [0, 10, 0] }}
                      transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
                      className="text-6xl"
                    >
                      →
                    </motion.div>
                  </div>

                  <div className="text-center p-6 bg-premium-surface/50 rounded-2xl border border-premium-border">
                    <div className="text-sm text-premium-mist/60 uppercase tracking-wider mb-2">Arrival</div>
                    <div className="text-4xl font-display font-black text-white mb-1">{tripData.destination_iata}</div>
                    <div className="text-lg text-gold-400">{tripData.destination_city}</div>
                  </div>
                </div>

                {/* Travel Details */}
                <div className="grid grid-cols-3 gap-4">
                  <div className="p-4 bg-premium-surface/30 rounded-xl border border-premium-border/50">
                    <div className="text-xs text-premium-mist/60 uppercase tracking-wider mb-1">Duration</div>
                    <div className="text-2xl font-bold text-white">{tripData.duration_days} days</div>
                  </div>

                  <div className="p-4 bg-premium-surface/30 rounded-xl border border-premium-border/50">
                    <div className="text-xs text-premium-mist/60 uppercase tracking-wider mb-1">Departure</div>
                    <div className="text-2xl font-bold text-white">
                      {new Date(tripData.departure_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                    </div>
                  </div>

                  <div className="p-4 bg-premium-surface/30 rounded-xl border border-premium-border/50">
                    <div className="text-xs text-premium-mist/60 uppercase tracking-wider mb-1">Return</div>
                    <div className="text-2xl font-bold text-white">
                      {new Date(tripData.return_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                    </div>
                  </div>
                </div>

                {/* Confidence Badge */}
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ type: 'spring', stiffness: 500, damping: 15, delay: 0.5 }}
                  className="mt-6 inline-block"
                >
                  <div className={`px-4 py-2 rounded-full font-bold text-sm ${
                    tripData.iata_confidence === 'high' 
                      ? 'bg-green-500/20 border border-green-500/50 text-green-400'
                      : tripData.iata_confidence === 'medium'
                      ? 'bg-yellow-500/20 border border-yellow-500/50 text-yellow-400'
                      : 'bg-gray-500/20 border border-gray-500/50 text-gray-400'
                  }`}>
                    {tripData.iata_confidence === 'high' ? '✓' : tripData.iata_confidence === 'medium' ? '~' : '?'} 
                    {' '}{tripData.iata_confidence.toUpperCase()} CONFIDENCE
                  </div>
                </motion.div>
              </div>
            </motion.div>
          )}

          {/* Flight Results Display */}
          {flightsData && flightsData.success && flightsData.flights.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: 40 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.3 }}
              className="mt-12 max-w-6xl mx-auto"
            >
              <h2 className="text-4xl font-display font-bold text-white mb-8 text-center">
                ✈️ Available Flights
              </h2>

              <div className="space-y-4">
                {flightsData.flights.map((flight, index) => (
                  <FlightCard
                    key={index}
                    flight={flight}
                    index={index}
                    isBestPrice={index === 0}
                  />
                ))}
              </div>
            </motion.div>
          )}

          {/* No Flights Message */}
          {flightsData && flightsData.success && flightsData.flights.length === 0 && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="mt-12 max-w-4xl mx-auto p-6 bg-yellow-500/10 border border-yellow-500/30 rounded-2xl backdrop-blur-xl"
            >
              <p className="text-yellow-400 text-center">
                No flights found for this route. Try different dates or destinations.
              </p>
            </motion.div>
          )}
        </div>
      </section>
    </main>
  );
}
