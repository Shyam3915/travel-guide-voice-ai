# 🌍 AI Travel Guide

An interactive AI-powered tourist guide application that provides concise or detailed spoken audio guides in multiple languages (English, Hindi, Tamil, Telugu) using Google Gemini and Murf AI.

---

## 🚀 Live Deployment on Vercel

This repository is pre-configured for **Vercel** serverless deployment with:
- **Frontend**: Static UI hosted on Vercel CDN.
- **Backend**: Python Serverless Functions in [`api/index.py`](api/index.py) using `@vercel/python`.
- **Routing**: Configured via [`vercel.json`](vercel.json).

### Method 1: Deploy via GitHub (Recommended)
1. Push this project to your GitHub repository:
   ```bash
   git add .
   git commit -m "Configure Vercel deployment"
   git remote add origin https://github.com/<your-username>/<your-repo-name>.git
   git push -u origin main
   ```
2. Go to [vercel.com/new](https://vercel.com/new).
3. Import your GitHub repository.
4. (Optional) Under **Environment Variables**, add:
   - `GEMINI_API_KEY`: Your Google Gemini API key.
   - `MURF_API_KEY`: Your Murf AI API key.
5. Click **Deploy**. Vercel will build and assign you a live `.vercel.app` URL.

---

### Method 2: Deploy via Vercel CLI
1. Open your terminal in this directory.
2. Log in to Vercel:
   ```bash
   vercel login
   ```
3. Deploy to production:
   ```bash
   vercel --prod
   ```

---

## 💻 Local Development

### 1. Backend
```bash
# Activate your virtual environment
.\.venv\Scripts\activate

# Install requirements
pip install -r requirements.txt

# Run serverless API entrypoint
python api/index.py
```
API runs on `http://127.0.0.1:5000`.

### 2. Frontend
Open `Frontend/index.html` in your browser (or use VS Code Live Server). The frontend dynamically connects to `http://127.0.0.1:5000` when run locally, and to `/api/...` when deployed on Vercel.
