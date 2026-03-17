"""
Extraction sub-agent — multimodal implementation (M4).
Converts PDF pages to images and uses GPT-4o vision for extraction.
Falls back to text-based extraction if image conversion fails.
"""

import base64
import json
import io
import re
from typing import Any

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

from langchain_openai import ChatOpenAI
from core.institution_patterns import detect_institution, detect_account_type


EXTRACTION_SYSTEM_PROMPT = """You are a financial document extraction assistant specializing in Canadian brokerage statements.

Extract ALL investment holdings from the provided statement. For each holding, return:
- name: Fund or security name
- symbol: Ticker symbol (if visible)
- quantity: Number of shares/units
- market_value: Current market value in CAD
- book_cost: Original cost (if available)
- mer: Management Expense Ratio in percent (if shown)
- account_type: Account type (RRSP, TFSA, RESP, RRIF, LIRA, Non-Registered, etc.)

Rules:
- Return ONLY a JSON array — no explanation, no markdown fences.
- If a field is not available, use null.
- Do NOT include cash balances unless they are money market funds.
- Numbers should be plain floats without dollar signs or commas.

Example:
[{"name":"Vanguard S&P 500 Index ETF","symbol":"VFV","quantity":150.0,"market_value":15234.50,"book_cost":12000.00,"mer":0.09,"account_type":"TFSA"}]"""


async def extraction_agent(pdf_bytes: bytes, state: dict) -> dict:
    """
    Extract holdings from a brokerage statement PDF.
    Pipeline: render pages → multimodal LLM extraction → validate → group
    """
    # Step 1: Convert PDF to images (multimodal) + extract text (fallback/institution detection)
    images = render_pdf_to_images(pdf_bytes)
    text = extract_text(pdf_bytes)

    if not images and (not text or len(text.strip()) < 50):
        return {
            "institution": "Unknown",
            "accounts": [],
            "confidence": 0,
            "error": "Could not process PDF. The file may be corrupted or empty.",
        }

    # Step 2: Detect institution from text
    institution = detect_institution(text) if text else {"name": "Unknown", "confidence": 0.1, "account_types_found": []}

    # Step 3: Multimodal LLM extraction (images first, text fallback)
    if images:
        holdings = await extract_holdings_multimodal(images)
    else:
        holdings = await extract_holdings_text(text)

    if not holdings:
        # Fallback: try text-based if multimodal returned nothing
        if images and text:
            holdings = await extract_holdings_text(text)

    # Step 4: Validate and score
    validated = validate_and_score(holdings, institution)

    # Step 5: Group into accounts
    accounts = group_into_accounts(validated, institution)

    overall_confidence = (
        sum(h.get("confidence", 0) for h in validated) / len(validated)
        if validated else 0
    )

    return {
        "institution": institution["name"],
        "institution_confidence": institution["confidence"],
        "accounts": accounts,
        "holdings_count": len(validated),
        "confidence": round(overall_confidence, 2),
    }


def render_pdf_to_images(pdf_bytes: bytes) -> list[str]:
    """Convert PDF pages to base64-encoded PNG images using PyMuPDF."""
    if not fitz:
        return []

    images = []
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        for page_num in range(min(len(doc), 10)):  # Cap at 10 pages
            page = doc[page_num]
            # Render at 2x resolution for better readability
            mat = fitz.Matrix(2.0, 2.0)
            pix = page.get_pixmap(matrix=mat)
            img_bytes = pix.tobytes("png")
            b64 = base64.b64encode(img_bytes).decode("utf-8")
            images.append(b64)
        doc.close()
    except Exception as e:
        print(f"PDF image render error: {e}")

    return images


def extract_text(pdf_bytes: bytes) -> str:
    """Extract text from PDF using pdfplumber (for institution detection + fallback)."""
    if not pdfplumber:
        return ""

    try:
        all_text = []
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    all_text.append(page_text)
        return "\n\n".join(all_text)
    except Exception as e:
        print(f"Text extraction error: {e}")
        return ""


async def extract_holdings_multimodal(images: list[str]) -> list:
    """Use GPT-4o vision to extract holdings from PDF page images."""
    llm = ChatOpenAI(model="gpt-4o", temperature=0, max_tokens=4096)

    # Build message with images
    content: list[dict] = [
        {"type": "text", "text": "Extract all investment holdings from this brokerage statement. Return ONLY a JSON array."}
    ]

    for b64_img in images:
        content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/png;base64,{b64_img}",
                "detail": "high",
            },
        })

    try:
        response = await llm.ainvoke([
            {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
            {"role": "user", "content": content},
        ])
        return parse_llm_json(response.content)

    except Exception as e:
        print(f"Multimodal extraction error: {e}")
        return []


async def extract_holdings_text(text: str) -> list:
    """Fallback: extract holdings from text using GPT-4o."""
    llm = ChatOpenAI(model="gpt-4o", temperature=0, max_tokens=4096)

    # Truncate if too long
    max_chars = 12000
    if len(text) > max_chars:
        half = max_chars // 2
        text = text[:half] + "\n\n... [truncated] ...\n\n" + text[-half:]

    try:
        response = await llm.ainvoke([
            {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
            {"role": "user", "content": f"Extract holdings from this statement text:\n\n{text}"},
        ])
        return parse_llm_json(response.content)

    except Exception as e:
        print(f"Text extraction LLM error: {e}")
        return []


def parse_llm_json(content: str) -> list:
    """Parse JSON from LLM response, handling markdown fences."""
    # Try extracting from ```json ... ``` block
    json_match = re.search(r'```(?:json)?\s*(.*?)\s*```', content, re.DOTALL)
    if json_match:
        raw = json_match.group(1)
    else:
        raw = content.strip()

    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            return parsed
        if isinstance(parsed, dict) and "holdings" in parsed:
            return parsed["holdings"]
        return []
    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}")
        # Last resort: find array in content
        arr_match = re.search(r'\[.*\]', content, re.DOTALL)
        if arr_match:
            try:
                parsed = json.loads(arr_match.group(0))
                if isinstance(parsed, list):
                    return parsed
            except json.JSONDecodeError:
                pass
        return []


def validate_and_score(holdings: list, institution: dict) -> list:
    """Validate extracted holdings and assign confidence scores."""
    validated = []

    for h in holdings:
        confidence = 0.5  # Base confidence

        # Has symbol → higher confidence
        if h.get("symbol"):
            confidence += 0.15

        # Has market value → higher confidence
        if h.get("market_value") and h["market_value"] > 0:
            confidence += 0.15

        # Has quantity → higher confidence
        if h.get("quantity") and h["quantity"] > 0:
            confidence += 0.1

        # Institution was detected → boost
        if institution.get("confidence", 0) > 0.5:
            confidence += 0.1

        # Validate market_value is reasonable
        mv = h.get("market_value")
        if mv is not None:
            try:
                mv = float(mv)
                if mv < 0:
                    mv = abs(mv)
                    confidence -= 0.1
                h["market_value"] = mv
            except (ValueError, TypeError):
                h["market_value"] = 0
                confidence -= 0.2

        # Validate quantity
        qty = h.get("quantity")
        if qty is not None:
            try:
                h["quantity"] = float(qty)
            except (ValueError, TypeError):
                h["quantity"] = 0

        # Clean symbol
        sym = h.get("symbol", "")
        if sym:
            h["symbol"] = sym.strip().upper().replace(".", "-")

        h["confidence"] = min(1.0, max(0.0, round(confidence, 2)))
        validated.append(h)

    return validated


def group_into_accounts(holdings: list, institution: dict) -> list:
    """Group holdings by account type."""
    account_map: dict[str, list] = {}

    for h in holdings:
        acct_type = h.get("account_type", "Unknown") or "Unknown"
        if acct_type not in account_map:
            account_map[acct_type] = []
        account_map[acct_type].append(h)

    accounts = []
    for acct_type, acct_holdings in account_map.items():
        total_value = sum(h.get("market_value", 0) for h in acct_holdings)
        accounts.append({
            "name": f"{institution['name']} — {acct_type}",
            "type": acct_type,
            "holdings": acct_holdings,
            "total_value": round(total_value, 2),
            "holdings_count": len(acct_holdings),
        })

    return accounts
