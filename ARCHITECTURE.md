# Ghana Freight Marketplace Platform — Enterprise Architecture

**Project Codename:** GHANA-FREIGHT  
**Version:** 1.0  
**Document Type:** System Architecture & Design Specification  
**Target Region:** Ghana → West Africa  
**Reference:** Courier Exchange (AI-Powered Equivalent)

---

## Executive Summary

An enterprise freight marketplace connecting shippers with couriers across Ghana and West Africa, powered by AI-driven pricing, fraud detection, and an integrated wallet/escrow system. The platform supports web dashboards, mobile applications, and administrative oversight.

---

## 1. System Architecture Diagram (Text Format)

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                              EDGE LAYER (CDN / WAF / DDoS Protection)                            │
│                              Cloudflare / AWS CloudFront                                          │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
                                                    │
                                                    ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                              API GATEWAY / BFF LAYER                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ Public API   │  │ Courier API  │  │ Shipper API  │  │ Admin API    │  │ Mobile API   │       │
│  │ (Rate Ltd)   │  │ (BFF)       │  │ (BFF)       │  │ (BFF)       │  │ (GraphQL)    │       │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘       │
│                                    Kong / AWS API Gateway / Azure APIM                            │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
                                                    │
        ┌───────────────────────────────────────────┼───────────────────────────────────────────┐
        │                                           │                                           │
        ▼                                           ▼                                           ▼
┌───────────────────┐                   ┌───────────────────────┐                   ┌───────────────────┐
│   PUBLIC WEBSITE  │                   │    WEB DASHBOARDS     │                   │   MOBILE APP      │
│   (Marketing)     │                   │  Courier | Shipper    │                   │   React Native    │
│   Next.js / SSG   │                   │  Next.js (App Router) │                   │   / Flutter       │
└───────────────────┘                   └───────────────────────┘                   └───────────────────┘
                                                    │
                                                    ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                              CORE APPLICATION LAYER (Microservices)                               │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐  │
│  │  Identity   │ │   Freight   │ │   Wallet    │ │ AI Pricing  │ │ AI Fraud    │ │ Notification│  │
│  │  Service    │ │   Service   │ │   Service   │ │   Engine    │ │  Detection  │ │   Service   │  │
│  │  (Auth)     │ │  (Listings) │ │  (Escrow)   │ │             │ │             │ │             │  │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘  │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐                                                  │
│  │  Location   │ │  Analytics  │ │   Admin     │                                                  │
│  │  Service    │ │  Service    │ │  Service    │                                                  │
│  └─────────────┘ └─────────────┘ └─────────────┘                                                  │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
                                                    │
                                                    ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                              MESSAGE BUS / EVENT STREAM                                           │
│                              Apache Kafka / RabbitMQ / Azure Service Bus                          │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
                                                    │
        ┌───────────────────────────────────────────┼───────────────────────────────────────────┐
        │                                           │                                           │
        ▼                                           ▼                                           ▼
┌───────────────────┐                   ┌───────────────────────┐                   ┌───────────────────┐
│   PRIMARY DB      │                   │   CACHE / SESSION     │                   │   AI / ML STORE   │
│   PostgreSQL      │                   │   Redis Cluster       │                   │   Vector DB       │
│   (Multi-tenant)  │                   │   (Sticky Sessions)   │                   │   (Pinecone/     │
│                   │                   │                       │                   │   pgvector)       │
└───────────────────┘                   └───────────────────────┘                   └───────────────────┘
        │                                           │                                           │
        ▼                                           ▼                                           ▼
┌───────────────────┐                   ┌───────────────────────┐                   ┌───────────────────┐
│   REPLICAS        │                   │   SEARCH              │                   │   BLOB STORAGE    │
│   (Read Replicas) │                   │   Elasticsearch       │                   │   S3 / Blob       │
└───────────────────┘                   └───────────────────────┘                   └───────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                              EXTERNAL INTEGRATIONS                                                │
│  MTN Mobile Money │ Vodafone Cash │ Paystack │ Flutterwave │ Ghana Post │ Google Maps │ SMS/USSD │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Recommended Tech Stack

### Frontend
| Layer | Technology | Rationale |
|-------|------------|-----------|
| **Public Website** | Next.js 14 (App Router), Tailwind CSS | SEO, fast loading, modern UX |
| **Courier Dashboard** | Next.js 14, React Query, Zustand | Real-time job feeds, PWA support |
| **Shipper Dashboard** | Next.js 14, React Query, Zustand | Booking flow, tracking, analytics |
| **Admin Panel** | Next.js 14, TanStack Table, Recharts | Compliance, audit, reporting |
| **Mobile App** | React Native (Expo) or Flutter | Cross-platform, offline support, push notifications |

### Backend
| Layer | Technology | Rationale |
|-------|------------|-----------|
| **API Gateway** | Kong / AWS API Gateway | Rate limiting, auth, versioning |
| **Runtime** | Node.js 20 LTS / .NET 8 | Ecosystem, Ghana dev talent, long-term support |
| **Framework** | NestJS (Node) or ASP.NET Core | Enterprise patterns, DI, testing |
| **API Style** | REST + GraphQL (mobile) | REST for dashboards, GraphQL for mobile efficiency |

### Data & Storage
| Layer | Technology | Rationale |
|-------|------------|-----------|
| **Primary DB** | PostgreSQL 16 | ACID, JSONB, pgvector for embeddings |
| **Cache** | Redis 7 Cluster | Sessions, rate limits, real-time |
| **Search** | Elasticsearch 8 | Full-text, geospatial, analytics |
| **Message Queue** | Apache Kafka / RabbitMQ | Event sourcing, async processing |
| **Object Storage** | AWS S3 / Azure Blob | Documents, photos, proofs |
| **Vector DB** | pgvector / Pinecone | Fraud embeddings, similarity search |

### AI/ML
| Layer | Technology | Rationale |
|-------|------------|-----------|
| **Pricing Engine** | Python, scikit-learn, XGBoost | Demand, distance, fuel, seasonality |
| **Fraud Detection** | Python, TensorFlow/PyTorch, SHAP | Behavioural + transactional signals |
| **Serving** | FastAPI, Triton / ONNX Runtime | Low-latency inference |
| **Feature Store** | Feast / Redis | Centralized feature management |

### Infrastructure
| Layer | Technology | Rationale |
|-------|------------|-----------|
| **Cloud** | AWS (primary) + Ghana data residency options | West Africa proximity, compliance |
| **Containers** | Docker, Kubernetes (EKS/AKS) | Scalability, portability |
| **CI/CD** | GitHub Actions / Azure DevOps | Automated pipelines |
| **Monitoring** | Datadog / New Relic + Grafana | APM, logs, metrics |
| **Secrets** | HashiCorp Vault / AWS Secrets Manager | Secure credential management |

### Payments
| Layer | Technology | Rationale |
|-------|------------|-----------|
| **Mobile Money** | MTN MoMo, Vodafone Cash, AirtelTigo | Ghana market dominance |
| **Card / Bank** | Paystack, Flutterwave | Pan-African coverage |
| **Escrow Logic** | Custom (wallet service) | Release on delivery confirmation |

---

## 3. Database Structure Overview

### Core Schema (PostgreSQL)

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              ORGANIZATION & USERS                                        │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│ organizations          │ users                 │ user_roles          │ role_permissions  │
│ id, name, type,        │ id, org_id, email,    │ user_id, role_id    │ role_id,          │
│ registration_number,   │ phone, password_hash, │ assigned_at         │ resource, action  │
│ address_id, status     │ kyc_status, created   │                     │                   │
└─────────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              FREIGHT & LISTINGS                                          │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│ freight_listings        │ freight_bids          │ freight_trips       │ trip_waypoints    │
│ id, shipper_id,         │ id, listing_id,       │ id, listing_id,     │ id, trip_id,      │
│ pickup_address_id,      │ courier_id, price,    │ courier_id,         │ sequence,         │
│ delivery_address_id,    │ eta, status, expires  │ status, started_at, │ address_id,       │
│ cargo_type, weight_kg,  │                       │ completed_at        │ eta, actual_at    │
│ dimensions, urgency,    │                       │                     │                   │
│ ai_suggested_price,     │                       │                     │                   │
│ status, created         │                       │                     │                   │
└─────────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              WALLET & ESCROW                                             │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│ wallets                 │ transactions          │ escrow_holds        │ payout_schedules  │
│ id, org_id, balance,    │ id, wallet_id,        │ id, trip_id,        │ id, courier_id,   │
│ currency, status        │ type, amount,         │ amount, status,     │ amount, due_date, │
│                         │ reference_type, id,   │ released_at         │ status, paid_at   │
│                         │ metadata, created     │                     │                   │
└─────────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              AI & FRAUD                                                  │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│ ai_pricing_runs         │ fraud_signals         │ fraud_events        │ pricing_model_ver │
│ id, listing_id,         │ id, entity_type,      │ id, event_type,     │ id, version,      │
│ model_version,          │ entity_id, score,     │ entity_id, score,   │ features,         │
│ features_json,          │ signals_json,         │ action_taken,       │ trained_at,       │
│ suggested_price,        │ created               │ created             │ metrics           │
│ confidence, created     │                       │                     │                   │
└─────────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              LOCATION & AUDIT                                            │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│ addresses               │ audit_logs            │ notifications       │ api_keys          │
│ id, country, region,    │ id, entity_type,      │ id, user_id,        │ id, org_id,       │
│ city, street, coords,   │ entity_id, action,    │ channel, payload,   │ key_hash, scopes, │
│ postal_code             │ actor_id, changes,    │ read_at, created    │ expires_at        │
│                         │ created               │                     │                   │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

### Key Indexes
- `freight_listings(status, created_at)` — listing feeds
- `freight_bids(listing_id, status)` — bid lookups
- `transactions(wallet_id, created_at)` — transaction history
- `addresses` — GiST index on `coords` for geospatial queries
- `fraud_signals(entity_type, entity_id, created_at)` — fraud lookups

### Multi-Tenancy
- Row-level security (RLS) on `organizations` as tenant key
- Separate schemas per major tenant for enterprise customers (optional)

---

## 4. API Structure Overview

### Base URL
```
https://api.ghanafreight.com/v1
```

### REST Endpoints (Grouped by Domain)

#### Identity Service
```
POST   /auth/register
POST   /auth/login
POST   /auth/refresh
POST   /auth/logout
POST   /auth/forgot-password
POST   /auth/verify-otp
GET    /users/me
PATCH  /users/me
POST   /users/me/kyc
```

#### Freight Service (Shipper)
```
POST   /listings
GET    /listings
GET    /listings/:id
PATCH  /listings/:id
DELETE /listings/:id
GET    /listings/:id/bids
POST   /listings/:id/accept-bid
GET    /listings/:id/trip
GET    /trips/:id
POST   /trips/:id/confirm-delivery
POST   /trips/:id/dispute
```

#### Freight Service (Courier)
```
GET    /listings/available (filter: origin, destination, date)
GET    /listings/:id
POST   /listings/:id/bids
GET    /my-bids
GET    /my-trips
PATCH  /trips/:id/status
POST   /trips/:id/proof-of-delivery
GET    /trips/:id/navigation
```

#### Wallet Service
```
GET    /wallets/me
GET    /wallets/me/transactions
POST   /wallets/me/deposit (Mobile Money / Card)
POST   /wallets/me/withdraw
GET    /wallets/me/escrow-holds
POST   /wallets/me/transfer (internal)
```

#### AI Pricing (Internal / BFF)
```
POST   /pricing/estimate  (listing payload → suggested price)
GET    /pricing/breakdown (listing_id → feature explanation)
```

#### Admin
```
GET    /admin/users
GET    /admin/organizations
PATCH  /admin/organizations/:id/status
GET    /admin/fraud/flags
POST   /admin/fraud/:event_id/action
GET    /admin/analytics/overview
GET    /admin/analytics/export
GET    /admin/audit-logs
```

### GraphQL (Mobile)
```
# Single endpoint for efficient mobile queries
POST   /graphql

# Key operations
- ShipmentList (paginated, filtered)
- ShipmentDetail (with bids, trip, wallet summary)
- CreateBid
- UpdateTripStatus
- WalletBalance
- Notifications (subscription)
```

### Webhooks (Outbound)
```
- listing.bid_received
- trip.status_changed
- trip.delivery_confirmed
- wallet.payout_completed
- fraud.flag_raised
```

---

## 5. User Roles and Permissions

### Role Hierarchy

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  SYSTEM_ADMIN (Platform Owner)                                                       │
│  • Full platform access                                                              │
│  • Manage regions, pricing models, fraud rules                                       │
│  • Access all tenants                                                                │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                        │
        ┌───────────────────────────────┼───────────────────────────────┐
        ▼                               ▼                               ▼
┌───────────────────┐         ┌───────────────────┐         ┌───────────────────┐
│  ORG_ADMIN        │         │  SHIPPER_ROLE      │         │  COURIER_ROLE     │
│  (Per Tenant)     │         │                    │         │                   │
│  • Manage org     │         │  • Create listings │         │  • View listings  │
│  • Manage users   │         │  • Accept bids     │         │  • Place bids     │
│  • View reports   │         │  • Confirm delivery│         │  • Manage trips   │
│  • Billing        │         │  • Wallet (credit) │         │  • Wallet (debit) │
└───────────────────┘         └───────────────────┘         └───────────────────┘
        │                               │                               │
        ├───────────────────────────────┼───────────────────────────────┤
        ▼                               ▼                               ▼
┌───────────────────┐         ┌───────────────────┐         ┌───────────────────┐
│  SHIPPER_VIEWER   │         │  COURIER_DRIVER   │         │  SUPPORT_AGENT    │
│  • Read-only      │         │  • Limited trip   │         │  • View tickets   │
│  • No financial   │         │    actions        │         │  • No financial   │
└───────────────────┘         └───────────────────┘         └───────────────────┘
```

### Permission Matrix (RBAC)

| Resource | Action | SHIPPER | COURIER | ORG_ADMIN | SYSTEM_ADMIN |
|----------|--------|---------|---------|-----------|--------------|
| listing | create | ✓ | — | ✓ | ✓ |
| listing | read (own) | ✓ | ✓* | ✓ | ✓ |
| listing | read (all) | — | ✓ (public) | — | ✓ |
| bid | create | — | ✓ | — | ✓ |
| bid | accept | ✓ | — | ✓ | ✓ |
| trip | update_status | — | ✓ | ✓ | ✓ |
| trip | confirm_delivery | ✓ | — | ✓ | ✓ |
| wallet | deposit | ✓ | ✓ | ✓ | ✓ |
| wallet | withdraw | ✓ | ✓ | ✓ | ✓ |
| wallet | view_escrow | ✓ | ✓ | ✓ | ✓ |
| admin.users | * | — | — | org only | ✓ |
| admin.fraud | * | — | — | — | ✓ |
| admin.analytics | * | — | — | org | ✓ |

*Couriers see listings filtered by availability and region.

### Additional Controls
- **KYC gates:** Wallet withdrawal, large bids, high-value listings require verified KYC.
- **Rate limits:** Public 100/hr; Authenticated 1000/hr; Partners 10000/hr.
- **IP allowlisting:** Optional for enterprise orgs.

---

## 6. Scaling Strategy for West Africa

### Phase 1: Ghana (Monolith-First)
- Single region: **Accra** (primary) + failover in **Lagos** or **Abuja** if needed.
- Start with modular monolith; extract services as load grows.
- Target: 10K MAU, 1K daily listings.

### Phase 2: Ghana Scale-Out
- Read replicas for PostgreSQL (2–3).
- Redis cluster for session and cache.
- CDN for static assets (Cloudflare PoPs in Lagos, Accra).
- Target: 100K MAU, 10K daily listings.

### Phase 3: West Africa Expansion
- **Multi-region deployment:**
  - Primary: Ghana (Accra)
  - Secondary: Nigeria (Lagos), Senegal (Dakar)
- **Data residency:** Per-country DB replicas where required (e.g. Nigeria).
- **Edge:** API edge nodes in major cities to reduce latency.
- **Mobile Money:** Integrate MoMo per country (MTN, Vodafone, Airtel).

### Phase 4: Hyper-Scale
- Full microservices; Kafka for event streaming.
- Separate AI inference cluster (GPU if needed).
- Elasticsearch cluster for search and analytics.
- Target: 1M+ MAU.

### Infrastructure Resilience
| Concern | Mitigation |
|---------|------------|
| Power | UPS, generator, multi-AZ deployment |
| Connectivity | Multi-ISP, USSD/SMS fallback for critical flows |
| Currency | Per-country wallet currencies (GHS, NGN, XOF) |
| Regulation | Local compliance (GDPR-like, data localization) |
| Cost | Spot/preemptible for non-critical workloads |

### Cost Optimization
- Reserved instances for steady-state compute.
- Object storage lifecycle policies (archive cold data).
- Compress and aggregate logs; retain only compliance-required audit data.
- Use serverless (Lambda/Functions) for sporadic workloads (e.g. webhooks).

---

## 7. Security Considerations

- **Auth:** OAuth2/OIDC, JWT with short expiry, refresh tokens in httpOnly cookies.
- **Secrets:** Vault/Secrets Manager; no secrets in code or config repos.
- **Encryption:** TLS 1.3 in transit; AES-256 at rest for sensitive fields.
- **PCI:** Delegate card handling to Paystack/Flutterwave (no card storage).
- **PII:** Hash/mask in logs; encryption for KYC documents.
- **Audit:** Immutable audit logs for financial and admin actions.

---

## 8. Deliverables Checklist

| Component | Status |
|-----------|--------|
| Public website | To build |
| Courier dashboard | To build |
| Shipper dashboard | To build |
| Admin panel | To build |
| Mobile app | To build |
| AI pricing engine | To build |
| AI fraud detection | To build |
| Wallet & escrow | To build |
| Multi-region scaling | Design complete |

---

*Document prepared for enterprise review. Next: detailed API contracts (OpenAPI), infra-as-code (Terraform), and sprint planning.*
