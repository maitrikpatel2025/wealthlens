"""
CRUD operations for WealthLens portfolio persistence.
Uses raw SQL against Supabase-managed schema.
"""

import json
import uuid
from typing import Any

from sqlalchemy import text
from core.db.connection import get_session


async def save_portfolio(user_id: str, extraction_result: dict) -> str:
    """Save extracted portfolio data (household -> accounts -> holdings).

    Returns the new household UUID.
    """
    household_id = str(uuid.uuid4())

    async with get_session() as session:
        # Insert household
        await session.execute(
            text("""
                INSERT INTO households (id, user_id, institution, confidence)
                VALUES (:id, :user_id, :institution, :confidence)
            """),
            {
                "id": household_id,
                "user_id": user_id,
                "institution": extraction_result.get("institution", "Unknown"),
                "confidence": extraction_result.get("confidence", 0),
            },
        )

        for account_data in extraction_result.get("accounts", []):
            account_id = str(uuid.uuid4())
            await session.execute(
                text("""
                    INSERT INTO accounts (id, household_id, name, account_type, total_value)
                    VALUES (:id, :household_id, :name, :account_type, :total_value)
                """),
                {
                    "id": account_id,
                    "household_id": household_id,
                    "name": account_data.get("name", ""),
                    "account_type": account_data.get("account_type", ""),
                    "total_value": account_data.get("total_value", 0),
                },
            )

            for holding_data in account_data.get("holdings", []):
                await session.execute(
                    text("""
                        INSERT INTO holdings (
                            id, account_id, symbol, name, quantity, market_value,
                            book_cost, mer, sector, asset_class, currency,
                            dividend_yield, beta, confidence
                        ) VALUES (
                            :id, :account_id, :symbol, :name, :quantity, :market_value,
                            :book_cost, :mer, :sector, :asset_class, :currency,
                            :dividend_yield, :beta, :confidence
                        )
                    """),
                    {
                        "id": str(uuid.uuid4()),
                        "account_id": account_id,
                        "symbol": holding_data.get("symbol", ""),
                        "name": holding_data.get("name", ""),
                        "quantity": holding_data.get("quantity", 0),
                        "market_value": holding_data.get("market_value", 0),
                        "book_cost": holding_data.get("book_cost"),
                        "mer": holding_data.get("mer"),
                        "sector": holding_data.get("sector"),
                        "asset_class": holding_data.get("asset_class"),
                        "currency": holding_data.get("currency", "CAD"),
                        "dividend_yield": holding_data.get("dividend_yield"),
                        "beta": holding_data.get("beta"),
                        "confidence": holding_data.get("confidence", 0.5),
                    },
                )

        # Save extraction record
        await session.execute(
            text("""
                INSERT INTO extractions (id, household_id, institution, holdings_count, confidence, raw_result)
                VALUES (:id, :household_id, :institution, :holdings_count, :confidence, :raw_result)
            """),
            {
                "id": str(uuid.uuid4()),
                "household_id": household_id,
                "institution": extraction_result.get("institution", ""),
                "holdings_count": sum(
                    len(a.get("holdings", []))
                    for a in extraction_result.get("accounts", [])
                ),
                "confidence": extraction_result.get("confidence", 0),
                "raw_result": json.dumps(extraction_result),
            },
        )

    return household_id


async def load_user_portfolios(user_id: str) -> list[dict]:
    """Load all households with nested accounts/holdings for a user.

    Returns the same shape as CopilotKit state households.
    """
    async with get_session() as session:
        rows = await session.execute(
            text("""
                SELECT id, institution, confidence, created_at
                FROM households
                WHERE user_id = :user_id
                ORDER BY created_at DESC
            """),
            {"user_id": user_id},
        )
        households_rows = rows.fetchall()

        households = []
        for h in households_rows:
            h_id, institution, confidence, created_at = h

            acc_rows = await session.execute(
                text("""
                    SELECT id, name, account_type, total_value
                    FROM accounts
                    WHERE household_id = :household_id
                """),
                {"household_id": h_id},
            )
            accounts = []
            for a in acc_rows.fetchall():
                a_id, a_name, a_type, a_total = a

                hold_rows = await session.execute(
                    text("""
                        SELECT symbol, name, quantity, market_value, book_cost,
                               mer, sector, asset_class, currency, dividend_yield,
                               beta, confidence
                        FROM holdings
                        WHERE account_id = :account_id
                    """),
                    {"account_id": a_id},
                )
                holdings = [
                    {
                        "symbol": r[0],
                        "name": r[1],
                        "quantity": r[2],
                        "market_value": r[3],
                        "book_cost": r[4],
                        "mer": r[5],
                        "sector": r[6],
                        "asset_class": r[7],
                        "currency": r[8],
                        "dividend_yield": r[9],
                        "beta": r[10],
                        "confidence": r[11],
                    }
                    for r in hold_rows.fetchall()
                ]

                accounts.append({
                    "id": str(a_id),
                    "name": a_name,
                    "account_type": a_type,
                    "total_value": a_total,
                    "holdings": holdings,
                })

            households.append({
                "id": str(h_id),
                "institution": institution,
                "accounts": accounts,
                "confidence": confidence,
                "extracted_at": created_at.isoformat() if created_at else None,
            })

        return households


async def delete_portfolio(user_id: str, household_id: str) -> bool:
    """Delete a household and all cascading data. Returns True if deleted."""
    async with get_session() as session:
        result = await session.execute(
            text("""
                DELETE FROM households
                WHERE id = :household_id AND user_id = :user_id
            """),
            {"household_id": household_id, "user_id": user_id},
        )
        return result.rowcount > 0


async def save_conversation(
    user_id: str,
    title: str,
    messages: list[dict],
    widgets: list[dict] | None = None,
) -> str:
    """Save a conversation with messages. Returns conversation UUID."""
    conv_id = str(uuid.uuid4())

    async with get_session() as session:
        await session.execute(
            text("""
                INSERT INTO conversations (id, user_id, title)
                VALUES (:id, :user_id, :title)
            """),
            {"id": conv_id, "user_id": user_id, "title": title},
        )

        for msg in messages:
            await session.execute(
                text("""
                    INSERT INTO conversation_messages (id, conversation_id, role, content, widgets_snapshot)
                    VALUES (:id, :conversation_id, :role, :content, :widgets_snapshot)
                """),
                {
                    "id": str(uuid.uuid4()),
                    "conversation_id": conv_id,
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", ""),
                    "widgets_snapshot": json.dumps(widgets) if widgets else None,
                },
            )

    return conv_id


async def load_user_conversations(user_id: str) -> list[dict]:
    """Load conversation list for a user (without messages)."""
    async with get_session() as session:
        rows = await session.execute(
            text("""
                SELECT id, title, created_at, updated_at
                FROM conversations
                WHERE user_id = :user_id
                ORDER BY updated_at DESC
            """),
            {"user_id": user_id},
        )
        return [
            {
                "id": str(r[0]),
                "title": r[1],
                "created_at": r[2].isoformat() if r[2] else None,
                "updated_at": r[3].isoformat() if r[3] else None,
            }
            for r in rows.fetchall()
        ]
