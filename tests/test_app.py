"""Pruebas de funcionamiento de PrestaUCP."""


def test_salud(cliente):
    assert cliente.get("/salud").json() == {"estado": "ok"}


def test_registro_y_login(cliente):
    r = cliente.post(
        "/registro",
        json={"nombre": "Carla Ruiz", "documento": "1088000111", "correo": "carla@presta.edu.co",
              "telefono": "3150000000", "clave": "carla2026"},
    )
    assert r.status_code == 201
    assert r.json()["rol"] == "estudiante"

    r = cliente.post("/login", json={"correo": "carla@presta.edu.co", "clave": "carla2026"})
    assert r.status_code == 200
    assert "token" in r.json()


def test_login_con_clave_incorrecta(cliente):
    r = cliente.post("/login", json={"correo": "ana@presta.edu.co", "clave": "otra"})
    assert r.status_code == 401


def test_mis_datos(cliente, ana):
    r = cliente.get("/me", headers=ana)
    assert r.status_code == 200
    assert r.json()["correo"] == "ana@presta.edu.co"


def test_listar_y_buscar_equipos(cliente):
    assert len(cliente.get("/equipos").json()) == 5
    r = cliente.get("/equipos?buscar=Canon")
    assert [e["nombre"] for e in r.json()] == ["Cámara Canon EOS"]


def test_solo_el_admin_crea_equipos(cliente, ana, admin):
    nuevo = {"nombre": "Micrófono Rode", "tipo": "audio"}
    assert cliente.post("/equipos", json=nuevo, headers=ana).status_code == 403
    assert cliente.post("/equipos", json=nuevo, headers=admin).status_code == 201


def test_pedir_prestamo(cliente, ana):
    r = cliente.post("/prestamos", json={"equipo_id": 2}, headers=ana)
    assert r.status_code == 201
    assert r.json()["estado"] == "activo"
    equipos = {e["id"]: e for e in cliente.get("/equipos").json()}
    assert equipos[2]["disponible"] == 0


def test_no_se_presta_un_equipo_ocupado(cliente, ana):
    r = cliente.post("/prestamos", json={"equipo_id": 3}, headers=ana)
    assert r.status_code == 409


def test_maximo_dos_prestamos_activos(cliente, ana):
    assert cliente.post("/prestamos", json={"equipo_id": 2}, headers=ana).status_code == 201
    r = cliente.post("/prestamos", json={"equipo_id": 4}, headers=ana)
    assert r.status_code == 400


def test_mis_prestamos(cliente, ana):
    prestamos = cliente.get("/prestamos", headers=ana).json()
    assert len(prestamos) == 1 and prestamos[0]["usuario_id"] == 2


def test_ver_mi_prestamo(cliente, ana):
    r = cliente.get("/prestamos/1", headers=ana)
    assert r.status_code == 200
    assert r.json()["usuario"] == "Ana Gómez"


def test_devolver_prestamo(cliente, ana, admin):
    r = cliente.post("/prestamos/1/devolver", headers=admin)
    assert r.status_code == 200
    assert r.json()["estado"] == "devuelto"
    equipos = {e["id"]: e for e in cliente.get("/equipos").json()}
    assert equipos[1]["disponible"] == 1


def test_sin_token_no_hay_acceso(cliente):
    assert cliente.get("/prestamos").status_code in (401, 403)
