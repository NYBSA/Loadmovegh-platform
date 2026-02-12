# LoadMoveGH — Production Deployment Guide

**Platform:** LoadMoveGH Freight Marketplace  
**Version:** 1.0  
**Last Updated:** February 2026  
**Target Region:** Ghana → West Africa

---

## Table of Contents

1. [Deployment Architecture Overview](#1-deployment-architecture-overview)
2. [Frontend — Vercel](#2-frontend--vercel)
3. [Backend API — Railway or Render](#3-backend-api--railway-or-render)
4. [Database — Supabase PostgreSQL](#4-database--supabase-postgresql)
5. [AI Microservice — Separate Python Container](#5-ai-microservice--separate-python-container)
6. [Mobile App — Google Play Store](#6-mobile-app--google-play-store)
7. [Environment Variables — Complete Reference](#7-environment-variables--complete-reference)
8. [Security Best Practices](#8-security-best-practices)
9. [Scaling Strategy](#9-scaling-strategy)
10. [Monitoring & Observability](#10-monitoring--observability)
11. [CI/CD Pipeline](#11-cicd-pipeline)
12. [Disaster Recovery & Backup](#12-disaster-recovery--backup)
13. [Go-Live Checklist](#13-go-live-checklist)

---

## 1. Deployment Architecture Overview

```
                        ┌──────────────┐
                        │  Cloudflare   │   CDN + WAF + DDoS protection
                        │  (DNS/Proxy)  │   www.loadmovegh.com  → Vercel (main site)
                        └──────┬───────┘   admin.loadmovegh.com → Vercel (admin console)
                               │           api.loadmovegh.com   → Railway/Render
                               │
          ┌────────────────────┼────────────────────┐
          │                    │                     │
          ▼                    ▼                     ▼
   ┌──────────────┐   ┌───────────────┐   ┌────────────────┐
   │   VERCEL      │   │  RAILWAY or   │   │  AI SERVICE    │
   │   (Frontend)  │   │  RENDER       │   │  (Railway/     │
   │               │   │  (FastAPI)    │   │   Render)      │
   │  Next.js 14   │   │               │   │                │
   │  3 dashboards │   │  Identity     │   │  ML Pricing    │
   │  + Admin      │   │  Freight      │   │  Fraud Engine  │
   │               │   │  Wallet       │   │  Load Matching │
   │               │   │  Escrow       │   │  AI Assistant  │
   │               │   │  Assistant    │   │                │
   └──────────────┘   └───────┬───────┘   └───────┬────────┘
                              │                    │
                              ▼                    ▼
                     ┌────────────────────────────────────┐
                     │       SUPABASE (PostgreSQL)         │
                     │       Connection pooler (PgBouncer) │
                     │       Row Level Security            │
                     └────────────────────────────────────┘
                              │
        ┌─────────────────────┼──────────────────────┐
        ▼                     ▼                      ▼
  ┌───────────┐     ┌──────────────────┐   ┌────────────────┐
  │  Supabase  │     │  Supabase        │   │  External APIs  │
  │  Storage   │     │  Realtime        │   │                 │
  │  (S3-compat│     │  (WebSocket)     │   │  MTN MoMo       │
  │  for KYC   │     │  for tracking    │   │  OpenAI         │
  │  docs/POD) │     │                  │   │  Google Maps    │
  └───────────┘     └──────────────────┘   │  SendGrid/SMTP  │
                                            └────────────────┘

  ┌──────────────────────────────────────────────────────────┐
  │  FLUTTER MOBILE APP                                       │
  │  → Google Play Store (Android)                            │
  │  → Apple App Store (iOS) — future                         │
  │  → Connects to api.loadmovegh.com                         │
  └──────────────────────────────────────────────────────────┘
```

---

## 2. Frontend — Vercel

### 2.1 Project Setup

```bash
# Connect repository to Vercel
cd web/
npx vercel link
```

**Vercel Dashboard Settings:**

| Setting | Value |
|---------|-------|
| Framework Preset | Next.js |
| Root Directory | `web` |
| Build Command | `next build` |
| Output Directory | `.next` |
| Install Command | `npm ci` |
| Node.js Version | 20.x |

### 2.2 Custom Domain

```
Domain:              loadmovegh.com
www redirect:        www.loadmovegh.com → loadmovegh.com (301)
SSL:                 Automatic (Let's Encrypt via Vercel)
```

In your DNS provider (**Hostinger** — where loadmovegh.com is registered):

```
Type    Name     Value                     TTL     Purpose
A       @        76.76.21.21               Auto    Root domain → Vercel
CNAME   www      cname.vercel-dns.com      Auto    www.loadmovegh.com → Vercel (main site)
CNAME   admin    cname.vercel-dns.com      Auto    admin.loadmovegh.com → Vercel (admin console)
CNAME   api      <your-railway-domain>     Auto    api.loadmovegh.com → Railway/Render (backend)
```

> **Tip:** Log in to Hostinger → Domains → loadmovegh.com → DNS/Nameservers → DNS Records.
> If using Cloudflare as a CDN proxy, point Hostinger nameservers to Cloudflare first,
> then set the above records inside Cloudflare's DNS panel.

### 2.3 Vercel Environment Variables

Set these in **Vercel Dashboard → Settings → Environment Variables**:

```bash
# API Connection
NEXT_PUBLIC_API_URL=https://api.loadmovegh.com/api/v1
NEXT_PUBLIC_WS_URL=wss://api.loadmovegh.com/ws

# Public keys only — NEVER put secrets in NEXT_PUBLIC_*
NEXT_PUBLIC_GOOGLE_MAPS_API_KEY=AIza...
NEXT_PUBLIC_APP_NAME=LoadMoveGH
NEXT_PUBLIC_APP_ENV=production

# Build-time only (server-side)
SENTRY_DSN=https://xxx@sentry.io/yyy
SENTRY_AUTH_TOKEN=sntrys_...
```

### 2.4 Vercel Configuration File

Create `web/vercel.json`:

```json
{
  "framework": "nextjs",
  "regions": ["cdg1"],
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        { "key": "X-Frame-Options", "value": "DENY" },
        { "key": "X-Content-Type-Options", "value": "nosniff" },
        { "key": "Referrer-Policy", "value": "strict-origin-when-cross-origin" },
        { "key": "Permissions-Policy", "value": "camera=(), microphone=(), geolocation=(self)" },
        {
          "key": "Content-Security-Policy",
          "value": "default-src 'self'; script-src 'self' 'unsafe-eval' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; connect-src 'self' https://api.loadmovegh.com wss://api.loadmovegh.com; font-src 'self' https://fonts.gstatic.com"
        }
      ]
    }
  ],
  "rewrites": [
    { "source": "/api/:path*", "destination": "https://api.loadmovegh.com/api/:path*" }
  ]
}
```

### 2.5 Deploy

```bash
# Preview deploy (automatic on every push to non-main branch)
git push origin feature/new-dashboard

# Production deploy (automatic on merge to main)
git push origin main

# Manual deploy
npx vercel --prod
```

---

## 3. Backend API — Railway or Render

### 3.1 Option A: Railway

#### Dockerfile

Create `api/Dockerfile`:

```dockerfile
FROM python:3.12-slim AS base

# System dependencies for psycopg, lightgbm
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Run database migrations then start server
EXPOSE 8000

CMD ["sh", "-c", "alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 4 --loop uvloop --http httptools"]
```

Create `api/.dockerignore`:

```
__pycache__
*.pyc
.env
.git
.venv
venv
ml_models/
*.egg-info
```

#### Railway Setup

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login and init
railway login
railway init

# Link to existing project
railway link

# Deploy
railway up
```

**Railway Dashboard:**

| Setting | Value |
|---------|-------|
| Service Type | Web Service |
| Root Directory | `api` |
| Builder | Dockerfile |
| Port | 8000 (auto-detected from $PORT) |
| Region | US-West or EU-West (lowest latency to Ghana) |
| Healthcheck Path | `/health` |
| Restart Policy | Always |

**Custom Domain:**

```
api.loadmovegh.com → Railway service
```

#### Railway Environment Variables

Set all variables from Section 7 below in **Railway Dashboard → Variables**.

### 3.2 Option B: Render

#### render.yaml (Blueprint)

Create `api/render.yaml`:

```yaml
services:
  - type: web
    name: loadmovegh-api
    runtime: docker
    dockerfilePath: ./Dockerfile
    dockerContext: .
    region: frankfurt  # Closest to West Africa
    plan: standard     # $25/mo — 2 GB RAM, auto-sleep disabled
    healthCheckPath: /health
    buildCommand: ""
    envVars:
      - key: PORT
        value: 8000
      - key: DATABASE_URL
        fromDatabase:
          name: loadmovegh-db
          property: connectionString
      # All other env vars set in Render Dashboard
    scaling:
      minInstances: 1
      maxInstances: 5
      targetMemoryPercent: 75
      targetCPUPercent: 70
```

#### Render Setup

1. Go to **dashboard.render.com** → **New** → **Web Service**
2. Connect your GitHub repo
3. Set **Root Directory** to `api`
4. Select **Docker** environment
5. Set **Region**: Frankfurt (closest to Accra)
6. Add environment variables from Section 7
7. Deploy

---

## 4. Database — Supabase PostgreSQL

### 4.1 Project Setup

1. Go to **supabase.com** → **New Project**
2. **Region**: Choose **Europe (Frankfurt)** — closest to West Africa with Supabase
3. **Database Password**: Generate a strong 32+ character password
4. **Plan**: Pro ($25/mo) — 8 GB RAM, daily backups, 500 MB storage

### 4.2 Connection Strings

Supabase provides multiple connection options:

```bash
# Direct connection (for migrations — NOT for app runtime)
DATABASE_URL_DIRECT=postgresql://postgres.[project-ref]:[password]@aws-0-eu-central-1.pooler.supabase.com:5432/postgres

# Transaction pooler (for FastAPI app — use this)
DATABASE_URL=postgresql+asyncpg://postgres.[project-ref]:[password]@aws-0-eu-central-1.pooler.supabase.com:6543/postgres?pgbouncer=true

# Session pooler (for long-running connections like Alembic migrations)
DATABASE_URL_MIGRATION=postgresql://postgres.[project-ref]:[password]@aws-0-eu-central-1.pooler.supabase.com:5432/postgres
```

### 4.3 Run Migrations

```bash
# Set migration connection string (direct, not pooled)
export DATABASE_URL="postgresql://postgres.[ref]:[password]@aws-0-eu-central-1.pooler.supabase.com:5432/postgres"

# Run all migrations
cd api/
alembic upgrade head

# Generate new migration after model changes
alembic revision --autogenerate -m "add_chat_sessions_table"
alembic upgrade head
```

### 4.4 Supabase Configuration

**Enable extensions** (via SQL Editor in Supabase Dashboard):

```sql
-- Required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";    -- UUID generation
CREATE EXTENSION IF NOT EXISTS "pgcrypto";     -- Encryption functions
CREATE EXTENSION IF NOT EXISTS "pg_trgm";      -- Fuzzy text search
CREATE EXTENSION IF NOT EXISTS "postgis";      -- Geospatial queries (optional)

-- Performance indexes (run after migrations)
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_listings_geo
  ON freight_listings USING gist (
    ST_MakePoint(origin_lng, origin_lat)
  );
```

**Connection pool settings** (Supabase Dashboard → Settings → Database):

| Setting | Value |
|---------|-------|
| Pool Mode | Transaction |
| Pool Size | 15 (Pro plan default) |
| Statement Timeout | 30s |

### 4.5 Supabase Storage (for KYC docs, POD images)

```sql
-- Create storage buckets via Supabase Dashboard or API
-- Bucket: kyc-documents (private)
-- Bucket: proof-of-delivery (private)
-- Bucket: profile-images (public)
```

### 4.6 Backups

- **Supabase Pro**: Daily automatic backups, 7-day retention
- **Point-in-Time Recovery**: Available on Pro plan (up to 7 days)
- **Manual backup**:

```bash
# Weekly manual backup to external storage
pg_dump "postgresql://..." | gzip > loadmovegh_backup_$(date +%Y%m%d).sql.gz
```

---

## 5. AI Microservice — Separate Python Container

### 5.1 Why Separate?

The AI/ML workloads (pricing engine, fraud detection, load matching) benefit from isolation:

- **Different scaling**: CPU/memory-intensive; scales independently
- **Different dependencies**: numpy, lightgbm, scikit-learn are heavy
- **Deployment independence**: Retrain and deploy models without touching the API
- **Resource isolation**: ML inference won't starve API response times

### 5.2 Dockerfile

Create `api/Dockerfile.ai`:

```dockerfile
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# AI-specific requirements
COPY requirements-ai.txt .
RUN pip install --no-cache-dir -r requirements-ai.txt

# Copy only AI-related code
COPY app/ai/ ./app/ai/
COPY app/ml/ ./app/ml/
COPY app/models/ ./app/models/
COPY app/schemas/ ./app/schemas/
COPY app/core/ ./app/core/
COPY ai_service.py .

# Model artifacts directory
RUN mkdir -p /app/ml_models

EXPOSE 8001

CMD ["uvicorn", "ai_service:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "2"]
```

Create `api/requirements-ai.txt`:

```
fastapi
uvicorn[standard]
pydantic>=2.0
pydantic-settings
sqlalchemy[asyncio]>=2.0
asyncpg
numpy
lightgbm
scikit-learn
httpx
openai
```

### 5.3 AI Service Entry Point

Create `api/ai_service.py`:

```python
"""
LoadMoveGH — AI Microservice Entry Point
Serves: Pricing Engine, Fraud Detection, Load Matching, AI Assistant
Runs as a separate container on port 8001.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.endpoints.pricing import router as pricing_router
from app.api.v1.endpoints.matching import router as matching_router
from app.api.v1.endpoints.fraud import router as fraud_router
from app.api.v1.endpoints.assistant import router as assistant_router
from app.core.config import settings

app = FastAPI(
    title="LoadMoveGH AI Service",
    description="ML Pricing, Fraud Detection, Load Matching & AI Assistant",
    version="1.0.0",
    docs_url="/ai/docs",
    redoc_url="/ai/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "https://api.loadmovegh.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(pricing_router, prefix="/ai/v1")
app.include_router(matching_router, prefix="/ai/v1")
app.include_router(fraud_router, prefix="/ai/v1")
app.include_router(assistant_router, prefix="/ai/v1")

@app.get("/ai/health")
async def health():
    return {"status": "healthy", "service": "loadmovegh-ai"}
```

### 5.4 Deploy on Railway (as second service)

```bash
# In Railway Dashboard:
# 1. Same project → "New Service" → Docker
# 2. Set Dockerfile path: api/Dockerfile.ai
# 3. Set root directory: api
# 4. Set PORT=8001
# 5. Internal networking: main API calls AI service via private URL

# Railway gives you an internal URL like:
# http://loadmovegh-ai.railway.internal:8001
```

### 5.5 AI Service Environment Variables

```bash
# Same database (read-only where possible)
DATABASE_URL=postgresql+asyncpg://...supabase.com:6543/postgres?pgbouncer=true

# OpenAI
OPENAI_API_KEY=sk-prod-...
OPENAI_MODEL=gpt-4o
OPENAI_MAX_TOKENS=2048
OPENAI_TEMPERATURE=0.4

# ML Models
PRICING_MODEL_DIR=/app/ml_models
PRICING_DEFAULT_DIESEL_PRICE=15.50

# Fraud thresholds
FRAUD_ALERT_THRESHOLD_MEDIUM=40.0
FRAUD_ALERT_THRESHOLD_HIGH=65.0
FRAUD_ALERT_THRESHOLD_CRITICAL=85.0

# Matching
MATCHING_MAX_RADIUS_KM=300
MATCHING_MIN_COMPOSITE_SCORE=30.0
```

### 5.6 Model Artifact Management

```bash
# Store trained models in Supabase Storage or S3
# Download at container startup:

# In Dockerfile.ai, add:
# RUN pip install supabase
# COPY scripts/download_models.py .
# RUN python download_models.py (or do it at runtime)

# Or mount a persistent volume on Railway:
# Railway Dashboard → Service → Volumes → Mount at /app/ml_models
```

---

## 6. Mobile App — Google Play Store

### 6.1 Pre-Release Build

```bash
cd mobile/

# Get dependencies
flutter pub get

# Run code generation (JSON serializable, Riverpod, Freezed)
dart run build_runner build --delete-conflicting-outputs

# Run tests
flutter test

# Build Android release APK
flutter build apk --release \
  --dart-define=API_BASE_URL=https://api.loadmovegh.com \
  --dart-define=GOOGLE_MAPS_API_KEY=AIza...

# Build Android App Bundle (required for Play Store)
flutter build appbundle --release \
  --dart-define=API_BASE_URL=https://api.loadmovegh.com \
  --dart-define=GOOGLE_MAPS_API_KEY=AIza...
```

### 6.2 Signing Configuration

Create `mobile/android/key.properties` (DO NOT commit this):

```properties
storePassword=YOUR_KEYSTORE_PASSWORD
keyPassword=YOUR_KEY_PASSWORD
keyAlias=loadmovegh
storeFile=/path/to/loadmovegh-release.keystore
```

Generate the keystore:

```bash
keytool -genkey -v \
  -keystore loadmovegh-release.keystore \
  -keyalg RSA -keysize 2048 -validity 10000 \
  -alias loadmovegh \
  -dname "CN=LoadMoveGH, OU=Engineering, O=LoadMoveGH Ltd, L=Accra, ST=Greater Accra, C=GH"
```

Update `mobile/android/app/build.gradle`:

```groovy
def keystoreProperties = new Properties()
def keystorePropertiesFile = rootProject.file('key.properties')
if (keystorePropertiesFile.exists()) {
    keystoreProperties.load(new FileInputStream(keystorePropertiesFile))
}

android {
    signingConfigs {
        release {
            keyAlias keystoreProperties['keyAlias']
            keyPassword keystoreProperties['keyPassword']
            storeFile keystoreProperties['storeFile'] ? file(keystoreProperties['storeFile']) : null
            storePassword keystoreProperties['storePassword']
        }
    }
    buildTypes {
        release {
            signingConfig signingConfigs.release
            minifyEnabled true
            shrinkResources true
            proguardFiles getDefaultProguardFile('proguard-android-optimize.txt'), 'proguard-rules.pro'
        }
    }
}
```

### 6.3 Google Play Console

1. **Create Developer Account**: $25 one-time fee at [play.google.com/console](https://play.google.com/console)
2. **Create App**: "LoadMoveGH — Ghana Freight Marketplace"
3. **Store Listing**:

| Field | Value |
|-------|-------|
| App Name | LoadMoveGH |
| Short Description | Ghana's AI-powered freight marketplace |
| Full Description | Connect with couriers, ship cargo, track deliveries, and pay securely with Mobile Money. |
| Category | Business |
| Content Rating | Everyone |
| Target Countries | Ghana (primary), Nigeria, Senegal |

4. **Upload AAB**: Upload `build/app/outputs/bundle/release/app-release.aab`
5. **Testing Tracks**:
   - **Internal Testing** → 10 testers for initial QA
   - **Closed Testing** → 100 beta users in Ghana
   - **Open Testing** → Public beta
   - **Production** → Full release

### 6.4 Play Store Compliance

- **Privacy Policy URL**: `https://loadmovegh.com/privacy`
- **Data Safety Form**: Declare collected data (location, financial, personal identifiers)
- **Permissions Justification**:
  - Location: Real-time shipment tracking
  - Camera: Proof of delivery photos
  - Notifications: Bid alerts, trip updates

### 6.5 Over-the-Air Updates (Optional)

Consider **Shorebird** for Flutter OTA patches:

```bash
# Install Shorebird
curl --proto '=https' --tlsv1.2 https://raw.githubusercontent.com/shorebirdtech/install/main/install.sh -sSf | bash

# Release with Shorebird
shorebird release android

# Push a patch (no Play Store review needed)
shorebird patch android
```

---

## 7. Environment Variables — Complete Reference

### 7.1 Backend API (Railway/Render)

```bash
# ══════════════════════════════════════════════════════════
#  APPLICATION
# ══════════════════════════════════════════════════════════
APP_NAME=LoadMoveGH
APP_ENV=production                          # CRITICAL: set to production
DEBUG=false                                  # CRITICAL: disable debug
API_V1_PREFIX=/api/v1

# ══════════════════════════════════════════════════════════
#  DATABASE (Supabase)
# ══════════════════════════════════════════════════════════
DATABASE_URL=postgresql+asyncpg://postgres.[ref]:[pw]@aws-0-eu-central-1.pooler.supabase.com:6543/postgres?pgbouncer=true

# ══════════════════════════════════════════════════════════
#  JWT SECRETS (generate with: openssl rand -hex 64)
# ══════════════════════════════════════════════════════════
JWT_SECRET_KEY=<64-char-hex-string>
JWT_REFRESH_SECRET_KEY=<different-64-char-hex-string>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15               # Shorter in production
REFRESH_TOKEN_EXPIRE_DAYS=7

# ══════════════════════════════════════════════════════════
#  EMAIL (SendGrid recommended for production)
# ══════════════════════════════════════════════════════════
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=SG.xxxx                        # SendGrid API key
EMAIL_FROM=noreply@loadmovegh.com
EMAIL_FROM_NAME=LoadMoveGH

# ══════════════════════════════════════════════════════════
#  OTP
# ══════════════════════════════════════════════════════════
OTP_EXPIRE_MINUTES=5                         # Shorter in production
OTP_LENGTH=6

# ══════════════════════════════════════════════════════════
#  MTN MOBILE MONEY (production keys)
# ══════════════════════════════════════════════════════════
MOMO_BASE_URL=https://proxy.momoapi.mtn.com  # Production URL
MOMO_COLLECTION_API_KEY=<production-key>
MOMO_COLLECTION_API_USER=<production-user>
MOMO_COLLECTION_SUBSCRIPTION_KEY=<production-sub-key>
MOMO_DISBURSEMENT_API_KEY=<production-key>
MOMO_DISBURSEMENT_API_USER=<production-user>
MOMO_DISBURSEMENT_SUBSCRIPTION_KEY=<production-sub-key>
MOMO_CALLBACK_HOST=https://api.loadmovegh.com
MOMO_ENVIRONMENT=production

# ══════════════════════════════════════════════════════════
#  PLATFORM FEES
# ══════════════════════════════════════════════════════════
PLATFORM_COMMISSION_RATE=0.05
WITHDRAWAL_FEE_RATE=0.01
WITHDRAWAL_FEE_MIN=0.50
WITHDRAWAL_FEE_MAX=10.00
MIN_DEPOSIT_AMOUNT=1.00
MIN_WITHDRAWAL_AMOUNT=5.00
MAX_TRANSACTION_AMOUNT=50000.00

# ══════════════════════════════════════════════════════════
#  AI / ML
# ══════════════════════════════════════════════════════════
OPENAI_API_KEY=sk-prod-...
OPENAI_MODEL=gpt-4o
OPENAI_MAX_TOKENS=2048
OPENAI_TEMPERATURE=0.4
OPENAI_MAX_SESSIONS_PER_USER=50
OPENAI_MAX_MESSAGES_PER_SESSION=100
PRICING_MODEL_DIR=ml_models
PRICING_DEFAULT_DIESEL_PRICE=15.50
PRICING_CONFIDENCE_THRESHOLD=0.50
MATCHING_MAX_RADIUS_KM=300
MATCHING_MIN_COMPOSITE_SCORE=30.0
MATCHING_DEFAULT_TOP_K=10

# ══════════════════════════════════════════════════════════
#  FRAUD DETECTION
# ══════════════════════════════════════════════════════════
FRAUD_ALERT_THRESHOLD_MEDIUM=40.0
FRAUD_ALERT_THRESHOLD_HIGH=65.0
FRAUD_ALERT_THRESHOLD_CRITICAL=85.0
FRAUD_AUTO_SCAN_ON_TRANSACTION=true
FRAUD_MAX_SIGNALS_PER_SCAN=50

# ══════════════════════════════════════════════════════════
#  CORS & FRONTEND
# ══════════════════════════════════════════════════════════
FRONTEND_URL=https://loadmovegh.com
CORS_ORIGINS=["https://loadmovegh.com","https://www.loadmovegh.com","https://admin.loadmovegh.com"]

# ══════════════════════════════════════════════════════════
#  MONITORING (optional)
# ══════════════════════════════════════════════════════════
SENTRY_DSN=https://xxx@o123.ingest.sentry.io/456
LOG_LEVEL=WARNING
```

### 7.2 Frontend (Vercel)

```bash
NEXT_PUBLIC_API_URL=https://api.loadmovegh.com/api/v1
NEXT_PUBLIC_GOOGLE_MAPS_API_KEY=AIza...
NEXT_PUBLIC_APP_NAME=LoadMoveGH
NEXT_PUBLIC_APP_ENV=production
SENTRY_DSN=https://xxx@sentry.io/yyy
```

### 7.3 Mobile App (compile-time)

```bash
# Passed via --dart-define at build time
API_BASE_URL=https://api.loadmovegh.com
GOOGLE_MAPS_API_KEY=AIza...
```

---

## 8. Security Best Practices

### 8.1 Authentication & Secrets

| Practice | Implementation |
|----------|---------------|
| JWT expiry | Access: 15 min, Refresh: 7 days |
| JWT secrets | 64-char random hex, generated per environment |
| Secret storage | Railway/Render encrypted env vars (never in code) |
| Password hashing | bcrypt with cost factor 12 |
| OTP | 6 digits, 5-min expiry, rate-limited (3 attempts/10 min) |
| API keys | SHA-256 hashed in DB, shown once on creation |

Generate secure secrets:

```bash
# JWT secrets
openssl rand -hex 64

# Database password
openssl rand -base64 32
```

### 8.2 Network Security

```
┌─ Cloudflare (free plan) ─────────────────────────────┐
│  ✓ DDoS protection (automatic)                        │
│  ✓ WAF rules (block SQL injection, XSS)               │
│  ✓ Rate limiting (100 req/10s per IP)                  │
│  ✓ Bot management                                      │
│  ✓ SSL/TLS 1.3 (full strict mode)                      │
│  ✓ Country blocking (if needed)                        │
│  ✓ Page rules: cache static assets 30d                 │
└───────────────────────────────────────────────────────┘
```

**Cloudflare WAF Rules:**

```
Rule 1: Block requests with SQL injection patterns
Rule 2: Block requests with XSS patterns
Rule 3: Rate limit /auth/* to 10 req/min per IP
Rule 4: Rate limit /assistant/* to 20 req/min per user
Rule 5: Challenge requests from Tor exit nodes
```

### 8.3 Data Protection

| Data Type | Protection |
|-----------|------------|
| Passwords | bcrypt hash, never stored plaintext |
| JWT tokens | Short-lived, httpOnly cookies (web), secure storage (mobile) |
| KYC documents | Encrypted at rest (Supabase Storage), time-limited signed URLs |
| Phone numbers | Stored in DB, masked in API responses (024****567) |
| Financial data | Audit logged, encrypted sensitive fields |
| PII in logs | Never log passwords, tokens, full phone numbers, card details |
| Database | TLS in transit, encrypted at rest (Supabase default) |

### 8.4 API Security Headers

Already configured in `vercel.json` above. For the backend:

```python
# Add to main.py
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["api.loadmovegh.com", "localhost"],
)
```

### 8.5 Dependency Security

```bash
# Python — audit for vulnerabilities
pip install pip-audit
pip-audit -r requirements.txt

# Node.js — audit for vulnerabilities
cd web && npm audit --production

# Flutter — check for outdated/vulnerable packages
cd mobile && flutter pub outdated
```

### 8.6 Mobile App Security

| Practice | Implementation |
|----------|---------------|
| Token storage | `flutter_secure_storage` (Keychain/Keystore) |
| Certificate pinning | Pin api.loadmovegh.com cert hash |
| Root detection | Detect rooted/jailbroken devices, warn user |
| Obfuscation | `flutter build apk --obfuscate --split-debug-info=debug-info/` |
| ProGuard | Enabled in release builds |
| No secrets in APK | All secrets fetched from API at runtime |

---

## 9. Scaling Strategy

### 9.1 Phase 1: Launch (0–10K MAU)

```
Vercel:    Hobby/Pro plan ($0–$20/mo)     — auto-scales
Railway:   Starter plan ($5/mo)            — 1 instance, 512 MB
AI Svc:    Same Railway project ($5/mo)    — 1 instance, 1 GB
Supabase:  Free/Pro plan ($0–$25/mo)       — 500 MB DB

Total: ~$35–$55/month
```

### 9.2 Phase 2: Growth (10K–100K MAU)

```
Vercel:    Pro plan ($20/mo)               — edge functions, analytics
Railway:   Pro plan ($20/mo base)          — auto-scale 1→4 instances
           2 GB RAM per instance
AI Svc:    Separate Railway service         — 4 GB RAM, 2 workers
Supabase:  Pro plan ($25/mo)               — 8 GB RAM, connection pooling
Redis:     Upstash Serverless ($0–$10/mo)  — session cache, rate limiting

Total: ~$100–$200/month
```

### 9.3 Phase 3: West Africa (100K+ MAU)

```
Vercel:    Enterprise                       — SLA, support
Railway:   Team plan                        — 8+ instances, 4 GB each
AI Svc:    Dedicated instance               — GPU for ML training
Supabase:  Team plan ($599/mo)              — read replicas, PITR
Redis:     Upstash Pro                      — global replication
CDN:       Cloudflare Pro ($20/mo)          — advanced WAF, analytics

Total: ~$800–$1,500/month
```

### 9.4 Auto-Scaling Configuration

**Railway** (via Dockerfile or `railway.toml`):

```toml
# api/railway.toml
[deploy]
healthcheckPath = "/health"
healthcheckTimeout = 5
numReplicas = 2
restartPolicyType = "ON_FAILURE"

[deploy.scaling]
minInstances = 1
maxInstances = 5
```

**Render** (`render.yaml` — already configured above):

```yaml
scaling:
  minInstances: 1
  maxInstances: 5
  targetMemoryPercent: 75
  targetCPUPercent: 70
```

### 9.5 Database Scaling Path

```
Phase 1:  Supabase Free/Pro (single instance, connection pooler)
Phase 2:  Supabase Pro + read replica (for analytics/reports)
Phase 3:  Supabase Team + multiple read replicas + regional
Phase 4:  Self-managed PostgreSQL on AWS RDS (if needed)
```

---

## 10. Monitoring & Observability

### 10.1 Monitoring Stack

```
┌──────────────────────────────────────────────────────────┐
│                    MONITORING STACK                        │
│                                                           │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐  │
│  │   Sentry     │  │  BetterStack  │  │  Checkly       │  │
│  │  (Errors)    │  │  (Logs)       │  │  (Uptime)      │  │
│  │              │  │              │  │                 │  │
│  │  Python SDK  │  │  Structured   │  │  HTTP checks   │  │
│  │  Next.js SDK │  │  JSON logs    │  │  every 1 min   │  │
│  │  Flutter SDK │  │  Log drain    │  │  Multi-region  │  │
│  └─────────────┘  └──────────────┘  └────────────────┘  │
│                                                           │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐  │
│  │  Supabase    │  │  Railway     │  │  Vercel        │  │
│  │  Dashboard   │  │  Metrics     │  │  Analytics     │  │
│  │              │  │              │  │                 │  │
│  │  DB metrics  │  │  CPU, RAM    │  │  Web Vitals    │  │
│  │  Query perf  │  │  Network     │  │  Edge latency  │  │
│  │  Storage     │  │  Deploy logs │  │  Build times   │  │
│  └─────────────┘  └──────────────┘  └────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

### 10.2 Sentry (Error Tracking) — Free Tier Available

**Backend:**

```bash
pip install sentry-sdk[fastapi]
```

```python
# Add to main.py
import sentry_sdk

sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    environment=os.getenv("APP_ENV", "production"),
    traces_sample_rate=0.2,       # 20% of requests traced
    profiles_sample_rate=0.1,     # 10% profiled
    send_default_pii=False,       # CRITICAL: no PII to Sentry
)
```

**Frontend (Next.js):**

```bash
cd web && npx @sentry/wizard@latest -i nextjs
```

**Mobile (Flutter):**

```yaml
# pubspec.yaml
dependencies:
  sentry_flutter: ^8.0.0
```

```dart
// main.dart
await SentryFlutter.init(
  (options) {
    options.dsn = 'https://xxx@sentry.io/yyy';
    options.environment = 'production';
    options.tracesSampleRate = 0.2;
    options.sendDefaultPii = false;
  },
  appRunner: () => runApp(const ProviderScope(child: LoadMoveGHApp())),
);
```

### 10.3 Uptime Monitoring — Checkly or UptimeRobot

**Endpoints to monitor:**

| Endpoint | Interval | Alert |
|----------|----------|-------|
| `https://loadmovegh.com` | 1 min | Slack + Email |
| `https://api.loadmovegh.com/health` | 1 min | Slack + SMS |
| `https://api.loadmovegh.com/ai/health` | 2 min | Slack + Email |
| `https://api.loadmovegh.com/api/v1/auth/login` (POST test) | 5 min | Slack |

### 10.4 Structured Logging

```python
# api/app/core/logging_config.py
import logging
import json
import sys

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_obj = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "service": "loadmovegh-api",
        }
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_obj)

# Configure in main.py
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(JSONFormatter())
logging.basicConfig(level=logging.WARNING, handlers=[handler])
```

### 10.5 Key Metrics to Track

| Category | Metric | Alert Threshold |
|----------|--------|-----------------|
| **API** | Response time (p95) | > 2s |
| **API** | Error rate (5xx) | > 1% |
| **API** | Request rate | Sudden 10x spike |
| **DB** | Connection pool usage | > 80% |
| **DB** | Query time (p95) | > 500ms |
| **DB** | Storage usage | > 80% |
| **AI** | OpenAI latency | > 10s |
| **AI** | OpenAI token spend/day | > $50 |
| **Wallet** | Failed MoMo transactions | > 5% |
| **Fraud** | Critical alerts/hour | > 10 |
| **Mobile** | Crash-free rate | < 99% |
| **Uptime** | API availability | < 99.9% |

### 10.6 Cost Monitoring

| Service | Cost Alert |
|---------|------------|
| OpenAI API | > $100/month → review prompt optimization |
| Railway | > $50/month → review instance sizing |
| Supabase | > $50/month → review query patterns |
| Vercel | > $30/month → review image optimization |
| SendGrid | > $15/month → review email volume |

---

## 11. CI/CD Pipeline

### 11.1 GitHub Actions

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy LoadMoveGH

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  # ── Test Backend ────────────────────────────────────────
  test-api:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install -r api/requirements.txt
      - run: pip install pytest pytest-asyncio httpx
      - run: cd api && python -m pytest tests/ -v
        env:
          APP_ENV: test
          DATABASE_URL: sqlite+aiosqlite:///test.db

  # ── Test Frontend ───────────────────────────────────────
  test-web:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: web/package-lock.json
      - run: cd web && npm ci
      - run: cd web && npm run lint
      - run: cd web && npm run build
        env:
          NEXT_PUBLIC_API_URL: https://api.loadmovegh.com/api/v1

  # ── Test Mobile ─────────────────────────────────────────
  test-mobile:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: subosito/flutter-action@v2
        with:
          flutter-version: '3.24.0'
      - run: cd mobile && flutter pub get
      - run: cd mobile && flutter analyze
      - run: cd mobile && flutter test

  # ── Deploy Backend (Railway — auto-deploys from GitHub) ─
  # Railway auto-deploys on push to main. No step needed.

  # ── Deploy Frontend (Vercel — auto-deploys from GitHub) ─
  # Vercel auto-deploys on push to main. No step needed.
```

### 11.2 Pre-Deployment Checklist (automated)

```yaml
  security-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Check for secrets in code
        uses: trufflesecurity/trufflehog@main
        with:
          path: ./
      - name: Python dependency audit
        run: pip install pip-audit && pip-audit -r api/requirements.txt
      - name: Node dependency audit
        run: cd web && npm audit --production
```

---

## 12. Disaster Recovery & Backup

### 12.1 Backup Schedule

| Data | Frequency | Retention | Storage |
|------|-----------|-----------|---------|
| PostgreSQL (full) | Daily (Supabase auto) | 7 days (Pro) | Supabase |
| PostgreSQL (PITR) | Continuous (Pro plan) | 7 days | Supabase |
| ML model artifacts | On every training run | Last 5 versions | Supabase Storage |
| KYC documents | Replicated (Supabase Storage) | Indefinite | Supabase Storage |
| Environment configs | Git-encrypted (SOPS) | Indefinite | GitHub |

### 12.2 Recovery Procedures

**Scenario: Database corruption**
```bash
# Supabase Dashboard → Backups → Restore to point in time
# OR restore from daily backup
```

**Scenario: API service down**
```bash
# Railway: auto-restarts on failure (restart policy)
# Manual: railway up --force
# Render: auto-restarts, manual redeploy from dashboard
```

**Scenario: Frontend down**
```bash
# Vercel: instant rollback to previous deployment
# Dashboard → Deployments → click "..." → Promote to Production
```

### 12.3 Recovery Time Objectives

| Scenario | RTO | RPO |
|----------|-----|-----|
| API service crash | 30 seconds (auto-restart) | 0 (stateless) |
| Database corruption | 1 hour (PITR restore) | < 5 minutes |
| Frontend deployment failure | 2 minutes (Vercel rollback) | 0 |
| Full region failure | 4 hours (re-deploy to new region) | < 1 hour |

---

## 13. Go-Live Checklist

### Pre-Launch (1 week before)

- [ ] **Secrets**: All production secrets rotated from development values
- [ ] **JWT secrets**: Generated fresh 64-char keys for production
- [ ] **DEBUG=false**: Confirmed in all environments
- [ ] **CORS**: Only production domains listed
- [ ] **MoMo API**: Switched from sandbox to production
- [ ] **Database**: Migrations run, indexes created, backups tested
- [ ] **SSL**: Cloudflare SSL/TLS set to "Full (Strict)"
- [ ] **WAF**: Cloudflare WAF rules active
- [ ] **Monitoring**: Sentry, uptime checks, log drain configured
- [ ] **Error pages**: Custom 404 and 500 pages in place
- [ ] **Rate limiting**: Cloudflare rate rules active

### Pre-Launch (1 day before)

- [ ] **Load test**: Run 100 concurrent users against staging
- [ ] **Mobile**: Tested on 5+ real Android devices in Ghana
- [ ] **MoMo**: Test deposit + withdrawal with real GHS 1.00
- [ ] **Email**: Test verification and password reset flows
- [ ] **Backup**: Verify restore procedure works
- [ ] **Rollback plan**: Documented and tested

### Launch Day

- [ ] **DNS**: Point www.loadmovegh.com → Vercel, admin.loadmovegh.com → Vercel, api.loadmovegh.com → Railway/Render (via Hostinger DNS)
- [ ] **Play Store**: Publish app from closed testing to production
- [ ] **Team on standby**: Engineering on-call for 24 hours
- [ ] **Monitoring dashboard**: Open on big screen

### Post-Launch (first week)

- [ ] **Error rates**: Sentry showing < 0.5% error rate
- [ ] **API latency**: p95 under 2 seconds
- [ ] **MoMo success rate**: > 95%
- [ ] **User feedback**: Collect from first 100 users
- [ ] **Cost check**: Review OpenAI, Railway, Supabase spend
- [ ] **Scale check**: Review if auto-scaling triggered correctly

---

## Quick Reference — Production URLs

| Service | URL |
|---------|-----|
| Main Site | `https://www.loadmovegh.com` |
| Admin Console | `https://admin.loadmovegh.com` |
| API | `https://api.loadmovegh.com` |
| API Docs | `https://api.loadmovegh.com/docs` |
| AI Service | `https://api.loadmovegh.com/ai/docs` (internal) |
| Domain Registrar | Hostinger — `https://www.hostinger.com` |
| Supabase Dashboard | `https://supabase.com/dashboard/project/[ref]` |
| Railway Dashboard | `https://railway.app/project/[id]` |
| Vercel Dashboard | `https://vercel.com/loadmovegh` |
| Play Store | `https://play.google.com/store/apps/details?id=com.loadmovegh.app` |
| Sentry | `https://loadmovegh.sentry.io` |

---

*Document prepared for engineering team deployment. Review with DevOps and Security before executing.*
