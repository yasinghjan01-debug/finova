# FINOVA Deployment Guide (Vercel & Netlify)

FINOVA is built with a **hybrid architecture**:
1. **Next.js 14 Frontend & Serverless Edge Handlers**: Can be deployed with **1-click directly on Vercel or Netlify**. It includes self-contained built-in edge API routes that work immediately out-of-the-box.
2. **FastAPI Python ML Backend**: Can be hosted on any container platform (Railway, Render, Fly.io, AWS EC2, or local Docker) and connected via the `FASTAPI_BACKEND_URL` environment variable.

---

## 🚀 Option 1: Deploy to Vercel (Recommended)

### Step 1: Push Repository to GitHub
```bash
git init
git add .
git commit -m "feat: FINOVA 10/10 autonomous financial memory & trust network"
git remote add origin https://github.com/<your-username>/finova.git
git branch -M main
git push -u origin main
```

### Step 2: Import to Vercel
1. Go to [https://vercel.com/new](https://vercel.com/new) and select your `finova` repository.
2. In the **Root Directory** setting, click **Edit** and choose `apps/web`.
3. Vercel will automatically detect **Next.js**.
4. *(Optional)* Add Environment Variables:
   - `FASTAPI_BACKEND_URL`: `https://your-fastapi-backend.onrender.com/api/v1` (if running Python backend separately)
5. Click **Deploy**.

> **Note:** Even without setting an external backend URL, the Vercel deployment includes full built-in Serverless Route Handlers (`/api/v1/...`) supporting the Simulation Lab, Scam Shield ML scorer, Razorpay links, Financial Memory, and AI Assistant out of the box!

---

## 🌐 Option 2: Deploy to Netlify

### Step 1: Connect to Netlify
1. Go to [https://app.netlify.com/start](https://app.netlify.com/start) and choose your GitHub repo.
2. Configure the build settings:
   - **Base directory:** `apps/web`
   - **Build command:** `npm run build`
   - **Publish directory:** `apps/web/.next`
3. Click **Deploy site**.

---

## 🐍 Option 3: Deploy the Python Backend (Render / Railway / Docker)

If you wish to deploy the dedicated Python FastAPI + XGBoost ML backend:

### Render (Free Web Service)
1. In Render, create a new **Web Service** pointing to your repo.
2. **Root Directory:** `.`
3. **Runtime:** `Python 3`
4. **Build Command:** `pip install -r requirements.txt && python -m apps.api.ml.train_models && python -m apps.api.core.seed`
5. **Start Command:** `uvicorn apps.api.main:app --host 0.0.0.0 --port $PORT`

### Docker (1-Command)
```bash
docker-compose up --build -d
```
