"""
Quick Backend Test Script
Verifies all backend features are working
"""

import os
from dotenv import load_dotenv

load_dotenv()

print("=" * 60)
print("BACKEND FUNCTIONALITY TEST")
print("=" * 60)

# Test 1: Environment Variables
print("\n1. Testing Environment Variables...")
google_api = os.getenv("GOOGLE_API_KEY")
amadeus_id = os.getenv("AMADEUS_CLIENT_ID")
amadeus_secret = os.getenv("AMADEUS_CLIENT_SECRET")

print(f"   Google API Key: {'✓ Set' if google_api else '✗ Missing'}")
print(f"   Amadeus Client ID: {'✓ Set' if amadeus_id else '✗ Missing'}")
print(f"   Amadeus Secret: {'✓ Set' if amadeus_secret else '✗ Missing'}")

# Test 2: Import Core Modules
print("\n2. Testing Module Imports...")
try:
    from core import get_trip_dates
    print("   ✓ core.py imported successfully")
except Exception as e:
    print(f"   ✗ core.py import failed: {e}")

try:
    from iata_extractor import extract_iata_from_query, get_indian_airports_list
    print("   ✓ iata_extractor.py imported successfully")
except Exception as e:
    print(f"   ✗ iata_extractor.py import failed: {e}")

try:
    from amadeus_flights import AmadeusFlightSearch
    print("   ✓ amadeus_flights.py imported successfully")
except Exception as e:
    print(f"   ✗ amadeus_flights.py import failed: {e}")

# Test 3: IATA Extraction
print("\n3. Testing IATA Extraction...")
try:
    result = extract_iata_from_query("7 days in Dubai", "BOM")
    if result and result.get('iata_code'):
        print(f"   ✓ Extracted: {result['iata_code']} ({result['destination_city']})")
        print(f"   Confidence: {result['confidence']}")
    else:
        print("   ✗ IATA extraction returned no result")
except Exception as e:
    print(f"   ✗ IATA extraction failed: {e}")

# Test 4: Duration Extraction
print("\n4. Testing Duration Extraction...")
try:
    result = get_trip_dates("BOM", "7 days in Dubai")
    if result:
        print(f"   ✓ Duration: {result['duration_days']} days")
        print(f"   Departure: {result['departure_date']}")
        print(f"   Return: {result['return_date']}")
        print(f"   Model used: {result['model_used']}")
    else:
        print("   ✗ Duration extraction returned no result")
except Exception as e:
    print(f"   ✗ Duration extraction failed: {e}")

# Test 5: Amadeus Connection
print("\n5. Testing Amadeus API Connection...")
if amadeus_id and amadeus_secret:
    try:
        amadeus = AmadeusFlightSearch()
        print("   ✓ Amadeus client initialized")
        
        # Try to get token
        try:
            token = amadeus.get_access_token()
            if token:
                print("   ✓ Access token obtained successfully")
            else:
                print("   ✗ Could not get access token")
        except Exception as e:
            print(f"   ✗ Token request failed: {e}")
            
    except Exception as e:
        print(f"   ✗ Amadeus initialization failed: {e}")
else:
    print("   ⚠ Skipped (Amadeus credentials not configured)")

# Test 6: Airport List
print("\n6. Testing Airport List...")
try:
    airports = get_indian_airports_list()
    if airports and len(airports) > 0:
        print(f"   ✓ Loaded {len(airports)} airports")
        print(f"   Sample: {airports[0] if airports else 'None'}")
    else:
        print("   ✗ No airports loaded")
except Exception as e:
    print(f"   ✗ Airport list failed: {e}")

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)

# Summary
print("\nRECOMMENDATIONS:")
print("1. If any ✗ appears above, that feature needs fixing")
print("2. Make sure .env file exists with all API keys")
print("3. Run: pip install -r requirements.txt (if any imports failed)")
print("4. For Amadeus issues, check credentials at developers.amadeus.com")
print("5. For Gemini issues, check key at makersuite.google.com")
print("\n" + "=" * 60)
