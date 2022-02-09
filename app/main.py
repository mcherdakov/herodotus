from fastapi import FastAPI, Request

from app.db import Database
from auth.api import router as auth_router
from projects.api import router as projects_router
from senders.api import router as senders_router
from users.api import router as users_router


def create_app(use_db: Database | None = None):
    app = FastAPI()
    db = Database() if use_db is None else use_db

    app.include_router(auth_router)
    app.include_router(users_router)
    app.include_router(projects_router)
    app.include_router(senders_router)

    @app.middleware("http")
    async def db_pool_middleware(request: Request, next):
        request.state.pool = db.pool
        return await next(request)

    @app.on_event("startup")
    async def startup():
        await db.create_pool()

    @app.on_event("shutdown")
    async def shutdown():
        await db.close()

    return app
