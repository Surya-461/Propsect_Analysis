# Project Summary: Insurance Prospect IQ Platform

## 📋 Project Overview

**Insurance Prospect IQ Platform** — A B2B SaaS application that helps insurance underwriters rapidly analyze prospect companies using AI-powered intelligence. The system aggregates data from multiple sources (news, financial reports, regulatory filings, industry data) and synthesizes insights using Google Gemini AI to produce comprehensive underwriting-grade reports.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  FRONTEND (React 19 + Vite)                  │
│   SearchForm → ProgressTracker → ReportView → HistoryModal   │
│        (Displays & Exports: Markdown/PDF/Print)              │
└─────────────┬───────────────────────────────────────────────┘
              │ HTTP/REST (Axios)
              │ port 5173 ↔ port 8000
┌─────────────▼───────────────────────────────────────────────┐
│                  BACKEND (FastAPI/Python)                    │
│   Routes: /analyze, /chat, /analyses, /health               │
└─────────────┬───────────────────────────────────────────────┘
              │
      ┌───────┴──────────────────────────┐
      │                                  │
   ┌──▼──────────────┐          ┌───────▼──────┐
   │ Research Engine │          │ AI Integration│
   │                 │          │  (Gemini API) │
   │ • Google News   │          │               │
   │ • Wikipedia     │          │ • Rate limiting
   │ • Finance data  │          │ • Fallbacks   │
   │ • Regulatory    │          │ • Multi-model │
   │ • Industry      │          │               │
   └────────┬────────┘          └───────┬───────┘
            │                           │
            └───────────┬───────────────┘
                        ▼
         ┌──────────────────────────────┐
         │   Data Synthesis & Analysis  │
         │   (Summarizer Module)        │
         │                              │
         │   Evidence → Gemini Summary  │
         └────────────┬─────────────────┘
                      ▼
         ┌──────────────────────────────┐
         │   PostgreSQL Database        │
         │   • Analysis history         │
         │   • Report data (JSON)       │
         │   • Executive summaries      │
         └──────────────────────────────┘
```

---

## 🎯 How It Works (Main Workflow)

### **1. User Initiates Analysis**
- User enters company name in frontend SearchForm
- Frontend sends: `POST /api/analyze {prospect_name, extra_parameters}`

### **2. Multi-Source Research Collection**
Backend orchestrator collects intelligence from 6 independent sources:
- **Google News**: Recent company mentions & press coverage
- **Wikipedia**: Knowledge graph & company information
- **Financial Data**: Investor reports & financial metrics
- **Industry Press**: Sector-specific news & insights
- **Regulatory Filings**: SEC filings & compliance documents
- **Annual Reports**: Official company reports & disclosures

### **3. Data Processing**
- Deduplicates evidence by URL
- Filters out competitor articles (strict entity matching)
- Organizes findings by 6 research parameters:
  - Company Scale
  - Business Growth
  - Market Position
  - Financial Strength
  - Insurance Performance
  - [Custom parameters]

### **4. AI Synthesis (Single Gemini Call)**
- Aggregates all evidence into compact JSON
- Sends **ONE** Gemini API call with all parameters
- If rate-limited → fallback to rule-based synthesis
- Generates executive summary & parameter-specific insights

### **5. Display & Storage**
- Returns comprehensive report to frontend
- Stores in PostgreSQL for history/audit trail
- Frontend displays:
  - Executive summary
  - Individual parameter cards
  - Source citations
  - Export options (Markdown, PDF, Print)

### **6. Historical Access**
- Users view saved analyses in History modal
- Load previous reports or delete outdated analyses

---

## 🔌 Backend Components

| Component | File | Purpose |
|-----------|------|---------|
| **API Endpoints** | `api/routes.py` | 5 REST endpoints for analysis, chat, history |
| **Research Orchestrator** | `research/orchestrator.py` | Coordinates multi-source research gathering |
| **Source Manager** | `research/source_manager.py` | Aggregates 6 evidence collectors |
| **Evidence Collectors** | `research/collectors/*.py` | Google News, Wikipedia, Finance, Industry, Regulatory, Reports |
| **AI Integration** | `ai/gemini.py` | Thread-safe Gemini API with rate limiting & fallback |
| **Analysis** | `analysis/summarizer.py` | Synthesizes evidence into parameter reports |
| **Data Models** | `models/*.py` | Request/response structures & database models |
| **Database** | `database.py` | PostgreSQL connection & ORM setup |
| **Configuration** | `config/research_parameters.py` | Research parameter definitions & search queries |

---

## 🎨 Frontend Components

| Component | File | Purpose |
|-----------|------|---------|
| **Main App** | `App.jsx` | State management, routing, UI orchestration |
| **Search Form** | `SearchForm.jsx` | Company name input & submission |
| **Progress Tracker** | `ProgressTracker.jsx` | Real-time progress updates during analysis |
| **Report View** | `ReportView.jsx` | Report display with export/print options |
| **History Modal** | `HistoryModal.jsx` | View, load, delete saved analyses |
| **Header/Footer** | `Header.jsx`, `Footer.jsx` | Navigation & branding |

---

## 💾 Technology Stack

### Backend
- **Framework**: FastAPI (Python)
- **Database**: PostgreSQL + SQLAlchemy ORM
- **AI**: Google Gemini API (Configurable via `GEMINI_MODEL`, e.g., `gemini-flash-lite-latest`, with fallbacks)
- **External APIs**: Tavily (optional), OpenAI (optional)
- **Server**: Uvicorn (port 8000)

### Frontend
- **Framework**: React 19.2.8
- **Build Tool**: Vite 8.2.0
- **HTTP Client**: Axios 1.19.0
- **Icons**: Lucide React 1.31.0
- **Dev Server**: Vite (port 5173)

### Infrastructure
- **Database**: PostgreSQL (localhost:5432)
- **Environment**: Python dotenv for secrets
- **API Key**: `GEMINI_API_KEY` in `.env`

---

## 🔐 Key Design Patterns

| Pattern | Benefit |
|---------|---------|
| **Single AI Request** | Minimizes Gemini API calls & cost |
| **Graceful Degradation** | Falls back to synthesis if AI unavailable |
| **Thread-Safe Rate Limiting** | Prevents API 429 (rate limit) errors |
| **Strict Entity Filtering** | Avoids competitor/irrelevant data |
| **Multi-Source Aggregation** | Comprehensive, unbiased research |
| **RESTful History** | Full audit trail in PostgreSQL |

---

## 📊 Data Flow Diagram

```
┌─ USER SEARCHES COMPANY ──┐
│                          │
└──────────┬───────────────┘
           │ React SearchForm
           ▼
    POST /api/analyze
           │
    ┌──────▼───────────┐
    │ 6 Data Collectors│
    │  (Parallel Fetch) │
    └──────┬───────────┘
           │
    ┌──────▼─────────────────────┐
    │ Deduplicate & Filter       │
    │ (by URL, entity matching)  │
    └──────┬─────────────────────┘
           │
    ┌──────▼──────────────────┐
    │ Compact JSON Evidence   │
    │ (Max 2 sources/param)   │
    └──────┬─────────────────┘
           │
    ┌──────▼──────────────────┐
    │ SINGLE Gemini Call      │
    │ (or fallback synthesis) │
    └──────┬──────────────────┘
           │
    ┌──────▼──────────────────┐
    │ Save to PostgreSQL      │
    │ (analyses table)        │
    └──────┬──────────────────┘
           │
    ┌──────▼──────────────────┐
    │ Return to Frontend      │
    │ (Display ReportView)    │
    └──────────────────────────┘
```

---

## ⚡ Quick Start (Running the App)

### **Backend**
```bash
cd backend
pip install -r requirements.txt
export GEMINI_API_KEY="your-api-key"
uvicorn main:app --reload
# Runs on http://localhost:8000
```

### **Frontend**
```bash
cd frontend
npm install
npm run dev
# Runs on http://localhost:5173
```

### **Database**
Ensure PostgreSQL is running on `localhost:5432` with credentials configured in `.env`

---

## ✅ Strengths

- ✨ Clean separation of concerns (research → analysis → synthesis)
- 🔄 Graceful fallback mechanisms for API failures
- 🧵 Thread-safe API rate limiting
- 📊 Rich export options (Markdown, PDF, Print)
- 🔍 Strict filtering to avoid competitor data
- 📝 Full audit trail in database

---

## ⚠️ Considerations

- 🔌 Dependent on Gemini API availability
- 🔐 No authentication visible (consider adding auth layer)
- 🏊 Monitor PostgreSQL connection pool usage
- 🎯 Entity filtering may miss valid subsidiaries/related entities

---

## 📞 Support & Contact

For issues or questions, review the relevant component files or API documentation in FastAPI Swagger UI at `http://localhost:8000/docs`

