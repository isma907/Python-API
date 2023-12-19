from datetime import timedelta
from fastapi import APIRouter, Depends, FastAPI, Form, HTTPException, Header
from fastapi.security import OAuth2PasswordRequestForm
from auth import (
    create_access_token,
    verify_user_token,
    get_user,
    verify_password,
)
from fastapi.middleware.cors import CORSMiddleware
from routes.users import router as user_router
import os
from dotenv import load_dotenv
from jose import jwt


load_dotenv()

# python -m uvicorn main:app --reload

app = FastAPI()
router = APIRouter()
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
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    authorization: str = Header(None),
):
    if form_data.username and form_data.password:
        # Authenticate based on username and password if provided
        user = get_user(form_data.username)
        hashed_password = user.password

        if not user or not verify_password(form_data.password, hashed_password):
            raise HTTPException(
                status_code=400, detail="Incorrect username or password"
            )

        # Generate access token for user
        access_token_expires = timedelta(
            minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))
        )
        access_token = create_access_token(
            data={"username": user.username}, expires_delta=access_token_expires
        )
    elif authorization:
        # Extract token from Authorization header
        credentials_exception = HTTPException(
            status_code=401,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            token_type, token = authorization.split()
            if token_type.lower() != "bearer":
                raise credentials_exception
        except (ValueError, jwt.JWTError):
            raise credentials_exception

        # Your validation logic goes here
        # ...

        # Generate access token for user
        access_token_expires = timedelta(
            minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))
        )
        access_token = create_access_token(
            data={"some_data": "example"}, expires_delta=access_token_expires
        )
    else:
        raise HTTPException(status_code=400, detail="Invalid authentication data")

    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/register-client", dependencies=[Depends(verify_user_token)])
async def register_client(client_name: str = Form(...), user: dict = Depends(get_user)):
    client_id = str(hash(client_name))
    client_secret = str(hash(client_name + "secret"))

    return {
        "client_id": client_id,
        "client_secret": client_secret,
        "client_name": client_name,
    }
