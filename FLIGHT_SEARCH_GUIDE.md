# Flight Search Integration Guide

## Complete Workflow: From NLP Query to Real Flights ✈️

Your system now has **end-to-end trip planning**:
1. **User Query** → Natural language input
2. **AI Extraction** → Gets IATA codes + duration
3. **Flight Search** → Real-time flights from Amadeus

---

## How to Use

### Step 1: Enter Trip Query 📝
Select your Indian base airport and describe your trip:
```
Examples:
- "7 days in Dubai"
- "weekend trip to Singapore"
- "2 weeks vacation in Switzerland"
```

### Step 2: AI Extracts Details 🤖
Gemini AI automatically extracts:
- **Origin**: Selected Indian airport (e.g., BOM)
- **Destination**: Extracted IATA code (e.g., DXB)
- **Duration**: Trip length in days
- **Dates**: Departure and return dates

### Step 3: Search Real Flights 🔍
Click **"Search Real-Time Flights"** button to:
- Query Amadeus API with extracted route
- Get live flight offers with prices
- See detailed flight information

---

## Flight Information Displayed

### For Each Flight:
✅ **Price** - Total cost in INR/USD/etc.
✅ **Carrier** - Airline code and flight number
✅ **Timing** - Departure and arrival times
✅ **Duration** - Total travel time
✅ **Stops** - Number of connections
✅ **Seats** - Available bookable seats
✅ **Terminals** - Departure/arrival terminal info

### Outbound + Return
- Full details for both directions
- Separate timing for each leg
- Different carriers for each flight if applicable

---

## Example Usage

### Query: "7 days in Dubai"

**AI Extraction:**
```
Origin:      BOM (Mumbai)
Destination: DXB (Dubai)
Duration:    7 days
Departure:   Dec 12, 2025
Return:      Dec 19, 2025
```

**Click "Search Real-Time Flights"**

**Results Show:**
```
💺 Flight 1 - INR 22,557.00
   🛫 Outbound: UL144
   🏛️ BOM → CMB → DXB
   ⏱️ 26h 35m | 🔄 1 stop
   
   🛬 Return: UL143
   🏛️ DXB → CMB → BOM
   ⏱️ 24h 20m | 🔄 1 stop

💺 Flight 2 - INR 24,421.00
   🛫 Outbound: UL142
   🏛️ BOM → CMB → DXB
   ⏱️ 15h 30m | 🔄 1 stop
   
   [... more flights ...]
```

---

## Technical Details

### Amadeus Test API
- Uses **test environment** (free tier)
- Returns real flight structure
- Limited to test data routes

### API Endpoints Used
```python
Authentication: 
  POST /v1/security/oauth2/token

Flight Search:
  GET /v2/shopping/flight-offers
```

### Parameters Sent
```python
{
  "originLocationCode": "BOM",
  "destinationLocationCode": "DXB",
  "departureDate": "2025-12-12",
  "returnDate": "2025-12-19",
  "adults": 1,
  "currencyCode": "INR",
  "max": 10
}
```

### Response Parsed
```python
{
  "total_offers": 5,
  "flights": [
    {
      "price": {"total": "22557.00", "currency": "INR"},
      "outbound": {
        "departure": {"iata": "BOM", "time": "..."},
        "arrival": {"iata": "DXB", "time": "..."},
        "duration": "PT26H35M",
        "stops": 1,
        "carrier": "UL"
      },
      "return": {...}
    }
  ]
}
```

---

## Error Handling

### No Flights Found
```
"No flights found for the selected route and dates."
```
**Reasons:**
- Route not available in test environment
- Dates too far in future/past
- No service on that route

### API Credentials Not Set
```
"Configure Amadeus API credentials to search flights"
```
**Fix:** Add credentials to `.env`:
```env
AMADEUS_CLIENT_ID=your_client_id
AMADEUS_CLIENT_SECRET=your_secret
```

### Invalid IATA Code
```
"Flight search error: Invalid IATA code"
```
**Reason:** Destination extraction failed
**Fix:** Try more specific query (city name instead of country)

---

## Supported Routes (Test Environment)

### Common Working Routes:
✅ BOM → DXB (Mumbai → Dubai)
✅ DEL → LHR (Delhi → London)
✅ BLR → SIN (Bangalore → Singapore)
✅ MAA → CDG (Chennai → Paris)

### May Not Work:
❌ Very small destinations
❌ Domestic Indian flights
❌ Routes with no connectivity

---

## Production Considerations

### To Use in Production:

1. **Switch to Production API**
   ```python
   # In amadeus_flights.py, change:
   AMADEUS_AUTH_URL = "https://api.amadeus.com/v1/security/oauth2/token"
   AMADEUS_FLIGHT_SEARCH_URL = "https://api.amadeus.com/v2/shopping/flight-offers"
   ```

2. **Get Production Credentials**
   - Sign up at https://developers.amadeus.com
   - Move app to production
   - Replace test credentials

3. **Add More Features**
   - Cabin class selection (Economy/Business)
   - Number of passengers
   - Direct flights only filter
   - Sort by price/duration
   - Booking integration

---

## Data Flow Diagram

```
User Input
    ↓
"7 days in Dubai"
    ↓
┌──────────────────────┐
│ Gemini AI Extraction │
├──────────────────────┤
│ Destination: DXB     │
│ Duration: 7 days     │
└──────────────────────┘
    ↓
┌──────────────────────┐
│ Trip Details Display │
├──────────────────────┤
│ BOM → DXB           │
│ Dec 12 - Dec 19     │
│ [Search Flights]    │ ← User clicks
└──────────────────────┘
    ↓
┌──────────────────────┐
│ Amadeus API Call     │
├──────────────────────┤
│ GET /flight-offers   │
│ origin=BOM          │
│ destination=DXB     │
│ dates=...           │
└──────────────────────┘
    ↓
┌──────────────────────┐
│ Flight Results       │
├──────────────────────┤
│ 5 offers found      │
│ Prices from ₹22,557 │
│ View details ↓      │
└──────────────────────┘
```

---

## Benefits of This Integration

✅ **Seamless Flow** - From idea to real flights in 2 clicks
✅ **No Manual Entry** - AI extracts everything automatically
✅ **Real Data** - Actual flights from global booking systems
✅ **Complete Info** - All details needed for booking decision
✅ **Indian Focus** - Starts from major Indian airports
✅ **Smart Extraction** - Handles natural language input

---

## Next Steps

You can now extend this to:
1. **Hotel Search** - Add accommodation APIs
2. **Price Tracking** - Monitor flight prices over time
3. **Multi-city Trips** - Extend IATA extraction for multiple destinations
4. **Booking Integration** - Add payment and booking flow
5. **Itinerary Builder** - Combine flights, hotels, activities

The foundation is ready - you have:
- ✅ NLP parsing
- ✅ IATA extraction  
- ✅ Date calculation
- ✅ Flight search API
- ✅ Beautiful UI

Perfect for building a complete travel platform! 🚀
