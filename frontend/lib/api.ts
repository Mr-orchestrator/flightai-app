/**
 * API Client for FlightAI Backend
 * Connects Next.js frontend to Python FastAPI backend
 */

import axios from 'axios';
import Cookies from 'js-cookie';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Auto-attach JWT token to all requests
api.interceptors.request.use((config) => {
  const token = Cookies.get('flightai_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ==================== TYPE DEFINITIONS ====================

export interface Airport {
  iata: string;
  city: string;
  name: string;
  country: string;
}

export interface TripExtractionRequest {
  origin_iata: string;
  user_query: string;
  fallback_days?: number;
}

export interface TripExtractionResponse {
  success: boolean;
  origin_iata: string;
  origin_city: string;
  destination_iata: string | null;
  destination_city: string | null;
  iata_confidence: 'high' | 'medium' | 'low';
  duration_days: number;
  departure_date: string;
  return_date: string;
  model_used: string;
  used_fallback: boolean;
  error: string | null;
}

export interface FlightSearchRequest {
  origin: string;
  destination: string;
  departure_date: string;
  return_date?: string;
  adults?: number;
  max_results?: number;
  currency?: string;
  travel_class?: string;
  non_stop?: boolean;
  max_stops?: number;
}

export interface FlightSegment {
  departure: {
    iata: string;
    time: string;
    terminal?: string;
  };
  arrival: {
    iata: string;
    time: string;
    terminal?: string;
  };
  carrier: string;
  flight_number: string;
  aircraft: string;
  aircraft_name: string;
  duration: string;
  cabin: string;
  fare_class: string;
  operating_carrier: string;
}

export interface FlightJourney {
  duration: string;
  stops: number;
  departure: {
    iata: string;
    time: string;
    terminal?: string;
  };
  arrival: {
    iata: string;
    time: string;
    terminal?: string;
  };
  carrier: string;
  carrier_name: string;
  segments: FlightSegment[];
}

export interface Flight {
  price: {
    total: number;
    base?: number;
    currency: string;
    fees?: number;
    grand_total?: number;
  };
  seats_available: number | string;
  validating_airline: string;
  outbound: FlightJourney;
  return?: FlightJourney;
}

export interface FlightSearchResponse {
  success: boolean;
  total_offers: number;
  origin: string;
  destination: string;
  flights: Flight[];
  error?: string;
}

export interface AirlineInfo {
  carrier_code: string;
  airline_name: string;
  website: string | null;
  has_direct_booking: boolean;
}

// ==================== API FUNCTIONS ====================

/**
 * Get list of available airports
 */
export const getAirports = async (): Promise<Airport[]> => {
  try {
    const response = await api.get<Airport[]>('/airports');
    return response.data;
  } catch (error) {
    console.error('Error fetching airports:', error);
    throw new Error('Failed to fetch airports');
  }
};

/**
 * Extract trip details from natural language query
 */
export const extractTrip = async (
  request: TripExtractionRequest
): Promise<TripExtractionResponse> => {
  try {
    const response = await api.post<TripExtractionResponse>('/extract-trip', request);
    return response.data;
  } catch (error) {
    console.error('Error extracting trip:', error);
    throw new Error('Failed to extract trip details');
  }
};

/**
 * Search for flights
 */
export const searchFlights = async (
  request: FlightSearchRequest
): Promise<FlightSearchResponse> => {
  try {
    const response = await api.post<FlightSearchResponse>('/search-flights', request);
    return response.data;
  } catch (error) {
    console.error('Error searching flights:', error);
    throw new Error('Failed to search flights');
  }
};

/**
 * Get airline information
 */
export const getAirlineInfo = async (carrierCode: string): Promise<AirlineInfo> => {
  try {
    const response = await api.get<AirlineInfo>(`/airline-info/${carrierCode}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching airline info:', error);
    throw new Error('Failed to fetch airline information');
  }
};

/**
 * Health check
 */
export const healthCheck = async (): Promise<{ status: string; amadeus_configured: boolean; google_api_configured: boolean }> => {
  try {
    const response = await api.get('/health');
    return response.data;
  } catch (error) {
    console.error('Error checking health:', error);
    throw new Error('API is unavailable');
  }
};

// ==================== AUTO PACKAGE TYPES ====================

export interface ActivityItem {
  time: string;
  activity: string;
  estimated_cost_inr: number;
  data_source?: 'amadeus' | 'suggested';
}

export interface DayItinerary {
  day: number;
  title: string;
  activities: ActivityItem[];
}

export interface HotelInfo {
  name: string;
  star_rating: number;
  price_per_night_inr: number;
  area: string;
  data_source?: 'amadeus' | 'estimated';
}

export interface FlightEstimate {
  travel_class: string;
  estimated_price_inr?: number;
  price_inr?: number;
  airline_name?: string;
  flight_number?: string;
  stops?: number;
  duration?: string;
  data_source?: 'amadeus' | 'estimated';
}

export interface TravelPackage {
  tier: 'budget' | 'standard' | 'premium';
  name: string;
  tagline: string;
  destination_city: string;
  destination_iata: string;
  duration_days: number;
  estimated_total_inr: number;
  hotel: HotelInfo;
  flights: FlightEstimate;
  daily_itinerary: DayItinerary[];
  inclusions: string[];
  highlights: string[];
  // Pipeline fields
  flight_offer_id?: string;
  hotel_offer_id?: string;
  activity_ids?: string[];
  flight_price_inr?: number;
  hotel_total_inr?: number;
  fx_rate_used?: number;
  validation_warnings?: string[];
  // Personalization
  personalization_reasons?: string[];
  preference_matches?: string[];
}

export interface AutoPackageRequest {
  destination?: string;
  destination_iata?: string;
  duration_days?: number;
  budget_inr?: number;
  natural_language_query?: string;
  preferences?: {
    interests?: string[];
    budget_level?: string;
    travel_style?: string;
  };
}

export interface AutoPackageResponse {
  success: boolean;
  packages: TravelPackage[];
  personalization_note: string;
  model_used: string | null;
  used_fallback: boolean;
  data_quality: 'full_realtime' | 'partial_realtime' | 'estimated' | 'insufficient_data';
  data_quality_detail?: {
    flights: string;
    hotels: string;
    activities: string;
    overall: string;
  };
  error: string | null;
  amadeus_data?: {
    flights_found: number;
    hotels_found: number;
    activities_found: number;
  };
  tier_totals?: {
    budget: number;
    standard: number;
    premium: number;
  };
  validation_warnings?: string[];
  inference_log?: Record<string, unknown>;
  // Profile intelligence metadata
  resolved_origin?: { iata: string; source: string };
  booking_count?: number;
}

export interface NLPParseRequest {
  query: string;
}

export interface NLPParseResponse {
  success: boolean;
  destination: string | null;
  destination_iata: string | null;
  duration_days: number | null;
  budget_inr: number | null;
  interests: string[];
  travel_style: string;
  travel_companions: string | null;
  specific_requests: string | null;
  model_used: string | null;
  error: string | null;
}

export interface OnboardingStatus {
  onboarding_completed: boolean;
  has_preferences: boolean;
  has_travel_history: boolean;
}

export interface SavePreferencesRequest {
  interests?: string[];
  budget_level?: string;
  travel_style?: string;
  preferred_destinations?: string[];
  travel_companions?: string;
  accommodation_preference?: string;
  budget_range_min?: number;
  budget_range_max?: number;
  travel_frequency?: string;
  dietary_needs?: string[];
  accessibility_needs?: string[];
  preferred_airlines?: string[];
  onboarding_step?: number;
}

// ==================== SSE PROGRESS TYPES ====================

export interface ProgressEvent {
  step: 'nlp' | 'profile' | 'flights' | 'hotels' | 'activities' | 'ai' | 'validate' | 'done';
  message: string;
  percent: number;
}

export type SSEEvent =
  | { type: 'progress'; data: ProgressEvent }
  | { type: 'complete'; data: AutoPackageResponse }
  | { type: 'error'; data: { message: string } };

export interface TravelHistoryItem {
  id: number;
  origin_iata: string;
  destination_iata: string;
  destination_city: string | null;
  duration_days: number | null;
  query_text: string | null;
  searched_at: string;
}

// ==================== PACKAGE API FUNCTIONS ====================

export const fetchAutoPackages = async (
  request: AutoPackageRequest
): Promise<AutoPackageResponse> => {
  try {
    const response = await api.post<AutoPackageResponse>('/auto-packages', request, {
      timeout: 300000, // 5 min — Amadeus + LLM calls take time
    });
    return response.data;
  } catch (error) {
    console.error('Error generating packages:', error);
    throw new Error('Failed to generate travel packages');
  }
};

export const getTravelHistory = async (): Promise<TravelHistoryItem[]> => {
  try {
    const response = await api.get<TravelHistoryItem[]>('/travel-history');
    return response.data;
  } catch (error) {
    console.error('Error fetching travel history:', error);
    throw new Error('Failed to fetch travel history');
  }
};

export const nlpParse = async (query: string): Promise<NLPParseResponse> => {
  try {
    const response = await api.post<NLPParseResponse>('/nlp-parse', { query });
    return response.data;
  } catch (error) {
    console.error('Error parsing query:', error);
    throw new Error('Failed to parse travel query');
  }
};

export const getOnboardingStatus = async (): Promise<OnboardingStatus> => {
  try {
    const response = await api.get<OnboardingStatus>('/onboarding-status');
    return response.data;
  } catch (error) {
    console.error('Error fetching onboarding status:', error);
    throw new Error('Failed to fetch onboarding status');
  }
};

export const savePreferences = async (prefs: SavePreferencesRequest): Promise<{ success: boolean }> => {
  try {
    const response = await api.post('/save-preferences', prefs);
    return response.data;
  } catch (error) {
    console.error('Error saving preferences:', error);
    throw new Error('Failed to save preferences');
  }
};

// ==================== BOOKING + ENGAGEMENT TYPES ====================

export interface BookPackageRequest {
  tier: string;
  origin_iata: string;
  destination_iata: string;
  destination_city?: string;
  duration_days?: number;
  cabin_class?: string;
  hotel_star_rating?: number;
  carrier_codes?: string[];
  hotel_name?: string;
  total_price_inr?: number;
  package_snapshot_id?: string;
}

export interface TrackEngagementRequest {
  signal_type: 'tier_expand' | 'tier_view';
  destination_iata?: string;
  tier?: string;
  cabin_class?: string;
  hotel_star_rating?: number;
}

/**
 * Save a trip booking — primary signal for personalization
 */
export const bookPackage = async (
  request: BookPackageRequest
): Promise<{ success: boolean; booking_id?: number }> => {
  try {
    const response = await api.post('/book-package', request);
    return response.data;
  } catch (error) {
    console.error('Error saving booking:', error);
    throw new Error('Failed to save trip');
  }
};

/**
 * Track implicit engagement signal — fire and forget
 */
export const trackEngagement = async (
  request: TrackEngagementRequest
): Promise<void> => {
  try {
    await api.post('/track-engagement', request);
  } catch (error) {
    // Fire-and-forget: log but don't throw
    console.warn('Engagement tracking failed:', error);
  }
};

// ==================== SSE STREAMING CLIENT ====================

/**
 * Fetch auto packages with real-time progress via Server-Sent Events.
 * Falls back to the non-streaming endpoint if SSE fails to connect.
 */
export const fetchAutoPackagesStream = (
  request: AutoPackageRequest,
  onProgress: (event: ProgressEvent) => void,
  onComplete: (data: AutoPackageResponse) => void,
  onError: (error: string) => void,
): (() => void) => {
  const controller = new AbortController();
  const token = Cookies.get('flightai_token');

  const run = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/auto-packages-stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify(request),
        signal: controller.signal,
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('No response body');
      }

      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        // Parse SSE events from buffer
        const lines = buffer.split('\n');
        buffer = '';

        let eventType = '';
        let eventData = '';

        for (const line of lines) {
          if (line.startsWith('event: ')) {
            eventType = line.slice(7).trim();
          } else if (line.startsWith('data: ')) {
            eventData = line.slice(6);
          } else if (line === '' && eventType && eventData) {
            // End of event — process it
            try {
              const parsed = JSON.parse(eventData);
              if (eventType === 'progress') {
                onProgress(parsed as ProgressEvent);
              } else if (eventType === 'complete') {
                onComplete(parsed as AutoPackageResponse);
              } else if (eventType === 'error') {
                onError(parsed.message || 'Unknown error');
              }
            } catch (parseErr) {
              console.warn('SSE parse error:', parseErr);
            }
            eventType = '';
            eventData = '';
          } else if (line !== '') {
            // Incomplete event, put back in buffer
            buffer += line + '\n';
          }
        }
      }
    } catch (err: unknown) {
      if (err instanceof Error && err.name === 'AbortError') {
        return; // User cancelled
      }
      console.error('SSE stream failed, falling back:', err);
      // Fallback to non-streaming endpoint
      try {
        onProgress({ step: 'ai', message: 'Generating packages...', percent: 50 });
        const result = await fetchAutoPackages(request);
        onComplete(result);
      } catch (fallbackErr) {
        onError(fallbackErr instanceof Error ? fallbackErr.message : 'Failed to generate packages');
      }
    }
  };

  run();

  // Return abort function
  return () => controller.abort();
};

export default api;
