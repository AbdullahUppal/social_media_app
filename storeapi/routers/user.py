import logging
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm

import tasks
from database import database, user_table
from models.user import UserIn
from security import (
    authenticate_user,
    create_confirmation_token,
    create_access_token,
    get_password_hash,
    get_subject_for_token_type,
    get_user,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/register", status_code=201)
async def register(user: UserIn, request: Request, background_tasks: BackgroundTasks):
    if await get_user(user.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    hashed_password = get_password_hash(user.password)
    query = user_table.insert().values(
        email=user.email,
        password=hashed_password,
        # donot save password in plain text, use hashing in production
    )

    logger.debug(query)

    await database.execute(query)
    # wrap the
    background_tasks.add_task(
        tasks.send_user_registered_email(
            user.email,
            #  request.url_for --> generate a URL for mentioned endpoint
            confirmation_url=request.url_for(
                "confirm_email", token=create_confirmation_token(user.email)
            ),
        )
    )
    logger.info("User registered successfully", extra={"email": user.email})
    return {"detail": "User created. Please confirm your email."}


# updating to work with swagger UI
@router.post("/token")
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user = await authenticate_user(form_data.username, form_data.password)
    access_token = create_access_token(email=user.email)
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/confirm/{token}", response_model=UserIn)
async def confirm_email(token: str):
    email = get_subject_for_token_type(token, "confirmation")
    query = (
        user_table.update().where(user_table.c.email == email).values(confirmed=True)
    )

    logger.debug(query)
    await database.execute(query)
    return {"details": "User confirmed"}
