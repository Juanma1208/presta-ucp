"""PrestaUCP: API para el préstamo de equipos de la universidad."""
import os
import sqlite3
from contextlib import asynccontextmanager
from datetime import date, timedelta
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.auth import crear_token, solo_admin, usuario_actual, verificar_clave, hash_clave
from app.db import conectar, crear_tablas

MAX_PRESTAMOS_ACTIVOS = 2
ESTATICOS = Path(__file__).parent / "static"


@asynccontextmanager
async def inicio(app: FastAPI):
    crear_tablas()
    yield


# Fila 19 · ASVS 13.4.2: debug apagado (sin trazas al cliente). /docs se sirve aparte (ver abajo)
# y /redoc se desactiva porque carga scripts de un CDN.
app = FastAPI(
    title="PrestaUCP",
    description="Préstamo de equipos de la universidad",
    version="1.0",
    debug=False,
    docs_url=None,
    redoc_url=None,
    lifespan=inicio,
)
app.mount("/static", StaticFiles(directory=ESTATICOS), name="static")

# Fila 19 · CORS con lista blanca. Por defecto ningún otro origen puede llamar a la API desde
# un navegador; los orígenes permitidos se configuran en CORS_ORIGENES (separados por comas).
ORIGENES = [o.strip() for o in os.environ.get("CORS_ORIGENES", "").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGENES,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)

# Fila 19 · ASVS 3.4.x: cabeceras de seguridad en todas las respuestas.
CSP_API = "default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'"
CSP_DOCS = (
    "default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self' data:; "
    "connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'"
)


@app.middleware("http")
async def cabeceras_de_seguridad(request: Request, call_next):
    respuesta = await call_next(request)
    ruta = request.url.path
    h = respuesta.headers
    h["Content-Security-Policy"] = CSP_DOCS if ruta == "/docs" else CSP_API
    h["X-Content-Type-Options"] = "nosniff"
    h["X-Frame-Options"] = "DENY"
    h["Referrer-Policy"] = "no-referrer"
    h["Permissions-Policy"] = "camera=(), microphone=(), geolocation=(), payment=()"
    h["Cross-Origin-Opener-Policy"] = "same-origin"
    h["Cross-Origin-Resource-Policy"] = "same-origin"
    h["Cross-Origin-Embedder-Policy"] = "require-corp"
    if not ruta.startswith("/static/"):
        h["Cache-Control"] = "no-store"
    return respuesta


DOCS_HTML = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>PrestaUCP - Swagger UI</title>
<link rel="stylesheet" href="/static/swagger/swagger-ui.css">
<link rel="icon" type="image/png" href="/static/swagger/favicon-32x32.png">
</head>
<body>
<div id="swagger-ui"></div>
<script src="/static/swagger/swagger-ui-bundle.js"></script>
<script src="/static/swagger/docs-init.js"></script>
</body>
</html>
"""


# Swagger UI servido desde la propia app (sin CDN ni JavaScript en línea): así /docs no carga
# scripts de otro dominio (ZAP 90003 y 10017) y la CSP puede ser script-src 'self'.
@app.get("/docs", include_in_schema=False)
def documentacion():
    return HTMLResponse(DOCS_HTML)


class Registro(BaseModel):
    nombre: str
    documento: str
    correo: str
    telefono: str
    clave: str


class Login(BaseModel):
    correo: str
    clave: str


class EquipoNuevo(BaseModel):
    nombre: str
    tipo: str


class PrestamoNuevo(BaseModel):
    equipo_id: int
    dias: int = 3


@app.get("/salud")
def salud():
    return {"estado": "ok"}


# ----------------------------- Usuarios -----------------------------

@app.post("/registro", status_code=201)
def registrar(datos: Registro):
    con = conectar()
    # La conexión se cierra siempre, también si el INSERT falla. Antes quedaba abierta y la base
    # se bloqueaba («database is locked», 364 errores durante el escaneo de ZAP).
    try:
        cur = con.execute(
            "INSERT INTO usuarios (nombre, documento, correo, telefono, clave, rol) VALUES (?, ?, ?, ?, ?, ?)",
            # T2 (Lab 1) · ASVS 15.3.3: toda cuenta nueva es estudiante; el rol no viene del cliente.
            (datos.nombre, datos.documento, datos.correo, datos.telefono, hash_clave(datos.clave), "estudiante"),
        )
        con.commit()
        usuario = con.execute("SELECT * FROM usuarios WHERE id = ?", (cur.lastrowid,)).fetchone()
    except sqlite3.IntegrityError:
        con.rollback()
        raise HTTPException(status_code=409, detail="El correo o el documento ya están registrados")
    finally:
        con.close()
    return dict(usuario)


@app.post("/login")
def login(datos: Login):
    con = conectar()
    usuario = con.execute("SELECT * FROM usuarios WHERE correo = ?", (datos.correo,)).fetchone()
    con.close()
    if not usuario:
        raise HTTPException(status_code=404, detail="El usuario no existe")
    if not verificar_clave(datos.clave, usuario["clave"]):
        raise HTTPException(status_code=401, detail="Contraseña incorrecta")
    return {"token": crear_token(usuario["id"], usuario["rol"]), "rol": usuario["rol"]}


@app.get("/me")
def mis_datos(usuario: dict = Depends(usuario_actual)):
    con = conectar()
    fila = con.execute(
        "SELECT id, nombre, documento, correo, telefono, rol FROM usuarios WHERE id = ?", (usuario["id"],)
    ).fetchone()
    con.close()
    return dict(fila)


# ----------------------------- Equipos -----------------------------

@app.get("/equipos")
def listar_equipos(buscar: str = ""):
    con = conectar()
    # T1 (Lab 1) · ASVS 1.2.4: consulta parametrizada; el % va dentro del parámetro.
    filas = con.execute("SELECT * FROM equipos WHERE nombre LIKE ?", (f"%{buscar}%",)).fetchall()
    con.close()
    return [dict(f) for f in filas]


@app.post("/equipos", status_code=201)
def crear_equipo(datos: EquipoNuevo, admin: dict = Depends(solo_admin)):
    con = conectar()
    cur = con.execute("INSERT INTO equipos (nombre, tipo) VALUES (?, ?)", (datos.nombre, datos.tipo))
    con.commit()
    con.close()
    return {"id": cur.lastrowid, "nombre": datos.nombre, "tipo": datos.tipo, "disponible": 1}


# ----------------------------- Préstamos -----------------------------

@app.post("/prestamos", status_code=201)
def pedir_prestamo(datos: PrestamoNuevo, usuario: dict = Depends(usuario_actual)):
    con = conectar()
    equipo = con.execute("SELECT * FROM equipos WHERE id = ?", (datos.equipo_id,)).fetchone()
    if not equipo:
        con.close()
        raise HTTPException(status_code=404, detail="El equipo no existe")
    if not equipo["disponible"]:
        con.close()
        raise HTTPException(status_code=409, detail="El equipo ya está prestado")

    activos = con.execute(
        "SELECT COUNT(*) FROM prestamos WHERE usuario_id = ? AND estado = 'activo'", (usuario["id"],)
    ).fetchone()[0]
    if activos >= MAX_PRESTAMOS_ACTIVOS:
        con.close()
        raise HTTPException(status_code=400, detail=f"Máximo {MAX_PRESTAMOS_ACTIVOS} préstamos activos")

    hoy = date.today()
    limite = hoy + timedelta(days=datos.dias)
    cur = con.execute(
        "INSERT INTO prestamos (usuario_id, equipo_id, fecha_inicio, fecha_limite) VALUES (?, ?, ?, ?)",
        (usuario["id"], datos.equipo_id, hoy.isoformat(), limite.isoformat()),
    )
    con.execute("UPDATE equipos SET disponible = 0 WHERE id = ?", (datos.equipo_id,))
    con.commit()
    con.close()
    return {"id": cur.lastrowid, "equipo_id": datos.equipo_id, "fecha_limite": limite.isoformat(), "estado": "activo"}


@app.get("/prestamos")
def mis_prestamos(usuario: dict = Depends(usuario_actual)):
    con = conectar()
    if usuario["rol"] == "admin":
        filas = con.execute("SELECT * FROM prestamos").fetchall()
    else:
        filas = con.execute("SELECT * FROM prestamos WHERE usuario_id = ?", (usuario["id"],)).fetchall()
    con.close()
    return [dict(f) for f in filas]


@app.get("/prestamos/{prestamo_id}")
def ver_prestamo(prestamo_id: int, usuario: dict = Depends(usuario_actual)):
    con = conectar()
    fila = con.execute(
        """
        SELECT p.id, p.estado, p.fecha_inicio, p.fecha_limite,
               e.nombre AS equipo, u.nombre AS usuario, u.documento, u.correo, u.telefono
        FROM prestamos p
        JOIN equipos e ON e.id = p.equipo_id
        JOIN usuarios u ON u.id = p.usuario_id
        WHERE p.id = ? AND (p.usuario_id = ? OR ? = 'admin')
        """,
        # T4 (Lab 1) · ASVS 8.2.2: solo el dueño (o el admin) ve el préstamo.
        (prestamo_id, usuario["id"], usuario["rol"]),
    ).fetchone()
    con.close()
    if not fila:
        raise HTTPException(status_code=404, detail="Préstamo no encontrado")
    return dict(fila)


@app.post("/prestamos/{prestamo_id}/devolver")
def devolver(prestamo_id: int, admin: dict = Depends(solo_admin)):  # T5 (Lab 1) · ASVS 8.3.1
    con = conectar()
    prestamo = con.execute("SELECT * FROM prestamos WHERE id = ?", (prestamo_id,)).fetchone()
    if not prestamo:
        con.close()
        raise HTTPException(status_code=404, detail="Préstamo no encontrado")
    if prestamo["estado"] != "activo":
        con.close()
        raise HTTPException(status_code=400, detail="El préstamo ya fue devuelto")
    con.execute("UPDATE prestamos SET estado = 'devuelto' WHERE id = ?", (prestamo_id,))
    con.execute("UPDATE equipos SET disponible = 1 WHERE id = ?", (prestamo["equipo_id"],))
    con.commit()
    con.close()
    return {"id": prestamo_id, "estado": "devuelto"}
