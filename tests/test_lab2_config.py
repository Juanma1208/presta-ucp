"""Lab 2 · Pruebas de los hallazgos de Semgrep y ZAP (filas 2 y 19 de ASVS).

Con el código anterior fallan; con las correcciones pasan.
"""
from pathlib import Path

from tests.conftest import token

RAIZ = Path(__file__).resolve().parent.parent
NUEVO = {"nombre": "Carla Ruiz", "documento": "1088000111", "correo": "carla@presta.edu.co",
         "telefono": "3150000000", "clave": "carla2026"}


# --- Fila 2 · ASVS 11.4.2: hash lento y con sal (Semgrep insecure-hash-algorithm-md5) ---

def test_fila2_la_clave_no_se_guarda_con_md5():
    from app.auth import hash_clave

    h = hash_clave("1")
    assert h != "c4ca4238a0b923820dcc509a6f75849b"
    assert h.startswith("pbkdf2_sha256$")


def test_fila2_la_misma_clave_da_hashes_distintos_por_la_sal():
    from app.auth import hash_clave, verificar_clave

    a, b = hash_clave("ana12345"), hash_clave("ana12345")
    assert a != b
    assert verificar_clave("ana12345", a) and verificar_clave("ana12345", b)
    assert not verificar_clave("otra", a)


def test_fila2_el_login_sigue_funcionando(cliente):
    cliente.post("/registro", json=NUEVO)
    r = cliente.post("/login", json={"correo": NUEVO["correo"], "clave": NUEVO["clave"]})
    assert r.status_code == 200


# --- Fila 19 · CORS con lista blanca (Semgrep wildcard-cors) ---------------------------

def test_fila19_cors_no_acepta_un_origen_cualquiera(cliente):
    r = cliente.get("/salud", headers={"Origin": "https://malo.example"})
    assert "access-control-allow-origin" not in r.headers


# --- Fila 19 · Cabeceras de seguridad (ZAP 10020, 10021, 10038, 10063, 90004) ----------

def test_fila19_cabeceras_de_seguridad_en_la_api(cliente):
    h = cliente.get("/salud").headers
    assert h["x-content-type-options"] == "nosniff"
    assert h["x-frame-options"] == "DENY"
    assert "frame-ancestors 'none'" in h["content-security-policy"]
    assert "default-src 'none'" in h["content-security-policy"]
    assert "permissions-policy" in h
    assert h["cross-origin-resource-policy"] == "same-origin"


def test_fila19_las_respuestas_con_datos_personales_no_se_guardan_en_cache(cliente, ana):
    assert cliente.get("/me", headers=ana).headers["cache-control"] == "no-store"


def test_fila19_docs_funciona_sin_scripts_de_otro_dominio(cliente):
    r = cliente.get("/docs")
    assert r.status_code == 200
    assert "swagger-ui" in r.text
    assert "cdn.jsdelivr.net" not in r.text          # ZAP 90003 (SRI) y 10017
    assert "<script>" not in r.text                   # sin JavaScript en línea
    csp = r.headers["content-security-policy"]
    assert "script-src 'self'" in csp and "unsafe-inline" not in csp
    assert cliente.get("/static/swagger/swagger-ui-bundle.js").status_code == 200


# --- Fila 19 · ASVS 13.4.2: debug apagado, sin trazas al usuario -----------------------

def test_fila19_debug_apagado():
    from app.main import app

    assert app.debug is False


def test_fila19_correo_repetido_responde_409_sin_traza(cliente):
    r = cliente.post("/registro", json={**NUEVO, "correo": "ana@presta.edu.co"})
    assert r.status_code == 409
    assert "Traceback" not in r.text
    assert "sqlite3" not in r.text


def test_fila19_tras_un_error_la_base_no_queda_bloqueada(cliente):
    for _ in range(3):
        cliente.post("/registro", json={**NUEVO, "correo": "ana@presta.edu.co"})
    r = cliente.post("/registro", json=NUEVO)
    assert r.status_code == 201


# --- Fila 19 · Semgrep missing-user: el contenedor no corre como root ------------------

def test_fila19_dockerfile_usa_un_usuario_sin_privilegios():
    lineas = [l.strip() for l in (RAIZ / "Dockerfile").read_text().splitlines() if l.strip()]
    usuarios = [l.split()[1] for l in lineas if l.startswith("USER ")]
    assert usuarios and usuarios[-1] not in ("root", "0")
