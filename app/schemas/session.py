# app/schemas/session.py (VERSÃO CORRIGIDA)

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID # <-- 1. IMPORTE O TIPO UUID
from app.services.db import metadata

active_sessions_table = sa.Table(
    "active_sessions",
    metadata,
    sa.Column("id", sa.Integer, primary_key=True),
    # --- A CORREÇÃO ESTÁ AQUI ---
    # Trocamos sa.Integer por UUID para ser compatível com o 'id' da tabela 'users'
    sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
    # --------------------------
    sa.Column("token_jti", sa.String, nullable=False, unique=True, index=True),
    sa.Column("ip_address", sa.String, nullable=True),
    sa.Column("user_agent", sa.String, nullable=True),
    sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    sa.Column("last_seen_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
)

token_denylist_table = sa.Table(
    "token_denylist",
    metadata,
    sa.Column("id", sa.Integer, primary_key=True),
    sa.Column("jti", sa.String, nullable=False, unique=True, index=True),
    sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
)