"""create documents table

Revision ID: a1365da9510f
Revises: 
Create Date: 2026-03-14 15:38:04.099456

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = 'a1365da9510f'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'documents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False, comment='用户ID'),
        sa.Column('source', sa.String(length=50), nullable=True, comment='来源: cninfo/upload/manual'),
        sa.Column('title', sa.String(length=200), nullable=True, comment='展示标题'),
        sa.Column('company', sa.String(length=100), nullable=True, comment='公司'),
        sa.Column('stock_code', sa.String(length=20), nullable=True, comment='股票代码'),
        sa.Column('year', sa.Integer(), nullable=True, comment='年份'),
        sa.Column('pdf_path', sa.String(length=500), nullable=False, comment='PDF相对路径'),
        sa.Column('sha256', sa.String(length=64), nullable=True, comment='文件hash(可选)'),
        sa.Column('created_at', sa.DateTime(), nullable=True, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=True, comment='更新时间'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'pdf_path', name='uq_documents_user_pdf_path')
    )
    op.create_index(op.f('ix_documents_company'), 'documents', ['company'], unique=False)
    op.create_index(op.f('ix_documents_id'), 'documents', ['id'], unique=False)
    op.create_index(op.f('ix_documents_sha256'), 'documents', ['sha256'], unique=False)
    op.create_index(op.f('ix_documents_stock_code'), 'documents', ['stock_code'], unique=False)
    op.create_index(op.f('ix_documents_user_id'), 'documents', ['user_id'], unique=False)
    op.create_index(op.f('ix_documents_year'), 'documents', ['year'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_documents_year'), table_name='documents')
    op.drop_index(op.f('ix_documents_user_id'), table_name='documents')
    op.drop_index(op.f('ix_documents_stock_code'), table_name='documents')
    op.drop_index(op.f('ix_documents_sha256'), table_name='documents')
    op.drop_index(op.f('ix_documents_id'), table_name='documents')
    op.drop_index(op.f('ix_documents_company'), table_name='documents')
    op.drop_table('documents')
