"""
Streamlit UI for AI Trip Duration Recommender with IATA Code Extraction
Run with: streamlit run app.py
"""
import streamlit as st
from datetime import datetime
import os
from dotenv import load_dotenv

# Import core functionality
from core import get_trip_dates
from iata_extractor import extract_iata_from_query, get_indian_airports_list, INDIAN_AIRPORTS
from amadeus_flights import AmadeusFlightSearch, format_duration, format_datetime, get_airline_name, get_aircraft_name, get_airline_website
try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

# Load environment variables
load_dotenv()

# Configure page
st.set_page_config(
    page_title="FlightAI - Smart Flight Search & Booking",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Load custom fonts
st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=Poppins:wght@400;500;600;700;800&display=swap" rel="stylesheet">
""", unsafe_allow_html=True)

# Custom CSS for professional airline-grade UI
st.markdown("""
<style>
    /* Import Fonts */
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }
    
    /* Main theme colors - Lufthansa inspired */
    :root {
        --primary-blue: #05164D;
        --accent-yellow: #F9B233;
        --light-bg: #F8F9FB;
        --white: #FFFFFF;
        --text-primary: #05164D;
        --text-secondary: #6B7280;
        --border-light: #E5E7EB;
        --success-green: #059669;
        --gradient-primary: linear-gradient(135deg, #05164D 0%, #1E3A8A 100%);
        --gradient-accent: linear-gradient(135deg, #F9B233 0%, #FBBF24 100%);
        --shadow-sm: 0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24);
        --shadow-md: 0 4px 6px rgba(0,0,0,0.1), 0 2px 4px rgba(0,0,0,0.06);
        --shadow-lg: 0 10px 15px rgba(0,0,0,0.1), 0 4px 6px rgba(0,0,0,0.05);
        --shadow-xl: 0 20px 25px rgba(0,0,0,0.15), 0 8px 10px rgba(0,0,0,0.1);
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display: none;}
    
    /* Main container styling */
    .main {
        background: var(--light-bg);
        padding: 0 !important;
    }
    
    .block-container {
        padding: 3rem 2rem !important;
        max-width: 1600px !important;
    }
    
    /* Professional Header */
    .airline-header {
        background: var(--white);
        padding: 1.5rem 3rem;
        box-shadow: var(--shadow-sm);
        border-bottom: 3px solid var(--accent-yellow);
        margin-bottom: 2rem;
        position: sticky;
        top: 0;
        z-index: 1000;
    }
    
    /* Flight Card - Premium Design */
    .flight-card {
        background: var(--white);
        border-radius: 16px;
        padding: 0;
        margin-bottom: 1.5rem;
        border: 1px solid var(--border-light);
        overflow: hidden;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: var(--shadow-md);
    }
    
    .flight-card:hover {
        transform: translateY(-8px);
        box-shadow: var(--shadow-xl);
        border-color: var(--accent-yellow);
    }
    
    .flight-card-header {
        background: var(--gradient-primary);
        padding: 1.5rem 2rem;
        color: var(--white);
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .flight-card-body {
        padding: 2rem;
    }
    
    /* Premium Buttons */
    .stButton > button {
        background: var(--gradient-primary);
        color: var(--white);
        border: none;
        padding: 1rem 2.5rem;
        font-weight: 700;
        font-size: 1rem;
        letter-spacing: 0.5px;
        border-radius: 12px;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: var(--shadow-md);
        text-transform: uppercase;
    }
    
    .stButton > button:hover {
        transform: translateY(-3px) scale(1.02);
        box-shadow: var(--shadow-xl);
        background: linear-gradient(135deg, #1E3A8A 0%, #3B82F6 100%);
    }
    
    .stButton > button:active {
        transform: translateY(-1px) scale(0.98);
    }
    
    /* Secondary Buttons */
    .stButton > button[kind="secondary"] {
        background: var(--white);
        color: var(--primary-blue);
        border: 2px solid var(--primary-blue);
    }
    
    /* Premium Input Fields */
    .stTextInput input, .stTextArea textarea, .stSelectbox select, .stNumberInput input {
        border-radius: 12px;
        border: 2px solid var(--border-light);
        padding: 1rem 1.25rem;
        font-size: 1rem;
        transition: all 0.3s;
        background: var(--white);
        font-weight: 500;
    }
    
    .stTextInput input:focus, .stTextArea textarea:focus, .stSelectbox select:focus, .stNumberInput input:focus {
        border-color: var(--accent-yellow);
        box-shadow: 0 0 0 4px rgba(249, 178, 51, 0.1);
        outline: none;
    }
    
    /* Premium Metrics */
    [data-testid="stMetricValue"] {
        font-size: 2.5rem;
        font-weight: 800;
        color: var(--primary-blue);
        font-family: 'Poppins', sans-serif;
        line-height: 1;
    }
    
    [data-testid="stMetricLabel"] {
        font-size: 0.875rem;
        color: var(--text-secondary);
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 0.5rem;
    }
    
    [data-testid="stMetricDelta"] {
        font-size: 0.875rem;
        font-weight: 600;
    }
    
    /* Selectbox and number input */
    .stSelectbox, .stNumberInput {
        border-radius: 8px;
    }
    
    /* Radio buttons */
    .stRadio > label {
        font-weight: 600;
        color: #1A1A1A;
        font-size: 1rem;
    }
    
    /* Premium Expander - Flight Details */
    .streamlit-expanderHeader {
        background: var(--white);
        border: 2px solid var(--border-light);
        border-radius: 16px;
        font-weight: 700;
        font-size: 1.125rem;
        color: var(--primary-blue);
        padding: 1.5rem 2rem;
        transition: all 0.3s;
        box-shadow: var(--shadow-sm);
    }
    
    .streamlit-expanderHeader:hover {
        background: var(--gradient-primary);
        color: var(--white);
        border-color: var(--primary-blue);
        box-shadow: var(--shadow-md);
        transform: translateX(8px);
    }
    
    .streamlit-expanderContent {
        border: 2px solid var(--border-light);
        border-top: none;
        border-radius: 0 0 16px 16px;
        padding: 2rem;
        background: var(--white);
    }
    
    /* Premium Alert Messages */
    .stSuccess {
        background: linear-gradient(135deg, #059669 0%, #10B981 100%);
        color: var(--white);
        border-radius: 12px;
        padding: 1.25rem 1.5rem;
        border: none;
        font-weight: 600;
        box-shadow: var(--shadow-md);
    }
    
    .stInfo {
        background: var(--gradient-primary);
        color: var(--white);
        border-radius: 12px;
        padding: 1.25rem 1.5rem;
        border: none;
        font-weight: 600;
        box-shadow: var(--shadow-md);
    }
    
    .stWarning {
        background: linear-gradient(135deg, #F59E0B 0%, #F9B233 100%);
        color: var(--primary-blue);
        border-radius: 12px;
        padding: 1.25rem 1.5rem;
        border: none;
        font-weight: 600;
        box-shadow: var(--shadow-md);
    }
    
    .stError {
        background: linear-gradient(135deg, #DC2626 0%, #EF4444 100%);
        color: var(--white);
        border-radius: 12px;
        padding: 1.25rem 1.5rem;
        border: none;
        font-weight: 600;
        box-shadow: var(--shadow-md);
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        padding: 1rem 2rem;
        font-weight: 600;
        border-radius: 8px 8px 0 0;
    }
    
    /* Premium Link Buttons - Booking CTAs */
    .stLinkButton > a {
        text-decoration: none;
        border-radius: 12px;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        font-weight: 700;
        padding: 0.875rem 1.75rem;
        display: inline-block;
        text-align: center;
        box-shadow: var(--shadow-sm);
    }
    
    .stLinkButton > a:hover {
        transform: translateY(-3px);
        box-shadow: var(--shadow-lg);
    }
    
    /* Premium Sidebar */
    [data-testid="stSidebar"] {
        background: var(--white);
        border-right: 1px solid var(--border-light);
        box-shadow: var(--shadow-md);
    }
    
    [data-testid="stSidebar"] > div:first-child {
        background: var(--gradient-primary);
        padding: 2rem 1.5rem;
        margin-bottom: 2rem;
    }
    
    [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
        color: var(--primary-blue);
        font-weight: 800;
    }
    
    /* Premium Price Display */
    .price-tag {
        background: var(--gradient-accent);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 900;
        font-size: 3rem;
        font-family: 'Poppins', sans-serif;
        line-height: 1;
        letter-spacing: -1px;
    }
    
    .price-container {
        background: linear-gradient(135deg, #FEF3C7 0%, #FDE68A 100%);
        padding: 1.5rem 2rem;
        border-radius: 16px;
        border: 2px solid var(--accent-yellow);
        box-shadow: var(--shadow-md);
    }
    
    .best-price-badge {
        background: var(--success-green);
        color: var(--white);
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: 700;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        display: inline-block;
        box-shadow: var(--shadow-sm);
    }
    
    /* Premium Route Display */
    .route-display {
        background: var(--white);
        padding: 3rem 2rem;
        border-radius: 20px;
        border: 2px solid var(--border-light);
        margin: 2rem 0;
        box-shadow: var(--shadow-lg);
        position: relative;
        overflow: hidden;
    }
    
    .route-display::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 6px;
        background: var(--gradient-accent);
    }
    
    .route-city {
        background: var(--gradient-primary);
        padding: 2rem;
        border-radius: 16px;
        color: var(--white);
        box-shadow: var(--shadow-md);
        transition: all 0.3s;
    }
    
    .route-city:hover {
        transform: scale(1.05);
        box-shadow: var(--shadow-xl);
    }
    
    .route-arrow {
        font-size: 3rem;
        color: var(--accent-yellow);
        animation: slideRight 2s infinite;
    }
    
    @keyframes slideRight {
        0%, 100% { transform: translateX(0); }
        50% { transform: translateX(10px); }
    }
    
    /* Loading animation */
    .stSpinner > div {
        border-top-color: #667eea !important;
    }
    
    /* Premium Dividers */
    hr {
        margin: 3rem 0;
        border: none;
        height: 2px;
        background: linear-gradient(90deg, transparent 0%, var(--accent-yellow) 50%, transparent 100%);
    }
    
    /* Flight Timeline */
    .flight-timeline {
        position: relative;
        padding: 2rem 0;
    }
    
    .flight-timeline::before {
        content: '';
        position: absolute;
        top: 50%;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, var(--primary-blue) 0%, var(--accent-yellow) 100%);
        transform: translateY(-50%);
    }
    
    .flight-stop {
        background: var(--white);
        border: 4px solid var(--primary-blue);
        border-radius: 50%;
        width: 24px;
        height: 24px;
        position: relative;
        z-index: 10;
    }
    
    /* Seat Availability Indicator */
    .seats-available {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.75rem 1.25rem;
        border-radius: 20px;
        font-weight: 700;
        font-size: 0.875rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .seats-high {
        background: linear-gradient(135deg, #D1FAE5 0%, #A7F3D0 100%);
        color: #065F46;
        border: 2px solid #10B981;
    }
    
    .seats-medium {
        background: linear-gradient(135deg, #FEF3C7 0%, #FDE68A 100%);
        color: #92400E;
        border: 2px solid #F59E0B;
    }
    
    .seats-low {
        background: linear-gradient(135deg, #FEE2E2 0%, #FECACA 100%);
        color: #991B1B;
        border: 2px solid #EF4444;
    }
    
    /* Airline Logo Placeholder */
    .airline-logo {
        width: 80px;
        height: 80px;
        background: var(--white);
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 2rem;
        border: 2px solid var(--border-light);
        box-shadow: var(--shadow-sm);
    }
    
    /* Loading Spinner */
    .stSpinner > div {
        border-top-color: var(--accent-yellow) !important;
        border-right-color: var(--primary-blue) !important;
    }
    
    /* Radio Button Groups */
    .stRadio > div {
        background: var(--white);
        padding: 1.5rem;
        border-radius: 12px;
        border: 2px solid var(--border-light);
    }
    
    .stRadio > label {
        font-weight: 700;
        color: var(--primary-blue);
        font-size: 1rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0;
        background: var(--white);
        border-radius: 12px;
        padding: 0.5rem;
        border: 2px solid var(--border-light);
    }
    
    .stTabs [data-baseweb="tab"] {
        padding: 1rem 2rem;
        font-weight: 700;
        border-radius: 8px;
        transition: all 0.3s;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background: var(--light-bg);
    }
    
    .stTabs [aria-selected="true"] {
        background: var(--gradient-primary) !important;
        color: var(--white) !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'results_history' not in st.session_state:
    st.session_state.results_history = []
if 'flight_results' not in st.session_state:
    st.session_state.flight_results = None
if 'searching_flights' not in st.session_state:
    st.session_state.searching_flights = False

# Configure Gemini API
api_key = os.getenv("GOOGLE_API_KEY")
if api_key and GENAI_AVAILABLE:
    genai.configure(api_key=api_key)
    api_status = "Connected"
    api_color = "green"
else:
    api_status = "Not Configured (Using Fallback Parser)"
    api_color = "orange"

# Configure Amadeus API
amadeus_client_id = os.getenv("AMADEUS_CLIENT_ID")
amadeus_client_secret = os.getenv("AMADEUS_CLIENT_SECRET")
if amadeus_client_id and amadeus_client_secret:
    amadeus_status = "Connected"
    amadeus_color = "green"
    amadeus_searcher = AmadeusFlightSearch()
else:
    amadeus_status = "Not Configured"
    amadeus_color = "red"
    amadeus_searcher = None

# Premium Airline-Grade Header
st.markdown("""
<div style='background: linear-gradient(135deg, #05164D 0%, #1E3A8A 100%); padding: 2.5rem 3rem; margin: -3rem -2rem 3rem -2rem; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border-bottom: 4px solid #F9B233;'>
    <div style='max-width: 1600px; margin: 0 auto; display: flex; align-items: center; justify-content: space-between;'>
        <div style='flex: 1;'>
            <div style='display: flex; align-items: center; gap: 1.5rem;'>
                <div style='background: #F9B233; width: 80px; height: 80px; border-radius: 16px; display: flex; align-items: center; justify-content: center; font-size: 2.5rem; box-shadow: 0 4px 12px rgba(249,178,51,0.4);'>
                    ✈️
                </div>
                <div>
                    <h1 style='margin: 0; color: white; font-size: 3rem; font-weight: 900; font-family: Poppins, sans-serif; letter-spacing: -1px;'>
                        FlightAI
                    </h1>
                    <p style='margin: 0.5rem 0 0 0; color: #F9B233; font-size: 1.1rem; font-weight: 600; letter-spacing: 1px;'>
                        SMART FLIGHT BOOKING PLATFORM
                    </p>
                </div>
            </div>
        </div>
        <div style='display: flex; gap: 1rem; align-items: center;'>
            <div style='background: rgba(255,255,255,0.1); backdrop-filter: blur(10px); padding: 1rem 1.5rem; border-radius: 12px; border: 2px solid rgba(249,178,51,0.3);'>
                <div style='color: #F9B233; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 0.25rem;'>AI-Powered</div>
                <div style='color: white; font-weight: 600; font-size: 0.9rem;'>🤖 Smart Search</div>
            </div>
            <div style='background: rgba(255,255,255,0.1); backdrop-filter: blur(10px); padding: 1rem 1.5rem; border-radius: 12px; border: 2px solid rgba(249,178,51,0.3);'>
                <div style='color: #F9B233; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 0.25rem;'>Real-Time</div>
                <div style='color: white; font-weight: 600; font-size: 0.9rem;'>🌐 Live Prices</div>
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    
    # API Status
    st.markdown(f"**Gemini API:** :{api_color}[{api_status}]")
    st.markdown(f"**Amadeus API:** :{amadeus_color}[{amadeus_status}]")
    
    if not api_key:
        st.warning("Set GOOGLE_API_KEY in .env file to use AI extraction")
    if not amadeus_searcher:
        st.warning("Set Amadeus credentials in .env to search flights")
    
    st.divider()
    
    # Configuration
    st.subheader("Configuration")
    fallback_days = st.slider("Fallback Duration (days)", 1, 30, 7)
    max_duration = st.slider("Max Duration (days)", 30, 365, 365)
    
    st.divider()
    
    # Examples
    st.subheader("📝 Example Queries")
    examples = [
        "7 days in Paris",
        "weekend trip to Dubai",
        "2 week vacation in Singapore",
        "a week in Switzerland",
        "5 days in London",
        "trip to Thailand for 10 days"
    ]
    for ex in examples:
        if st.button(ex, key=f"ex_{ex}", use_container_width=True):
            st.session_state.example_query = ex
    
    st.divider()
    
    # Clear history
    if st.button("🗑️ Clear History", use_container_width=True):
        st.session_state.results_history = []
        st.rerun()

# Premium Search Container
st.markdown("""
<div style='background: white; padding: 3rem; border-radius: 20px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); border: 2px solid #E5E7EB; position: relative; overflow: hidden;'>
    <div style='position: absolute; top: 0; left: 0; right: 0; height: 6px; background: linear-gradient(90deg, #F9B233 0%, #FBBF24 100%);'></div>
    <div style='margin-bottom: 2rem;'>
        <h2 style='color: #05164D; font-size: 1.75rem; font-weight: 800; margin: 0; font-family: Poppins, sans-serif;'>🔍 Search Your Perfect Flight</h2>
        <p style='color: #6B7280; margin: 0.5rem 0 0 0; font-size: 1rem;'>AI-powered search finds the best flights for your journey</p>
    </div>
""", unsafe_allow_html=True)

# Main content
col_left, col_right = st.columns([2, 1])

with col_left:
    st.subheader("🔍 Plan Your Trip")
    
    # Get Indian airports for dropdown
    indian_airports = get_indian_airports_list()
    airport_options = [apt["label"] for apt in indian_airports]
    airport_codes = [apt["code"] for apt in indian_airports]
    
    # Origin selection (dropdown for Indian airports)
    selected_idx = st.selectbox(
        "🛫 Select Your Base Airport (India)",
        range(len(airport_options)),
        format_func=lambda x: airport_options[x],
        help="Choose your departure airport from major Indian international airports"
    )
    origin_iata = airport_codes[selected_idx]
    origin_city = INDIAN_AIRPORTS[origin_iata]["city"]
    
    st.caption(f"Selected: **{origin_iata}** - {origin_city}")
    
    # Check for example query
    default_query = st.session_state.get('example_query', '')
    if default_query:
        st.session_state.pop('example_query')
    
    # Trip description
    query = st.text_area(
        "🌍 Trip Description",
        value=default_query,
        placeholder="e.g., 7 days in Switzerland, weekend trip to Dubai, vacation in Singapore",
        help="Describe your trip in natural language - AI will extract destination and duration",
        height=100
    )
    
    # Extract button
    if st.button("🚀 Extract Trip Details", type="primary", use_container_width=True):
        if not query.strip():
            st.error("Please enter a trip description")
        else:
            with st.spinner("🤖 AI is extracting trip details..."):
                try:
                    # Extract IATA code
                    iata_result = extract_iata_from_query(query)
                    
                    # Extract duration
                    duration_result = get_trip_dates(
                        origin_text=origin_city,
                        user_query=query,
                        fallback_days=fallback_days,
                        max_duration=max_duration
                    )
                    
                    # Combine results
                    combined_result = {
                        **duration_result,
                        'origin_iata': origin_iata,
                        'origin_city': origin_city,
                        'destination_city': iata_result['destination_city'],
                        'destination_iata': iata_result['iata_code'],
                        'iata_confidence': iata_result['confidence'],
                        'iata_fallback': iata_result['used_fallback']
                    }
                    
                    # Add to history
                    st.session_state.results_history.insert(0, {
                        'timestamp': datetime.now().strftime("%H:%M:%S"),
                        'query': query,
                        'result': combined_result
                    })
                    
                    st.success("✅ Trip details extracted successfully!")
                    
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

with col_right:
    st.subheader("ℹ️ How It Works")
    st.markdown("""
    **AI-Powered Extraction:**
    1. 🏛️ Select Indian base airport
    2. 📝 Describe trip naturally
    3. 🤖 Gemini extracts:
       - Destination IATA code
       - Trip duration in days
       - Travel dates
    
    **Supported Formats:**
    - "7 days in Paris"
    - "weekend Dubai trip"
    - "2 weeks in Switzerland"
    - "visiting London for 5 days"
    """)

# Close search card
st.markdown("</div>", unsafe_allow_html=True)

# Results section
if st.session_state.results_history:
    st.markdown("""
    <div style='background: white; padding: 2.5rem; border-radius: 16px; box-shadow: 0 8px 16px rgba(0,0,0,0.1); margin-top: 2rem;'>
    """, unsafe_allow_html=True)
    
    st.subheader("📊 Extracted Trip Details")
    
    latest = st.session_state.results_history[0]
    result = latest['result']
    
    # Premium Flight Route Display
    st.markdown("### ✈️ Your Journey")
    route_col1, route_col2, route_col3 = st.columns([2, 1, 2])
    
    with route_col1:
        st.markdown(f"""
        <div class='route-city'>
            <div style='font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; opacity: 0.8; margin-bottom: 0.5rem;'>Departure</div>
            <div style='font-size: 3rem; font-weight: 900; margin: 0.5rem 0; font-family: Poppins, sans-serif;'>{result.get('origin_iata', 'N/A')}</div>
            <div style='font-size: 1.125rem; font-weight: 600;'>{result.get('origin_city', 'Origin')}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with route_col2:
        st.markdown("""
        <div style='text-align: center; padding: 40px 0;'>
            <div class='route-arrow'>→</div>
        </div>
        """, unsafe_allow_html=True)
    
    with route_col3:
        dest_iata = result.get('destination_iata', 'N/A')
        dest_city = result.get('destination_city', 'Destination')
        confidence = result.get('iata_confidence', 'low')
        
        # Confidence badge color
        if confidence == 'high':
            badge_color = '#059669'
            badge_text = '✓ HIGH CONFIDENCE'
        elif confidence == 'medium':
            badge_color = '#F59E0B'
            badge_text = '~ MEDIUM'
        else:
            badge_color = '#6B7280'
            badge_text = '? LOW'
        
        st.markdown(f"""
        <div class='route-city'>
            <div style='font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; opacity: 0.8; margin-bottom: 0.5rem;'>Arrival</div>
            <div style='font-size: 3rem; font-weight: 900; margin: 0.5rem 0; font-family: Poppins, sans-serif;'>{dest_iata}</div>
            <div style='font-size: 1.125rem; font-weight: 600; margin-bottom: 0.75rem;'>{dest_city}</div>
            <div style='background: {badge_color}; padding: 0.375rem 0.875rem; border-radius: 12px; font-size: 0.7rem; font-weight: 700; display: inline-block;'>{badge_text}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Additional metrics
    metric_cols = st.columns(3)
    
    with metric_cols[0]:
        st.metric(
            "📅 Duration",
            f"{result['duration_days']} days"
        )
    
    with metric_cols[1]:
        st.metric(
            "🛫 Departure",
            result['departure_date'].strftime("%b %d, %Y")
        )
    
    with metric_cols[2]:
        st.metric(
            "🛬 Return",
            result['return_date'].strftime("%b %d, %Y")
        )
    
    # Search Flights Button with Class Selection
    st.markdown("---")
    
    # Flight search options - Row 1
    search_col1, search_col2, search_col3 = st.columns([1, 1, 1])
    
    with search_col1:
        num_adults = st.number_input("👥 Adults", min_value=1, max_value=9, value=1, key="num_adults")
    
    with search_col2:
        cabin_class = st.selectbox(
            "🎫 Cabin Class",
            options=["ECONOMY", "PREMIUM_ECONOMY", "BUSINESS", "FIRST"],
            index=0,
            key="cabin_class",
            format_func=lambda x: {
                "ECONOMY": "Economy",
                "PREMIUM_ECONOMY": "Premium Economy",
                "BUSINESS": "Business",
                "FIRST": "First Class"
            }[x]
        )
    
    with search_col3:
        max_results = st.number_input("📊 Max Results", min_value=1, max_value=20, value=10, key="max_results")
    
    # Flight search options - Row 2 (Layover preference)
    filter_col1, filter_col2, filter_col3 = st.columns([1, 1, 1])
    
    with filter_col1:
        flight_type = st.radio(
            "✈️ Flight Type",
            options=["any", "direct", "max_1_stop"],
            index=0,
            key="flight_type",
            format_func=lambda x: {
                "any": "🔄 Any (with or without layover)",
                "direct": "✈️ Direct flights only",
                "max_1_stop": "🔁 Max 1 stop"
            }[x],
            horizontal=False
        )
    
    st.markdown("")  # Small spacing
    
    col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
    with col_btn2:
        if amadeus_searcher and result.get('destination_iata') and result.get('origin_iata'):
            if st.button("🔍 Search Real-Time Flights", type="primary", use_container_width=True, key="search_flights_btn"):
                st.session_state.searching_flights = True
                st.session_state.flight_results = None
                
                with st.spinner("✈️ Searching flights on Amadeus..."):
                    try:
                        # Determine non-stop parameter
                        non_stop = (flight_type == "direct")
                        
                        flight_results = amadeus_searcher.search_flights(
                            origin=result['origin_iata'],
                            destination=result['destination_iata'],
                            departure_date=result['departure_date'],
                            return_date=result['return_date'],
                            adults=num_adults,
                            max_results=max_results,
                            travel_class=cabin_class,
                            non_stop=non_stop
                        )
                        
                        # Filter for max 1 stop if selected
                        if flight_type == "max_1_stop" and flight_results.get('flights'):
                            filtered_flights = [
                                f for f in flight_results['flights']
                                if f['outbound']['stops'] <= 1 and 
                                (not f.get('return') or f['return']['stops'] <= 1)
                            ]
                            flight_results['flights'] = filtered_flights
                            flight_results['total_offers'] = len(filtered_flights)
                        
                        st.session_state.flight_results = flight_results
                        st.session_state.searching_flights = False
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Flight search failed: {str(e)}")
                        st.session_state.searching_flights = False
        else:
            if not amadeus_searcher:
                st.info("🔒 Configure Amadeus API credentials to search flights")
            elif not result.get('destination_iata'):
                st.warning("⚠️ Destination IATA code not available")
    
    # Details in expander
    with st.expander("🔍 Technical Details"):
        detail_col1, detail_col2 = st.columns(2)
        
        with detail_col1:
            st.markdown("**📝 Query Information**")
            st.write(f"**Original Query:** {latest['query']}")
            st.write(f"**Timestamp:** {latest['timestamp']}")
            st.write(f"**Origin:** {result.get('origin_city')} ({result.get('origin_iata')})")
            st.write(f"**Destination:** {result.get('destination_city')} ({result.get('destination_iata')})")
        
        with detail_col2:
            st.markdown("**🤖 AI Extraction Details**")
            st.write(f"**Duration Model:** {result.get('model_used', 'N/A')}")
            st.write(f"**Duration Fallback:** {'Yes' if result.get('used_fallback') else 'No'}")
            st.write(f"**IATA Confidence:** {result.get('iata_confidence', 'N/A').upper()}")
            st.write(f"**IATA Fallback:** {'Yes' if result.get('iata_fallback') else 'No'}")
            if result.get('error'):
                st.warning(f"**Error:** {result['error']}")
    
    # Close results card
    st.markdown("</div>", unsafe_allow_html=True)

# Flight Results Display
if st.session_state.flight_results:
    st.divider()
    st.subheader("✈️ Available Flights")
    
    flights_data = st.session_state.flight_results
    
    if flights_data.get('success') and flights_data.get('flights'):
        st.success(f"Found {flights_data['total_offers']} flight offers from {flights_data['origin']} to {flights_data['destination']}")
        
        # Display each flight
        for idx, flight in enumerate(flights_data['flights'], 1):
            # Determine seat availability class
            seats = flight.get('seats_available', 0)
            if isinstance(seats, int):
                if seats > 9:
                    seat_class = 'seats-high'
                    seat_icon = '✓'
                    seat_status = f'{seats} SEATS'
                elif seats > 4:
                    seat_class = 'seats-medium'
                    seat_icon = '⚠'
                    seat_status = f'{seats} SEATS'
                else:
                    seat_class = 'seats-low'
                    seat_icon = '!'
                    seat_status = f'ONLY {seats} LEFT'
            else:
                seat_class = 'seats-medium'
                seat_icon = '?'
                seat_status = 'CHECK AVAILABILITY'
            
            # Create expander title with price
            expander_title = f"💺 Flight {idx} - {get_airline_name(flight['outbound']['carrier'])} • {flight['price']['currency']} {flight['price']['total']}"
            if idx == 1:
                expander_title = f"🏆 {expander_title} • BEST PRICE"
            
            with st.expander(expander_title, expanded=(idx==1)):
                
                # Premium Price Display
                st.markdown(f"""
                <div class='price-container' style='margin-bottom: 2rem;'>
                    <div style='display: flex; justify-content: space-between; align-items: center;'>
                        <div>
                            <div style='font-size: 0.75rem; color: #92400E; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 0.5rem;'>Total Price</div>
                            <div class='price-tag'>{flight['price']['currency']} {flight['price']['total']}</div>
                            {f"<div style='color: #92400E; font-size: 0.875rem; font-weight: 600; margin-top: 0.5rem;'>Base Fare: {flight['price']['currency']} {flight['price']['base']}</div>" if flight['price'].get('base') else ""}
                        </div>
                        <div style='text-align: right;'>
                            <div class='{seat_class}' style='margin-bottom: 0.75rem;'>
                                {seat_icon} {seat_status}
                            </div>
                            {"<div class='best-price-badge'>BEST PRICE</div>" if idx == 1 else ""}
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Flight Overview Metrics
                overview_cols = st.columns(4)
                with overview_cols[0]:
                    st.metric("✈️ Airline", get_airline_name(flight.get('validating_airline', 'N/A')))
                with overview_cols[1]:
                    st.metric("🎫 Cabin", flight['outbound'].get('cabin', 'Economy'))
                with overview_cols[2]:
                    st.metric("🔄 Stops", f"{flight['outbound']['stops']} stop{'s' if flight['outbound']['stops'] != 1 else ''}")
                with overview_cols[3]:
                    st.metric("⏱️ Duration", format_duration(flight['outbound']['duration']))
                
                # Booking Links
                st.markdown("")
                st.markdown("**🔗 Book This Flight:**")
                
                # Generate booking URLs
                origin_code = flight['outbound']['departure']['iata']
                dest_code = flight['outbound']['arrival']['iata']
                dep_date = flight['outbound']['departure']['time'][:10] if flight['outbound']['departure'].get('time') else ''
                carrier = flight['outbound']['carrier']
                airline_website = get_airline_website(carrier)
                
                # Primary booking button
                booking_col1, booking_col2, booking_col3 = st.columns([1, 2, 1])
                with booking_col2:
                    if airline_website:
                        carrier_name = get_airline_name(carrier)
                        st.link_button(
                            f"✈️ Book on {carrier_name} Official Website",
                            airline_website,
                            use_container_width=True,
                            type="primary"
                        )
                    else:
                        google_flights_url = f"https://www.google.com/travel/flights?q=flights+from+{origin_code}+to+{dest_code}+on+{dep_date}"
                        st.link_button(
                            "🎫 Book This Flight on Google Flights",
                            google_flights_url,
                            use_container_width=True,
                            type="primary"
                        )
                
                # Alternative booking platforms
                st.caption("Or compare prices on:")
                alt_col1, alt_col2, alt_col3 = st.columns(3)
                with alt_col1:
                    google_flights_url = f"https://www.google.com/travel/flights?q=flights+from+{origin_code}+to+{dest_code}+on+{dep_date}"
                    st.link_button("🔍 Google Flights", google_flights_url, use_container_width=True)
                with alt_col2:
                    kayak_url = f"https://www.kayak.com/flights/{origin_code}-{dest_code}/{dep_date}"
                    st.link_button("🌊 Kayak", kayak_url, use_container_width=True)
                with alt_col3:
                    skyscanner_url = f"https://www.skyscanner.com/transport/flights/{origin_code.lower()}/{dest_code.lower()}/{dep_date.replace('-', '')}"
                    st.link_button("🌐 Skyscanner", skyscanner_url, use_container_width=True)
                
                st.markdown("---")
                
                # Outbound Flight
                st.markdown("#### 🛫 Outbound Flight")
                st.write(f"**Total Duration:** {format_duration(flight['outbound']['duration'])} | **Stops:** {flight['outbound']['stops']}")
                
                # Display each segment
                for seg_idx, segment in enumerate(flight['outbound']['segments'], 1):
                    st.markdown(f"**Leg {seg_idx}: {segment['departure']['iata']} → {segment['arrival']['iata']}**")
                    
                    seg_col1, seg_col2, seg_col3, seg_col4 = st.columns(4)
                    
                    with seg_col1:
                        st.write("**Departure**")
                        st.write(f"🏛️ {segment['departure']['iata']}")
                        st.write(f"🕐 {format_datetime(segment['departure']['time'])}")
                        if segment['departure'].get('terminal'):
                            st.caption(f"Terminal {segment['departure']['terminal']}")
                    
                    with seg_col2:
                        st.write("**Flight**")
                        carrier_name = get_airline_name(segment['carrier'])
                        st.write(f"✈️ {carrier_name}")
                        st.write(f"🔢 {segment['carrier']}{segment['flight_number']}")
                        if segment.get('operating_carrier') and segment['operating_carrier'] != segment['carrier']:
                            st.caption(f"Operated by: {get_airline_name(segment['operating_carrier'])}")
                    
                    with seg_col3:
                        st.write("**Details**")
                        st.write(f"⏱️ {format_duration(segment['duration'])}")
                        st.write(f"�️ {get_aircraft_name(segment.get('aircraft'))}")
                        if segment.get('cabin'):
                            st.caption(f"Cabin: {segment['cabin']}")
                    
                    with seg_col4:
                        st.write("**Arrival**")
                        st.write(f"🏛️ {segment['arrival']['iata']}")
                        st.write(f"🕐 {format_datetime(segment['arrival']['time'])}")
                        if segment['arrival'].get('terminal'):
                            st.caption(f"Terminal {segment['arrival']['terminal']}")
                    
                    # Show layover time if not the last segment
                    if seg_idx < len(flight['outbound']['segments']):
                        st.caption("⏳ Layover at " + segment['arrival']['iata'])
                        st.markdown("---")
                
                # Return Flight (if exists)
                if flight.get('return'):
                    st.markdown("---")
                    st.markdown("#### 🛬 Return Flight")
                    st.write(f"**Total Duration:** {format_duration(flight['return']['duration'])} | **Stops:** {flight['return']['stops']}")
                    
                    # Display each segment
                    for seg_idx, segment in enumerate(flight['return']['segments'], 1):
                        st.markdown(f"**Leg {seg_idx}: {segment['departure']['iata']} → {segment['arrival']['iata']}**")
                        
                        seg_col1, seg_col2, seg_col3, seg_col4 = st.columns(4)
                        
                        with seg_col1:
                            st.write("**Departure**")
                            st.write(f"🏛️ {segment['departure']['iata']}")
                            st.write(f"🕐 {format_datetime(segment['departure']['time'])}")
                            if segment['departure'].get('terminal'):
                                st.caption(f"Terminal {segment['departure']['terminal']}")
                        
                        with seg_col2:
                            st.write("**Flight**")
                            carrier_name = get_airline_name(segment['carrier'])
                            st.write(f"✈️ {carrier_name}")
                            st.write(f"🔢 {segment['carrier']}{segment['flight_number']}")
                            if segment.get('operating_carrier') and segment['operating_carrier'] != segment['carrier']:
                                st.caption(f"Operated by: {get_airline_name(segment['operating_carrier'])}")
                        
                        with seg_col3:
                            st.write("**Details**")
                            st.write(f"⏱️ {format_duration(segment['duration'])}")
                            st.write(f"�️ {get_aircraft_name(segment.get('aircraft'))}")
                            if segment.get('cabin'):
                                st.caption(f"Cabin: {segment['cabin']}")
                        
                        with seg_col4:
                            st.write("**Arrival**")
                            st.write(f"🏛️ {segment['arrival']['iata']}")
                            st.write(f"🕐 {format_datetime(segment['arrival']['time'])}")
                            if segment['arrival'].get('terminal'):
                                st.caption(f"Terminal {segment['arrival']['terminal']}")
                        
                        # Show layover time if not the last segment
                        if seg_idx < len(flight['return']['segments']):
                            st.caption("⏳ Layover at " + segment['arrival']['iata'])
                            st.markdown("---")
    
    elif flights_data.get('message'):
        st.info(flights_data['message'])
    else:
        st.warning("No flights found for the selected route.")

# History section
if len(st.session_state.results_history) > 1:
    st.divider()
    st.subheader("📜 Previous Queries")
    
    for idx, item in enumerate(st.session_state.results_history[1:], 1):
        res = item['result']
        route_text = f"{res.get('origin_iata', 'N/A')} → {res.get('destination_iata', 'N/A')}"
        
        with st.expander(f"[{item['timestamp']}] {route_text} | {item['query'][:40]}..."):
            cols = st.columns(4)
            with cols[0]:
                st.write(f"**Route:** {res.get('origin_iata')} → {res.get('destination_iata')}")
            with cols[1]:
                st.write(f"**Duration:** {res['duration_days']} days")
            with cols[2]:
                st.write(f"**Departure:** {res['departure_date'].strftime('%b %d')}")
            with cols[3]:
                st.write(f"**Return:** {res['return_date'].strftime('%b %d')}")
            
            st.caption(f"Destination: {res.get('destination_city', 'N/A')} | Confidence: {res.get('iata_confidence', 'N/A').upper()}")

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: gray;'>
    <small>Powered by Google Gemini AI | Built with Streamlit</small>
</div>
""", unsafe_allow_html=True)
