"""vinculo produto tendencia

Revision ID: 5b9f1e2a7c3d
Revises: 8d2e5b7c41a9
Create Date: 2026-11-11 09:15:08.402117

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '5b9f1e2a7c3d'
down_revision: Union[str, Sequence[str], None] = '8d2e5b7c41a9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('produtos', sa.Column('tendencia_codigo', sa.String(length=50), nullable=True))
    op.create_index(op.f('ix_produtos_tendencia_codigo'), 'produtos', ['tendencia_codigo'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_produtos_tendencia_codigo'), table_name='produtos')
    op.drop_column('produtos', 'tendencia_codigo')
