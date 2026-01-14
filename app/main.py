# app/main.py (VERSÃO CORRIGIDA E COMPATÍVEL + CORS FIX)

from fastapi import FastAPI, Request, APIRouter, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import update
from sqlalchemy.sql import func
from jose import jwt, JWTError
from prometheus_client import make_asgi_app

from app.settings import settings
from app.logging_conf import configure_logging
from app.services.db import engine, async_session_maker, init_db 
from app.errors import botocore_error_handler, generic_error_handler
from botocore.exceptions import BotoCoreError, ClientError

from app.routes import health, events, ingest, search, admin, privacy, users, metrics, auth, uploads, sessions, \
    users_me, gallery, photos, comments, dowload_link
from app.schemas.session import active_sessions_table
from app.security.jwt import SECRET_KEY, ALGORITHM

# --- Configuração Inicial ---
configure_logging()
app = FastAPI(
    title="Face Event MVP",
    description="API para gerenciamento de eventos e reconhecimento facial.",
    version="1.0.0"
)

# --- Middleware CORS ---
origins = settings.CORS_ALLOW_ORIGINS.split(",") if settings.CORS_ALLOW_ORIGINS != "*" else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://moments-floripasquare.com.br","http://192.168.0.108:3000", "https://www.moments-floripasquare.com.br"],
    allow_credentials = True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Middleware JWT / last_seen ---
@app.middleware("http")
async def update_last_seen_middleware(request: Request, call_next):
    auth_header = request.headers.get("authorization")
    if auth_header and auth_header.lower().startswith("bearer "):
        token = auth_header.split(" ")[1]
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            jti = payload.get("jti")
            if jti:
                async with async_session_maker() as session:
                    async with session.begin():
                        stmt = (
                            update(active_sessions_table)
                            .where(active_sessions_table.c.token_jti == jti)
                            .values(last_seen_at=func.now())
                        )
                        await session.execute(stmt)
        except JWTError:
            pass
    response = await call_next(request)
    return response

# --- Middleware OPTIONS preflight ---
@app.options("/{full_path:path}")
async def preflight_handler(full_path: str):
    return Response(status_code=200)

# --- Eventos de startup/shutdown ---
@app.on_event("startup")
async def on_startup():
    pass

@app.on_event("shutdown")
async def on_shutdown():
    await engine.dispose() 

# --- Prometheus Metrics ---
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# --- Rotas ---
api_router = APIRouter()

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(events.router, prefix="/events", tags=["Events"])
api_router.include_router(search.router, prefix="/search", tags=["Search"])
api_router.include_router(privacy.router, prefix="/privacy", tags=["Privacy"])
api_router.include_router(ingest.router, prefix="/ingest", tags=["Ingest"])
api_router.include_router(uploads.router, prefix="/uploads", tags=["Uploads"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(users_me.router, prefix="/users", tags=["Users Me"])
app.include_router(gallery.router, prefix="/gallery", tags=["Gallery"])
app.include_router(comments.router, prefix="/comments", tags=["Comments"])
app.include_router(dowload_link.router, prefix="/download", tags=["Download"])

app.include_router(photos.router, prefix="/photos", tags=["Photos"])
# Rotas de Administração
admin_router = APIRouter(prefix="/admin")
admin_router.include_router(admin.router, tags=["Admin"])
admin_router.include_router(metrics.router, prefix="/metrics", tags=["Admin Metrics"])
admin_router.include_router(sessions.router, prefix="/sessions", tags=["Admin Sessions"])
api_router.include_router(admin_router)


app.include_router(api_router)

# --- Exception Handlers ---
app.add_exception_handler(BotoCoreError, botocore_error_handler)
app.add_exception_handler(ClientError, botocore_error_handler)
app.add_exception_handler(Exception, generic_error_handler)

