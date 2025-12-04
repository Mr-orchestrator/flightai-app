# 📦 UPLOAD TO GITHUB - COMPLETE GUIDE

## ✅ **PREPARATION COMPLETE**
- `.gitignore` is updated (protects your API keys)
- All files are ready to upload

---

## 🚀 **STEP-BY-STEP GITHUB UPLOAD**

### **STEP 1: Create GitHub Repository**

1. **Go to GitHub:**
   - Open: https://github.com/new
   - OR: https://github.com → Click "+" → "New repository"

2. **Repository Settings:**
   ```
   Repository name: flightai-app
   (or any name you prefer)
   
   Description: AI-powered premium flight booking platform
   
   Visibility: ✓ Public (or Private if you prefer)
   
   ⚠️ DO NOT initialize with:
   □ README (we already have one)
   □ .gitignore (we already have one)
   □ License (optional)
   ```

3. **Click:** "Create repository"

4. **Copy the repository URL:**
   - You'll see: `https://github.com/yourusername/flightai-app.git`
   - Keep this page open!

---

### **STEP 2: Initialize Git & Push (PowerShell Commands)**

Open PowerShell and run these commands:

```powershell
# Navigate to your project
cd "d:\Ai recommendor"

# Initialize git (if not already)
git init

# Add all files (except those in .gitignore)
git add .

# Check what will be committed (should NOT see .env file!)
git status

# Commit files
git commit -m "Initial commit: FlightAI premium booking platform"

# Link to your GitHub repository
# Replace YOUR_USERNAME and YOUR_REPO with your actual values
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git

# Push to GitHub
git branch -M main
git push -u origin main
```

---

### **STEP 3: Verify Upload**

1. Go back to your GitHub repository page
2. Refresh the page
3. You should see all your files!

**Check that `.env` is NOT uploaded** (security!)

---

### **ALTERNATIVE: Upload via GitHub Desktop (Easier)**

If you prefer a GUI:

1. **Download GitHub Desktop:**
   - https://desktop.github.com/

2. **Install and login**

3. **Add repository:**
   - File → Add Local Repository
   - Choose: `d:\Ai recommendor`
   - Click "Add Repository"

4. **Publish:**
   - Click "Publish repository"
   - Name: flightai-app
   - Click "Publish"

---

## 🔐 **SECURITY CHECK**

Before pushing, verify `.env` is ignored:

```powershell
cd "d:\Ai recommendor"
git status
```

**Should show:**
```
Untracked files:
  (use "git add <file>..." to include in what will be committed)
        .env   ← This should be RED/untracked, NOT green/staged!
```

If `.env` is green (staged), run:
```powershell
git reset .env
```

---

## 🎯 **AFTER GITHUB UPLOAD**

### **Deploy Backend to Render:**

1. Go to: https://dashboard.render.com
2. New + → Web Service
3. **Connect GitHub repository**
4. Select: `flightai-app` repository
5. Configure:
   ```
   Build: pip install -r requirements.txt
   Start: uvicorn api_server:app --host 0.0.0.0 --port $PORT
   ```
6. Add environment variables (API keys)
7. Deploy!

**Render will auto-deploy on every Git push!** 🎉

---

## 🔄 **UPDATE CODE LATER**

When you make changes:

```powershell
cd "d:\Ai recommendor"
git add .
git commit -m "Description of changes"
git push
```

Render will automatically redeploy!

---

## 🆘 **TROUBLESHOOTING**

### **Error: "fatal: not a git repository"**
```powershell
git init
```

### **Error: "remote origin already exists"**
```powershell
git remote remove origin
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
```

### **Error: "failed to push"**
```powershell
git pull origin main --rebase
git push -u origin main
```

### **Accidentally committed .env?**
```powershell
# Remove from git (but keep local file)
git rm --cached .env
git commit -m "Remove .env from repository"
git push

# Then add to .gitignore (already done for you!)
```

---

## 📊 **WHAT GETS UPLOADED:**

✅ All Python files (api_server.py, core.py, etc.)
✅ Frontend folder (Next.js app)
✅ requirements.txt
✅ render.yaml
✅ README.md
✅ .gitignore

❌ .env (protected!)
❌ node_modules (too large)
❌ __pycache__ (temporary)
❌ .next (build folder)

---

## 🎉 **BENEFITS OF GITHUB + RENDER**

✅ **Auto-deploy:** Push code → Render auto-updates
✅ **Version control:** Track all changes
✅ **Collaboration:** Share with team
✅ **Backup:** Code is safe in cloud
✅ **Free:** Both GitHub and Render free tiers

---

## 📝 **QUICK COMMANDS**

```powershell
# One-time setup
cd "d:\Ai recommendor"
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main

# Future updates
git add .
git commit -m "Your update message"
git push
```

---

## 🎯 **READY TO UPLOAD?**

1. Create GitHub repo: https://github.com/new
2. Copy the repository URL
3. Run the PowerShell commands above
4. Deploy to Render using GitHub connection

**Your code will be safe and auto-deployable!** 🚀
