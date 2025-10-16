from fastapi import APIRouter, HTTPException, status, Request
from ..schemas.persona import PersonaUpsert
from app.api.models.persona import create_persona


router = APIRouter(prefix="/personas", tags=["personas"])


@router.put("/setting", status_code=status.HTTP_201_CREATED)
async def put_my_persona(payload: PersonaUpsert, request: Request):
    user_id = request.session.get("user_id") if hasattr(request, "session") else None
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not logged in")

    try:
        persona_id = await create_persona(
            user_id=int(user_id),
            persona_img=payload.persona_img,
            persona_parameters=payload.persona_parameters,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save persona: {e}")

    return {"ok": True, "persona_id": int(persona_id)}
