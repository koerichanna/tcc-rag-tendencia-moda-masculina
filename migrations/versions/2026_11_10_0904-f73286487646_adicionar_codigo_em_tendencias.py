"""adicionar codigo em tendencias

Revision ID: f73286487646
Revises: 1cbf7407b813
Create Date: 2026-11-10 09:04:26.638866

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'f73286487646'
down_revision: Union[str, Sequence[str], None] = '1cbf7407b813'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Registros que a ingestão antiga gravou só pelo termo. O código permite que a ingestão
# passe a atualizar esses registros em vez de duplicá-los.
CODIGOS_POR_TERMO = {
    "Camisas de Linho e Tecidos Naturais": "trend_linho_01",
    "Calças de Corte Reto e Wide Leg": "trend_wide_leg_02",
    "Desaceleração de Calças Jeans Skinny": "trend_skinny_queda_03",
    "Calças Jeans Skinny": "trend_skinny_queda_03",
    "Paleta de Cores Terrosas e Tons Naturais": "trend_tons_terrosos_04",
    "Camisetas Oversized em Algodão Pesado": "trend_oversized_tee_05",
    "Tênis de Couro Minimalista Branco": "trend_tenis_minimalista_06",
    "Mocassins Penny Loafer e Solado Tratorado": "trend_loafers_mocassim_07",
    "Jaquetas Bomber e Sobretudos Leves": "trend_jaquetas_bomber_08",
    "Bermudas Chino e Alfaiatadas Acima do Joelho": "trend_bermuda_alfaiataria_09",
    "Camisas e Tecidos Tecnológicos Antiamassado": "trend_easy_care_10",
}


def upgrade() -> None:
    op.add_column('tendencias', sa.Column('codigo', sa.String(length=50), nullable=True))
    op.create_unique_constraint('uq_tendencias_codigo', 'tendencias', ['codigo'])

    tendencias = sa.table('tendencias', sa.column('id', sa.Integer), sa.column('termo'), sa.column('codigo'))
    conn = op.get_bind()
    for termo, codigo in CODIGOS_POR_TERMO.items():
        # Se houver duplicados do mesmo termo, só o mais antigo recebe o código.
        primeiro = conn.execute(
            sa.select(sa.func.min(tendencias.c.id)).where(tendencias.c.termo == termo)
        ).scalar()
        ja_usado = conn.execute(
            sa.select(tendencias.c.id).where(tendencias.c.codigo == codigo)
        ).first()
        if primeiro is not None and ja_usado is None:
            conn.execute(tendencias.update().where(tendencias.c.id == primeiro).values(codigo=codigo))


def downgrade() -> None:
    op.drop_constraint('uq_tendencias_codigo', 'tendencias', type_='unique')
    op.drop_column('tendencias', 'codigo')
