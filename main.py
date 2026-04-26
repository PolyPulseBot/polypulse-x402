"""
PolyPulse x402 — Snapshot API
Returns top 30 active Polymarket markets for $0.005 USDC per call.

Currently configured for Base Sepolia (testnet) with public facilitator.
Switch to Base mainnet (eip155:8453) + CDP facilitator when ready for prod.
"""

import os
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

# Base Sepolia for testing (free, no CDP key needed)
NETWORK = os.getenv("NETWORK", "eip155:84532")
FACILITATOR_URL = os.getenv("FACILITATOR_URL", "https://x402.org/facilitator")

SNAPSHOT_PRICE = "$0.005"
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
}

# ───── FastAPI App ───────────────────────────────────────────
app = FastAPI(
    title="PolyPulse x402",
    description="Paid Polymarket data APIs for AI agents",
    version="0.1.0"
)

app.add_middleware(PaymentMiddlewareASGI, routes=routes, server=server)

# ───── Routes ────────────────────────────────────────────────
@app.get("/")
def root():
    """Health check / info endpoint — free."""
    return {
        "service": "PolyPulse x402",
        "version": "0.1.0",
        "endpoints": {
            "/v1/snapshot": f"{SNAPSHOT_PRICE} per call — top 30 Polymarket markets"
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
