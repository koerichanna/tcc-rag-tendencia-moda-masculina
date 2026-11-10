"""Aplica as migrations pendentes. Roda antes da API subir (ver Dockerfile)."""
import logging
import pathlib

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect

from database import engine

# Revisão que corresponde às tabelas criadas pelo antigo Base.metadata.create_all().
REVISAO_INICIAL = "1cbf7407b813"

logger = logging.getLogger("projeto_moda.migrar")


def aplicar():
    cfg = Config(str(pathlib.Path(__file__).with_name("alembic.ini")))
    tabelas = inspect(engine).get_table_names()

    if "produtos" in tabelas and "alembic_version" not in tabelas:
        # Banco criado antes do Alembic: as tabelas já existem, só registra a versão.
        logger.info("Banco sem controle de versão, marcando como %s", REVISAO_INICIAL)
        command.stamp(cfg, REVISAO_INICIAL)

    command.upgrade(cfg, "head")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    aplicar()
