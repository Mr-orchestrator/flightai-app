@echo off
echo ========================================
echo  DEPLOYING FLIGHTAI TO VERCEL
echo ========================================
echo.

cd frontend

echo [1/3] Installing Vercel CLI...
call npm install -g vercel

echo.
echo [2/3] Logging in to Vercel...
echo (This will open your browser)
call vercel login

echo.
echo [3/3] Deploying to production...
call vercel --prod

echo.
echo ========================================
echo  DEPLOYMENT COMPLETE!
echo ========================================
echo.
echo Your app is now live!
echo Copy the URL shown above.
echo.
pause
