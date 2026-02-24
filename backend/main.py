from typing import AsyncGenerator

from fastapi import FastAPI
from backend.app.api.v1 import api_router
from backend.app.db.session import init_db
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    await init_db()
    print("🚀 TaskFlow started!")
    yield
    print("👋 TaskFlow stopped!")


app = FastAPI(title="TaskFlow", version="1.0.0", lifespan=lifespan)
app.include_router(api_router)
