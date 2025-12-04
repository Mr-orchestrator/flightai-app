/**
 * API Client for FlightAI Backend
 * Connects Next.js frontend to Python FastAPI backend
 */

import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
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

export default api;
