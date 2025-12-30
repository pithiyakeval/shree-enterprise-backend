🚀 Shree Enterprise Backend

Production-ready backend service for the Shree Enterprise platform, built with FastAPI and designed for scalable deployment on Render / Railway.

This backend powers:

Lead capture & management

Admin APIs

AI chatbot APIs

Health monitoring

Secure production configuration

🧱 Tech Stack

Backend Framework: FastAPI (Python)

Database: PostgreSQL

ORM: SQLAlchemy + Alembic

Server: Uvicorn

Containerization: Docker (local & testing)

Deployment: Render

Version Control: Git + GitHub

📁 Project Structure
shree-enterprise-backend/
├── backend/
│   ├── app/
│   │   ├── ai/              # AI / chatbot logic
│   │   ├── routers/         # API routes (lead, admin, chat)
│   │   ├── middleware/      # Custom middlewares
│   │   ├── config.py        # Environment configuration
│   │   ├── database.py      # DB connection
│   │   └── main.py          # FastAPI entry point
│   └── alembic/             # Database migrations
│
├── requirements.txt         # Python dependencies
├── .gitignore               # Ignored files
└── README.md                # Project documentation

⚙️ Environment Variables

The backend is fully environment-driven.
All sensitive values are injected at runtime (not committed to GitHub).

Required Variables
ENVIRONMENT=production
DATABASE_URL=postgresql://user:password@host:5432/dbname
FRONTEND_URL=https://shreeenterprise.live
ENABLE_DOCS=false


ℹ️ These variables are configured directly in the Render Dashboard.

▶️ Running Locally (Without Docker)
1️⃣ Create virtual environment
python -m venv .venv
source .venv/bin/activate

2️⃣ Install dependencies
pip install -r requirements.txt

3️⃣ Start the server
uvicorn backend.app.main:app --reload


Backend will be available at:

http://localhost:8000

🐳 Running with Docker (Production-Style)

Used for local production testing (not required on Render).

docker compose up --build

🔍 API Health Check
GET /api/health

Example response:
{
  "status": "ok",
  "environment": "production"
}

🤖 AI Chatbot API
POST /api/chat
Content-Type: application/json

{
  "message": "Hello"
}

🛡️ Production Features

✅ Centralized error handling

✅ Environment-based configuration

✅ Clean API routing (/api/*)

✅ CORS protection

✅ Health monitoring endpoint

✅ Production-safe logging

✅ Secrets never committed to GitHub

🚀 Deployment (Render)
Deployment Overview

Source: GitHub

Runtime: Python

Build Command:

pip install -r requirements.txt


Start Command:

uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT


Render automatically injects the $PORT variable.

🔐 Security Notes

.env files are never committed

Database credentials stored securely in Render

AI models and infra configs excluded from GitHub

Backend port is not publicly exposed (handled by platform proxy)

📌 Author

Keval Ahir
Backend & Full-Stack Developer
Focused on production-grade APIs, scalable systems, and clean architecture.

📄 License