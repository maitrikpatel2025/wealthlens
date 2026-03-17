# WealthLens

AI-powered portfolio intelligence platform for Canadian investors. Upload brokerage statements, get instant visual dashboards with CFA-level analysis.

## Architecture

```
cokit-test/
├── app/
│   ├── client/          # Next.js 15 frontend (React 19, TypeScript)
│   └── server/          # Python FastAPI backend (LangChain, GPT-4o)
├── design-token/        # Brand color & typography tokens
├── scripts/             # Dev startup/shutdown scripts
├── specs/               # Specifications (placeholder)
└── ai_docs/             # AI documentation (placeholder)
```

## How It Works

1. **Upload** a brokerage statement PDF (RBC, TD, Wealthsimple, Questrade, etc.)
2. **Extract** holdings via GPT-4o multimodal vision + text parsing
3. **Enrich** with live market data from Financial Modeling Prep + yfinance
4. **Dashboard** auto-generates 7-8 widgets (allocations, fees, top holdings, etc.)
5. **Chat** with AI to ask about risk, fees, allocation, income, performance
6. **Export** dashboard to PDF or print

## Tech Stack

| Layer       | Technology                                      |
| ----------- | ----------------------------------------------- |
| Frontend    | Next.js 15, React 19, TailwindCSS 4, Recharts  |
| AI Chat     | CopilotKit, AG-UI Protocol                      |
| Backend     | FastAPI, Uvicorn, LangChain, LangGraph          |
| LLM         | OpenAI GPT-4o (vision + text)                   |
| Market Data | Financial Modeling Prep API, yfinance            |
| Database    | PostgreSQL / SQLite (optional), SQLModel, Alembic|
| PDF Parsing | PyMuPDF, pdfplumber                             |

## Prerequisites

- Node.js 20+ and pnpm
- Python 3.12 and Poetry
- API keys: OpenAI, Financial Modeling Prep (optional: Google, Tavily)

## Quick Start

1. **Clone and configure environment**
   ```bash
   cp .env.sample app/client/.env
   # Edit app/client/.env with your API keys
   # Server .env is symlinked to client .env
   ```

2. **Install dependencies**
   ```bash
   # Frontend
   cd app/client && pnpm install

   # Backend
   cd app/server && poetry install
   ```

3. **Run both servers**
   ```bash
   ./scripts/start.sh
   ```
   - Frontend: http://localhost:3000
   - Backend: http://localhost:8000

4. **Stop servers**
   ```bash
   ./scripts/stop_apps.sh
   ```

## Environment Variables

| Variable         | Required | Description                        |
| ---------------- | -------- | ---------------------------------- |
| `OPENAI_API_KEY` | Yes      | OpenAI API key (GPT-4o)           |
| `GOOGLE_API_KEY` | No       | Google Gemini API key              |
| `TAVILY_API_KEY` | No       | Tavily search API key              |
| `FMP_API_KEY`    | No       | Financial Modeling Prep API key    |
| `DATABASE_URL`   | No       | PostgreSQL/SQLite connection string|
| `CLERK_SECRET_KEY`| No      | Clerk auth secret (optional)       |

## Supported Brokerages

RBC Direct Investing, TD Direct Investing, Wealthsimple, Questrade, BMO InvestorLine, CIBC Investor's Edge, Scotia iTRADE, National Bank, Desjardins, Manulife, Sun Life, Great-West Lifeco, IG Wealth, Edward Jones, CI Direct Investing

## Supported Account Types

RRSP, TFSA, RESP, RRIF, LIRA, RDSP, FHSA, Non-Registered, Corporate

## License

Private
