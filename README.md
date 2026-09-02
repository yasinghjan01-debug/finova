# FINOVA — AI Financial Memory & Revenue Recovery Controller
### *Human-in-the-Loop Financial Automation for Freelancers, Merchants & SMBs*

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com)
[![Next.js 14](https://img.shields.io/badge/Next.js-14.2-black.svg)](https://nextjs.org/)
[![XGBoost](https://img.shields.io/badge/XGBoost-2.1.0-orange.svg)](https://xgboost.readthedocs.io/)
[![Razorpay](https://img.shields.io/badge/Razorpay-Production%20Ready-blue.svg)](https://razorpay.com/docs/)
[![Tamper-Evident Audit](https://img.shields.io/badge/Audit%20Chain-SHA--256%20Cryptographic-green.svg)](#cryptographic-tamper-evident-audit-chain)
[![Tests Passing](https://img.shields.io/badge/Test%20Matrix-32%2F32%20PASSED-brightgreen.svg)](#18-point-verification-test-matrix)

---

## 💡 Core Philosophy
> **"AI investigates, recommends and prepares; human policy authorizes sensitive money movements and external communications."**

Traditional accounting apps either record transactions passively without intelligence, or attempt blind autonomy that risks sending inappropriate collection messages or moving money without authorization. 

**FINOVA** solves this for Indian SMBs and freelancers through **governed financial automation**:
1. **Remembers** every financial relationship, payment proof, and counterparty alias.
2. **Reconciles** bank & UPI settlements against open invoices and informal credits.
3. **Protects** merchants from impersonation scams, urgent transfer spoofing, and rogue VPAs.
4. **Recovers** overdue receivables with compliant escalations and deterministic **stopping rules**.
5. **Proves** every system action with a **tamper-evident SHA-256 cryptographic hash chain**.

---

## 🏛️ End-to-End System Architecture

```
                                 RAZORPAY GATEWAY
                                        │
                 ┌──────────────────────┴──────────────────────┐
                 ↓                                             ↓
         Orders API (POST /orders)              Payment Links API (POST /payment_links)
                 │                                             │
                 └──────────────────────┬──────────────────────┘
                                        ↓
                                     PAYMENT
                                        ↓
                         WEBHOOK INGESTION GATEWAY
                                        │
             ┌──────────────────────────┴──────────────────────────┐
             ↓                                                     ↓
   HMAC-SHA256 Signature                                x-razorpay-event-id
    Validation (P0 Security)                              Idempotency Check
             │                                                     │
             └──────────────────────────┬──────────────────────────┘
                                        ↓
                         WEBHOOK_EVENTS AUDIT STORE
                                        ↓
                             FINANCIAL MEMORY ENGINE
                  (OCR Parser • UTR Extraction • Entity Resolution)
                                        ↓
                         FINANCIAL RELATIONSHIP GRAPH
                   (Ledger Calculations • Trust Scoring • Timelines)
                                        ↓
                             RECONCILIATION ENGINE
                  (Auto-Matching • Partial Settlements • Honest Exceptions)
                                        ↓
                         RECOVERY & OBLIGATION ENGINE
                 (Stage Transitions • Stopping Rules • Razorpay Links)
                                        ↓
                        CRYPTOGRAPHIC AUDIT HASH CHAIN
                (SHA-256 Event Chaining • Mathematical Tamper Evidence)
```

---

## 🧠 5 Core Intelligence Engines

### 1. Payment Memory Engine
- Ingests structured transactions (UPI, Netbanking) and unstructured evidence (payment screenshots, SMS notifications).
- Extracts 12-digit Indian banking UTRs, amounts, dates, and sender metadata.
- Resolves identities across messy contact names, secondary VPAs, and alternative phone numbers.

### 2. Financial Relationship Engine
- Maintains a real-time bilateral ledger for every customer, vendor, and contractor.
- Calculates dynamic **Trust Scores (0–100)** based on repayment history, average delay days, and relationship longevity.

### 3. Reconciliation Engine & Honest Exceptions
- Auto-reconciles inbound payments against outstanding advances and invoices.
- Supports exact matching, partial settlements, and multi-milestone payments.
- Features an **Honest Exceptions Queue**: flags genuine ambiguities (amount mismatches, unassigned credits) for human review rather than forcing false positive matches.

### 4. Scam Shield & ML Impersonation Engine
- Evaluates transfer requests against counterparty historical baselines using XGBoost.
- Detects new originating phone numbers, unknown payment destination VPAs, 7x+ amount spikes, and coercive urgency cues.
- Provides explainable risk breakdowns with distinct **P(fraud)** and **Policy Action Levels**.

### 5. Revenue Recovery Controller & Stopping Rules
- Automated receivable aging with polite stage progression:
  - **Day 1**: Gentle due nudge
  - **Day 3**: Reminder notice
  - **Day 7**: Official Razorpay Payment Link dispatch
  - **Day 14+**: Manual administrative escalation
- **Strict Stopping Rules (Buildathon Compliance)**:
  - Automatically halts all reminders immediately upon payment capture (`payment_link.paid` webhook).
  - Immediately halts if counterparty disputes or merchant triggers `POST /recovery/stop`.
  - Compulsorily stops automated nudges if 3 attempts are reached without response.

---

## 🔬 Rigorous Machine Learning Benchmark (Held-Out Test Split)

Evaluated on **50,000 synthetic Indian fintech records** with natural edge cases, class imbalance (8% fraud prevalence), and realistic noise. Evaluated on a strict **70% Train (35,000) / 15% Validation (7,500) / 15% Held-Out Test (7,500)** split.

| Model Architecture | Precision | Recall | F1 Score | ROC-AUC | False Positives | False Positive Rate | Est. Friction Cost (₹150/FP) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Logistic Regression (Baseline)** | 78.30% | 99.83% | 87.77% | 0.9984 | 166 / 7,500 | 2.41% | ₹24,900 |
| **Random Forest Classifier** | 98.85% | 100.00% | 99.42% | 1.0000 | 7 / 7,500 | 0.10% | ₹1,050 |
| **XGBoost (FINOVA Production)** | **99.67%** | **100.00%** | **99.83%** | **1.0000** | **2 / 7,500** | **0.03%** | **₹300** |

> **Transparent Artifacts**: Complete CSV datasets (`train.csv`, `val.csv`, `test.csv`, `feature_schema.json`), serialised model (`risk_model.joblib`), and classification metrics (`metrics.json`) are committed in `apps/api/ml/`.

---

## 🛡️ Cryptographic Tamper-Evident Audit Chain

Every state transition in FINOVA is immutably recorded in an **append-only SHA-256 cryptographic hash chain**:
$$\text{Hash}_n = \text{SHA256}(\text{Seq}_n \parallel \text{Hash}_{n-1} \parallel \text{EventType} \parallel \text{Actor} \parallel \text{Timestamp} \parallel \text{Payload})$$

- **Genesis Block**: Sequence #1 anchors to 64 zero-bytes.
- **Mathematical Verification**: Calling `GET /api/v1/audit/verify` walks the entire chain from block #1 to present. Any manual alteration of database rows immediately breaks the chain and flags tamper detection with the exact sequence number!

---

## 🧪 18-Point Verification Test Matrix

All 18 critical fintech requirements pass in the automated test suite:

| Test # | Test Scenario | Verification Target | Status |
| :---: | :--- | :--- | :---: |
| **TEST 01** | Create Razorpay order | `POST /api/v1/razorpay/orders` creates standard order | ✅ **PASSED** |
| **TEST 02** | Payment captured webhook | Webhook ingested and signature verified | ✅ **PASSED** |
| **TEST 03** | Invalid webhook signature rejected | Tampered HMAC signature returns HTTP 400 | ✅ **PASSED** |
| **TEST 04** | Duplicate webhook ignored | `x-razorpay-event-id` idempotency deduplication | ✅ **PASSED** |
| **TEST 05** | Out-of-order webhook handled | Payment captured before local order sync | ✅ **PASSED** |
| **TEST 06** | Payment reconciled | Inbound payment matched to open obligation | ✅ **PASSED** |
| **TEST 07** | Partial payment calculated | Remaining amount properly decremented | ✅ **PASSED** |
| **TEST 08** | Screenshot OCR | Extracts amount, sender, UTR from payment text | ✅ **PASSED** |
| **TEST 09** | UTR extracted | 12-digit Indian banking RRN/UTR normalized | ✅ **PASSED** |
| **TEST 10** | Fraud model prediction | XGBoost predicts anomalous transfer risk | ✅ **PASSED** |
| **TEST 11** | Held-out evaluation | Honest metrics benchmark with false positive cost | ✅ **PASSED** |
| **TEST 12** | High-risk action requires approval | High-risk transfers blocked from autonomous execution | ✅ **PASSED** |
| **TEST 13** | Recovery stopping rule | Recovery halted upon dispute or explicit stop | ✅ **PASSED** |
| **TEST 14** | Payment Link created | Razorpay Payment Link generated with reference ID | ✅ **PASSED** |
| **TEST 15** | Payment Link paid webhook | `payment_link.paid` triggers obligation settlement | ✅ **PASSED** |
| **TEST 16** | Recovery balance updated | Relationship ledger updated to ₹0 | ✅ **PASSED** |
| **TEST 17** | Audit hash verified | SHA-256 chain integrity verified mathematically | ✅ **PASSED** |
| **TEST 18** | Unauthorized user access rejected | Invalid/forged JWT tokens return HTTP 401 | ✅ **PASSED** |

---

## 🚀 Quickstart & Reproduction

### 1. Run Automated Tests (32/32 Passing)
```bash
python -m pytest apps/api/tests -v
```

### 2. Retrain ML Model & Regenerate Datasets
```bash
python -m apps.api.ml.train_models
```

### 3. Run Backend (FastAPI)
```bash
uvicorn apps.api.main:app --host 127.0.0.1 --port 8000 --reload
# Interactive Swagger Documentation: http://127.0.0.1:8000/docs
```

### 4. Run Frontend (Next.js 14)
```bash
cd apps/web
npm install
npm run dev
# Dashboard: http://localhost:3000
```

### 5. Production Docker Compose
```bash
docker-compose up --build
```

---

## 📦 Deployment (Vercel & Netlify)

- **Vercel**: Deploy directory `apps/web`. Uses built-in Next.js Serverless Edge Handlers (`/api/v1/[...slug]`).
- **Netlify**: Connect GitHub repository, Base directory: `apps/web`, Build command: `npm run build`.
- See [`DEPLOYMENT.md`](DEPLOYMENT.md) for full guide.
