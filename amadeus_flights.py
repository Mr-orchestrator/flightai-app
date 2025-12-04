"""
Amadeus Flight Search Integration
Search real-time flights using origin/destination IATA codes
"""
import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

AMADEUS_CLIENT_ID = os.getenv("AMADEUS_CLIENT_ID")
AMADEUS_CLIENT_SECRET = os.getenv("AMADEUS_CLIENT_SECRET")

# Amadeus API endpoints
AMADEUS_AUTH_URL = "https://test.api.amadeus.com/v1/security/oauth2/token"
AMADEUS_FLIGHT_SEARCH_URL = "https://test.api.amadeus.com/v2/shopping/flight-offers"

class AmadeusFlightSearch:
    def __init__(self):
        self.client_id = AMADEUS_CLIENT_ID
        self.client_secret = AMADEUS_CLIENT_SECRET
        self.access_token = None
        self.token_expiry = None
    
    def get_access_token(self):
        """Get or refresh Amadeus access token"""
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
