import logging
from logging.config import fileConfig

from alembic import context

import models  # noqa: F401  (registra as tabelas no Base.metadata)
from database import Base, engine

config = context.config
# Só configura o logging pelo alembic.ini quando roda pelo comando `alembic`; chamado pela
# aplicação (migrar.py, ingestion.py), mantém a configuração dela.
if config.config_file_name is not None and not logging.getLogger().handlers:
    fileConfig(config.config_file_name, disable_existing_loggers=False)

target_metadata = Base.metadata


def run_migrations_offline():
    # Gera o SQL sem conectar no banco: alembic upgrade head --sql
    context.configure(
        url=engine.url.render_as_string(hide_password=False),
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    # Usa o mesmo engine da aplicação, então vale o DATABASE_URL do ambiente.
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
