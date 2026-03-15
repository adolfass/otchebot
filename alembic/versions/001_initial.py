"""Initial schema - create complaints table

Revision ID: 001_initial
Revises:
Create Date: 2026-03-15 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Создание enum типа для статусов
    complaint_status = sa.Enum('new', 'sent', 'processed', name='complaint_status')
    complaint_status.create(op.get_bind())

    # Создание таблицы complaints
    op.create_table(
        'complaints',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('username', sa.String(length=255), nullable=True),
        sa.Column('first_name', sa.String(length=255), nullable=True),
        sa.Column('last_name', sa.String(length=255), nullable=True),
        sa.Column('photo_file_id', sa.String(length=512), nullable=True),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('status', complaint_status, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # Создание индексов
    op.create_index(op.f('ix_complaints_status'), 'complaints', ['status'], unique=False)
    op.create_index(op.f('ix_complaints_user_id'), 'complaints', ['user_id'], unique=False)


def downgrade() -> None:
    # Удаление индексов
    op.drop_index(op.f('ix_complaints_user_id'), table_name='complaints')
    op.drop_index(op.f('ix_complaints_status'), table_name='complaints')

    # Удаление таблицы
    op.drop_table('complaints')

    # Удаление enum типа
    complaint_status = sa.Enum('new', 'sent', 'processed', name='complaint_status')
    complaint_status.drop(op.get_bind())
