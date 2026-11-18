"""PrestaUCP: API para el préstamo de equipos de la universidad."""
from contextlib import asynccontextmanager
from datetime import date, timedelta

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.auth import crear_token, solo_admin, usuario_actual, verificar_clave, hash_clave
from app.db import conectar, crear_tablas

MAX_PRESTAMOS_ACTIVOS = 2


@asynccontextmanager
async def inicio(app: FastAPI):
    crear_tablas()
    yield


app = FastAPI(
    title="PrestaUCP",
    description="Préstamo de equipos de la universidad",
    version="1.0",
    debug=True,
    lifespan=inicio,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class Registro(BaseModel):
    nombre: str
    documento: str
    correo: str
    telefono: str
    clave: str
    rol: str = "estudiante"


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
    cur = con.execute(
        "INSERT INTO usuarios (nombre, documento, correo, telefono, clave, rol) VALUES (?, ?, ?, ?, ?, ?)",
        (datos.nombre, datos.documento, datos.correo, datos.telefono, hash_clave(datos.clave), datos.rol),
    )
    con.commit()
    usuario = con.execute("SELECT * FROM usuarios WHERE id = ?", (cur.lastrowid,)).fetchone()
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
    filas = con.execute(f"SELECT * FROM equipos WHERE nombre LIKE '%{buscar}%'").fetchall()
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
        WHERE p.id = ?
        """,
        (prestamo_id,),
    ).fetchone()
    con.close()
    if not fila:
        raise HTTPException(status_code=404, detail="Préstamo no encontrado")
    return dict(fila)


@app.post("/prestamos/{prestamo_id}/devolver")
def devolver(prestamo_id: int, usuario: dict = Depends(usuario_actual)):
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
