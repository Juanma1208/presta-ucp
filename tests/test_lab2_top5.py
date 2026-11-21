"""Lab 2 · Pruebas del top 5 del Lab 1 (T1 a T5).

Cada prueba verifica el requisito que se escribió en seguridad/lab1/LAB1.md.
Con el código original fallan; con las correcciones pasan.
"""
from datetime import datetime, timedelta, timezone

import jwt

from tests.conftest import token

SECRETO_VIEJO = "presta-ucp-2026"
SQL_UNION = "' UNION SELECT id, correo, clave, rol FROM usuarios--"


# --- T1 (T-17) · Inyección SQL en la búsqueda · ASVS 1.2.4 ---------------------------

def test_t1_union_no_devuelve_correos_ni_hashes(cliente):
    r = cliente.get("/equipos", params={"buscar": SQL_UNION})
    assert r.status_code == 200
    texto = r.text
    assert "@presta.edu.co" not in texto
    assert "admin" not in texto
    assert r.json() == []


def test_t1_busqueda_con_apostrofo_funciona(cliente):
    r = cliente.get("/equipos", params={"buscar": "D'Ángel"})
    assert r.status_code == 200
    assert r.json() == []


def test_t1_busqueda_normal_sigue_funcionando(cliente):
    r = cliente.get("/equipos", params={"buscar": "Canon"})
    assert [e["nombre"] for e in r.json()] == ["Cámara Canon EOS"]


# --- T2 (T-01) · Asignación masiva del rol · ASVS 15.3.3 -----------------------------

def test_t2_registro_ignora_el_rol_del_cliente(cliente):
    r = cliente.post(
        "/registro",
        json={"nombre": "Intruso", "documento": "222", "correo": "intruso@presta.edu.co",
              "telefono": "301", "clave": "clave1234", "rol": "admin"},
    )
    assert r.status_code == 201
    assert r.json()["rol"] == "estudiante"

    intruso = token(cliente, "intruso@presta.edu.co", "clave1234")
    r = cliente.post("/equipos", json={"nombre": "x", "tipo": "y"}, headers=intruso)
    assert r.status_code == 403


# --- T3 (T-02) · Secreto del JWT en el código y tokens sin exp · ASVS 13.3.1, 9.2.1 ---

def test_t3_token_forjado_con_el_secreto_viejo_es_rechazado(cliente):
    exp = datetime.now(timezone.utc) + timedelta(hours=1)
    forjado = jwt.encode({"sub": "999", "rol": "admin", "exp": exp}, SECRETO_VIEJO, algorithm="HS256")
    r = cliente.post("/equipos", json={"nombre": "x", "tipo": "y"},
                     headers={"Authorization": f"Bearer {forjado}"})
    assert r.status_code == 401


def test_t3_el_token_tiene_exp(cliente, ana):
    datos = jwt.decode(ana["Authorization"].split()[1], options={"verify_signature": False})
    assert "exp" in datos


def test_t3_token_vencido_es_rechazado(cliente):
    from app.auth import ALGORITMO, SECRET_KEY

    vencido = jwt.encode(
        {"sub": "2", "rol": "estudiante", "exp": datetime.now(timezone.utc) - timedelta(minutes=1)},
        SECRET_KEY, algorithm=ALGORITMO,
    )
    r = cliente.get("/me", headers={"Authorization": f"Bearer {vencido}"})
    assert r.status_code == 401


def test_t3_token_sin_exp_es_rechazado(cliente):
    from app.auth import ALGORITMO, SECRET_KEY

    sin_exp = jwt.encode({"sub": "2", "rol": "estudiante"}, SECRET_KEY, algorithm=ALGORITMO)
    r = cliente.get("/me", headers={"Authorization": f"Bearer {sin_exp}"})
    assert r.status_code == 401


# --- T4 (T-07) · BOLA en /prestamos/{id} · ASVS 8.2.2 --------------------------------

def test_t4_ana_no_ve_el_prestamo_de_beto(cliente, ana):
    r = cliente.get("/prestamos/2", headers=ana)
    assert r.status_code == 404
    assert "1088654321" not in r.text
    assert "3207654321" not in r.text


def test_t4_prestamo_ajeno_responde_igual_que_uno_inexistente(cliente, ana):
    ajeno = cliente.get("/prestamos/2", headers=ana)
    inexistente = cliente.get("/prestamos/999", headers=ana)
    assert ajeno.status_code == inexistente.status_code == 404
    assert ajeno.json() == inexistente.json()


def test_t4_ana_sigue_viendo_su_prestamo_y_el_admin_todos(cliente, ana, admin):
    assert cliente.get("/prestamos/1", headers=ana).status_code == 200
    assert cliente.get("/prestamos/2", headers=admin).status_code == 200


# --- T5 (T-08) · Devolver sin rol admin · ASVS 8.3.1 ---------------------------------

def test_t5_un_estudiante_no_puede_devolver(cliente, ana, beto):
    r = cliente.post("/prestamos/2/devolver", headers=beto)
    assert r.status_code == 403
    r = cliente.post("/prestamos/1/devolver", headers=ana)
    assert r.status_code == 403

    equipos = {e["id"]: e for e in cliente.get("/equipos").json()}
    assert equipos[1]["disponible"] == 0
    assert equipos[3]["disponible"] == 0


def test_t5_el_admin_si_puede_devolver(cliente, admin):
    r = cliente.post("/prestamos/2/devolver", headers=admin)
    assert r.status_code == 200
    assert r.json()["estado"] == "devuelto"
