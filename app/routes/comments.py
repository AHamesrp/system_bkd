from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, func
from uuid import uuid4
from app.services.db import get_conn
from app.schemas.comments import comments_table, CommentIn, CommentResponse
from app.schemas.user import users_table

router = APIRouter()


# --- Criar um novo comentário ---
@router.post("", response_model=CommentResponse)
async def create_comment(comment: CommentIn, session: AsyncSession = Depends(get_conn)):
    new_id = uuid4()

    await session.execute(
        insert(comments_table).values(
            id=new_id,
            user_id=comment.user_id,
            event_slug=comment.event_slug,
            comment=comment.comment,
        )
    )
    await session.commit()

    result = await session.execute(
        select(comments_table).where(comments_table.c.id == new_id)
    )
    created_comment = result.fetchone()

    if not created_comment:
        raise HTTPException(status_code=500, detail="Erro ao criar comentário")

    return CommentResponse(**created_comment._mapping)


# --- Listar comentários de um evento com nome + sobrenome do usuário ---
@router.get("/{event_slug}", response_model=list[CommentResponse])
async def list_comments(event_slug: str, session: AsyncSession = Depends(get_conn)):
    result = await session.execute(
        select(
            comments_table.c.id,
            comments_table.c.user_id,
            comments_table.c.event_slug,
            comments_table.c.comment,
            comments_table.c.created_at,
            func.concat(users_table.c.name, ' ', users_table.c.last_name).label("user_full_name"),
            users_table.c.instagram.label("user_instagram"),
        )
        .join(users_table, users_table.c.id == comments_table.c.user_id)
        .where(comments_table.c.event_slug == event_slug)
        .order_by(comments_table.c.created_at.desc())
    )

    comments = result.fetchall()
    return [CommentResponse(**c._mapping) for c in comments]
