from __future__ import annotations
import os
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import PlainTextResponse

router = APIRouter(prefix="/webhooks/instagram", tags=["instagram"])

VERIFY_TOKEN = os.getenv("META_WEBHOOK_VERIFY_TOKEN", "")


@router.get("")
async def verify_webhook(request: Request):
    """
    Meta(Webhooks) verification endpoint.
    GET query params: hub.mode, hub.verify_token, hub.challenge
    Respond with the hub.challenge if verify_token matches.
    """
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if not (mode and token and challenge):
        raise HTTPException(status_code=400, detail="missing_query_params")

    if mode == "subscribe" and VERIFY_TOKEN and token == VERIFY_TOKEN:
        return PlainTextResponse(challenge, status_code=200)

    raise HTTPException(status_code=403, detail="verification_failed")


@router.post("")
async def receive_webhook(body: dict):
    """
    Receive Instagram Graph Webhook events.
    For now, just acknowledge. You can extend to process events.
    """
    # TODO: add signature validation (X-Hub-Signature) if needed
    # and process body events.
    return {"ok": True}
