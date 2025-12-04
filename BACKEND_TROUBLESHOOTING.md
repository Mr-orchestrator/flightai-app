# 🔧 BACKEND TROUBLESHOOTING GUIDE

## ⚠️ ISSUE: "Previously all features were working, now nothing works"

---

## 🎯 **QUICK DIAGNOSIS**

Run this test script to see what's broken:

```bash
cd "d:\Ai recommendor"
python test_backend.py
```

This will check:
- ✓ Environment variables (API keys)
- ✓ Module imports
- ✓ IATA extraction
- ✓ Duration extraction
- ✓ Amadeus API connection
- ✓ Airport list

---

## 🔍 **WHAT CHANGED?**

### **Before:**
- You had a **Streamlit app** (`app.py`)
- Everything ran in one Python process
- Direct function calls

### **After (What We Built):**
- **Next.js frontend** (port 3000)
- **FastAPI backend** (port 8000) - NEW!
- **REST API communication** between them

### **THE GOOD NEWS:**
Your original Python backend logic (`core.py`, `iata_extractor.py`, `amadeus_flights.py`) is **completely untouched**. We just wrapped it in REST endpoints.

---

## ✅ **VERIFY OLD APP STILL WORKS**

### **Test 1: Run Original Streamlit App**

```bash
cd "d:\Ai recommendor"
streamlit run app.py
```

Open: http://localhost:8501

**If Streamlit works:**
- ✅ Your backend logic is fine
- ✅ API keys are working
- ✅ Problem is in new FastAPI wrapper or frontend

**If Streamlit doesn't work:**
- ❌ Something broke in core Python files
- ❌ Check environment variables
- ❌ Check dependencies

---

## 🔧 **VERIFY NEW API SERVER**

### **Test 2: Start FastAPI Server**

```bash
cd "d:\Ai recommendor"
python api_server.py
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

### **Test 3: Check API Health**

Open browser to: http://localhost:8000

Should return:
```json
{
  "status": "online",
  "service": "FlightAI API",
  "version": "2.0.0"
}
```

### **Test 4: Check API Documentation**

Open: http://localhost:8000/docs

You should see interactive API documentation with:
- GET /airports
- POST /extract-trip
- POST /search-flights
- GET /airline-info/{code}

---

## 🐛 **COMMON ISSUES & FIXES**

### **Issue 1: "Module not found" errors**

**Symptom:**
```
ModuleNotFoundError: No module named 'fastapi'
```

**Fix:**
```bash
pip install fastapi uvicorn
```

### **Issue 2: "Cannot import from core/iata_extractor/amadeus_flights"**

**Symptom:**
```
ImportError: cannot import name 'get_trip_dates' from 'core'
```

**Fix:**
Make sure you're in the correct directory:
```bash
cd "d:\Ai recommendor"
python api_server.py
```

### **Issue 3: API returns 500 errors**

**Symptom:**
```
INFO:     127.0.0.1:52841 - "GET /airports HTTP/1.1" 500 Internal Server Error
```

**Fix:**
Check the terminal for Python errors. Common causes:
- Missing environment variables
- Amadeus/Gemini API issues
- Malformed data in functions

### **Issue 4: CORS errors in browser**

**Symptom:**
```
Access to fetch at 'http://localhost:8000' from origin 'http://localhost:3000' 
has been blocked by CORS policy
```

**Fix:**
Already handled in `api_server.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### **Issue 5: Environment variables not loaded**

**Symptom:**
```
Gemini API key not configured
Amadeus credentials missing
```

**Fix:**
1. Check `.env` file exists in root directory
2. Verify it contains:
```env
GOOGLE_API_KEY=your_key_here
AMADEUS_CLIENT_ID=your_id
AMADEUS_CLIENT_SECRET=your_secret
```

3. Restart the API server after editing `.env`

---

## 🧪 **MANUAL API TESTING**

### **Test Airports Endpoint:**

```bash
# In browser or PowerShell:
curl http://localhost:8000/airports
```

Should return list of airports:
```json
[
  {
    "iata": "BOM",
    "city": "Mumbai",
    "name": "Chhatrapati Shivaji Maharaj International Airport",
    "country": "India"
  },
  ...
]
```

### **Test Trip Extraction:**

```bash
curl -X POST http://localhost:8000/extract-trip ^
  -H "Content-Type: application/json" ^
  -d "{\"origin_iata\": \"BOM\", \"user_query\": \"7 days in Dubai\", \"fallback_days\": 7}"
```

Should return:
```json
{
  "success": true,
  "origin_iata": "BOM",
  "destination_iata": "DXB",
  "destination_city": "Dubai",
  "duration_days": 7,
  ...
}
```

---

## 📊 **DEBUGGING CHECKLIST**

### **Backend (Python):**
- [ ] `.env` file exists and has API keys
- [ ] `pip install fastapi uvicorn` completed
- [ ] Can import core, iata_extractor, amadeus_flights
- [ ] `python test_backend.py` shows all ✓
- [ ] `streamlit run app.py` works (old app)
- [ ] `python api_server.py` starts without errors
- [ ] http://localhost:8000 returns JSON
- [ ] http://localhost:8000/docs shows API docs

### **Frontend (Next.js):**
- [ ] `npm install` completed in `frontend/` directory
- [ ] `npm run dev` starts without errors
- [ ] http://localhost:3000 loads
- [ ] Browser console shows no errors
- [ ] Can see background animation
- [ ] Can select airport from dropdown

---

## 🔄 **COMPLETE RESTART PROCEDURE**

If everything is broken, try this:

### **1. Stop Everything:**
```bash
# Stop all running processes
# Ctrl+C in all terminals
```

### **2. Verify Environment:**
```bash
cd "d:\Ai recommendor"
python test_backend.py
```

### **3. Test Old App:**
```bash
streamlit run app.py
# If this works, backend is fine
```

### **4. Start New Stack:**

**Terminal 1 - Backend:**
```bash
cd "d:\Ai recommendor"
python api_server.py
```

**Terminal 2 - Frontend:**
```bash
cd "d:\Ai recommendor\frontend"
npm run dev
```

### **5. Verify Connection:**
- Backend: http://localhost:8000
- Frontend: http://localhost:3000
- Check browser console for errors

---

## 📝 **ERROR LOG LOCATIONS**

### **Python API Server:**
- Errors appear in terminal where `python api_server.py` runs
- Look for red text or tracebacks

### **Next.js Frontend:**
- Terminal: Build errors
- Browser Console (F12): Runtime errors
- Network tab: API call failures

### **Streamlit (Old App):**
- Terminal where `streamlit run app.py` runs
- Browser shows errors inline

---

## 🆘 **STILL NOT WORKING?**

### **Provide This Information:**

1. **Output of test script:**
```bash
python test_backend.py
```

2. **Error messages from API server terminal**

3. **Browser console errors** (F12 → Console tab)

4. **Which specific feature isn't working:**
   - Airport dropdown not loading?
   - Trip extraction failing?
   - Flight search not working?
   - Frontend not displaying?

---

## 💡 **MOST LIKELY CAUSES**

Based on "previously working, now broken":

### **1. API Server Not Running (90% probability)**
```bash
# Make sure this is running:
python api_server.py
```

### **2. Wrong Directory**
```bash
# API server MUST run from root:
cd "d:\Ai recommendor"
python api_server.py

# NOT from frontend directory
```

### **3. Port Conflicts**
```bash
# Kill existing processes on port 8000:
netstat -ano | findstr :8000
taskkill /PID <process_id> /F
```

### **4. Environment Variables**
```bash
# Re-check .env file exists and is correct
```

---

## ✅ **EXPECTED WORKING STATE**

When everything works:

### **Terminal 1:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

### **Terminal 2:**
```
✓ Ready in 5.3s
○ Compiling /
✓ Compiled / in 3.2s
```

### **Browser (http://localhost:3000):**
- Background animation visible
- Airport dropdown populated
- No console errors
- Can type in text area

---

## 🚀 **QUICK FIX COMMANDS**

```bash
# Complete reset:
cd "d:\Ai recommendor"
pip install fastapi uvicorn python-dotenv
python test_backend.py
python api_server.py

# In new terminal:
cd "d:\Ai recommendor\frontend"
npm install
npm run dev
```

---

**Run `python test_backend.py` first and report what fails!** 🔍
