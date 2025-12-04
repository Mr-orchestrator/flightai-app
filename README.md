# AI Trip Planner with IATA Code Extraction

AI-powered system to extract **destination IATA codes** and **trip duration** from natural language queries using Google Gemini with robust fallback parsing.

## Features

### 🎯 IATA Code Extraction (NEW!)
- **Smart Destination Detection**: AI extracts destination city/country from natural language
- **Automatic IATA Codes**: Converts destinations to 3-letter airport codes
- **Indian Airport Base**: Dropdown selection of 12 major Indian international airports
- **Confidence Scoring**: High/Medium/Low confidence ratings for extractions
- **Popular Destinations**: Covers 50+ international airports worldwide

### ⏱️ Duration Extraction
- **AI-First Extraction**: Uses Google Gemini models to intelligently parse trip duration
- **Robust Fallback**: Regex-based local parser when AI fails
- **Flexible Input**: Handles various formats:
  - Digits: "7 days", "10 nights"
  - Words: "one week", "five days"  
  - Special: "weekend" (2 days), "a week and a half" (11 days)
  - Ranges: "10-12 days" (uses lower bound)
- **Multiple Model Support**: Tries several Gemini variants automatically
- **Date Calculation**: Returns departure (+8 days from today) and return dates

### 🎨 Beautiful Web UI
- Visual flight route display (Origin → Destination)
- Color-coded confidence indicators
- Query history tracking
- Real-time AI extraction
- **Real-time flight search with Amadeus API** (NEW!)
  - Search actual flights between extracted routes
  - View prices, timings, stops, and carriers
  - Compare multiple flight options
  - See outbound and return flight details

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API Keys

Create a `.env` file in the project root:

```env
GOOGLE_API_KEY=your_google_api_key_here
AMADEUS_CLIENT_ID=your_amadeus_client_id
AMADEUS_CLIENT_SECRET=your_amadeus_secret
```

**Get API Keys:**
- **Google Gemini**: https://makersuite.google.com/app/apikey
- **Amadeus** (for travel booking): https://developers.amadeus.com/

### 3. Verify Setup

List available Gemini models:

```bash
python ge.py
```

## Usage

### Web UI (Recommended)

Launch the interactive web interface:

```bash
streamlit run app.py
```

Features:
- Clean, intuitive interface
- Real-time duration extraction
- Query history tracking
- API status monitoring
- Example queries for quick testing

### As a Module

```python
from core import get_trip_dates
import google.generativeai as genai
import os
from dotenv import load_dotenv

# Configure
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Extract trip duration
result = get_trip_dates(
    origin_text="Mumbai",
    user_query="plan a 7 day trip to Switzerland"
)

print(f"Duration: {result['duration_days']} days")
print(f"Departure: {result['departure_date']}")
print(f"Return: {result['return_date']}")
print(f"Model used: {result['model_used']}")
print(f"Used fallback: {result['used_fallback']}")
```

### As a Script

Run the example queries:

```bash
python core.py
```

## Files

- **`app.py`**: Streamlit web UI with IATA extraction and flight search (recommended)
- **`iata_extractor.py`**: AI-powered IATA code extraction module
- **`amadeus_flights.py`**: Real-time flight search using Amadeus API
- **`core.py`**: Trip duration extraction module
- **`ge.py`**: Utility to list available Gemini models
- **`test_basic.py`**: Test suite for validation
- **`.env`**: API credentials (create this)
- **`requirements.txt`**: Python dependencies
- **`USAGE_GUIDE.md`**: Detailed usage guide

## API Response Format

```python
{
    "duration_days": int,          # Extracted duration (1-365)
    "departure_date": date,        # Today + 8 days
    "return_date": date,           # Departure + duration
    "raw_model_output": str|None,  # Raw AI response
    "model_used": str|None,        # Which Gemini model succeeded
    "used_fallback": bool,         # True if local parser was used
    "error": str|None              # Error message if any
}
```

## Supported Models

The system tries these Gemini models in order:
- gemini-2.5-pro
- gemini-2.5-flash
- gemini-pro-latest
- gemini-flash-latest

## Error Handling

- If all Gemini models fail → Falls back to local regex parser
- If duration is invalid (<1 or >365 days) → Uses fallback
- If no duration found → Returns default 7 days

## Indian Airports Supported

The system includes 12 major Indian international airports:
- **DEL** - New Delhi (Indira Gandhi International)
- **BOM** - Mumbai (Chhatrapati Shivaji Maharaj International)
- **BLR** - Bangalore (Kempegowda International)
- **HYD** - Hyderabad (Rajiv Gandhi International)
- **MAA** - Chennai International
- **CCU** - Kolkata (Netaji Subhas Chandra Bose International)
- **COK** - Kochi (Cochin International)
- **AMD** - Ahmedabad (Sardar Vallabhbhai Patel International)
- **PNQ** - Pune Airport
- **GOI** - Goa International
- **TRV** - Thiruvananthapuram International
- **IXC** - Chandigarh International

## Examples

```python
# IATA + Duration Extraction
"7 days in Switzerland"  # → ZRH, 7 days
"weekend trip to Dubai"  # → DXB, 2 days
"2 weeks in Singapore"   # → SIN, 14 days
"visiting London for 5 days"  # → LHR, 5 days
"vacation in Thailand"   # → BKK, 7 days (default)

# Duration formats supported
"plan a 2 week vacation"  # → 14 days
"5 day trip to Paris"  # → 5 days
"one week holiday"  # → 7 days
"weekend getaway"  # → 2 days
"a week and a half"  # → 11 days
"10-14 days in Europe"  # → 10 days (uses lower bound)
```

## Troubleshooting

**API Key not found:**
- Ensure `.env` exists with `GOOGLE_API_KEY=...`
- Check the key is valid at https://makersuite.google.com

**Module not found:**
- Run `pip install -r requirements.txt`

**All models failing:**
- Check internet connection
- Verify API key is active
- The system will use fallback parser automatically

## License

MIT
