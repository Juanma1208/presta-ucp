import pytest
from fastapi.testclient import TestClient


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
