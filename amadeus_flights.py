"""
Amadeus Travel API Integration
Search real-time flights, hotels, and activities using Amadeus APIs
"""
import os
import logging
import threading
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()

AMADEUS_CLIENT_ID = os.getenv("AMADEUS_CLIENT_ID")
AMADEUS_CLIENT_SECRET = os.getenv("AMADEUS_CLIENT_SECRET")

# Amadeus API base + endpoints
AMADEUS_BASE_URL = "https://test.api.amadeus.com"
AMADEUS_AUTH_URL = f"{AMADEUS_BASE_URL}/v1/security/oauth2/token"
AMADEUS_FLIGHT_SEARCH_URL = f"{AMADEUS_BASE_URL}/v2/shopping/flight-offers"
AMADEUS_HOTEL_LIST_URL = f"{AMADEUS_BASE_URL}/v1/reference-data/locations/hotels/by-city"
AMADEUS_HOTEL_OFFERS_URL = f"{AMADEUS_BASE_URL}/v3/shopping/hotel-offers"
AMADEUS_ACTIVITIES_URL = f"{AMADEUS_BASE_URL}/v1/shopping/activities"

# IATA code to city coordinates mapping for hotel/activity searches
CITY_COORDINATES = {
    # India
    "DEL": {"lat": 28.6139, "lon": 77.2090, "city": "New Delhi"},
    "BOM": {"lat": 19.0760, "lon": 72.8777, "city": "Mumbai"},
    "BLR": {"lat": 12.9716, "lon": 77.5946, "city": "Bangalore"},
    "HYD": {"lat": 17.3850, "lon": 78.4867, "city": "Hyderabad"},
    "MAA": {"lat": 13.0827, "lon": 80.2707, "city": "Chennai"},
    "CCU": {"lat": 22.5726, "lon": 88.3639, "city": "Kolkata"},
    "COK": {"lat": 9.9312, "lon": 76.2673, "city": "Kochi"},
    "GOI": {"lat": 15.2993, "lon": 74.1240, "city": "Goa"},
    "AMD": {"lat": 23.0225, "lon": 72.5714, "city": "Ahmedabad"},
    "PNQ": {"lat": 18.5204, "lon": 73.8567, "city": "Pune"},
    "JAI": {"lat": 26.9124, "lon": 75.7873, "city": "Jaipur"},
    "TRV": {"lat": 8.5241, "lon": 76.9366, "city": "Thiruvananthapuram"},
    "IXC": {"lat": 30.7333, "lon": 76.7794, "city": "Chandigarh"},
    "VNS": {"lat": 25.3176, "lon": 82.9739, "city": "Varanasi"},
    "SXR": {"lat": 34.0837, "lon": 74.7973, "city": "Srinagar"},
    # Middle East
    "DXB": {"lat": 25.2048, "lon": 55.2708, "city": "Dubai"},
    "AUH": {"lat": 24.4539, "lon": 54.3773, "city": "Abu Dhabi"},
    "DOH": {"lat": 25.2854, "lon": 51.5310, "city": "Doha"},
    "BAH": {"lat": 26.2285, "lon": 50.5860, "city": "Bahrain"},
    "MCT": {"lat": 23.5880, "lon": 58.3829, "city": "Muscat"},
    "RUH": {"lat": 24.7136, "lon": 46.6753, "city": "Riyadh"},
    "JED": {"lat": 21.4858, "lon": 39.1925, "city": "Jeddah"},
    # Southeast Asia
    "SIN": {"lat": 1.3521, "lon": 103.8198, "city": "Singapore"},
    "BKK": {"lat": 13.7563, "lon": 100.5018, "city": "Bangkok"},
    "KUL": {"lat": 3.1390, "lon": 101.6869, "city": "Kuala Lumpur"},
    "HKG": {"lat": 22.3193, "lon": 114.1694, "city": "Hong Kong"},
    "SGN": {"lat": 10.8231, "lon": 106.6297, "city": "Ho Chi Minh City"},
    "HAN": {"lat": 21.0285, "lon": 105.8542, "city": "Hanoi"},
    "MNL": {"lat": 14.5995, "lon": 120.9842, "city": "Manila"},
    "DPS": {"lat": -8.3405, "lon": 115.1690, "city": "Bali"},
    # East Asia
    "NRT": {"lat": 35.6762, "lon": 139.6503, "city": "Tokyo"},
    "ICN": {"lat": 37.5665, "lon": 126.9780, "city": "Seoul"},
    "PEK": {"lat": 39.9042, "lon": 116.4074, "city": "Beijing"},
    "PVG": {"lat": 31.2304, "lon": 121.4737, "city": "Shanghai"},
    # Europe
    "LHR": {"lat": 51.5074, "lon": -0.1278, "city": "London"},
    "CDG": {"lat": 48.8566, "lon": 2.3522, "city": "Paris"},
    "FRA": {"lat": 50.1109, "lon": 8.6821, "city": "Frankfurt"},
    "AMS": {"lat": 52.3676, "lon": 4.9041, "city": "Amsterdam"},
    "FCO": {"lat": 41.9028, "lon": 12.4964, "city": "Rome"},
    "BCN": {"lat": 41.3874, "lon": 2.1686, "city": "Barcelona"},
    "MAD": {"lat": 40.4168, "lon": -3.7038, "city": "Madrid"},
    "IST": {"lat": 41.0082, "lon": 28.9784, "city": "Istanbul"},
    "ZRH": {"lat": 47.3769, "lon": 8.5417, "city": "Zurich"},
    "VIE": {"lat": 48.2082, "lon": 16.3738, "city": "Vienna"},
    "MUC": {"lat": 48.1351, "lon": 11.5820, "city": "Munich"},
    # Americas
    "JFK": {"lat": 40.7128, "lon": -74.0060, "city": "New York"},
    "LAX": {"lat": 34.0522, "lon": -118.2437, "city": "Los Angeles"},
    "SFO": {"lat": 37.7749, "lon": -122.4194, "city": "San Francisco"},
    "ORD": {"lat": 41.8781, "lon": -87.6298, "city": "Chicago"},
    "YYZ": {"lat": 43.6532, "lon": -79.3832, "city": "Toronto"},
    # Oceania
    "SYD": {"lat": -33.8688, "lon": 151.2093, "city": "Sydney"},
    "MEL": {"lat": -37.8136, "lon": 144.9631, "city": "Melbourne"},
    # Africa
    "JNB": {"lat": -26.2041, "lon": 28.0473, "city": "Johannesburg"},
    "CAI": {"lat": 30.0444, "lon": 31.2357, "city": "Cairo"},
    "NBO": {"lat": -1.2921, "lon": 36.8219, "city": "Nairobi"},
    # Maldives / Sri Lanka
    "MLE": {"lat": 4.1755, "lon": 73.5093, "city": "Male"},
    "CMB": {"lat": 6.9271, "lon": 79.8612, "city": "Colombo"},
}

class AmadeusFlightSearch:
    def __init__(self):
        self.client_id = AMADEUS_CLIENT_ID
        self.client_secret = AMADEUS_CLIENT_SECRET
        self.access_token = None
        self.token_expiry = None
        self._token_lock = threading.Lock()  # Thread-safe for parallel calls

    def get_access_token(self):
        """Get or refresh Amadeus access token (thread-safe)."""
        with self._token_lock:
            # Check if token is still valid
            if self.access_token and self.token_expiry:
                if datetime.now() < self.token_expiry:
                    return self.access_token

            # Get new token
            try:
                response = requests.post(
                    AMADEUS_AUTH_URL,
                    data={
                        'grant_type': 'client_credentials',
                        'client_id': self.client_id,
                        'client_secret': self.client_secret
                    },
                    timeout=10
                )
                response.raise_for_status()

                data = response.json()
                self.access_token = data['access_token']
                expires_in = data.get('expires_in', 1800)  # default 30 min
                self.token_expiry = datetime.now() + timedelta(seconds=expires_in - 60)

                return self.access_token

            except Exception as e:
                raise Exception(f"Failed to get Amadeus access token: {str(e)}")
    
    def search_flights(self, origin, destination, departure_date, return_date=None, 
                      adults=1, max_results=10, currency="INR", travel_class=None, non_stop=False):
        """
        Search for flights
        
        Args:
            origin (str): Origin IATA code (e.g., "BOM")
            destination (str): Destination IATA code (e.g., "DXB")
            departure_date (str|date): Departure date (YYYY-MM-DD)
            return_date (str|date|None): Return date for round-trip
            adults (int): Number of adult passengers
            max_results (int): Maximum number of flight offers to return
            currency (str): Currency code for prices
            travel_class (str): Cabin class (ECONOMY, PREMIUM_ECONOMY, BUSINESS, FIRST)
            non_stop (bool): If True, only return direct flights (no layovers)
        
        Returns:
            dict: Flight search results with parsed offers
        """
        try:
            # Get access token
            token = self.get_access_token()
            
            # Format dates
            if isinstance(departure_date, datetime):
                departure_date = departure_date.strftime("%Y-%m-%d")
            elif hasattr(departure_date, 'strftime'):
                departure_date = departure_date.strftime("%Y-%m-%d")
            
            if return_date:
                if isinstance(return_date, datetime):
                    return_date = return_date.strftime("%Y-%m-%d")
                elif hasattr(return_date, 'strftime'):
                    return_date = return_date.strftime("%Y-%m-%d")
            
            # Build request parameters
            params = {
                'originLocationCode': origin,
                'destinationLocationCode': destination,
                'departureDate': departure_date,
                'adults': adults,
                'currencyCode': currency,
                'max': max_results
            }
            
            if return_date:
                params['returnDate'] = return_date
            
            if travel_class:
                params['travelClass'] = travel_class
            
            if non_stop:
                params['nonStop'] = 'true'
            
            # Make API request
            headers = {
                'Authorization': f'Bearer {token}'
            }
            
            response = requests.get(
                AMADEUS_FLIGHT_SEARCH_URL,
                params=params,
                headers=headers,
                timeout=15
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Parse results
            return self._parse_flight_offers(data, origin, destination)
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 400:
                error_data = e.response.json()
                error_msg = error_data.get('errors', [{}])[0].get('detail', 'Bad request')
                raise Exception(f"Flight search error: {error_msg}")
            raise Exception(f"Amadeus API error: {str(e)}")
        except Exception as e:
            raise Exception(f"Flight search failed: {str(e)}")
    
    def _parse_flight_offers(self, data, origin, destination):
        """Parse Amadeus flight offers response"""
        offers = data.get('data', [])
        
        if not offers:
            return {
                'success': True,
                'origin': origin,
                'destination': destination,
                'total_offers': 0,
                'flights': [],
                'message': 'No flights found for the selected route and dates.'
            }
        
        parsed_flights = []
        
        for offer in offers[:10]:  # Limit to 10 offers
            try:
                flight_info = self._parse_single_offer(offer)
                parsed_flights.append(flight_info)
            except Exception as e:
                # Skip offers that fail to parse
                continue
        
        return {
            'success': True,
            'origin': origin,
            'destination': destination,
            'total_offers': len(offers),
            'flights': parsed_flights,
            'currency': data.get('dictionaries', {}).get('currencies', {})
        }
    
    def _parse_single_offer(self, offer):
        """Parse a single flight offer"""
        price = offer.get('price', {})
        itineraries = offer.get('itineraries', [])
        traveler_pricings = offer.get('travelerPricings', [{}])
        
        # Parse outbound flight
        outbound = itineraries[0] if len(itineraries) > 0 else {}
        segments = outbound.get('segments', [])
        
        if not segments:
            return None
        
        first_segment = segments[0]
        last_segment = segments[-1]
        
        # Parse all segments for detailed info
        outbound_segments = []
        for seg in segments:
            outbound_segments.append({
                'departure': {
                    'iata': seg.get('departure', {}).get('iataCode'),
                    'time': seg.get('departure', {}).get('at'),
                    'terminal': seg.get('departure', {}).get('terminal')
                },
                'arrival': {
                    'iata': seg.get('arrival', {}).get('iataCode'),
                    'time': seg.get('arrival', {}).get('at'),
                    'terminal': seg.get('arrival', {}).get('terminal')
                },
                'carrier': seg.get('carrierCode'),
                'flight_number': seg.get('number'),
                'aircraft': seg.get('aircraft', {}).get('code'),
                'duration': seg.get('duration'),
                'cabin': seg.get('cabin'),
                'operating_carrier': seg.get('operating', {}).get('carrierCode')
            })
        
        # Get fare details
        fare_detail = traveler_pricings[0].get('fareDetailsBySegment', [{}])[0] if traveler_pricings else {}
        
        # Basic flight info
        flight_info = {
            'id': offer.get('id'),
            'price': {
                'total': price.get('total'),
                'currency': price.get('currency', 'INR'),
                'base': price.get('base'),
                'fees': price.get('fees', []),
                'grand_total': price.get('grandTotal')
            },
            'outbound': {
                'departure': {
                    'iata': first_segment.get('departure', {}).get('iataCode'),
                    'time': first_segment.get('departure', {}).get('at'),
                    'terminal': first_segment.get('departure', {}).get('terminal')
                },
                'arrival': {
                    'iata': last_segment.get('arrival', {}).get('iataCode'),
                    'time': last_segment.get('arrival', {}).get('at'),
                    'terminal': last_segment.get('arrival', {}).get('terminal')
                },
                'duration': outbound.get('duration'),
                'stops': len(segments) - 1,
                'carrier': first_segment.get('carrierCode'),
                'flight_number': first_segment.get('number'),
                'aircraft': first_segment.get('aircraft', {}).get('code'),
                'cabin': fare_detail.get('cabin', 'Economy'),
                'fare_class': fare_detail.get('class'),
                'segments': outbound_segments
            },
            'seats_available': offer.get('numberOfBookableSeats', 'N/A'),
            'instant_ticketing': offer.get('instantTicketingRequired', False),
            'validating_airline': offer.get('validatingAirlineCodes', ['N/A'])[0]
        }
        
        # Parse return flight if exists
        if len(itineraries) > 1:
            return_flight = itineraries[1]
            return_segments = return_flight.get('segments', [])
            
            if return_segments:
                first_return = return_segments[0]
                last_return = return_segments[-1]
                
                # Parse all return segments
                return_segments_details = []
                for seg in return_segments:
                    return_segments_details.append({
                        'departure': {
                            'iata': seg.get('departure', {}).get('iataCode'),
                            'time': seg.get('departure', {}).get('at'),
                            'terminal': seg.get('departure', {}).get('terminal')
                        },
                        'arrival': {
                            'iata': seg.get('arrival', {}).get('iataCode'),
                            'time': seg.get('arrival', {}).get('at'),
                            'terminal': seg.get('arrival', {}).get('terminal')
                        },
                        'carrier': seg.get('carrierCode'),
                        'flight_number': seg.get('number'),
                        'aircraft': seg.get('aircraft', {}).get('code'),
                        'duration': seg.get('duration'),
                        'cabin': seg.get('cabin'),
                        'operating_carrier': seg.get('operating', {}).get('carrierCode')
                    })
                
                return_fare = traveler_pricings[0].get('fareDetailsBySegment', [{}])
                return_fare_detail = return_fare[1] if len(return_fare) > 1 else return_fare[0] if return_fare else {}
                
                flight_info['return'] = {
                    'departure': {
                        'iata': first_return.get('departure', {}).get('iataCode'),
                        'time': first_return.get('departure', {}).get('at'),
                        'terminal': first_return.get('departure', {}).get('terminal')
                    },
                    'arrival': {
                        'iata': last_return.get('arrival', {}).get('iataCode'),
                        'time': last_return.get('arrival', {}).get('at'),
                        'terminal': last_return.get('arrival', {}).get('terminal')
                    },
                    'duration': return_flight.get('duration'),
                    'stops': len(return_segments) - 1,
                    'carrier': first_return.get('carrierCode'),
                    'flight_number': first_return.get('number'),
                    'aircraft': first_return.get('aircraft', {}).get('code'),
                    'cabin': return_fare_detail.get('cabin', 'Economy'),
                    'fare_class': return_fare_detail.get('class'),
                    'segments': return_segments_details
                }
        
        return flight_info

    # ==================== HOTEL SEARCH ====================

    def search_hotels_by_city(self, city_code, check_in, check_out, adults=1,
                              ratings=None, currency="INR", max_hotels=15):
        """
        Search for hotels in a city using Amadeus Hotel APIs.

        Step 1: Get hotel list by city code
        Step 2: Get offers/prices for those hotels

        Args:
            city_code: IATA city code (e.g., "DXB")
            check_in: Check-in date (YYYY-MM-DD or date object)
            check_out: Check-out date (YYYY-MM-DD or date object)
            adults: Number of adult guests
            ratings: List of star ratings to filter (e.g., [3,4,5])
            currency: Currency code
            max_hotels: Max number of hotels to return

        Returns:
            dict with success, hotels list, errors
        """
        try:
            token = self.get_access_token()
            headers = {'Authorization': f'Bearer {token}'}

            # Format dates
            if hasattr(check_in, 'strftime'):
                check_in = check_in.strftime("%Y-%m-%d")
            if hasattr(check_out, 'strftime'):
                check_out = check_out.strftime("%Y-%m-%d")

            # Step 1: Get hotel list by city
            params = {'cityCode': city_code.upper()}
            if ratings:
                params['ratings'] = ','.join(str(r) for r in ratings)

            resp = requests.get(
                AMADEUS_HOTEL_LIST_URL,
                params=params,
                headers=headers,
                timeout=15
            )
            resp.raise_for_status()
            hotel_list_data = resp.json().get('data', [])

            if not hotel_list_data:
                return {
                    'success': True,
                    'city_code': city_code,
                    'hotels': [],
                    'total_found': 0,
                    'message': f'No hotels found in {city_code}'
                }

            # Take top hotels (limit to avoid API overload)
            hotel_ids = [h['hotelId'] for h in hotel_list_data[:max_hotels]]
            logger.info(f"Hotel list API returned {len(hotel_list_data)} hotels for {city_code}")

            # Step 2: Try to get offers/prices in small batches
            parsed_hotels = []
            live_hotel_ids = set()

            # Try batches of 3 to reduce 400 errors from Amadeus
            batch_size = 3
            for i in range(0, min(len(hotel_ids), 12), batch_size):
                batch = hotel_ids[i:i + batch_size]
                try:
                    offer_params = {
                        'hotelIds': ','.join(batch),
                        'adults': adults,
                        'checkInDate': check_in,
                        'checkOutDate': check_out,
                        'currency': currency,
                    }

                    offers_resp = requests.get(
                        AMADEUS_HOTEL_OFFERS_URL,
                        params=offer_params,
                        headers=headers,
                        timeout=20
                    )
                    if offers_resp.status_code == 200:
                        offers_data = offers_resp.json().get('data', [])
                        for hotel_offer in offers_data:
                            parsed = self._parse_hotel_offer(hotel_offer, hotel_list_data)
                            if parsed:
                                parsed_hotels.append(parsed)
                                live_hotel_ids.add(parsed['hotel_id'])
                        logger.info(f"Hotel offers batch {i//batch_size + 1}: got {len(offers_data)} offers")
                    else:
                        logger.warning(f"Hotel offers batch {i//batch_size + 1} returned {offers_resp.status_code}")
                except Exception as e:
                    logger.warning(f"Hotel offers batch {i//batch_size + 1} failed: {e}")

            # Fill remaining with list data (estimated prices) for hotels not in live set
            if len(parsed_hotels) < max_hotels:
                remaining = [h for h in hotel_list_data[:max_hotels]
                             if h.get('hotelId') not in live_hotel_ids]
                parsed_hotels.extend(self._hotels_from_list(remaining[:max_hotels - len(parsed_hotels)]))

            # Sort by star rating (higher first) then estimated price
            parsed_hotels.sort(key=lambda h: (-(h.get('star_rating') or 0), h.get('price_per_night', float('inf'))))

            return {
                'success': True,
                'city_code': city_code,
                'hotels': parsed_hotels,
                'total_found': len(parsed_hotels),
            }

        except requests.exceptions.HTTPError as e:
            error_detail = ''
            try:
                error_detail = e.response.json().get('errors', [{}])[0].get('detail', '')
            except Exception:
                pass
            return {
                'success': False,
                'city_code': city_code,
                'hotels': [],
                'total_found': 0,
                'error': f'Hotel search error: {error_detail or str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'city_code': city_code,
                'hotels': [],
                'total_found': 0,
                'error': f'Hotel search failed: {str(e)}'
            }

    def _parse_hotel_offer(self, hotel_offer, hotel_list_data):
        """Parse a single hotel offer from Amadeus response."""
        try:
            hotel = hotel_offer.get('hotel', {})
            hotel_id = hotel.get('hotelId', '')
            name = hotel.get('name', 'Unknown Hotel')

            # Find star rating from hotel list data
            rating = None
            geo = {}
            for h in hotel_list_data:
                if h.get('hotelId') == hotel_id:
                    rating = h.get('rating')
                    geo = h.get('geoCode', {})
                    break

            # Get first offer (cheapest)
            offers = hotel_offer.get('offers', [])
            if not offers:
                return None

            first_offer = offers[0]
            price_info = first_offer.get('price', {})
            total_price = float(price_info.get('total', 0))
            currency = price_info.get('currency', 'INR')

            # Calculate per night price
            room = first_offer.get('room', {})
            room_type = room.get('typeEstimated', {})

            check_in = first_offer.get('checkInDate', '')
            check_out = first_offer.get('checkOutDate', '')
            nights = 1
            if check_in and check_out:
                try:
                    d1 = datetime.strptime(check_in, "%Y-%m-%d")
                    d2 = datetime.strptime(check_out, "%Y-%m-%d")
                    nights = max((d2 - d1).days, 1)
                except Exception:
                    pass

            price_per_night = total_price / nights if nights > 0 else total_price

            return {
                'hotel_id': hotel_id,
                'name': name,
                'star_rating': int(rating) if rating else None,
                'latitude': geo.get('latitude'),
                'longitude': geo.get('longitude'),
                'price_total': total_price,
                'price_per_night': round(price_per_night, 2),
                'currency': currency,
                'room_type': room_type.get('category', 'STANDARD'),
                'bed_type': room_type.get('bedType', 'UNKNOWN'),
                'beds': room_type.get('beds', 1),
                'check_in': check_in,
                'check_out': check_out,
                'nights': nights,
                'data_source': 'amadeus',
            }
        except Exception:
            return None

    def _hotels_from_list(self, hotel_list_data):
        """Create hotel entries from hotel list data when offers aren't available.
        Uses real hotel names/ratings from Amadeus but marks prices as estimated."""
        # Rough price estimates per star rating (INR per night)
        price_estimates = {1: 1500, 2: 2500, 3: 4000, 4: 7000, 5: 15000}

        parsed = []
        for h in hotel_list_data:
            rating = h.get('rating')
            star = int(rating) if rating else 3
            geo = h.get('geoCode', {})

            parsed.append({
                'hotel_id': h.get('hotelId', ''),
                'name': h.get('name', 'Unknown Hotel'),
                'star_rating': star,
                'latitude': geo.get('latitude'),
                'longitude': geo.get('longitude'),
                'price_total': None,
                'price_per_night': price_estimates.get(star, 5000),
                'currency': 'INR',
                'room_type': 'STANDARD',
                'bed_type': 'UNKNOWN',
                'beds': 1,
                'check_in': None,
                'check_out': None,
                'nights': None,
                'data_source': 'amadeus_list',  # Real name, estimated price
            })
        return parsed

    # ==================== ACTIVITY/TOURS SEARCH ====================

    def search_activities(self, latitude, longitude, radius=20):
        """
        Search for tours and activities near a location using Amadeus API.

        Args:
            latitude: Location latitude
            longitude: Location longitude
            radius: Search radius in km (default 20)

        Returns:
            dict with success, activities list
        """
        try:
            token = self.get_access_token()
            headers = {'Authorization': f'Bearer {token}'}

            params = {
                'latitude': latitude,
                'longitude': longitude,
                'radius': radius,
            }

            resp = requests.get(
                AMADEUS_ACTIVITIES_URL,
                params=params,
                headers=headers,
                timeout=15
            )
            resp.raise_for_status()
            activities_data = resp.json().get('data', [])

            parsed = []
            for activity in activities_data:
                parsed_activity = self._parse_activity(activity)
                if parsed_activity:
                    parsed.append(parsed_activity)

            return {
                'success': True,
                'activities': parsed,
                'total_found': len(parsed),
            }

        except requests.exceptions.HTTPError as e:
            error_detail = ''
            try:
                error_detail = e.response.json().get('errors', [{}])[0].get('detail', '')
            except Exception:
                pass
            return {
                'success': False,
                'activities': [],
                'total_found': 0,
                'error': f'Activity search error: {error_detail or str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'activities': [],
                'total_found': 0,
                'error': f'Activity search failed: {str(e)}'
            }

    def _parse_activity(self, activity):
        """Parse a single activity from Amadeus response."""
        try:
            price = activity.get('price', {})
            amount = price.get('amount')
            currency = price.get('currencyCode', 'USD')

            pictures = activity.get('pictures', [])
            picture_url = pictures[0] if pictures else None

            return {
                'id': activity.get('id'),
                'name': activity.get('name', 'Unknown Activity'),
                'description': (activity.get('shortDescription') or activity.get('description', ''))[:200],
                'price': float(amount) if amount else None,
                'currency': currency,
                'rating': activity.get('rating'),
                'picture_url': picture_url,
                'booking_link': activity.get('bookingLink'),
                'duration': activity.get('duration'),
                'category': activity.get('category'),
                'data_source': 'amadeus',
            }
        except Exception:
            return None

    # ==================== COORDINATE HELPERS ====================

    @staticmethod
    def get_city_coordinates(iata_code):
        """Get lat/lon coordinates for a city by IATA code."""
        return CITY_COORDINATES.get(iata_code.upper())

    def get_city_coordinates_with_fallback(self, iata_code):
        """Get coordinates from hardcoded dict, falling back to Amadeus Location API."""
        coords = CITY_COORDINATES.get(iata_code.upper())
        if coords:
            return coords

        # Fallback: use Amadeus Airport/City search API
        try:
            token = self.get_access_token()
            resp = requests.get(
                f"{AMADEUS_BASE_URL}/v1/reference-data/locations",
                params={"keyword": iata_code, "subType": "CITY,AIRPORT"},
                headers={"Authorization": f"Bearer {token}"},
                timeout=10,
            )
            if resp.status_code == 200:
                data = resp.json().get("data", [])
                if data:
                    geo = data[0].get("geoCode", {})
                    city_name = data[0].get("address", {}).get("cityName", iata_code)
                    result = {
                        "lat": geo.get("latitude"),
                        "lon": geo.get("longitude"),
                        "city": city_name,
                    }
                    if result["lat"] and result["lon"]:
                        # Cache for future use
                        CITY_COORDINATES[iata_code.upper()] = result
                        return result
        except Exception:
            pass

        return None

    @staticmethod
    def get_city_name(iata_code):
        """Get city name from IATA code."""
        coords = CITY_COORDINATES.get(iata_code.upper())
        return coords['city'] if coords else iata_code


def format_duration(duration_str):
    """Convert ISO 8601 duration to readable format (e.g., PT5H30M -> 5h 30m)"""
    if not duration_str:
        return "N/A"
    
    duration_str = duration_str.replace('PT', '')
    hours = 0
    minutes = 0
    
    if 'H' in duration_str:
        parts = duration_str.split('H')
        hours = int(parts[0])
        duration_str = parts[1] if len(parts) > 1 else ''
    
    if 'M' in duration_str:
        minutes = int(duration_str.replace('M', ''))
    
    if hours and minutes:
        return f"{hours}h {minutes}m"
    elif hours:
        return f"{hours}h"
    elif minutes:
        return f"{minutes}m"
    return "N/A"

def format_datetime(dt_str):
    """Format ISO datetime string to readable format"""
    if not dt_str:
        return "N/A"
    try:
        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        return dt.strftime("%b %d, %I:%M %p")
    except:
        return dt_str

def get_airline_name(carrier_code):
    """Get airline name from carrier code"""
    airlines = {
        # Indian Carriers
        'AI': 'Air India',
        'UK': 'Vistara',
        '6E': 'IndiGo',
        'SG': 'SpiceJet',
        'G8': 'Go First',
        'I5': 'AirAsia India',
        '9W': 'Jet Airways',
        # Middle East
        'EK': 'Emirates',
        'QR': 'Qatar Airways',
        'EY': 'Etihad Airways',
        'WY': 'Oman Air',
        'GF': 'Gulf Air',
        # Asian Airlines
        'UL': 'SriLankan Airlines',
        'SQ': 'Singapore Airlines',
        'TG': 'Thai Airways',
        'CX': 'Cathay Pacific',
        'MH': 'Malaysia Airlines',
        'VJ': 'VietJet Air',
        'BL': 'Jetstar Pacific',
        'VN': 'Vietnam Airlines',
        'TR': 'Scoot',
        '3K': 'Jetstar Asia',
        'AK': 'AirAsia',
        'D7': 'AirAsia X',
        'FD': 'Thai AirAsia',
        'NH': 'All Nippon Airways',
        'JL': 'Japan Airlines',
        'OZ': 'Asiana Airlines',
        'KE': 'Korean Air',
        # European Airlines
        'BA': 'British Airways',
        'LH': 'Lufthansa',
        'AF': 'Air France',
        'KL': 'KLM',
        'EI': 'Aer Lingus',
        'VS': 'Virgin Atlantic',
        'IB': 'Iberia',
        'AZ': 'ITA Airways',
        'LX': 'Swiss International',
        'OS': 'Austrian Airlines',
        'SN': 'Brussels Airlines',
        # American Airlines
        'AA': 'American Airlines',
        'UA': 'United Airlines',
        'DL': 'Delta Air Lines',
        'AC': 'Air Canada',
        'WS': 'WestJet',
        # Oceania
        'QF': 'Qantas',
        'VA': 'Virgin Australia',
        'NZ': 'Air New Zealand',
        # Others
        'HR': 'Hahn Air',
        'LY': 'El Al',
        'MS': 'EgyptAir',
        'SA': 'South African Airways',
        'ET': 'Ethiopian Airlines',
        'KQ': 'Kenya Airways'
    }
    return airlines.get(carrier_code, carrier_code)

def get_airline_website(carrier_code):
    """Get airline booking website URL from carrier code"""
    websites = {
        # Indian Carriers
        'AI': 'https://www.airindia.com',
        'UK': 'https://www.airvistara.com',
        '6E': 'https://www.goindigo.in',
        'SG': 'https://www.spicejet.com',
        'G8': 'https://www.flygofirst.com',
        'I5': 'https://www.airasia.com/en/gb',
        # Middle East
        'EK': 'https://www.emirates.com',
        'QR': 'https://www.qatarairways.com',
        'EY': 'https://www.etihad.com',
        'WY': 'https://www.omanair.com',
        'GF': 'https://www.gulfair.com',
        # Asian Airlines
        'UL': 'https://www.srilankan.com',
        'SQ': 'https://www.singaporeair.com',
        'TG': 'https://www.thaiairways.com',
        'CX': 'https://www.cathaypacific.com',
        'MH': 'https://www.malaysiaairlines.com',
        'VJ': 'https://www.vietjetair.com',
        'VN': 'https://www.vietnamairlines.com',
        'TR': 'https://www.flyscoot.com',
        '3K': 'https://www.jetstar.com',
        'AK': 'https://www.airasia.com',
        'NH': 'https://www.ana.co.jp',
        'JL': 'https://www.jal.co.jp',
        'KE': 'https://www.koreanair.com',
        # European Airlines
        'BA': 'https://www.britishairways.com',
        'LH': 'https://www.lufthansa.com',
        'AF': 'https://www.airfrance.com',
        'KL': 'https://www.klm.com',
        'VS': 'https://www.virginatlantic.com',
        'IB': 'https://www.iberia.com',
        'LX': 'https://www.swiss.com',
        # American Airlines
        'AA': 'https://www.aa.com',
        'UA': 'https://www.united.com',
        'DL': 'https://www.delta.com',
        'AC': 'https://www.aircanada.com',
        # Oceania
        'QF': 'https://www.qantas.com',
        'NZ': 'https://www.airnewzealand.com'
    }
    return websites.get(carrier_code, None)

def get_aircraft_name(aircraft_code):
    """Get aircraft name from code"""
    aircraft = {
        # Airbus A320 Family
        '318': 'Airbus A318',
        '319': 'Airbus A319',
        '320': 'Airbus A320',
        '321': 'Airbus A321',
        '32A': 'Airbus A320 (Sharklets)',
        '32B': 'Airbus A321 (Sharklets)',
        '32N': 'Airbus A320neo',
        '32Q': 'Airbus A321neo',
        # Airbus A330 Family
        '330': 'Airbus A330',
        '332': 'Airbus A330-200',
        '333': 'Airbus A330-300',
        '338': 'Airbus A330-800neo',
        '339': 'Airbus A330-900neo',
        # Airbus A340 Family
        '342': 'Airbus A340-200',
        '343': 'Airbus A340-300',
        '345': 'Airbus A340-500',
        '346': 'Airbus A340-600',
        # Airbus A350 Family
        '350': 'Airbus A350',
        '351': 'Airbus A350-1000',
        '359': 'Airbus A350-900',
        # Airbus A380
        '388': 'Airbus A380-800',
        '380': 'Airbus A380',
        # Boeing 737 Family
        '733': 'Boeing 737-300',
        '734': 'Boeing 737-400',
        '735': 'Boeing 737-500',
        '736': 'Boeing 737-600',
        '737': 'Boeing 737-700',
        '738': 'Boeing 737-800',
        '739': 'Boeing 737-900',
        '73H': 'Boeing 737-800',
        '73J': 'Boeing 737-900',
        '7M8': 'Boeing 737 MAX 8',
        '7M9': 'Boeing 737 MAX 9',
        # Boeing 747
        '744': 'Boeing 747-400',
        '747': 'Boeing 747',
        '748': 'Boeing 747-8',
        # Boeing 757
        '752': 'Boeing 757-200',
        '753': 'Boeing 757-300',
        # Boeing 767
        '762': 'Boeing 767-200',
        '763': 'Boeing 767-300',
        '764': 'Boeing 767-400',
        # Boeing 777 Family
        '772': 'Boeing 777-200',
        '77L': 'Boeing 777-200LR',
        '773': 'Boeing 777-300',
        '77W': 'Boeing 777-300ER',
        '777': 'Boeing 777',
        # Boeing 787 Dreamliner
        '787': 'Boeing 787',
        '788': 'Boeing 787-8',
        '789': 'Boeing 787-9',
        '78J': 'Boeing 787-10',
        # Regional Jets
        'E75': 'Embraer E175',
        'E90': 'Embraer E190',
        'E95': 'Embraer E195',
        'CR9': 'Bombardier CRJ-900',
        'CRJ': 'Bombardier CRJ',
        # Turboprops
        'AT7': 'ATR 72',
        'AT5': 'ATR 42',
        'DH4': 'Dash 8-400'
    }
    return aircraft.get(aircraft_code, aircraft_code if aircraft_code else 'N/A')

# Test function
if __name__ == "__main__":
    if not AMADEUS_CLIENT_ID or not AMADEUS_CLIENT_SECRET:
        print("ERROR: Amadeus credentials not found in .env")
        exit(1)
    
    searcher = AmadeusFlightSearch()
    
    # Test search
    print("Testing flight search: BOM -> DXB")
    departure = (datetime.now() + timedelta(days=10)).date()
    return_date = (datetime.now() + timedelta(days=17)).date()
    
    try:
        results = searcher.search_flights(
            origin="BOM",
            destination="DXB",
            departure_date=departure,
            return_date=return_date,
            adults=1,
            max_results=5
        )
        
        print(f"\nFound {results['total_offers']} flight offers")
        print(f"Showing {len(results['flights'])} flights:\n")
        
        for i, flight in enumerate(results['flights'], 1):
            print(f"{i}. {flight['price']['currency']} {flight['price']['total']}")
            print(f"   Outbound: {flight['outbound']['carrier']}{flight['outbound']['flight_number']}")
            print(f"   {flight['outbound']['departure']['iata']} -> {flight['outbound']['arrival']['iata']}")
            print(f"   Duration: {format_duration(flight['outbound']['duration'])}")
            print(f"   Stops: {flight['outbound']['stops']}")
            print()
            
    except Exception as e:
        print(f"Error: {e}")
