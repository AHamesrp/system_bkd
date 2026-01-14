from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert, select
from app.schemas.metrics import metrics_table, MetricIn
from typing import Optional
from datetime import datetime


# Adiciona uma nova métrica
async def add_metric(conn: AsyncSession, metric: MetricIn):
    stmt = (
        insert(metrics_table)
        .values(metric.model_dump(exclude_none=True))
        .returning(metrics_table)
    )
    result = await conn.execute(stmt)
    row = result.mappings().first()
    return _normalize_metric_row(row)


# Lista métricas com filtros opcionais
async def get_metrics(
    conn: AsyncSession,
    user_id: Optional[str] = None,
    event_slug: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
):
    stmt = select(metrics_table)
    if user_id:
        stmt = stmt.where(metrics_table.c.user_id == user_id)
    if event_slug:
        stmt = stmt.where(metrics_table.c.event_slug == event_slug)

    stmt = stmt.order_by(metrics_table.c.created_at.desc()).limit(limit).offset(offset)

    result = await conn.execute(stmt)
    rows = result.mappings().all()
    return [_normalize_metric_row(r) for r in rows]


# Função auxiliar para registrar a métrica
async def track(
    conn: AsyncSession,
    action: str,
    user_id: Optional[str] = None,
    event_slug: Optional[str] = None,
    data: Optional[dict] = None,
):
    metric_payload = MetricIn(
        user_id=user_id, event_slug=event_slug, type=action, data=data
    )
    await add_metric(conn, metric_payload)


# Função interna para converter UUID e datetime → str
def _normalize_metric_row(row):
    if not row:
        return None
    return {
        "id": str(row["id"]),
        "user_id": str(row["user_id"]) if row["user_id"] else None,
        "event_slug": row["event_slug"],
        "type": row["type"],
        "count": row["count"],
        "data": row["data"],
        "created_at": (
            row["created_at"].isoformat()
            if isinstance(row["created_at"], datetime)
            else str(row["created_at"])
        ),
    }
