# Cabin Class Selection Feature

## Overview
Users can now select their preferred cabin class and number of passengers before searching flights, giving them complete control over their search preferences.

---

## ✈️ Search Options Available

### 1. Number of Adults (👥)
- **Range**: 1-9 passengers
- **Default**: 1 adult
- **Purpose**: Search for group travel

### 2. Cabin Class (🎫)
Four cabin classes available:

| Option | Display Name | Description |
|--------|--------------|-------------|
| `ECONOMY` | Economy | Standard economy seating |
| `PREMIUM_ECONOMY` | Premium Economy | Enhanced economy with more space |
| `BUSINESS` | Business | Business class with lie-flat seats |
| `FIRST` | First Class | Luxury first class service |

**Default**: Economy

### 3. Max Results (📊)
- **Range**: 1-20 flight offers
- **Default**: 10 offers
- **Purpose**: Control how many options to display

---

## 🎨 UI Layout

### Location
The selection controls appear **directly above the "Search Real-Time Flights" button**:

```
┌─────────────────────────────────────────────────┐
│  Route Display (BOM → DXB)                      │
│  Duration, Dates, etc.                          │
├─────────────────────────────────────────────────┤
│                                                  │
│  ┌──────────┬──────────────────┬─────────────┐ │
│  │ 👥 Adults│  🎫 Cabin Class  │📊 Max Results│ │
│  │    1     │    Economy       │     10       │ │
│  └──────────┴──────────────────┴─────────────┘ │
│                                                  │
│       [🔍 Search Real-Time Flights]             │
│                                                  │
└─────────────────────────────────────────────────┘
```

### Spacing
- 3-column layout (equal width)
- Clean spacing between options
- Button centered below selections

---

## 🔧 How It Works

### User Flow
1. **Extract Trip Details** - AI gets route and dates
2. **Select Preferences**:
   - Choose number of adults
   - Select cabin class
   - Set max results
3. **Click Search** - System queries Amadeus with preferences
4. **View Results** - Flights matching selected class displayed

### API Integration
```python
amadeus_searcher.search_flights(
    origin="BOM",
    destination="DXB",
    departure_date="2025-12-12",
    return_date="2025-12-19",
    adults=2,                    # ← From selection
    travel_class="BUSINESS",     # ← From selection
    max_results=15               # ← From selection
)
```

---

## 📊 Cabin Class Differences

### Economy
- **Price**: Lowest fares
- **Seat**: Standard seating
- **Baggage**: Basic allowance
- **Service**: Standard meals
- **Best For**: Budget travelers

### Premium Economy
- **Price**: 20-50% more than economy
- **Seat**: Extra legroom, wider seats
- **Baggage**: Additional allowance
- **Service**: Enhanced meals, priority boarding
- **Best For**: Comfort on long flights

### Business
- **Price**: 2-4x economy
- **Seat**: Lie-flat seats, more space
- **Baggage**: Generous allowance
- **Service**: Premium meals, lounge access
- **Best For**: Comfort, productivity

### First Class
- **Price**: 3-5x economy (or more)
- **Seat**: Private suites, maximum space
- **Baggage**: Maximum allowance
- **Service**: Gourmet meals, exclusive lounges
- **Best For**: Luxury travel

---

## 💰 Price Impact Examples

### Route: BOM → DXB (7 days)

| Class | Typical Price (INR) | Difference |
|-------|---------------------|------------|
| Economy | ₹22,000 | Base |
| Premium Economy | ₹35,000 | +59% |
| Business | ₹75,000 | +241% |
| First Class | ₹150,000+ | +582% |

*Prices are approximate and vary by airline, season, and availability*

---

## 🎯 Use Cases

### 1. Family Travel
```
👥 Adults: 4
🎫 Class: Economy
📊 Results: 15

→ Compare multiple family-friendly options
```

### 2. Business Trip
```
👥 Adults: 1
🎫 Class: Business
📊 Results: 10

→ Find lie-flat seats for productivity
```

### 3. Honeymoon/Luxury
```
👥 Adults: 2
🎫 Class: First Class
📊 Results: 5

→ Luxury experience, fewer options needed
```

### 4. Group Travel
```
👥 Adults: 8
🎫 Class: Economy
📊 Results: 20

→ Maximum options for large group
```

---

## 🔄 Search Behavior

### What Changes with Class Selection?

#### Economy Search
- **Results**: Most availability
- **Airlines**: All carriers
- **Options**: Maximum variety
- **Prices**: Widest range

#### Business/First Search
- **Results**: Limited availability
- **Airlines**: Premium carriers focus
- **Options**: Fewer flights (not all routes have premium)
- **Prices**: Higher, more consistent

### Amadeus API Parameters
```json
{
  "originLocationCode": "BOM",
  "destinationLocationCode": "DXB",
  "departureDate": "2025-12-12",
  "returnDate": "2025-12-19",
  "adults": 1,
  "travelClass": "BUSINESS",  // ← Filters results
  "currencyCode": "INR",
  "max": 10
}
```

---

## 📱 Display Updates

### Flight Cards Show Selected Class
When you select **Business**, results show:
```
💰 INR 75,000
Cabin Class: BUSINESS
🏢 Emirates Business Class
```

### Consistency Check
- Selected class in options: **Business**
- Results display: **Business**
- Flight segments: **Business** for each leg

---

## ⚙️ Technical Details

### State Management
```python
# Session state tracks selections
num_adults = st.number_input("👥 Adults", ...)
cabin_class = st.selectbox("🎫 Cabin Class", ...)
max_results = st.number_input("📊 Max Results", ...)

# Passed to search function
amadeus_searcher.search_flights(
    adults=num_adults,
    travel_class=cabin_class,
    max_results=max_results
)
```

### Validation
- **Adults**: Automatically constrained to 1-9
- **Class**: Dropdown prevents invalid values
- **Results**: Limited to 1-20 to avoid API limits

---

## 🚀 Future Enhancements

### Possible Additions:
1. **Children & Infants**
   - Add child/infant passenger fields
   - Age-specific pricing

2. **Direct Flights Only**
   - Checkbox to filter non-stop flights
   - Useful for business travelers

3. **Flexible Dates**
   - ±3 days option
   - Find cheaper nearby dates

4. **Preferred Airlines**
   - Multi-select for airline filtering
   - Loyalty program preferences

5. **Max Stops Filter**
   - Select 0 (direct), 1, or 2+ stops
   - Balance price vs. convenience

6. **Baggage Options**
   - No bags, 1 bag, 2+ bags
   - Filter by baggage needs

---

## ✅ Benefits

### For Users:
- ✅ **Control**: Choose exact preferences
- ✅ **Relevant Results**: Only see preferred class
- ✅ **Group Booking**: Easy multi-passenger search
- ✅ **Time Saving**: Fewer irrelevant results

### For System:
- ✅ **Targeted Queries**: More efficient API calls
- ✅ **Better UX**: Users get what they want
- ✅ **Professional**: Like commercial booking sites
- ✅ **Flexible**: Easy to add more filters

---

## 📋 Quick Reference

### Default Values
```
Adults: 1
Cabin: Economy
Results: 10
```

### Common Selections

**Solo Budget Travel:**
- Adults: 1, Economy, 10 results

**Couple Business:**
- Adults: 2, Business, 10 results

**Family Vacation:**
- Adults: 4, Economy, 15 results

**Luxury Honeymoon:**
- Adults: 2, First, 5 results

**Group Tour:**
- Adults: 8-9, Economy, 20 results

---

Your flight search is now as flexible as professional booking platforms! 🎉
