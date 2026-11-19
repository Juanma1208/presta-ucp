import os

import pytest
from fastapi.testclient import TestClient

# Secreto solo para las pruebas (la app exige JWT_SECRET de al menos 32 bytes).
os.environ.setdefault("JWT_SECRET", "secreto-de-pruebas-que-no-se-usa-en-produccion")


@pytest.fixture
def cliente(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "prueba.db"))
    from app.main import app

    with TestClient(app) as c:
        yield c


def token(cliente, correo, clave):
    r = cliente.post("/login", json={"correo": correo, "clave": clave})
    return {"Authorization": f"Bearer {r.json()['token']}"}


@pytest.fixture
def ana(cliente):
    return token(cliente, "ana@presta.edu.co", "ana12345")


@pytest.fixture
def admin(cliente):
    return token(cliente, "admin@presta.edu.co", "admin123")


@pytest.fixture
def beto(cliente):
    return token(cliente, "beto@presta.edu.co", "beto12345")
