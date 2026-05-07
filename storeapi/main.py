import logging
from contextlib import asynccontextmanager

import uvicorn
from asgi_correlation_id import CorrelationIdMiddleware
from fastapi import FastAPI, HTTPException
from fastapi.exception_handlers import http_exception_handler

from database import database
from logging_config import configure_logging
from routers.posts import router as posts_router
from routers.upload import router as upload_router
from routers.user import router as user_router

logger = logging.getLogger(__name__)


@asynccontextmanager  # make sure that the lifespan is async and also the code after yield is run when the app is shutting down/crashing
async def lifespan(app: FastAPI):
    configure_logging()  # making sure the log is configured before the app starts
    logger.info("Hello World")
    await database.connect()  # run this when app is ready to run
    yield  # wait
    await database.disconnect()  # run this when app is shutting down


app = FastAPI(
    lifespan=lifespan
)  # lifespan is used to run some code when the app is ready to run and when it is shutting down
app.add_middleware(CorrelationIdMiddleware)  # add the middleware to the app

app.include_router(posts_router)
app.include_router(upload_router)
app.include_router(user_router)


# adding the log and raising proper error msg if we get an error
@app.exception_handler(HTTPException)
async def http_exception_handle_longing(request, exc):
    logger.error(f"HTTPException: {exc.status_code} {exc.detail}")
    return await http_exception_handler(request, exc)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
