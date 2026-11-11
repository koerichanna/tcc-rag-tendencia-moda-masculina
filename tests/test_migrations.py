import pathlib

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, text

from database import Base, engine

CFG = Config(str(pathlib.Path(__file__).parent.parent / "alembic.ini"))


def _limpar_banco():
    Base.metadata.drop_all(bind=engine)
    with engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS alembic_version"))


def test_migrations_criam_todas_as_tabelas_dos_models():
    _limpar_banco()
    command.upgrade(CFG, "head")

    tabelas = set(inspect(engine).get_table_names())
    assert set(Base.metadata.tables) <= tabelas

    # Falha se algum model foi alterado sem gerar a migration correspondente.
    command.check(CFG)

    command.downgrade(CFG, "base")
    assert not set(Base.metadata.tables) & set(inspect(engine).get_table_names())
    _limpar_banco()
