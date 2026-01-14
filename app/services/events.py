from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update
from app.schemas.event import CreateEventIn, EventOut, events_table, UpdateEventIn
from pydantic import AnyUrl
from typing import List, Optional


# Buscar evento por slug
async def get_event_by_slug(conn: AsyncSession, slug: str) -> Optional[EventOut]:
    stmt = select(events_table).where(events_table.c.slug == slug)
    result = await conn.execute(stmt)
    row = result.mappings().first()
    return EventOut(**row) if row else None


async def create_event(conn: AsyncSession, event_data: CreateEventIn) -> EventOut:
    # ✅ Usar .model_dump() que é o padrão mais novo do Pydantic
    data_dict = event_data.model_dump()

    # Converter campos do tipo Url para str
    for key, value in data_dict.items():
        if isinstance(value, AnyUrl):
            data_dict[key] = str(value)

    # ✅ Garante que os horários não sejam salvos na criação
    data_dict['start_time'] = None
    data_dict['end_time'] = None

    stmt = insert(events_table).values(**data_dict).returning(events_table)
    result = await conn.execute(stmt)
    await conn.commit()
    row = result.mappings().first()
    return EventOut.model_validate(row)  # ✅ Usar .model_validate() para Pydantic v2


# Listar eventos
async def list_events(conn: AsyncSession) -> List[EventOut]:
    stmt = select(events_table)
    result = await conn.execute(stmt)
    rows = result.mappings().all()
    return [EventOut.model_validate(row) for row in rows]


async def update_event(conn: AsyncSession, slug: str, payload: UpdateEventIn) -> Optional[EventOut]:
    """
    Atualiza um evento existente com os dados fornecidos.
    Apenas os campos presentes no payload são atualizados.
    """
    # .model_dump(exclude_unset=True) é crucial para PATCH:
    # ele cria um dicionário apenas com os campos que o cliente enviou.
    update_data = payload.model_dump(exclude_unset=True)

    # Se o payload estiver vazio, não faz nada no banco.
    if not update_data:
        return await get_event_by_slug(conn, slug)

    # Converte a URL para string, se ela foi enviada.
    if 'privacy_url' in update_data and update_data['privacy_url']:
        update_data['privacy_url'] = str(update_data['privacy_url'])

    stmt = (
        update(events_table)
        .where(events_table.c.slug == slug)
        .values(**update_data)
        .returning(events_table)  # Retorna a linha atualizada do banco
    )

    result = await conn.execute(stmt)
    await conn.commit()

    row = result.mappings().first()

    # Se 'row' for None, significa que o evento com aquele slug não foi encontrado.
    return EventOut.model_validate(row) if row else None