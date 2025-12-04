# Quick Start Guide - AI Trip Planner with IATA Extraction

## What's New? 🚀

Your system now **extracts IATA airport codes** from natural language using Gemini AI!

## How It Works

### 1. Select Base Airport 🛫
Choose from 12 major Indian international airports:
- Mumbai (BOM), Delhi (DEL), Bangalore (BLR), etc.

### 2. Describe Your Trip 📝
Just type naturally:
- "7 days in Switzerland"
- "weekend trip to Dubai"
- "2 weeks vacation in Singapore"

### 3. AI Extracts Everything 🤖
- **Destination IATA**: ZRH (Zurich), DXB (Dubai), SIN (Singapore)
- **Duration**: 7 days, 2 days, 14 days
- **Dates**: Departure and return dates
- **Confidence**: High/Medium/Low rating

## Visual Flight Route Display

The UI shows a beautiful visual route:

```
┌──────────┐       ✈️       ┌──────────┐
│   BOM    │   ─────────>   │   DXB    │
│  Mumbai  │                │  Dubai   │
└──────────┘                └──────────┘
                            (HIGH Confidence)
```

## Example Queries

### Direct City Names
```
"7 days in Paris"           → CDG (Paris Charles de Gaulle)
"weekend in London"         → LHR (London Heathrow)
"10 days in Singapore"      → SIN (Singapore)
```

### Country Names (Uses Main Airport)
```
"trip to Switzerland"       → ZRH (Zurich)
"vacation in Thailand"      → BKK (Bangkok)
"visiting Japan"            → NRT (Tokyo Narita)
```

### Natural Language
```
"going to Dubai for 5 days" → DXB, 5 days
"weekend getaway to Goa"    → GOI, 2 days
"2 week Europe trip"        → Extracts best match
```

## Supported Destinations (50+ Airports)

### Asia
- Dubai (DXB), Singapore (SIN), Bangkok (BKK)
- Hong Kong (HKG), Tokyo (NRT), Seoul (ICN)
- Kuala Lumpur (KUL), Doha (DOH), Abu Dhabi (AUH)

### Europe
- London (LHR), Paris (CDG), Frankfurt (FRA)
- Amsterdam (AMS), Zurich (ZRH), Rome (FCO)
- Barcelona (BCN), Madrid (MAD), Istanbul (IST)

### North America
- New York (JFK), Los Angeles (LAX), San Francisco (SFO)
- Chicago (ORD), Toronto (YYZ), Vancouver (YVR)

### Others
- Sydney (SYD), Melbourne (MEL), Auckland (AKL)
- Johannesburg (JNB), Cairo (CAI)

## Confidence Levels

### 🟢 High (Green)
- Exact city match: "Paris" → CDG
- Popular destination: "Dubai" → DXB

### 🔵 Medium (Blue)
- Country inference: "Thailand" → BKK
- Partial match

### 🟡 Low (Yellow)
- Ambiguous query
- Fallback regex used

## Technical Details

### Files Added
- **`iata_extractor.py`**: Core IATA extraction logic
- **Updated `app.py`**: Enhanced UI with route display

### AI Models Used
1. **Gemini 2.5 Flash** - Primary model (fastest)
2. **Gemini 2.5 Pro** - Fallback (more accurate)
3. **Regex Parser** - Final fallback

### API Flow
```
User Query
    ↓
Gemini AI (IATA Extraction)
    ↓
Gemini AI (Duration Extraction)
    ↓
Combine Results
    ↓
Display Route: ORIGIN → DESTINATION
```

## Testing

Run the IATA extractor standalone:
```bash
python iata_extractor.py
```

Expected output:
```
Query: plan trip to swiss for 7 days
  Destination: Zurich
  IATA: ZRH
  Confidence: high
  Fallback: False
```

## Launch the UI

```bash
streamlit run app.py
```

Access at: http://localhost:8501

## What Makes This Unique?

✅ **No manual IATA lookup** - AI does it automatically
✅ **Indian airport base** - Dropdown selection
✅ **Natural language** - No need for structured queries
✅ **Visual route display** - Beautiful UI
✅ **Confidence scoring** - Know when to trust results
✅ **50+ destinations** - Covers major international airports
✅ **Dual extraction** - Gets both IATA and duration in one go

## Next Steps

You can now integrate this with:
- Flight search APIs (Amadeus credentials already in .env)
- Hotel booking systems
- Travel itinerary builders
- Price comparison tools

The system gives you clean route data:
```python
{
  "origin_iata": "BOM",
  "destination_iata": "DXB",
  "duration_days": 7,
  "departure_date": "2025-12-12",
  "return_date": "2025-12-19",
  "confidence": "high"
}
```

Perfect for passing to flight booking APIs! 🎯
