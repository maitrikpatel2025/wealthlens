# WealthLens Client

Next.js 15 frontend for the WealthLens portfolio intelligence platform.

## Tech Stack

- **Framework**: Next.js 15.3.4 with Turbopack
- **UI**: React 19, TailwindCSS 4, Lucide Icons
- **Charts**: Recharts 3.0.2
- **AI Integration**: CopilotKit (react-core, react-ui, runtime-client-gql)
- **Protocol**: AG-UI Client for agent state streaming

## Project Structure

```
src/
├── app/
│   ├── api/
│   │   ├── copilotkit/route.ts   # CopilotKit runtime → backend agent
│   │   └── upload/route.ts       # PDF upload → backend extraction
│   ├── components/
│   │   ├── chat-panel.tsx        # AI chat interface with upload button
│   │   ├── dashboard-canvas.tsx  # Widget grid + export controls
│   │   ├── pdf-upload.tsx        # Drag-and-drop PDF upload modal
│   │   ├── side-nav.tsx          # Conversation history sidebar
│   │   ├── suggestion-cards.tsx  # Starter prompts when no data
│   │   ├── tool-logs.tsx         # Real-time tool execution status
│   │   ├── top-nav.tsx           # Header with theme toggle, auth
│   │   └── widgets/
│   │       ├── widget-renderer.tsx  # Dynamic responsive grid layout
│   │       ├── widget-wrapper.tsx   # Widget card with toolbar
│   │       ├── pie-widget.tsx       # Pie/donut chart
│   │       ├── bar-widget.tsx       # Bar chart
│   │       ├── line-widget.tsx      # Multi-series line chart
│   │       ├── table-widget.tsx     # Data table with sorting
│   │       ├── gauge-widget.tsx     # Risk score gauge
│   │       ├── summary-widget.tsx   # Key metrics cards
│   │       ├── treemap-widget.tsx   # Treemap visualization
│   │       ├── sankey-widget.tsx    # Flow diagram
│   │       ├── expand-modal.tsx     # Full-screen widget modal
│   │       └── widget-toolbar.tsx   # Expand/remove controls
│   ├── export/page.tsx           # Print/PDF export page
│   ├── globals.css               # TailwindCSS + custom theme
│   ├── layout.tsx                # Root layout with fonts
│   └── page.tsx                  # Main dashboard + chat page
├── types/
│   ├── api.ts                    # HoldingData, AccountData, HouseholdData
│   └── widgets.ts                # WidgetType, WidgetSpec, GridPosition
└── utils/
    └── prompts.ts                # Client-side prompt utilities
```

## API Routes

### POST `/api/copilotkit`
Proxies CopilotKit agent requests to the Python backend at `http://127.0.0.1:8000/wealthlens-agent`. Uses OpenAI adapter.

### POST `/api/upload`
Accepts PDF file uploads (multipart/form-data), forwards to backend `/upload-statement`, returns extracted holdings and auto-generated dashboard widgets.

## Widget Types

| Type      | Description                    | Data Source              |
| --------- | ------------------------------ | ------------------------ |
| `pie`     | Allocation breakdown           | compute_allocation       |
| `bar`     | Comparative values             | compute_fees, auto_dash  |
| `line`    | Time series / trends           | compare_performance      |
| `table`   | Holdings data table            | auto_dashboard           |
| `gauge`   | Risk score (0-100)             | portfolio_risk           |
| `summary` | Key metric cards               | auto_dashboard           |
| `treemap` | Hierarchical allocation        | compute_allocation       |
| `sankey`  | Flow diagram                   | income_analysis          |

## Development

```bash
# Install dependencies
pnpm install

# Development server (Turbopack)
pnpm dev          # http://localhost:3000

# Production build
pnpm build
pnpm start

# Lint
pnpm lint
```

## Environment

Create `.env` in this directory (or copy from root `.env.sample`):

```
OPENAI_API_KEY=your_key_here
```

## Design

- **Colors**: Emerald (primary), Sky (secondary), Amber (accent), Slate (neutral)
- **Fonts**: Geist Sans + Geist Mono (with Inter fallback)
- **Theme**: Dark/light mode toggle, dashboard-first layout
- **Layout**: Resizable split pane — dashboard (left) + chat (right)
