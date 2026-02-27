from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1 import api_router
from app.db.session import init_db


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    await init_db()
    print("TaskFlow started!")
    yield
    print("TaskFlow stopped!")


app = FastAPI(title="TaskFlow", version="1.0.0", lifespan=lifespan)
app.include_router(api_router)
