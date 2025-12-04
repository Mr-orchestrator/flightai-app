# ⚡ QUICK DEPLOY - 5 MINUTES TO LIVE

## 🎯 **FASTEST WAY: Render + Vercel (100% FREE)**

---

## 📦 **STEP 1: Deploy Backend (2 minutes)**

### **Go to Render.com:**
1. Visit: https://render.com
2. Sign up with GitHub (free)
3. Click: **"New +" → "Web Service"**

### **Connect Your Code:**
- **Option A:** Connect GitHub repo
- **Option B:** Upload files manually

### **Configure:**
```
Name: flightai-backend
Environment: Python 3
Build Command: pip install -r requirements.txt
Start Command: uvicorn api_server:app --host 0.0.0.0 --port $PORT
```

### **Add Environment Variables:**
Click "Environment" tab and add:
```
GOOGLE_API_KEY = your_gemini_api_key
AMADEUS_CLIENT_ID = your_amadeus_id
AMADEUS_CLIENT_SECRET = your_amadeus_secret
```

### **Deploy!**
- Click "Create Web Service"
- Wait 2-3 minutes for build
- Copy your URL: `https://flightai-backend-xxxx.onrender.com`

---

## 🎨 **STEP 2: Deploy Frontend (3 minutes)**

### **Update API URL:**

In `d:\Ai recommendor\frontend` folder, create `.env.local`:
```env
NEXT_PUBLIC_API_BASE_URL=https://your-backend-url.onrender.com
```

### **Go to Vercel.com:**
1. Visit: https://vercel.com
2. Sign up with GitHub (free)
3. Click: **"Add New..." → "Project"**

### **Import Project:**
- **Option A:** Connect GitHub repo
- **Option B:** Upload `frontend` folder

### **Configure:**
```
Framework Preset: Next.js (auto-detected)
Root Directory: frontend (if importing whole repo)
Build Command: npm run build
Output Directory: .next
```

### **Add Environment Variable:**
```
NEXT_PUBLIC_API_BASE_URL = https://your-backend-url.onrender.com
```

### **Deploy!**
- Click "Deploy"
- Wait 1-2 minutes
- Copy your URL: `https://your-app.vercel.app`

---

## ✅ **DONE! YOUR APP IS LIVE!**

### **URLs:**
- **Frontend (Public URL):** `https://your-app.vercel.app`
- **Backend API:** `https://your-backend.onrender.com`

### **Share with Anyone:**
Just send them the Vercel URL! 🎉

---

## 🔄 **UPDATE BACKEND CORS (IMPORTANT!)**

After deployment, update `api_server.py` line 30:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://your-app.vercel.app"  # Add your Vercel URL here
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Then redeploy backend:
- On Render: Git push or click "Manual Deploy"

---

## 📱 **TEST YOUR LIVE APP:**

1. Open: `https://your-app.vercel.app`
2. Select departure city
3. Type: "dubai"
4. Click: "Extract Trip Details with AI"
5. View flights!

---

## 🎁 **BONUS: Custom Domain (Optional)**

### **Add Your Own Domain:**

**On Vercel:**
1. Go to project settings
2. Click "Domains"
3. Add: `flightai.yourdomain.com`
4. Update DNS records (Vercel shows instructions)

**On Render:**
1. Go to service settings
2. Click "Custom Domains"
3. Add domain and update DNS

---

## 💰 **COSTS:**

- **Render Free Tier:**
  - ✅ 750 hours/month (enough for demo)
  - ✅ Auto-sleep after 15 min inactivity
  - ✅ Wakes up in ~30 seconds on request
  
- **Vercel Free Tier:**
  - ✅ Unlimited bandwidth
  - ✅ 100 GB-hours/month
  - ✅ Always on (no sleep)

**Total Cost: $0/month** 🎉

---

## 🚀 **UPGRADE OPTIONS (If Needed):**

### **If you need 24/7 uptime:**

**Render Paid Plan ($7/month):**
- No auto-sleep
- Faster builds
- More resources

### **If you get lots of traffic:**

**Vercel Pro ($20/month):**
- More compute
- Better analytics
- Priority support

---

## 📊 **MONITORING:**

### **Check if backend is sleeping:**
```bash
curl https://your-backend.onrender.com
```

If slow first time = was sleeping (normal on free tier)

### **Keep backend awake (optional):**
Use a service like:
- UptimeRobot (free)
- BetterUptime (free)

Set to ping your backend every 10 minutes.

---

## 🆘 **TROUBLESHOOTING:**

### **"Failed to fetch" error:**
- ✅ Check backend URL in frontend `.env.local`
- ✅ Verify backend is deployed and running
- ✅ Check CORS settings in `api_server.py`

### **Backend returns 500 error:**
- ✅ Check environment variables are set
- ✅ Verify API keys are valid
- ✅ Check Render logs for Python errors

### **Frontend shows old version:**
- ✅ Clear browser cache
- ✅ Hard refresh: Ctrl + Shift + R
- ✅ Redeploy on Vercel

---

## 🎉 **YOU'RE DONE!**

Your premium Flight AI app is now:
- ✅ Live on the internet
- ✅ Accessible from anywhere
- ✅ Free to use
- ✅ Auto-scaled
- ✅ HTTPS secured

**Share the URL and impress everyone!** 🌍✈️✨
