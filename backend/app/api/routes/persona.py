from fastapi import APIRouter, HTTPException, status, Request
from ..schemas.persona import PersonaUpsert
from app.api.models.persona import create_persona, get_user_personas
import logging

log = logging.getLogger("personas")


router = APIRouter(prefix="/api/personas", tags=["personas"])

@router.get("/me", status_code=status.HTTP_200_OK)
async def list_my_personas(request: Request):
    user_id = request.session.get("user_id") if hasattr(request, "session") else None
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not logged in")

    try:
        rows = await get_user_personas(int(user_id))
        items = []
        for r in rows:
            params = r.get("persona_parameters") or {}
            # UI 표시용 이름: parameters.name 이 있으면 사용, 없으면 "프로필 {num}"
            disp = params.get("name") or f"프로필 {r.get('user_persona_num')}"
            items.append({
                "num": r.get("user_persona_num"),
                "img": r.get("persona_img"),
                "name": disp,
            })
        return {"ok": True, "items": items}
    except Exception as e:
        log.exception("Failed to list personas for user_id=%s: %s", user_id, e)
        raise HTTPException(status_code=500, detail="Failed to list personas")


@router.put("/setting", status_code=status.HTTP_201_CREATED)
async def put_my_persona(payload: PersonaUpsert, request: Request):
    user_id = request.session.get("user_id") if hasattr(request, "session") else None
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not logged in")

    try:
        # Debug: trace minimal payload info (lengths only) and user_id
        try:
            pp_keys = list(payload.persona_parameters.keys())[:8]
        except Exception:
            pp_keys = []
        log.info("PUT /personas/setting by user_id=%s img=%s params_keys=%s", user_id, payload.persona_img, pp_keys)

        persona_id, persona_num = await create_persona(
            user_id=int(user_id),
            persona_img=payload.persona_img,
            persona_parameters=payload.persona_parameters,
        )
    except ValueError as e:
        if str(e) == "persona_limit_reached":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="persona_limit_reached")
        raise
    except Exception as e:
        log.exception("Failed to save persona for user_id=%s: %s", user_id, e)
        raise HTTPException(status_code=500, detail=f"Failed to save persona: {e}")

    return {"ok": True, "persona_id": int(persona_id), "persona_num": int(persona_num)}


