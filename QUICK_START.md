# 🚀 QUICK START GUIDE

## ✅ Prerequisites Complete
- ✅ FastAPI + Uvicorn installed
- ✅ Node modules installed
- ✅ Next.js app files created

---

## 🎬 HOW TO START THE PREMIUM UI

### **Option 1: Use Batch Launcher (Easy)**

From the **root directory** (`d:\Ai recommendor`):
```bash
START_PREMIUM_UI.bat
```

### **Option 2: Manual Start (Two Terminals)**

#### Terminal 1 - Start Python Backend:
```bash
cd "d:\Ai recommendor"
python api_server.py
```
**Backend will run on:** http://localhost:8000  
**API Docs:** http://localhost:8000/docs

#### Terminal 2 - Start Next.js Frontend:
```bash
cd "d:\Ai recommendor\frontend"
npm run dev
```
**Frontend will run on:** http://localhost:3000

---

## 🌐 ACCESS THE APPLICATION

Open your browser to: **http://localhost:3000**

You should see:
- ✨ Animated particle background
- 🌌 Premium navy gradient
- ✈️ FlightAI logo with glow
- 🎴 Floating search card with glassmorphism
- 🎬 Cinematic entrance animations

---

## 🔧 TROUBLESHOOTING

### Error: "Cannot find path 'api_server.py'"
**Problem:** You're in the wrong directory  
**Solution:** Make sure you're in `d:\Ai recommendor` (not `frontend`)

### Error: "Couldn't find any pages or app directory"
**Problem:** Missing Next.js app files  
**Solution:** Already fixed! Files created:
- ✅ `frontend/app/layout.tsx`
- ✅ `frontend/app/page.tsx`
- ✅ `frontend/app/globals.css`

### Error: "Port already in use"
**Solution:** Kill existing process:
```bash
# For port 8000 (Python)
netstat -ano | findstr :8000
taskkill /PID <process_id> /F

# For port 3000 (Next.js)
netstat -ano | findstr :3000
taskkill /PID <process_id> /F
```

### Error: "Cannot connect to backend"
**Solution:** Make sure Python API is running first (Terminal 1)

---

## 📝 CORRECT TERMINAL COMMANDS

### ❌ WRONG (What you tried):
```bash
# From frontend directory
START_PREMIUM_UI.bat  # Wrong location
python api_server.py   # Wrong location
cd frontend            # Already in frontend!
```

### ✅ CORRECT:

**Terminal 1:**
```bash
cd "d:\Ai recommendor"     # Go to root first
python api_server.py        # Start backend
```

**Terminal 2:**
```bash
cd "d:\Ai recommendor"     # Go to root first
cd frontend                 # Then go to frontend
npm run dev                 # Start Next.js
```

---

## 🎯 WHAT YOU'LL SEE

### Page Load Sequence (0-3 seconds):
```
0.0s → Dark screen
0.3s → Background gradient fades in
0.6s → Navbar slides down
1.0s → Hero badge pops in
1.2s → "Your Next" fades up
1.8s → Search card swipes in
2.0s → Ready for interaction!
```

### Search Flow:
1. Select origin airport (dropdown)
2. Type trip description ("7 days in Dubai")
3. Click "Extract Trip Details with AI"
4. Watch loading animation
5. See trip summary with route display
6. View flight results with premium cards

---

## 📊 SYSTEM STATUS CHECK

Before starting, verify:
- ✅ Python backend files exist (`api_server.py`, `core.py`, etc.)
- ✅ Frontend files exist (`frontend/app/page.tsx`, etc.)
- ✅ Node modules installed (`frontend/node_modules/` exists)
- ✅ Environment variables set (`.env` file with API keys)

---

## 🎬 READY TO LAUNCH!

**Run these exact commands in order:**

```powershell
# Terminal 1 - Backend
cd "d:\Ai recommendor"
python api_server.py

# Terminal 2 - Frontend (new terminal)
cd "d:\Ai recommendor\frontend"
npm run dev
```

**Then open:** http://localhost:3000

**Enjoy your CRED-level premium UI!** ✨✈️
