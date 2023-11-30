from datetime import timedelta
from fastapi import APIRouter, Depends, FastAPI, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from security import ACCESS_TOKEN_EXPIRE_MINUTES
from routes.auth import (
    create_access_token,
    verify_user_token,
    get_user,
    verify_password,
)
from fastapi.middleware.cors import CORSMiddleware
from routes.users import router as user_router


# python -m uvicorn main:app --reload
router = APIRouter()

app = FastAPI()
origins = ["http://localhost", "http://localhost:8080"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ROUTES
app.include_router(
    user_router,
    prefix="/users",
    tags=["users"],
    dependencies=[Depends(verify_user_token)],
)


# AUTH Endpoint
@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = get_user(form_data.username)
    hashedPassword = user.password
    if not user or not verify_password(form_data.password, hashedPassword):
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"username": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
