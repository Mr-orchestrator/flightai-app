# 🚀 DEPLOY YOUR APP NOW - STEP BY STEP

## ✅ **OPTION 1: DEPLOY FRONTEND TO VERCEL (EASIEST)**

### **Step 1: Install Vercel CLI**
```bash
cd "d:\Ai recommendor\frontend"
npm install -g vercel
```

### **Step 2: Login to Vercel**
```bash
vercel login
```
- Opens browser
- Sign up/login with GitHub (free account)

### **Step 3: Deploy Frontend**
```bash
vercel --prod
```

Follow prompts:
- Set up and deploy? **Y**
- Which scope? **Your account**
- Link to existing project? **N**
- Project name? **flightai** (or your choice)
- Directory? **Press Enter** (current directory)
- Override settings? **N**

**Wait 2-3 minutes...**

✅ **You'll get a URL like:** `https://flightai-xxx.vercel.app`

---

## ✅ **OPTION 2: DEPLOY BACKEND TO RENDER**

Since I can't deploy to your Render account directly, follow these steps:

### **Step 1: Go to Render.com**
1. Visit: https://dashboard.render.com
2. Sign up with GitHub (free)

### **Step 2: Create New Web Service**
1. Click **"New +"** button
2. Select **"Web Service"**
3. Choose **"Deploy from GitHub"** or **"Deploy from template"**

### **Step 3: Configure Service**

**If connecting GitHub:**
- Connect your repository
- Select branch: `main` or `master`

**If uploading manually:**
- Upload these files from `d:\Ai recommendor`:
  - `api_server.py`
  - `core.py`
  - `iata_extractor.py`
  - `amadeus_flights.py`
  - `requirements.txt`
  - `.env` (with your API keys)
  - All other Python files

### **Step 4: Service Settings**
```
Name: flightai-backend
Environment: Python 3
Region: Choose closest to you
Branch: main
Build Command: pip install -r requirements.txt
Start Command: uvicorn api_server:app --host 0.0.0.0 --port $PORT
```

### **Step 5: Add Environment Variables**
Click "Environment" tab and add:
```
GOOGLE_API_KEY = your_actual_gemini_key
AMADEUS_CLIENT_ID = your_actual_amadeus_id
AMADEUS_CLIENT_SECRET = your_actual_amadeus_secret
```

⚠️ **DO NOT include quotes around values!**

### **Step 6: Deploy Backend**
- Click **"Create Web Service"**
- Wait 3-5 minutes for build
- Copy your backend URL (e.g., `https://flightai-backend-xxxx.onrender.com`)

---

## 🔗 **STEP 3: CONNECT FRONTEND TO BACKEND**

After both are deployed:

### **Update Frontend Environment Variable**

```bash
cd "d:\Ai recommendor\frontend"
vercel env add NEXT_PUBLIC_API_BASE_URL production
```

Enter value: `https://your-backend-url.onrender.com`

### **Redeploy Frontend**
```bash
vercel --prod
```

---

## ✅ **ALTERNATIVE: DEPLOY BOTH AT ONCE WITH RAILWAY**

### **Step 1: Install Railway CLI**
```bash
npm install -g @railway/cli
```

### **Step 2: Login**
```bash
railway login
```

### **Step 3: Deploy Backend**
```bash
cd "d:\Ai recommendor"
railway init
railway up
```

Set environment variables:
```bash
railway variables set GOOGLE_API_KEY=your_key
railway variables set AMADEUS_CLIENT_ID=your_id
railway variables set AMADEUS_CLIENT_SECRET=your_secret
```

Get backend URL:
```bash
railway domain
```

### **Step 4: Deploy Frontend**
```bash
cd frontend
railway init
railway variables set NEXT_PUBLIC_API_BASE_URL=https://your-backend-url.railway.app
railway up
```

**Cost:** $5/month per service = $10/month total

---

## 🎯 **RECOMMENDED PATH FOR YOU:**

### **FREE OPTION (Render + Vercel):**
1. ✅ Deploy frontend to Vercel (via CLI above)
2. ✅ Deploy backend to Render (via dashboard)
3. ✅ Update frontend env variable
4. ✅ Redeploy frontend

**Time:** 10 minutes  
**Cost:** $0/month

### **PAID OPTION (Railway):**
1. ✅ Deploy backend to Railway (via CLI above)
2. ✅ Deploy frontend to Railway (via CLI above)

**Time:** 5 minutes  
**Cost:** $10/month

---

## 📱 **TEST YOUR DEPLOYED APP**

Once deployed:

1. Open your Vercel URL
2. Try searching: "HYD to dubai"
3. Check if flights appear

If errors:
- Check browser console (F12)
- Verify backend URL is correct
- Check backend logs on Render/Railway

---

## 🆘 **NEED HELP?**

### **Common Issues:**

**"Failed to fetch":**
```bash
# Check backend URL in Vercel dashboard
# Settings → Environment Variables → NEXT_PUBLIC_API_BASE_URL
```

**Backend 500 error:**
```bash
# Check Render logs
# Dashboard → Your Service → Logs
```

**CORS error:**
Update `api_server.py` line 30 with your Vercel URL, then redeploy backend.

---

## 🎉 **READY TO DEPLOY?**

Choose your path:

**🚀 Fast & Free (Recommended):**
```bash
# Frontend (2 minutes)
cd "d:\Ai recommendor\frontend"
npm install -g vercel
vercel login
vercel --prod
```
Then deploy backend manually on Render.com

**💰 Fast & Paid:**
```bash
# Both services (5 minutes)
npm install -g @railway/cli
railway login
cd "d:\Ai recommendor"
railway init && railway up
```

**Let's deploy! 🚀**
