import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

# Os testes nunca devem rodar contra o banco de desenvolvimento, porque as
# fixtures recriam as tabelas. Usa TEST_DATABASE_URL ou o mesmo servidor do
# .env com o banco "moda_test".
load_dotenv()
url_base = os.getenv("DATABASE_URL", "postgresql://postgres:admin@localhost:5432/moda_db")
url_teste = make_url(os.getenv("TEST_DATABASE_URL") or make_url(url_base).set(database="moda_test"))

admin = create_engine(url_teste.set(database="postgres"), isolation_level="AUTOCOMMIT")
with admin.connect() as conn:
    existe = conn.execute(text("SELECT 1 FROM pg_database WHERE datname = :n"), {"n": url_teste.database}).scalar()
    if not existe:
        conn.execute(text(f'CREATE DATABASE "{url_teste.database}"'))
admin.dispose()

os.environ["DATABASE_URL"] = url_teste.render_as_string(hide_password=False)
os.environ.setdefault("CHROMA_PERSIST_DIRECTORY", "./data/test_chroma")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

import ingestion  # noqa: E402
from database import Base, engine  # noqa: E402
from main import app, get_db  # noqa: E402

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def base_vetorial_indexada():
    ingestion.indexar_no_chromadb(ingestion.carregar_dados_mercado())


@pytest.fixture
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db_session):
    app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
