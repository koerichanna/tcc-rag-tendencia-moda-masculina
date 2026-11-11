"""perfil e ativo em usuarios

Revision ID: 8d2e5b7c41a9
Revises: 1c43da5a2917
Create Date: 2026-11-10 14:10:42.318204

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '8d2e5b7c41a9'
down_revision: Union[str, Sequence[str], None] = '1c43da5a2917'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('usuarios', sa.Column('perfil', sa.String(length=20), server_default='usuario', nullable=False))
    op.add_column('usuarios', sa.Column('ativo', sa.Boolean(), server_default=sa.true(), nullable=False))
    # Até aqui só existiam usuários criados pelo terminal, pela administradora: viram admin.
    op.execute("UPDATE usuarios SET perfil = 'admin'")


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('usuarios', 'ativo')
    op.drop_column('usuarios', 'perfil')
