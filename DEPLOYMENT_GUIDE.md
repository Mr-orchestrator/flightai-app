# 🚀 DEPLOYMENT GUIDE - HOST YOUR FLIGHT AI APP

## 📦 **YOUR APP STRUCTURE**

```
Backend (Python FastAPI):  Port 8000
Frontend (Next.js):        Port 3000
```

---

## 🌐 **DEPLOYMENT OPTIONS**

### **Option 1: FREE HOSTING (Recommended for Demo)**

#### **Backend → Render.com (FREE)**
#### **Frontend → Vercel (FREE)**

### **Option 2: PAID HOSTING (Production)**

#### **Backend → Railway / Heroku**
#### **Frontend → Vercel / Netlify**

### **Option 3: VPS (Full Control)**

#### **Backend + Frontend → DigitalOcean / AWS / Azure**

---

## 🎯 **OPTION 1: FREE HOSTING (EASIEST)**

### **📦 PART A: Deploy Backend to Render.com**

#### **1. Prepare Backend Files:**

Create `requirements.txt` (if not exists):
```bash
cd "d:\Ai recommendor"
pip freeze > requirements.txt
```

**Or manually create with essentials:**
```txt
fastapi==0.104.1
uvicorn==0.24.0
python-dotenv==1.0.0
google-generativeai==0.3.1
amadeus==8.1.0
pydantic==2.5.0
python-multipart==0.0.6
```

#### **2. Create `render.yaml`:**

```yaml
services:
  - type: web
    name: flightai-backend
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn api_server:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: GOOGLE_API_KEY
        sync: false
      - key: AMADEUS_CLIENT_ID
        sync: false
      - key: AMADEUS_CLIENT_SECRET
        sync: false
```

#### **3. Deploy to Render:**

1. **Sign up:** https://render.com (free with GitHub)
2. **Create Web Service:**
   - Connect GitHub repo
   - Or upload files manually
3. **Environment Variables:**
   - Add `GOOGLE_API_KEY`
   - Add `AMADEUS_CLIENT_ID`
   - Add `AMADEUS_CLIENT_SECRET`
4. **Deploy!**
5. **Get URL:** `https://your-app.onrender.com`

---

### **📦 PART B: Deploy Frontend to Vercel**

#### **1. Update API URL:**

In `frontend/.env.local`:
```env
NEXT_PUBLIC_API_BASE_URL=https://your-backend.onrender.com
```

#### **2. Deploy to Vercel:**

```bash
cd "d:\Ai recommendor\frontend"

# Install Vercel CLI
npm install -g vercel

# Login
vercel login

# Deploy
vercel --prod
```

**Or use Vercel Dashboard:**
1. **Sign up:** https://vercel.com
2. **Import Git Repository** or **Upload folder**
3. **Framework:** Next.js (auto-detected)
4. **Root Directory:** `frontend`
5. **Environment Variables:**
   - `NEXT_PUBLIC_API_BASE_URL` = your Render backend URL
6. **Deploy!**
7. **Get URL:** `https://your-app.vercel.app`

---

## 🎯 **OPTION 2: RAILWAY (EASY + FAST)**

### **Backend + Frontend on Railway:**

#### **1. Install Railway CLI:**
```bash
npm install -g @railway/cli
```

#### **2. Login:**
```bash
railway login
```

#### **3. Deploy Backend:**
```bash
cd "d:\Ai recommendor"
railway init
railway up

# Set environment variables
railway variables set GOOGLE_API_KEY=your_key
railway variables set AMADEUS_CLIENT_ID=your_id
railway variables set AMADEUS_CLIENT_SECRET=your_secret
```

#### **4. Deploy Frontend:**
```bash
cd frontend
railway init
railway up

# Set backend URL
railway variables set NEXT_PUBLIC_API_BASE_URL=https://your-backend.railway.app
```

**Cost:** $5/month per service (Backend + Frontend = $10/month)

---

## 🎯 **OPTION 3: VERCEL (ALL-IN-ONE)**

Vercel can host both backend and frontend!

### **Deploy Everything:**

```bash
cd "d:\Ai recommendor"

# Create vercel.json
```

**vercel.json:**
```json
{
  "version": 2,
  "builds": [
    {
      "src": "api_server.py",
      "use": "@vercel/python"
    },
    {
      "src": "frontend/package.json",
      "use": "@vercel/next"
    }
  ],
  "routes": [
    {
      "src": "/api/(.*)",
      "dest": "api_server.py"
    },
    {
      "src": "/(.*)",
      "dest": "frontend/$1"
    }
  ]
}
```

```bash
vercel --prod
```

---

## 🎯 **OPTION 4: DOCKER (PRODUCTION-READY)**

### **1. Create Dockerfile for Backend:**

**Dockerfile.backend:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "api_server:app", "--host", "0.0.0.0", "--port", "8000"]
```

### **2. Create Dockerfile for Frontend:**

**Dockerfile.frontend:**
```dockerfile
FROM node:18-alpine

WORKDIR /app

COPY frontend/package*.json ./
RUN npm install

COPY frontend/ .

RUN npm run build

EXPOSE 3000

CMD ["npm", "start"]
```

### **3. Create docker-compose.yml:**

```yaml
version: '3.8'

services:
  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    ports:
      - "8000:8000"
    environment:
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
      - AMADEUS_CLIENT_ID=${AMADEUS_CLIENT_ID}
      - AMADEUS_CLIENT_SECRET=${AMADEUS_CLIENT_SECRET}
    
  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_BASE_URL=http://backend:8000
    depends_on:
      - backend
```

### **4. Deploy:**

```bash
docker-compose up -d
```

**Can deploy to:**
- DigitalOcean App Platform
- AWS ECS
- Google Cloud Run
- Azure Container Instances

---

## 🎯 **OPTION 5: VPS (FULL CONTROL)**

### **Providers:**
- DigitalOcean ($5/month)
- Linode ($5/month)
- Vultr ($5/month)
- AWS EC2 (Free tier available)

### **Setup on Ubuntu Server:**

```bash
# SSH into server
ssh root@your-server-ip

# Update system
apt update && apt upgrade -y

# Install Python & Node.js
apt install python3 python3-pip nodejs npm nginx -y

# Clone your code
git clone your-repo-url /var/www/flightai
cd /var/www/flightai

# Install backend dependencies
pip3 install -r requirements.txt

# Install PM2 (process manager)
npm install -g pm2

# Start backend
pm2 start "uvicorn api_server:app --host 0.0.0.0 --port 8000" --name backend

# Install frontend dependencies
cd frontend
npm install
npm run build

# Start frontend
pm2 start "npm start" --name frontend

# Save PM2 config
pm2 save
pm2 startup

# Configure Nginx (reverse proxy)
# See NGINX configuration below
```

**Nginx Config (`/etc/nginx/sites-available/flightai`):**
```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
# Enable site
ln -s /etc/nginx/sites-available/flightai /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx

# Install SSL (optional but recommended)
apt install certbot python3-certbot-nginx -y
certbot --nginx -d your-domain.com
```

---

## 📊 **COST COMPARISON**

| Option | Backend | Frontend | Total/Month |
|--------|---------|----------|-------------|
| **Render + Vercel** | Free | Free | **$0** |
| **Railway** | $5 | $5 | **$10** |
| **Vercel All-in-One** | Included | Free | **$0-20** |
| **DigitalOcean Droplet** | - | - | **$5** |
| **AWS (with free tier)** | Free | Free | **$0-10** |

---

## 🎯 **RECOMMENDED FOR YOU:**

### **🏆 Best Option: Render + Vercel (FREE)**

**Why:**
- ✅ Completely free
- ✅ Easy to deploy
- ✅ Auto-scaling
- ✅ HTTPS included
- ✅ GitHub integration
- ✅ No credit card needed

**Steps:**
1. Deploy backend to Render.com (5 minutes)
2. Deploy frontend to Vercel.com (3 minutes)
3. Update frontend env with backend URL
4. Done! ✨

---

## 📝 **QUICK START: RENDER + VERCEL**

### **1. Backend on Render:**

```bash
# 1. Go to render.com
# 2. New Web Service
# 3. Connect GitHub or upload files
# 4. Name: flightai-backend
# 5. Build Command: pip install -r requirements.txt
# 6. Start Command: uvicorn api_server:app --host 0.0.0.0 --port $PORT
# 7. Add environment variables (API keys)
# 8. Deploy!
```

**Your backend URL:** `https://flightai-backend.onrender.com`

### **2. Frontend on Vercel:**

```bash
cd "d:\Ai recommendor\frontend"

# Create .env.local
echo "NEXT_PUBLIC_API_BASE_URL=https://flightai-backend.onrender.com" > .env.local

# Deploy
npx vercel --prod
```

**Your frontend URL:** `https://your-app.vercel.app`

---

## ✅ **DONE!**

Your app is now live at:
- **Frontend:** `https://your-app.vercel.app`
- **Backend API:** `https://your-backend.onrender.com`

**Share the frontend URL with anyone!** 🎉

---

## 🔒 **SECURITY CHECKLIST**

Before deploying:

- ✅ Never commit `.env` file
- ✅ Use environment variables for secrets
- ✅ Enable HTTPS (auto on Vercel/Render)
- ✅ Set CORS to your frontend URL only
- ✅ Rate limiting (for production)
- ✅ Input validation

---

## 🆘 **TROUBLESHOOTING**

### **Backend Issues:**
- Check environment variables are set
- Verify API keys are valid
- Check server logs

### **Frontend Issues:**
- Verify `NEXT_PUBLIC_API_BASE_URL` is correct
- Check browser console for CORS errors
- Ensure backend is running

### **CORS Errors:**
Update `api_server.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend.vercel.app"],  # Your Vercel URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 🎉 **YOU'RE LIVE!**

Your premium Flight AI application is now accessible worldwide! 🌍✈️
