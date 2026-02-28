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
  data_quality: 'full_realtime' | 'partial_realtime' | 'estimated';
  error: string | null;
  amadeus_data?: {
    flights_found: number;
    hotels_found: number;
    activities_found: number;
  };
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
}

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
    const response = await api.post<AutoPackageResponse>('/auto-packages', request);
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

export default api;
