# 📄 pactParser: AI-Powered Contract Intelligence System

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green)
![MongoDB](https://img.shields.io/badge/MongoDB-Latest-brightgreen)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red)
![Docker](https://img.shields.io/badge/Docker-Ready-blue)

**An intelligent, scalable system for automated contract parsing and business intelligence extraction**

[Features](#-features) • [Architecture](#-architecture) • [Getting Started](#-getting-started) • [API Documentation](#-api-documentation) • [Tech Stack](#-tech-stack)

</div>

---

## 🎯 Problem Statement

Modern businesses in AR/SaaS platforms handle hundreds of contracts with varying formats, terms, and structures. Manual review is a critical bottleneck—it's time-consuming, expensive, and error-prone, leading to:

- 💸 Missed revenue opportunities
- ⏰ Payment delays and cash flow issues
- ⚠️ Compliance and legal risks
- 📊 Poor business intelligence visibility

**pactParser** solves this by providing an automated, AI-powered system that ingests contracts and delivers immediate, actionable intelligence with confidence scoring and gap analysis.

---

## ✨ Features

### Core Capabilities

- **🚀 Asynchronous Processing**: Non-blocking upload and background processing using Celery + Redis
- **🤖 LLM-Powered Extraction**: Leverages Groq's LLaMA-3.3-70B for intelligent data parsing
- **📊 Weighted Scoring Algorithm**: Industry-standard 0-100 confidence scoring with gap analysis
- **⚡ Real-time Status Tracking**: Live progress monitoring with WebSocket-style polling
- **🗄️ Robust Data Storage**: MongoDB-based persistence with optimized indexing
- **🐳 Fully Dockerized**: One-command deployment with docker-compose
- **📱 Interactive UI**: Real-time dashboard with contract management and detailed views

### Data Extraction

pactParser extracts critical business intelligence including:

- **Party Identification**: Legal entities, signatories, and roles
- **Financial Details**: Line items, totals, currencies, and tax information
- **Payment Structure**: Terms, schedules, methods, and banking details
- **Revenue Classification**: Recurring vs. one-time, billing cycles, renewal terms
- **Service Level Agreements**: Metrics, penalties, and support terms
- **Account Information**: Billing and technical contacts

---

## 🏗️ Architecture

### System Design

```
┌─────────────┐
│   Browser   │
│  (User UI)  │
└──────┬──────┘
       │ HTTP
       ▼
┌─────────────────────┐
│  Streamlit Frontend │◄────────┐
│   (Port 8501)       │         │
└──────┬──────────────┘         │
       │ REST API               │
       ▼                        │
┌─────────────────────┐         │
│   FastAPI Backend   │         │ Real-time
│   (Port 8000)       │         │ Polling
└──┬────────────────┬─┘         │
   │                │           │
   │ Write          │ Dispatch  │
   ▼                ▼           │
┌──────────┐    ┌──────────┐   │
│ MongoDB  │    │  Redis   │   │
│ Database │    │  Queue   │   │
└──────────┘    └─────┬────┘   │
                      │         │
                      ▼         │
              ┌─────────────┐  │
              │   Celery    │  │
              │   Worker    │  │
              └──────┬──────┘  │
                     │         │
                     ▼         │
              ┌─────────────┐  │
              │   Groq LLM  │  │
              │   API       │  │
              └──────┬──────┘  │
                     │         │
              Score & Parse    │
                     │         │
                     ▼         │
              Update MongoDB───┘
```

### Data Flow Pipeline

1. **Upload**: User uploads PDF → FastAPI saves file + creates DB record
2. **Queue**: FastAPI dispatches async task to Celery via Redis
3. **Process**: Celery worker executes 4-stage pipeline:
   - 📄 Extract text from PDF (30%)
   - 🤖 Parse with LLM (70%)
   - 📊 Score and analyze gaps (90%)
   - ✅ Save results to MongoDB (100%)
4. **Monitor**: Frontend polls status endpoint for real-time updates
5. **View**: User accesses extracted data and analytics

---

## 🚀 Getting Started

### Prerequisites

- **Docker & Docker Compose** (required for containerized deployment)
- **Groq API Key** ([Get one free here](https://console.groq.com))

### Quick Start (Recommended)

**1. Clone the repository**

```bash
git clone https://github.com/gupta-v/pactParser
cd pactParser
```

**2. Create environment file**

```bash
touch backend/.env
```

**3. Add your Groq API key**
Open `backend/.env` and add:

```env
GROQ_API_KEY=gsk_your_api_key_here
```

**4. Launch the application**

```bash
docker-compose up --build
```

That's it! The entire stack will start automatically.

### Access Points

- **Frontend UI**: http://localhost:8501
- **Backend API**: http://localhost:8000
- **API Docs (Swagger)**: http://localhost:8000/docs
- **API Docs (ReDoc)**: http://localhost:8000/redoc

---

## 💻 Local Development Setup

For development without Docker:

### Prerequisites

- Python 3.11+
- MongoDB running on `localhost:27017`
- Redis running on `localhost:6379`

### Setup Steps

**1. Install dependencies**

```bash
pip install -r requirements.txt
```

**2. Configure environment**
Create `backend/.env`:

```env
GROQ_API_KEY=gsk_your_api_key_here
MONGO_CONNECTION_STRING=mongodb://localhost:27017
REDIS_CONNECTION_STRING=redis://localhost:6379/0
```

**3. Start services** (in separate terminals)

Terminal 1 - Backend API:

```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Terminal 2 - Celery Worker:

```bash
cd backend
celery -A app.celery_app.celery_app worker --loglevel=info -P eventlet
```

Terminal 3 - Frontend:

```bash
cd frontend
streamlit run streamlit-app.py
```

---

## 📚 API Documentation

### Endpoints Overview

| Method | Endpoint                   | Description                    |
| ------ | -------------------------- | ------------------------------ |
| `POST` | `/contracts/upload`        | Upload new contract (PDF)      |
| `GET`  | `/contracts/{id}/status`   | Poll processing status         |
| `GET`  | `/contracts/{id}`          | Get extracted contract data    |
| `GET`  | `/contracts`               | List all contracts (paginated) |
| `GET`  | `/contracts/{id}/download` | Download original PDF          |

### Example Usage

**Upload a Contract**

```bash
curl -X POST "http://localhost:8000/contracts/upload" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@contract.pdf"
```

Response:

```json
{
  "contract_id": "a1b2c3d4-5678-90ab-cdef-1234567890ab",
  "filename": "contract.pdf",
  "status": "pending"
}
```

**Check Status**

```bash
curl "http://localhost:8000/contracts/{contract_id}/status"
```

Response:

```json
{
  "contract_id": "a1b2c3d4-5678-90ab-cdef-1234567890ab",
  "status": "processing",
  "progress_percentage": 70,
  "error_message": null
}
```

**Get Extracted Data**

```bash
curl "http://localhost:8000/contracts/{contract_id}"
```

For full interactive documentation, visit: http://localhost:8000/docs

---

## 📊 Scoring Algorithm

pactParser implements a weighted scoring system (0-100 points):

| Category                   | Weight | Criteria                          |
| -------------------------- | ------ | --------------------------------- |
| **Financial Completeness** | 30 pts | Total value, MRR, line items      |
| **Party Identification**   | 25 pts | Legal names, roles, signatories   |
| **Payment Terms Clarity**  | 20 pts | Terms, schedules, methods         |
| **SLA Definition**         | 15 pts | Metrics, penalties, support terms |
| **Contact Information**    | 10 pts | Billing and technical contacts    |

### Gap Analysis

The system automatically identifies missing critical fields and provides actionable feedback:

```json
{
  "confidence_score": 75,
  "gap_analysis": [
    "Missing detailed line items",
    "SLA section found, but no specific metrics or penalties defined"
  ]
}
```

---

## 🛠️ Tech Stack

### Backend

- **FastAPI**: Modern, async Python web framework
- **Celery**: Distributed task queue for async processing
- **Redis**: Message broker and result backend
- **MongoDB**: Document database for flexible schema
- **LangChain**: LLM orchestration framework
- **Groq**: High-performance LLM inference (LLaMA-3.3-70B)
- **PyPDF**: PDF text extraction
- **Pydantic**: Data validation and schema generation

### Frontend

- **Streamlit**: Rapid Python-based web UI framework
- **Pandas**: Data manipulation and display

### Infrastructure

- **Docker & Docker Compose**: Containerization and orchestration
- **Eventlet**: Async I/O for Celery workers

---

## 📁 Project Structure

```
PACTPARSER/
├── backend/
│   ├── app/
│   │   ├── __pycache__/         # Python bytecode cache
│   │   ├── main.py              # FastAPI REST API server
│   │   ├── celery_app.py        # Celery configuration & initialization
│   │   ├── celery_worker.py     # Background task processing logic
│   │   ├── database.py          # MongoDB connection & async helpers
│   │   ├── models.py            # Pydantic data models & schemas
│   │   ├── llm_parser.py        # LLM extraction with LangChain
│   │   └── scoring.py           # Weighted scoring & gap analysis
│   ├── uploads/                 # Storage for uploaded PDF files
│   ├── .env                     # Environment variables (API keys)
│   └── .envexample              # Example environment configuration
│
├── frontend/
│   └── streamlit-app.py         # Streamlit web UI with real-time polling
│
├── samples/                     # Test contract PDFs
│   ├── sample_contract.pdf      # Standard test contract
│   ├── test_contract_missing_parties.pdf
│   ├── test_contract_missing_sla.pdf
│   ├── test_contract_missing_termination...pdf
│   └── test_contract_vague_financials.pdf
│
├── .gitignore                   # Git ignore rules
├── .dockerignore                # Docker ignore rules
├── backend.Dockerfile           # Backend container definition
├── docker-compose.yml           # Multi-container orchestration
├── frontend.Dockerfile          # Frontend container definition
├── README.md                    # Project documentation
└── requirements.txt             # Python dependencies (global)
```

### Key Directories Explained

- **`backend/app/`**: Core application logic with clear separation of concerns
- **`backend/uploads/`**: Persistent storage for uploaded contracts (mounted as Docker volume)
- **`frontend/`**: Lightweight Streamlit UI (can be replaced with React)
- **`samples/`**: Edge-case test contracts for validation and demo purposes

---

## 🎨 UI Walkthrough

### 1. Upload Contract

Drag and drop a PDF contract in the sidebar. Upload is instant with immediate confirmation.

### 2. Real-time Processing

Watch live progress as the system:

- Extracts text (30%)
- Parses with AI (70%)
- Scores and analyzes (90%)
- Completes (100%)

### 3. View Results

Click "Details" to see:

- **Summary Tab**: Revenue classification, payment structure
- **Gap Analysis Tab**: Missing fields and recommendations
- **Financial Tab**: Line items, totals, currency
- **Parties Tab**: Legal entities and contacts
- **SLA Tab**: Service level commitments
- **Raw JSON Tab**: Complete extracted data

### 4. Download Original

One-click download of the original PDF for reference.

---

## 🔧 Configuration

### Environment Variables

**Required:**

- `GROQ_API_KEY`: Your Groq API key

**Optional (auto-configured in Docker):**

- `MONGO_CONNECTION_STRING`: MongoDB connection URL
- `REDIS_CONNECTION_STRING`: Redis connection URL
- `API_BASE_URL`: Backend API URL (for frontend)

---

## 🚦 Performance & Scalability

### Current Capabilities

- **File Size**: Handles contracts up to 50MB
- **Concurrent Processing**: Multiple contracts processed simultaneously
- **Throughput**: ~2-5 contracts per minute (depending on LLM API limits)

### Horizontal Scaling

Scale Celery workers independently:

```bash
docker-compose up --scale backend-worker=5
```

This allows processing 5 contracts in parallel without affecting API responsiveness.

---

## 🎯 Design Decisions

### Why Streamlit Instead of React?

For this MVP, **Streamlit was a strategic choice**:

✅ **Rapid Development**: Built a fully functional UI in hours vs. days  
✅ **Python-Native**: Seamless integration with backend logic and data structures  
✅ **Feature-Rich**: Real-time polling, interactive dialogs, data visualization out-of-the-box  
✅ **Validation Focus**: Proves the entire data pipeline and business logic work flawlessly

The architecture is **frontend-agnostic**. The REST API can easily support a React/Next.js frontend when production-ready branding and UX customization are needed.

### Why Celery + Redis?

- **Non-blocking**: API remains responsive during heavy processing
- **Reliable**: Redis persistence ensures no task loss
- **Scalable**: Add workers without touching API code
- **Observable**: Built-in monitoring and logging

---

## 🔮 Future Enhancements

### Planned Features

- [ ] **React Frontend**: Production-ready UI with custom branding
- [ ] **Map-Reduce Parsing**: Handle contracts > 50MB by chunking
- [ ] **LangSmith Integration**: LLM call tracing and debugging
- [ ] **User Authentication**: OAuth2 with role-based access
- [ ] **Webhook Notifications**: Real-time alerts on completion
- [ ] **Batch Upload**: Process multiple contracts at once
- [ ] **Export to Excel**: Structured data export functionality
- [ ] **Unit Tests**: 60%+ coverage with pytest

### Advanced AI Features

- [ ] **Agentic Parsing**: Multi-step reasoning for complex contracts
- [ ] **Custom Fine-tuning**: Domain-specific model optimization
- [ ] **Clause Comparison**: Detect deviations from standard terms
- [ ] **Risk Scoring**: Identify potentially unfavorable clauses

---

## 🐛 Troubleshooting

### Common Issues

**"Connection Error: Cannot connect to backend API"**

- Ensure all Docker containers are running: `docker-compose ps`
- Check backend logs: `docker-compose logs backend-api`

**"Failed to connect to MongoDB"**

- MongoDB container may not be ready. Wait 10 seconds and refresh.
- Check MongoDB logs: `docker-compose logs mongo`

**"LLM parsing failed"**

- Verify `GROQ_API_KEY` is set correctly in `backend/.env`
- Check API quota: https://console.groq.com

**"File upload fails"**

- Ensure file is a valid PDF
- Check file size < 50MB
- Verify `uploads/` directory exists with write permissions

### Reset Everything

```bash
docker-compose down -v
docker-compose up --build
```

---

## 📝 Testing

### Manual Testing Checklist

- [ ] Upload a valid PDF contract
- [ ] Verify real-time status updates
- [ ] Check extracted data completeness
- [ ] Download original file
- [ ] Test with malformed PDF
- [ ] Test with non-PDF file
- [ ] Test concurrent uploads

### Sample Contracts

Test with various contract types:

- SaaS subscription agreements
- Professional services contracts
- License agreements
- Master service agreements (MSAs)

---

## 🤝 Contributing

This is a technical assignment project. For production use:

1. Fork the repository
2. Create a feature branch
3. Implement changes with tests
4. Submit a pull request

---

## 📄 License

This project was created as a technical assignment demonstration.

---

## 👨‍💻 Author

Built with ⚡ using Python, FastAPI, Celery, and Groq LLM

**Tech Stack Philosophy**: Python-first development using modern frameworks (FastAPI, Streamlit) for rapid, maintainable solutions.

---

## 🙏 Acknowledgments

- **Groq** for lightning-fast LLM inference
- **LangChain** for LLM orchestration patterns
- **FastAPI** for modern Python web development
- **Streamlit** for rapid UI prototyping

---

<div align="center">

**Built for the Contract Intelligence Parser Technical Assignment**

Made with ❤️ and ☕

</div>
