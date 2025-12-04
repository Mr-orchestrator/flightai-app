# Layover Filter Feature - Direct vs Connecting Flights

## Overview
Users can now filter flights based on their layover preferences, choosing between direct flights, flights with maximum 1 stop, or any flight type.

---

## ✈️ Flight Type Options

### 1. 🔄 Any (with or without layover)
- **Default option**
- Shows all available flights
- Includes direct and multi-stop flights
- **Best For**: Maximum options, lowest prices
- **Example**: Direct, 1-stop, 2-stop flights all shown

### 2. ✈️ Direct flights only
- Only non-stop flights
- No layovers or connections
- Fastest travel time
- **Best For**: Business travelers, time-sensitive trips
- **Example**: BOM → DXB non-stop (3h 30m)

### 3. 🔁 Max 1 stop
- Direct OR flights with exactly 1 layover
- No flights with 2+ stops
- Balance between options and convenience
- **Best For**: Reasonable price with acceptable travel time
- **Example**: BOM → CMB → DXB (with one stop in Colombo)

---

## 🎯 UI Layout

### Location
The flight type selector appears as **Row 2** below the main search options:

```
┌─────────────────────────────────────────────────┐
│  ROW 1: Search Options                          │
│  ┌─────────┬───────────────────┬────────────┐  │
│  │👥 Adults │ 🎫 Cabin Class   │📊 Max      │  │
│  │    1    │    Economy ▼     │ Results 10 │  │
│  └─────────┴───────────────────┴────────────┘  │
│                                                  │
│  ROW 2: Layover Filter                          │
│  ┌──────────────────────────────────────────┐  │
│  │ ✈️ Flight Type                           │  │
│  │ ○ 🔄 Any (with or without layover)       │  │
│  │ ● ✈️ Direct flights only                 │  │
│  │ ○ 🔁 Max 1 stop                          │  │
│  └──────────────────────────────────────────┘  │
│                                                  │
│       [🔍 Search Real-Time Flights]             │
└─────────────────────────────────────────────────┘
```

---

## 🔧 How It Works

### API Integration

#### For "Direct flights only":
```python
amadeus_searcher.search_flights(
    origin="BOM",
    destination="DXB",
    non_stop=True  # ← Amadeus API parameter
)
```

Amadeus API receives `nonStop=true` parameter and returns only direct flights.

#### For "Max 1 stop":
```python
# Step 1: Get all flights
flights = amadeus_searcher.search_flights(...)

# Step 2: Filter results
filtered = [
    f for f in flights 
    if f['outbound']['stops'] <= 1 and 
    f['return']['stops'] <= 1
]
```

Client-side filtering after receiving results.

#### For "Any":
No filtering applied - shows all results from Amadeus.

---

## 📊 Comparison: Flight Types

### Example Route: BOM → DXB (7 days)

#### Any (Default)
```
✅ Found 15 flight offers

Direct:        ₹45,000 | 3h 30m | 0 stops
1 Stop:        ₹22,000 | 8h 15m | 1 stop (CMB)
2 Stops:       ₹18,000 | 14h 30m | 2 stops (DEL, DOH)

Range: ₹18,000 - ₹45,000
```

#### Direct flights only
```
✅ Found 3 flight offers

Air India:     ₹45,000 | 3h 30m | 0 stops
Emirates:      ₹52,000 | 3h 25m | 0 stops
IndiGo:        ₹48,000 | 3h 35m | 0 stops

Range: ₹45,000 - ₹52,000
```

#### Max 1 stop
```
✅ Found 8 flight offers

Direct:        ₹45,000 | 3h 30m | 0 stops
Via Colombo:   ₹22,000 | 8h 15m | 1 stop
Via Delhi:     ₹24,000 | 9h 45m | 1 stop

Range: ₹22,000 - ₹45,000
```

---

## 💰 Price vs Convenience Trade-off

### Direct Flights
**Pros:**
- ✅ Fastest travel time
- ✅ No hassle of changing planes
- ✅ Less risk of missing connections
- ✅ Less tiring

**Cons:**
- ❌ Most expensive (2-3x more)
- ❌ Fewer departure times
- ❌ Limited to routes with direct service

**Typical Premium:** +100-150% over connecting flights

### Max 1 Stop
**Pros:**
- ✅ Much cheaper than direct
- ✅ More flight options
- ✅ Only one layover to manage
- ✅ Good balance of price/time

**Cons:**
- ❌ 2-4 hours longer travel
- ❌ Risk of missed connection
- ❌ More tiring

**Typical Savings:** 40-60% vs direct

### Any Flights
**Pros:**
- ✅ Maximum options
- ✅ Cheapest possible fares
- ✅ Most departure times
- ✅ Most flexibility

**Cons:**
- ❌ May include 2+ stops
- ❌ Very long travel times
- ❌ Multiple connection risks
- ❌ Most exhausting

**Typical Savings:** 50-70% vs direct

---

## 🎯 Use Cases

### 1. Business Trip (Time Sensitive)
```
Selection: ✈️ Direct flights only
Reason: Time is money, minimize travel time
Result: Fastest option, arrive fresh
```

### 2. Leisure Vacation (Price Conscious)
```
Selection: 🔄 Any
Reason: Save money, have time flexibility
Result: Best prices, more destinations
```

### 3. Weekend Getaway (Balanced)
```
Selection: 🔁 Max 1 stop
Reason: Reasonable price + acceptable time
Result: Good compromise
```

### 4. Family Travel
```
Selection: ✈️ Direct flights only
Reason: Kids hate layovers, reduce stress
Result: Smooth journey, happy family
```

### 5. Budget Backpacker
```
Selection: 🔄 Any
Reason: Every rupee counts
Result: Maximum savings
```

---

## 📱 Display Updates

### When Direct Selected:
```
✅ Found 3 direct flight offers from BOM to DXB

💺 Flight 1 - INR 45,000
Total Stops: 0 ← Highlighted
Duration: 3h 30m (Direct)
```

### When Max 1 Stop Selected:
```
✅ Found 8 flight offers (0-1 stops) from BOM to DXB

💺 Flight 1 - INR 22,000
Total Stops: 1
Duration: 8h 15m
Layover: CMB (2h 30m)
```

### When Any Selected:
```
✅ Found 15 flight offers from BOM to DXB

💺 Flight 1 - INR 18,000
Total Stops: 2
Duration: 14h 30m
Layovers: DEL (3h), DOH (2h)
```

---

## ⚙️ Technical Details

### Filtering Logic

#### Direct Flights (API-level):
```python
if non_stop:
    params['nonStop'] = 'true'
# Amadeus returns only direct flights
```

#### Max 1 Stop (Client-side):
```python
filtered_flights = [
    flight for flight in all_flights
    if flight['outbound']['stops'] <= 1 and
    (not flight['return'] or flight['return']['stops'] <= 1)
]
```

**Why client-side?** Amadeus doesn't have a "max stops" parameter, only "nonStop" (boolean).

#### Any Flights:
```python
# No filtering, return all results
return all_flights
```

---

## 🌍 Route Availability

### Routes Commonly Having Direct Flights:
- ✅ BOM → DXB (Mumbai to Dubai)
- ✅ DEL → LHR (Delhi to London)
- ✅ BLR → SIN (Bangalore to Singapore)
- ✅ BOM → LON (Mumbai to London)

### Routes Usually Requiring Connections:
- ❌ COK → SYD (Kochi to Sydney)
- ❌ CCU → LAX (Kolkata to Los Angeles)
- ❌ GOI → ZRH (Goa to Zurich)

### Pro Tip:
If "Direct flights only" returns 0 results, try "Max 1 stop" for better availability.

---

## 🔔 Smart Notifications

The system will inform you:

### If no direct flights:
```
ℹ️ No direct flights available for this route.
   Showing flights with layovers instead.
   Try "Max 1 stop" for fewer connections.
```

### If filtered results empty:
```
⚠️ No flights found with selected filters.
   Try selecting "Any" for more options.
```

---

## 🚀 Future Enhancements

### Possible Additions:
1. **Preferred Layover Cities**
   - Select/avoid specific connection airports
   - "Avoid Delhi" or "Prefer Dubai"

2. **Layover Duration Control**
   - Minimum: 1 hour (tight connection)
   - Maximum: 6 hours (long layover)

3. **Same Airline Only**
   - Reduce luggage re-check risk
   - Better customer service continuity

4. **Max Total Travel Time**
   - Filter by total journey duration
   - E.g., "Under 12 hours only"

5. **Overnight Layover Filter**
   - Exclude flights with night layovers
   - Or find them for hotel deals

---

## ✅ Benefits

### For Users:
- ✅ **Control**: Choose layover preference
- ✅ **Time Saving**: Skip multi-stop results if in hurry
- ✅ **Money Saving**: Find cheapest options easily
- ✅ **Stress Reduction**: Fewer connections = less worry

### For System:
- ✅ **API Efficiency**: Direct filter reduces API load
- ✅ **Better UX**: Relevant results only
- ✅ **Professional**: Like booking platforms (Expedia, Kayak)

---

## 📋 Quick Reference

### Decision Matrix:

| Priority | Select | Get |
|----------|--------|-----|
| Speed | Direct only | Fastest, expensive |
| Price | Any | Cheapest, slowest |
| Balance | Max 1 stop | Middle ground |
| Comfort | Direct only | Least tiring |
| Options | Any | Most choices |

### Default Recommendations:

**Business Travel:** Direct
**Family Vacation:** Max 1 stop
**Solo Backpacking:** Any
**Weekend Trip:** Direct or Max 1 stop
**Group Travel:** Max 1 stop

---

Your flight search now offers **professional-grade filtering**! 🎉
