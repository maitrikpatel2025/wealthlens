# WealthLens Server

Python FastAPI backend powering the WealthLens portfolio intelligence platform.

## Tech Stack

- **Framework**: FastAPI 0.115 + Uvicorn 0.35
- **Agent**: LangChain 0.3.26, LangGraph, CopilotKit 0.1.52
- **LLM**: OpenAI GPT-4o (via langchain-openai), Google Gemini (via langchain-gemini)
- **Market Data**: Financial Modeling Prep API (httpx), yfinance
- **PDF Parsing**: PyMuPDF (multimodal image extraction), pdfplumber (text extraction)
- **Database**: SQLModel + Alembic (PostgreSQL via asyncpg, SQLite via aiosqlite)
- **Other**: Pandas, Tavily (search), Redis (caching), boto3, PyJWT

## Project Structure

```
server/
├── main.py                         # FastAPI app, endpoints, SSE streaming
├── pyproject.toml                  # Dependencies (Poetry)
├── core/
│   ├── agent.py                    # LangGraph agent (planner → router → execute/respond)
│   ├── data_models.py              # Pydantic/TypedDict models (state, holdings, widgets)
│   ├── prompts.py                  # CFA-caliber system prompt + tool mapping
│   ├── constants.py                # Config constants (upload limits, etc.)
│   ├── institution_patterns.py     # Regex patterns for 15+ Canadian brokerages
│   ├── cache.py                    # Caching layer
│   ├── storage.py                  # Storage abstraction
│   ├── widget_tools.py             # Widget add/update/remove utilities
│   ├── sub_agents/
│   │   ├── extraction_agent.py     # PDF → structured holdings (GPT-4o vision)
│   │   ├── enrichment_agent.py     # Holdings → live market data (FMP + yfinance)
│   │   └── analytics_agent.py      # Analytics sub-agent (stub)
│   ├── tools/
│   │   ├── compute_allocation.py   # Asset class/sector/geographic/cap allocation
│   │   ├── compute_fees.py         # MER analysis, fee drag, alternatives
│   │   ├── portfolio_risk.py       # Beta, concentration, risk flags, scoring
│   │   ├── income_analysis.py      # Dividend yield, income by type, tax notes
│   │   ├── compare_performance.py  # Benchmark comparison (XIU, VFV, VGRO, etc.)
│   │   ├── rank_insights.py        # AI-ranked portfolio insights
│   │   ├── detect_concentration.py # Concentration threshold detection
│   │   ├── detect_overlap.py       # Cross-account overlap detection
│   │   ├── auto_dashboard.py       # Starter 7-8 widget dashboard generation
│   │   └── widget_tools.py         # Manual widget CRUD
│   └── db/
│       ├── connection.py           # Async DB session management
│       ├── models.py               # SQLModel ORM models
│       └── migrations/             # Alembic migrations
└── tests/
    ├── core/
    │   ├── test_agent.py
    │   ├── test_data_models.py
    │   └── test_prompts.py
    ├── sub_agents/
    │   └── test_extraction_agent.py
    └── tools/
        ├── test_compute_allocation.py
        ├── test_compute_fees.py
        └── test_widget_tools.py
```

## API Endpoints

### POST `/wealthlens-agent`
Agent endpoint for CopilotKit. Accepts `RunAgentInput` (AG-UI protocol), streams Server-Sent Events back:
- `RUN_STARTED` / `RUN_FINISHED` — lifecycle
- `STATE_SNAPSHOT` — initial state
- `STATE_DELTA` — widget/tool_log updates (JSON Patch)
- `TEXT_MESSAGE_START/CONTENT/END` — streaming assistant response

### POST `/upload-statement`
Accepts PDF file upload (max 20MB). Pipeline:
1. `extraction_agent` — GPT-4o vision extracts holdings from PDF pages
2. `enrichment_agent` — FMP + yfinance adds live prices, sector, beta, yield
3. `auto_dashboard` — generates 7-8 starter widgets
4. Returns JSON: `{ institution, accounts, confidence, widgets }`

## Agent Graph

```
START → planner → router → execute_tool → planner (loop)
                        └→ respond → END
```

- **Planner**: GPT-4o decides which tool to call based on user query
- **Router**: Parses tool call JSON from planner output
- **Execute Tool**: Runs tool function, auto-generates widgets from results
- **Respond**: Returns final text response to user

## Analysis Tools

| Tool                   | Input                          | Output                                    |
| ---------------------- | ------------------------------ | ----------------------------------------- |
| `compute_allocation`   | group_by (asset_class, sector, country, geographic_exposure, market_cap_class, currency, account_type) | Allocation breakdown + pie chart widget |
| `compute_fees`         | show_alternatives flag         | MER analysis, fee drag, low-cost alternatives + bar widgets |
| `portfolio_risk`       | —                              | Weighted beta, risk score, flags + gauge widget |
| `income_analysis`      | —                              | Yield, income by type, tax notes + widgets |
| `compare_performance`  | benchmark, period              | Return comparison vs XIU/VFV/VGRO etc.   |
| `rank_insights`        | —                              | AI-ranked portfolio observations          |
| `detect_concentration` | threshold                      | Over-concentrated positions               |
| `detect_overlap`       | —                              | Duplicate exposures across accounts       |
| `auto_dashboard`       | household data                 | 7-8 starter widgets                       |

## Development

```bash
# Install dependencies
poetry install

# Run development server
poetry run python main.py        # http://localhost:8000

# Run tests
poetry run pytest

# Run specific test
poetry run pytest tests/tools/test_compute_fees.py -v
```

## Environment

The server `.env` is symlinked to `../client/.env`. Required variables:

```
OPENAI_API_KEY=your_key         # Required — GPT-4o
FMP_API_KEY=your_key            # Optional — Financial Modeling Prep (richer market data)
GOOGLE_API_KEY=your_key         # Optional — Gemini
TAVILY_API_KEY=your_key         # Optional — web search
DATABASE_URL=postgresql+asyncpg://...  # Optional — persistent storage
CLERK_SECRET_KEY=your_key       # Optional — auth
```

## Supported Institutions

Extraction agent auto-detects 15+ Canadian brokerages via regex patterns:
RBC, TD, Wealthsimple, Questrade, BMO, CIBC, Scotia, National Bank, Desjardins, Manulife, Sun Life, Great-West Lifeco, IG Wealth, Edward Jones, CI Direct Investing
