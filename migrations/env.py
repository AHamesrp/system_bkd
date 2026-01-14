# migrations/env.py (VERSÃO FINAL CORRIGIDA)

from logging.config import fileConfig
from sqlalchemy import create_engine # Usaremos o create_engine síncrono
from sqlalchemy import pool
from alembic import context
import os
from dotenv import load_dotenv

# --- Adiciona a pasta raiz ao path para encontrar o módulo 'app' ---
import sys
sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__), '..')))


# --- Importe sua metadata centralizada ---
from app.services.db import metadata

# --- Importe TODOS os seus módulos de schema ---

# 1. Usuários
from app.schemas.user import users_table

# 2. Eventos
from app.schemas.event import events_table

# 3. Métricas
from app.schemas.metrics import metrics_table

# 4. Sessões e Token Denylist
from app.schemas.session import active_sessions_table, token_denylist_table

# 5. Fotos (Faltante Anteriormente)
from app.schemas.photo import photos_table

# 6. Comentários (Faltante Anteriormente)
from app.schemas.comments import comments_table

from app.schemas.dowload_link import download_links_table

from app.schemas.media import media_table

# Carrega variáveis do arquivo .env
load_dotenv()

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Define a metadata de destino para o autogenerate
target_metadata = metadata

# Monta a URL do banco a partir das variáveis de ambiente do .env
# Usamos uma versão SÍNCRONA da URL para o Alembic rodar.
DATABASE_URL = os.getenv("DATABASE_URL", "").replace("+asyncpg", "")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL não encontrada no .env")

# Sobrescreve a URL do alembic.ini com a URL construída do .env
config.set_main_option('sqlalchemy.url', DATABASE_URL)


def run_migrations_offline() -> None:
    """Roda migrações em modo 'offline'."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Roda migrações em modo 'online'."""
    # --- A MUDANÇA ESTÁ AQUI ---
    # Em vez de usar engine_from_config, criamos o engine diretamente
    # com a URL que já preparamos. É mais simples e evita o erro.
    connectable = create_engine(
        config.get_main_option("sqlalchemy.url"),
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()