from fastapi import APIRouter, HTTPException, Request

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/validate")
@router.get("/validate")
async def validate_token(request: Request):
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        raise HTTPException(status_code=401, detail="Missing token")
    return {"sub": "user", "role": "admin"}
