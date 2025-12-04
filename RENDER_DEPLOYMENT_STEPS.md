# 🚀 RENDER.COM BACKEND DEPLOYMENT - STEP BY STEP

## ✅ **PREPARATION COMPLETE**

Your files are ready:
- ✅ `requirements.txt` - Updated with all dependencies
- ✅ `render.yaml` - Render configuration
- ✅ `api_server.py` - Your backend API
- ✅ All Python backend files ready

---

## 📦 **DEPLOY TO RENDER.COM NOW**

### **STEP 1: Go to Render Dashboard**

1. Open browser: **https://dashboard.render.com**
2. **Sign up** (if new):
   - Click "Get Started for Free"
   - Sign up with GitHub (easiest)
   - OR sign up with email
3. **Login** (if existing account)

---

### **STEP 2: Create New Web Service**

1. Click the **"New +"** button (top right)
2. Select **"Web Service"**
3. You'll see two options:
   - **Build and deploy from a Git repository** (if you have GitHub)
   - **Deploy an existing image** (skip this)

---

### **STEP 3: Choose Deployment Method**

#### **OPTION A: Deploy from GitHub (Recommended)**

1. **Connect GitHub:**
   - Click "Connect GitHub"
   - Authorize Render
   - Select your repository
   - If no repo, create one first and push your code

2. **Configure repository:**
   - Repository: Select your repo
   - Branch: `main` or `master`

#### **OPTION B: Deploy without Git (Manual)**

If you don't have GitHub or want to deploy quickly:

1. **Use Public Git URL:**
   - Click "Public Git repository"
   - You can upload files manually after creating service

---

### **STEP 4: Configure Web Service Settings**

Fill in these details:

```
Name: flightai-backend
(or any name you prefer - this will be in your URL)

Region: Select closest to you
- Frankfurt (Europe)
- Ohio (US East)
- Oregon (US West)
- Singapore (Asia)

Branch: main
(or master, depending on your Git branch)

Root Directory: 
(leave blank if api_server.py is in root)

Runtime: Python 3

Build Command:
pip install -r requirements.txt

Start Command:
uvicorn api_server:app --host 0.0.0.0 --port $PORT
```

---

### **STEP 5: Select Free Plan**

1. Scroll down to **"Instance Type"**
2. Select: **"Free"** ($0/month)
   - 750 hours/month free
   - 512 MB RAM
   - Shared CPU
   - Sleeps after 15 min inactivity

---

### **STEP 6: Add Environment Variables (CRITICAL!)**

Click **"Advanced"** to expand, then scroll to **"Environment Variables"**

Add these THREE variables:

**Variable 1:**
```
Key: GOOGLE_API_KEY
Value: [YOUR_ACTUAL_GEMINI_API_KEY]
```

**Variable 2:**
```
Key: AMADEUS_CLIENT_ID
Value: [YOUR_ACTUAL_AMADEUS_CLIENT_ID]
```

**Variable 3:**
```
Key: AMADEUS_CLIENT_SECRET
Value: [YOUR_ACTUAL_AMADEUS_CLIENT_SECRET]
```

⚠️ **IMPORTANT:**
- Do NOT include quotes around the values
- Do NOT commit these to Git
- Copy exact values from your `.env` file

---

### **STEP 7: Create Web Service**

1. Review all settings
2. Click **"Create Web Service"** (bottom)
3. Render will start building...

---

### **STEP 8: Wait for Deployment**

You'll see a build log showing:

```
==> Cloning from https://github.com/...
==> Downloading cache...
==> Running build command: pip install -r requirements.txt
==> Collecting fastapi...
==> Installing dependencies...
==> Build successful!
==> Starting service...
==> Your service is live!
```

**This takes 3-5 minutes.** ⏳

---

### **STEP 9: Get Your Backend URL**

Once deployment succeeds:

1. You'll see **"Your service is live at"** 
2. Copy your URL: `https://flightai-backend-xxxx.onrender.com`
3. **SAVE THIS URL** - you need it for frontend!

---

### **STEP 10: Test Your Backend**

Open this in browser:
```
https://your-backend-url.onrender.com
```

Should show:
```json
{
  "status": "online",
  "service": "FlightAI API",
  "version": "2.0.0"
}
```

**Also test:**
```
https://your-backend-url.onrender.com/airports
```

Should return list of airports!

---

## 🔗 **STEP 11: Connect Frontend to Backend**

Now that backend is live, update your frontend:

```powershell
cd "d:\Ai recommendor\frontend"

# Add backend URL as environment variable
vercel env add NEXT_PUBLIC_API_BASE_URL production
```

When prompted, enter:
```
https://your-backend-url.onrender.com
```

Then redeploy frontend:
```powershell
vercel --prod
```

---

## ✅ **STEP 12: Update CORS (Important!)**

After getting your Vercel URL, update backend CORS:

In `api_server.py` (line 30-38):
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://your-frontend.vercel.app"  # ADD YOUR VERCEL URL
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Then push changes to GitHub (if using Git) or manually update on Render.

---

## 🎉 **YOU'RE DONE!**

Your full-stack app is now live:
- ✅ **Backend:** `https://flightai-backend.onrender.com`
- ✅ **Frontend:** `https://flightai.vercel.app`

---

## 🆘 **TROUBLESHOOTING**

### **Issue: Build Failed**
- Check logs for specific error
- Verify `requirements.txt` is correct
- Ensure all Python files are uploaded

### **Issue: Service Crashes on Start**
- Check if environment variables are set correctly
- Verify start command: `uvicorn api_server:app --host 0.0.0.0 --port $PORT`
- Check logs for Python errors

### **Issue: 500 Errors**
- Check logs (click "Logs" tab in Render dashboard)
- Verify API keys are valid
- Test endpoints individually

### **Issue: "Service Unavailable"**
- Free tier services sleep after 15 min
- First request takes ~30 seconds to wake up
- This is normal on free plan

---

## 💡 **TIPS**

### **Keep Service Awake (Optional):**
Use a free service like:
- UptimeRobot.com
- BetterUptime.com

Set to ping your backend every 10-14 minutes.

### **View Logs:**
In Render dashboard:
- Click on your service
- Click "Logs" tab
- See real-time logs

### **Manual Redeploy:**
- Click "Manual Deploy" → "Deploy latest commit"
- Or push to GitHub to auto-deploy

---

## 📊 **WHAT YOU GET (FREE TIER)**

✅ 750 hours/month (enough for demo)
✅ HTTPS included
✅ Auto-scaling
✅ Free subdomain
✅ Environment variables
✅ Build & deploy logs
❌ Service sleeps after 15 min inactivity
❌ Limited to 512 MB RAM

---

## 🎯 **NEXT STEPS**

After deployment:
1. ✅ Test backend URL in browser
2. ✅ Update frontend with backend URL
3. ✅ Redeploy frontend
4. ✅ Update CORS settings
5. ✅ Test full app end-to-end

**Ready to deploy? Follow the steps above!** 🚀
