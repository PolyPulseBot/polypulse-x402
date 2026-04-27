"""
PolyPulse x402 — Paid Polymarket APIs for AI agents

Endpoints:
  GET /              → Free service info
  GET /v1/snapshot   → $0.005 — top 30 active Polymarket markets
  GET /v1/digest     → $0.25  — bot's top 3+3 daily picks with reasoning

Currently configured for Base Sepolia (testnet) with public facilitator.
Switch to Base mainnet (eip155:8453) + CDP facilitator when ready for prod.
"""

import os
from datetime import datetime, timezone
import requests
from fastapi import FastAPI, HTTPException

from x402.http.middleware.fastapi import PaymentMiddlewareASGI
from x402.http import HTTPFacilitatorClient, FacilitatorConfig, PaymentOption
from x402.http.types import RouteConfig
from x402.server import x402ResourceServer
from x402.mechanisms.evm.exact import ExactEvmServerScheme

# ───── Configuration ─────────────────────────────────────────
PAYMENT_ADDRESS = os.getenv(
    "PAYMENT_ADDRESS",
    "0x388F8758922D23A0EBd3F87d6193735D7fDEcCB7"
)
NETWORK = os.getenv("NETWORK", "eip155:84532")
FACILITATOR_URL = os.getenv("FACILITATOR_URL", "https://x402.org/facilitator")

SNAPSHOT_PRICE = "$0.005"
DIGEST_PRICE = "$0.25"
GAMMA_API = "https://gamma-api.polymarket.com/markets"

# ───── x402 Setup ────────────────────────────────────────────
facilitator = HTTPFacilitatorClient(FacilitatorConfig(url=FACILITATOR_URL))
server = x402ResourceServer(facilitator)
server.register(NETWORK, ExactEvmServerScheme())

routes = {
    "GET /v1/snapshot": RouteConfig(
        accepts=[
            PaymentOption(
                scheme="exact",
                price=SNAPSHOT_PRICE,
                network=NETWORK,
                pay_to=PAYMENT_ADDRESS,
            ),
        ],
        mime_type="application/json",
        description="Top 30 active Polymarket markets by 24h volume",
    ),
    "GET /v1/digest": RouteConfig(
        accepts=[
            PaymentOption(
                scheme="exact",
                price=DIGEST_PRICE,
                network=NETWORK,
                pay_to=PAYMENT_ADDRESS,
            ),
        ],
        mime_type="application/json",
        description="PolyPulse Bot's top 3 prediction + top 3 sports picks with full reasoning and live bot actions",
    ),
}

# ───── FastAPI App ───────────────────────────────────────────
app = FastAPI(
    title="PolyPulse x402",
    description="Paid Polymarket data APIs for AI agents",
    version="0.2.0"
)

app.add_middleware(PaymentMiddlewareASGI, routes=routes, server=server)

# ───── Mock Digest Data ──────────────────────────────────────
# TODO Day 5: replace with Google Sheets read from Daily Digest tab
def get_latest_digest():
    """Returns mock digest data. Will be replaced with Sheet read on Day 5."""
    return {
        "scan_date": "2026-04-25",
        "is_stale": False,
        "served_at": datetime.now(timezone.utc).isoformat(),
        "predictions": [
            {
                "rank": 1,
                "market": "Strait of Hormuz traffic returns to normal by April 30?",
                "prediction": "NO",
                "edge_pct": 18.5,
                "confidence": "HIGH",
                "reasoning": "Iran's Foreign Ministry rejected normalization talks on April 25, citing ongoing US sanctions. Shipping insurers Lloyd's and Marsh both raised Hormuz war-risk premiums 40% this week. With 5 days left until resolution and traffic still 60% below pre-conflict baseline, market pricing of 76% NO underestimates the political deadlock.",
                "tier_source": "Opus",
                "bot_action": "BET_PLACED",
                "position_size_usd": 5.00
            },
            {
                "rank": 2,
                "market": "US x Iran permanent peace deal by April 30?",
                "prediction": "NO",
                "edge_pct": 12.0,
                "confidence": "HIGH",
                "reasoning": "No diplomatic channels open between Washington and Tehran as of April 25. Reuters and Bloomberg both confirm zero back-channel meetings since Israel strike on April 12. Permanent peace deals historically take 6-18 months minimum from first talks; 5 days is structurally impossible.",
                "tier_source": "Opus",
                "bot_action": "PASSED",
                "position_size_usd": None
            },
            {
                "rank": 3,
                "market": "Will Bitcoin close above $95k on April 30?",
                "prediction": "YES",
                "edge_pct": 8.2,
                "confidence": "MEDIUM",
                "reasoning": "BTC trading $96.4k as of April 26 with strong institutional inflows ($420M into spot ETFs week of April 21). Market pricing 62% YES looks underpriced given technical support at $93k held three times this month. Confidence MEDIUM because macro Fed news could move 5%+ either way.",
                "tier_source": "Sonnet",
                "bot_action": "PASSED",
                "position_size_usd": None
            }
        ],
        "sports": [
            {
                "rank": 1,
                "market": "Lakers vs Nuggets — Lakers ML",
                "prediction": "YES",
                "edge_pct": 7.4,
                "confidence": "MED-HIGH",
                "reasoning": "LeBron returned from rest April 24 looking fully healthy in shootaround. Nuggets missing Murray (questionable, hamstring) per Shams report April 25. Sportsbook line opened Lakers +3, moved to pick'em — sharp money on Lakers. Closing line value strongly favors LA.",
                "tier_source": "Opus",
                "bot_action": "BET_PLACED",
                "position_size_usd": 5.00
            },
            {
                "rank": 2,
                "market": "Celtics vs Heat — Over 215.5",
                "prediction": "YES",
                "edge_pct": 6.1,
                "confidence": "MED-HIGH",
                "reasoning": "Both teams in top 5 pace this month per CleaningTheGlass. Heat's top defender Adebayo questionable (knee). Last 4 meetings averaged 223 points combined. Total opened 213.5, moved to 215.5 — line still trails the trend.",
                "tier_source": "Sonnet",
                "bot_action": "PASSED",
                "position_size_usd": None
            },
            {
                "rank": 3,
                "market": "Warriors vs Suns — Suns +4.5",
                "prediction": "YES",
                "edge_pct": 5.3,
                "confidence": "MEDIUM",
                "reasoning": "Suns at home where they cover spread 64% this season. Warriors on second leg of back-to-back; historically -3% margin in those spots. Booker confirmed playing per April 25 practice report. Edge thin but trend supports the side.",
                "tier_source": "Sonnet",
                "bot_action": "PASSED",
                "position_size_usd": None
            }
        ],
        "summary": {
            "total_picks": 6,
            "bets_placed_today": 2,
            "total_position_size_usd": 10.00,
            "best_edge_pct": 18.5,
            "categories_active": ["predictions", "sports"]
        }
    }

# ───── Routes ────────────────────────────────────────────────
@app.get("/")
def root():
    """Health check / info endpoint — free."""
    return {
        "service": "PolyPulse x402",
        "version": "0.2.0",
        "endpoints": {
            "/v1/snapshot": f"{SNAPSHOT_PRICE} per call — top 30 Polymarket markets",
            "/v1/digest": f"{DIGEST_PRICE} per call — bot's top 3 prediction + 3 sports picks with reasoning"
        },
        "network": NETWORK,
        "facilitator": FACILITATOR_URL,
        "wallet": PAYMENT_ADDRESS
    }


@app.get("/v1/snapshot")
def snapshot():
    """Returns top 30 active Polymarket markets by 24h volume."""
    try:
        response = requests.get(
            GAMMA_API,
            params={
                "active": "true",
                "limit": 30,
                "order": "volume24hr",
                "ascending": "false"
            },
            timeout=10
        )
        response.raise_for_status()
        markets = response.json()

        return {
            "source": "polymarket-gamma",
            "count": len(markets),
            "markets": markets
        }

    except requests.RequestException as e:
        raise HTTPException(
            status_code=502,
            detail=f"Polymarket API unreachable: {str(e)}"
        )


@app.get("/v1/digest")
def digest():
    """Returns the latest PolyPulse Bot daily digest with top picks and bot actions."""
    return get_latest_digest()
