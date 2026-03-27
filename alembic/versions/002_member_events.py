"""Create member_events table

Revision ID: 002_member_events
Revises: 001_initial
Create Date: 2026-03-20 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import enum


# revision identifiers, used by Alembic.
revision: str = '002_member_events'
down_revision: Union[str, None] = '001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


class MemberEventType(enum.Enum):
    JOINED = "joined"
    LEFT = "left"


def upgrade() -> None:
    # Создание enum типа для событий
    member_event_type = sa.Enum('joined', 'left', name='member_event_type')
    member_event_type.create(op.get_bind(), checkfirst=True)

    # Создание таблицы member_events
    op.create_table(
        'member_events',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('username', sa.String(length=255), nullable=True),
        sa.Column('first_name', sa.String(length=255), nullable=True),
        sa.Column('event_type', sa.Enum('joined', 'left', name='member_event_type'), nullable=False),
        sa.Column('chat_id', sa.BigInteger(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # Создание индексов
    op.create_index('ix_member_events_user_id', 'member_events', ['user_id'], unique=False)
    op.create_index('ix_member_events_chat_id', 'member_events', ['chat_id'], unique=False)
    op.create_index('ix_member_events_created_at', 'member_events', ['created_at'], unique=False)


def downgrade() -> None:
    # Удаление индексов
    op.drop_index('ix_member_events_created_at', table_name='member_events')
    op.drop_index('ix_member_events_chat_id', table_name='member_events')
    op.drop_index('ix_member_events_user_id', table_name='member_events')

    # Удаление таблицы
    op.drop_table('member_events')

    # Удаление enum типа
    member_event_type = sa.Enum('joined', 'left', name='member_event_type')
    member_event_type.drop(op.get_bind(), checkfirst=True)
