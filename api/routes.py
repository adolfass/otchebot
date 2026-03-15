"""
Роуты API для работы с заявками.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel, Field
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import verify_api_key, get_db_session
from bot.database.crud import ComplaintCRUD
from bot.database.models import Complaint, ComplaintStatus


router = APIRouter()


# ==================== Pydantic Models ====================


class ProblemResponse(BaseModel):
    """Модель ответа с данными заявки."""

    id: int
    user_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    photo_file_id: Optional[str] = None
    text: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class MarkSentResponse(BaseModel):
    """Модель ответа после пометки заявки."""

    id: int
    status: str


class ProblemsListResponse(BaseModel):
    """Модель ответа со списком заявок."""

    items: List[ProblemResponse]
    total: int
    limit: int
    offset: int


# ==================== Endpoints ====================


@router.get(
    "/problems",
    response_model=ProblemsListResponse,
    summary="Get problems",
    description="Получение списка заявок с фильтрацией и пагинацией",
)
async def get_problems(
    status: str = Query(
        default="new",
        description="Фильтр по статусу (new, sent, processed)",
        pattern="^(new|sent|processed)$",
    ),
    limit: int = Query(
        default=100,
        ge=1,
        le=500,
        description="Максимальное количество записей",
    ),
    offset: int = Query(
        default=0,
        ge=0,
        description="Смещение для пагинации",
    ),
    mark_as_sent: bool = Query(
        default=False,
        description="Автоматически пометить возвращённые заявки как sent",
    ),
    db_session: AsyncSession = Depends(get_db_session),
    api_key: str = Depends(verify_api_key),
):
    """
    Получение списка заявок.

    - **status**: Фильтр по статусу (по умолчанию new)
    - **limit**: Количество записей (1-500)
    - **offset**: Смещение для пагинации
    - **mark_as_sent**: Автоматически пометить как sent
    """
    crud = ComplaintCRUD(db_session)

    # Преобразование статуса
    status_enum = ComplaintStatus(status)

    # Получение заявок
    if status_enum == ComplaintStatus.NEW:
        complaints, total = await crud.get_new(limit=limit, offset=offset)
    else:
        # Для других статусов используем прямой запрос
        from sqlalchemy import select
        from sqlalchemy.ext.asyncio import AsyncSession

        result = await db_session.execute(
            select(Complaint)
            .where(Complaint.status == status_enum)
            .order_by(Complaint.created_at.asc())
            .limit(limit)
            .offset(offset)
        )
        complaints = list(result.scalars().all())

        # Общее количество
        from sqlalchemy import func
        count_result = await db_session.execute(
            select(func.count()).where(Complaint.status == status_enum)
        )
        total = count_result.scalar() or 0

    # Опциональная пометка как sent
    if mark_as_sent and complaints:
        for complaint in complaints:
            if complaint.status == ComplaintStatus.NEW:
                await crud.mark_as_sent(complaint.id)

    return ProblemsListResponse(
        items=complaints,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post(
    "/problems/{problem_id}/mark_sent",
    response_model=MarkSentResponse,
    summary="Mark problem as sent",
    description="Пометка конкретной заявки как отправленной",
)
async def mark_problem_sent(
    problem_id: int,
    db_session: AsyncSession = Depends(get_db_session),
    api_key: str = Depends(verify_api_key),
):
    """
    Пометка заявки как отправленной внешнему агенту.

    - **problem_id**: ID заявки
    """
    crud = ComplaintCRUD(db_session)

    complaint = await crud.mark_as_sent(problem_id)

    if not complaint:
        raise HTTPException(
            status_code=404,
            detail=f"Заявка с ID {problem_id} не найдена",
        )

    return MarkSentResponse(id=complaint.id, status=complaint.status.value)


@router.get(
    "/problems/{problem_id}",
    response_model=ProblemResponse,
    summary="Get problem by ID",
    description="Получение конкретной заявки по ID",
)
async def get_problem(
    problem_id: int,
    db_session: AsyncSession = Depends(get_db_session),
    api_key: str = Depends(verify_api_key),
):
    """
    Получение заявки по ID.

    - **problem_id**: ID заявки
    """
    crud = ComplaintCRUD(db_session)

    complaint = await crud.get_by_id(problem_id)

    if not complaint:
        raise HTTPException(
            status_code=404,
            detail=f"Заявка с ID {problem_id} не найдена",
        )

    return complaint
