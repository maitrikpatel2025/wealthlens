from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, UploadFile, File, Request
from fastapi.responses import StreamingResponse, JSONResponse
import uuid
from typing import Any, Optional
import os
import uvicorn
import asyncio

from ag_ui.core import (
    RunAgentInput,
    StateSnapshotEvent,
    EventType,
    RunStartedEvent,
    RunFinishedEvent,
    TextMessageStartEvent,
    TextMessageEndEvent,
    TextMessageContentEvent,
    StateDeltaEvent,
)
from ag_ui.encoder import EventEncoder
from core.agent import agent_graph
from core.data_models import WealthLensState
from core.constants import MAX_UPLOAD_SIZE_BYTES


app = FastAPI()


def extract_user_id(request: Request = None) -> Optional[str]:
    """Extract user_id from Clerk JWT if available."""
    if not request:
        return None
    auth_header = request.headers.get("authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    try:
        import jwt
        token = auth_header[7:]
        clerk_secret = os.getenv("CLERK_SECRET_KEY", "")
        if not clerk_secret:
            return None
        payload = jwt.decode(token, options={"verify_signature": False})
        return payload.get("sub")
    except Exception:
        return None


@app.on_event("startup")
async def startup():
    """Initialize DB on startup if DATABASE_URL is set."""
    if os.getenv("DATABASE_URL"):
        try:
            from core.db.connection import init_db
            await init_db()
            print("Database initialized.")
        except Exception as e:
            print(f"DB init skipped: {e}")


@app.post("/wealthlens-agent")
async def wealthlens_agent(input_data: RunAgentInput):
    try:
        async def event_generator():
            encoder = EventEncoder()
            event_queue = asyncio.Queue()

            def emit_event(event):
                event_queue.put_nowait(event)

            message_id = str(uuid.uuid4())

            yield encoder.encode(
                RunStartedEvent(
                    type=EventType.RUN_STARTED,
                    thread_id=input_data.thread_id,
                    run_id=input_data.run_id,
                )
            )

            yield encoder.encode(
                StateSnapshotEvent(
                    type=EventType.STATE_SNAPSHOT,
                    snapshot={
                        "widgets": input_data.state.get("widgets", []),
                        "tool_logs": [],
                        "households": input_data.state.get("households", []),
                        "active_conversation_id": input_data.state.get("active_conversation_id", ""),
                    },
                )
            )

            state = WealthLensState(
                tools=input_data.tools,
                messages=input_data.messages,
                widgets=input_data.state.get("widgets", []),
                tool_logs=[],
                households=input_data.state.get("households", []),
                active_conversation_id=input_data.state.get("active_conversation_id", ""),
                plan=[],
                extraction_results=input_data.state.get("extraction_results", []),
                enrichment_cache=input_data.state.get("enrichment_cache", {}),
            )

            agent = await agent_graph()

            agent_task = asyncio.create_task(
                agent.ainvoke(
                    state, config={"configurable": {"emit_event": emit_event, "message_id": message_id}}
                )
            )

            while True:
                try:
                    event = await asyncio.wait_for(event_queue.get(), timeout=0.1)
                    yield encoder.encode(event)
                except asyncio.TimeoutError:
                    if agent_task.done():
                        break

            result = agent_task.result()

            # Emit widget updates if changed
            result_widgets = result.get("widgets", state.get("widgets", []))
            if result_widgets != input_data.state.get("widgets", []):
                yield encoder.encode(
                    StateDeltaEvent(
                        type=EventType.STATE_DELTA,
                        delta=[
                            {
                                "op": "replace",
                                "path": "/widgets",
                                "value": result_widgets,
                            }
                        ],
                    )
                )

            # Clear tool logs
            yield encoder.encode(
                StateDeltaEvent(
                    type=EventType.STATE_DELTA,
                    delta=[
                        {
                            "op": "replace",
                            "path": "/tool_logs",
                            "value": [],
                        }
                    ],
                )
            )

            # Emit assistant response
            result_messages = result.get("messages", state.get("messages", []))
            last_msg = result_messages[-1] if result_messages else None

            if last_msg and hasattr(last_msg, "content") and last_msg.content:
                content = last_msg.content

                # Strip tool call JSON blocks from the response shown to user
                import re
                content = re.sub(r'```json\s*\{[^`]*\}\s*```', '', content).strip()

                if content:
                    yield encoder.encode(
                        TextMessageStartEvent(
                            type=EventType.TEXT_MESSAGE_START,
                            message_id=message_id,
                            role="assistant",
                        )
                    )

                    n_parts = 5
                    part_length = max(1, len(content) // n_parts)
                    parts = [
                        content[i : i + part_length]
                        for i in range(0, len(content), part_length)
                    ]
                    if len(parts) > n_parts:
                        parts = parts[: n_parts - 1] + [
                            "".join(parts[n_parts - 1 :])
                        ]

                    for part in parts:
                        yield encoder.encode(
                            TextMessageContentEvent(
                                type=EventType.TEXT_MESSAGE_CONTENT,
                                message_id=message_id,
                                delta=part,
                            )
                        )
                        await asyncio.sleep(0.3)

                    yield encoder.encode(
                        TextMessageEndEvent(
                            type=EventType.TEXT_MESSAGE_END,
                            message_id=message_id,
                        )
                    )
            else:
                yield encoder.encode(
                    TextMessageStartEvent(
                        type=EventType.TEXT_MESSAGE_START,
                        message_id=message_id,
                        role="assistant",
                    )
                )
                yield encoder.encode(
                    TextMessageContentEvent(
                        type=EventType.TEXT_MESSAGE_CONTENT,
                        message_id=message_id,
                        delta="Something went wrong! Please try again.",
                    )
                )
                yield encoder.encode(
                    TextMessageEndEvent(
                        type=EventType.TEXT_MESSAGE_END,
                        message_id=message_id,
                    )
                )

            yield encoder.encode(
                RunFinishedEvent(
                    type=EventType.RUN_FINISHED,
                    thread_id=input_data.thread_id,
                    run_id=input_data.run_id,
                )
            )

    except Exception as e:
        print(e)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.post("/upload-statement")
async def upload_statement(file: UploadFile = File(...)):
    """Upload a brokerage statement PDF for extraction."""
    try:
        if not file.filename or not file.filename.lower().endswith(".pdf"):
            return JSONResponse({"error": "Only PDF files are accepted"}, status_code=400)

        pdf_bytes = await file.read()
        if len(pdf_bytes) > MAX_UPLOAD_SIZE_BYTES:
            return JSONResponse({"error": "File too large (max 20 MB)"}, status_code=400)

        from core.sub_agents.extraction_agent import extraction_agent
        from core.sub_agents.enrichment_agent import enrichment_agent
        from core.tools.auto_dashboard import auto_dashboard

        result = await extraction_agent(pdf_bytes, {})

        # Enrich holdings with live market data (FMP + yfinance)
        for account in result.get("accounts", []):
            holdings = account.get("holdings", [])
            if holdings:
                enriched = await enrichment_agent(holdings, {})
                account["holdings"] = enriched
                account["total_value"] = round(
                    sum(h.get("market_value", 0) for h in enriched), 2
                )

        # Generate starter dashboard widgets from enriched data
        household = {
            "institution": result.get("institution", "Unknown"),
            "accounts": result.get("accounts", []),
            "confidence": result.get("confidence", 0),
        }
        dashboard = auto_dashboard({}, {"households": [household]})
        result["widgets"] = dashboard.get("widgets", [])

        return JSONResponse(result)

    except Exception as e:
        print(f"Upload error: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


def main():
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
    )


if __name__ == "__main__":
    main()
