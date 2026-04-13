"""
scraper_inputs.py - Build scraper_engine_inputs event from any user query.

Uses Claude Haiku via direct REST API call (no anthropic SDK import needed)
to intelligently extract dynamic fields from any query.

Dynamic fields  (Haiku-generated, query-aware):
  - job_id           : unique job identifier
  - source_url       : most relevant URL to scrape
  - goal             : specific scraping objective
  - domain           : Retail / Pharma / Finance / Technology / etc.
  - competitor       : primary company/brand being monitored
  - competitor_names : list of competitors

Static fields (same for every request):
  - user_id          : "mock"
  - projectId        : "costco"
  - projectName      : "Costco Project"
  - monitoring_freq  : "daily"
"""

import json
import logging
import os
import uuid
from typing import Any, Dict

import requests

logger = logging.getLogger("SCRAPER_INPUTS")

# ---------------------------------------------------------------------------
# Static fields
# ---------------------------------------------------------------------------
_STATIC = {
    "user_id":          "mock",
    "projectId":        "costco",
    "projectName":      "Costco Project",
    "monitoring_freq":  "daily",
}

_ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
_HAIKU_MODEL       = "claude-haiku-4-5-20251001"

_SYSTEM = (
    "You are a web scraping planner. "
    "Given a user query, extract structured scraping inputs as a JSON object. "
    "Be specific, practical, and use real crawlable URLs."
)

_USER_TEMPLATE = """\
User query: "{query}"

Return a JSON object with EXACTLY these keys:
{{
  "job_id": "job-{job_id}",
  "source_url": "<single most relevant URL to scrape>",
  "goal": "<specific scraping goal: what to look for and what data to collect>",
  "domain": "<one of: Retail, Pharma, Finance, Technology, Healthcare, Supply Chain, General>",
  "competitor": "<primary company, brand, or entity the query is about>",
  "competitor_names": ["<name1>", "<name2>"]
}}

URL guidelines:
  Retail product  -> https://www.amazon.com/s?k=<product+name>
                     https://www.bestbuy.com/site/searchpage.jsp?st=<product>
  Pharma company  -> https://investor.<company>.com/news-releases
                     https://www.<company>.com/pipeline
  Stock/finance   -> https://finance.yahoo.com/quote/<TICKER>
  News/general    -> https://www.google.com/search?q=<topic>+news+2026&tbm=nws
  Supply chain    -> https://www.supplychaindive.com/?s=<topic>
  Competitor      -> https://www.<competitor>.com

Return ONLY the raw JSON object. No markdown. No explanation."""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_scraper_inputs(query: str) -> Dict[str, Any]:
    """
    Generate scraper_engine_inputs for a given query.

    Calls Claude Haiku via REST (no anthropic package required) to extract
    dynamic fields. Falls back to a keyword heuristic on any error.

    Args:
        query: Raw user query string.

    Returns:
        Complete scraper_engine_inputs dict ready to emit as a WebSocket event.
    """
    job_id = uuid.uuid4().hex[:8]

    dynamic = _call_haiku(query, job_id)
    result  = {**_STATIC, **dynamic}

    logger.info(
        f"scraper_engine_inputs | job={result.get('job_id')} "
        f"domain={result.get('domain')} competitor={result.get('competitor')} "
        f"url={result.get('source_url', '')[:60]}"
    )
    return result


# ---------------------------------------------------------------------------
# Internal: Haiku REST call
# ---------------------------------------------------------------------------

def _call_haiku(query: str, job_id: str) -> Dict[str, Any]:
    """Call Claude Haiku via Anthropic REST API to extract scraper fields."""
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        logger.warning("ANTHROPIC_API_KEY not set — using fallback scraper inputs.")
        return _fallback(query, job_id)

    payload = {
        "model":      _HAIKU_MODEL,
        "max_tokens": 400,
        "system":     _SYSTEM,
        "messages": [
            {
                "role":    "user",
                "content": _USER_TEMPLATE.format(query=query, job_id=job_id),
            }
        ],
    }

    headers = {
        "x-api-key":         api_key,
        "anthropic-version": "2023-06-01",
        "content-type":      "application/json",
    }

    try:
        resp = requests.post(
            _ANTHROPIC_API_URL,
            headers=headers,
            json=payload,
            timeout=15,
        )
        resp.raise_for_status()

        raw = resp.json()["content"][0]["text"].strip()

        # Strip markdown fences if the model added them
        if raw.startswith("```"):
            lines = raw.splitlines()
            raw   = "\n".join(
                l for l in lines
                if not l.startswith("```")
            ).strip()

        extracted = json.loads(raw)
        logger.info(f"Haiku extracted: {extracted}")
        return extracted

    except requests.exceptions.Timeout:
        logger.warning("Haiku API timeout — using fallback.")
        return _fallback(query, job_id)

    except requests.exceptions.HTTPError as e:
        logger.warning(f"Haiku API HTTP error {e} — using fallback.")
        return _fallback(query, job_id)

    except (json.JSONDecodeError, KeyError) as e:
        logger.warning(f"Failed to parse Haiku response ({e}) — using fallback.")
        return _fallback(query, job_id)

    except Exception as e:
        logger.warning(f"Unexpected error in Haiku call ({e}) — using fallback.")
        return _fallback(query, job_id)


# ---------------------------------------------------------------------------
# Internal: keyword-based fallback (no API needed)
# ---------------------------------------------------------------------------

def _fallback(query: str, job_id: str) -> Dict[str, Any]:
    """
    Simple keyword heuristic when Haiku is unavailable.
    Covers the most common retail / pharma / finance / tech domains.
    """
    q = query.lower()

    # Domain detection
    if any(w in q for w in ["stock", "inventory", "shelf", "reorder", "warehouse",
                             "costco", "walmart", "amazon", "retail", "store"]):
        domain     = "Retail"
        url_q      = query.replace(" ", "+")
        source_url = f"https://www.amazon.com/s?k={url_q}"
        competitor = next((w.title() for w in ["costco","walmart","amazon","target","bestbuy"]
                           if w in q), "Retailer")
    elif any(w in q for w in ["pharma", "drug", "fda", "clinical", "trial", "lilly",
                               "pfizer", "novartis", "glp", "ozempic", "pipeline"]):
        domain     = "Pharma"
        company    = next((w for w in ["lilly","pfizer","novartis","novo","roche","merck"]
                           if w in q), "pharma")
        source_url = f"https://investor.{company}.com/news-releases"
        competitor = company.title()
    elif any(w in q for w in ["stock price", "market", "earnings", "revenue",
                               "nasdaq", "nyse", "ticker", "finance"]):
        domain     = "Finance"
        source_url = f"https://finance.yahoo.com/search?q={query.replace(' ', '+')}"
        competitor = "Market"
    elif any(w in q for w in ["tech", "ai", "software", "saas", "cloud", "microsoft",
                               "google", "apple", "openai", "nvidia"]):
        domain     = "Technology"
        company    = next((w for w in ["microsoft","google","apple","nvidia","openai"]
                           if w in q), "tech")
        source_url = f"https://www.google.com/search?q={query.replace(' ','+')}&tbm=nws"
        competitor = company.title()
    else:
        domain     = "General"
        source_url = f"https://www.google.com/search?q={query.replace(' ','+')}&tbm=nws"
        competitor = "Unknown"

    return {
        "job_id":           f"job-{job_id}",
        "source_url":       source_url,
        "goal":             f"Search for information related to: {query}",
        "domain":           domain,
        "competitor":       competitor,
        "competitor_names": [competitor] if competitor != "Unknown" else [],
    }
