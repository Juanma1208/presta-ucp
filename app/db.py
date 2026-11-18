"""Conexión a la base de datos SQLite y datos iniciales."""
import os
import sqlite3

from app.auth import hash_clave


def ruta_db():
    return os.environ.get("DB_PATH", "presta.db")


def conectar():
    con = sqlite3.connect(ruta_db())
    con.row_factory = sqlite3.Row
    return con


def crear_tablas():
    con = conectar()
    con.executescript(
        """
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            documento TEXT NOT NULL,
            correo TEXT NOT NULL UNIQUE,
            telefono TEXT,
            clave TEXT NOT NULL,
            rol TEXT NOT NULL DEFAULT 'estudiante'
        );

        CREATE TABLE IF NOT EXISTS equipos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            tipo TEXT NOT NULL,
            disponible INTEGER NOT NULL DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS prestamos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL REFERENCES usuarios(id),
            equipo_id INTEGER NOT NULL REFERENCES equipos(id),
            fecha_inicio TEXT NOT NULL,
            fecha_limite TEXT NOT NULL,
            estado TEXT NOT NULL DEFAULT 'activo'
        );
        """
    )

    # Datos de prueba solo si la base está vacía
    if con.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0] == 0:
        usuarios = [
            ("Administrador", "1000000000", "admin@presta.edu.co", "3000000000", "admin123", "admin"),
            ("Ana Gómez", "1088123456", "ana@presta.edu.co", "3101234567", "ana12345", "estudiante"),
            ("Beto Ríos", "1088654321", "beto@presta.edu.co", "3207654321", "beto12345", "estudiante"),
        ]
        for nombre, documento, correo, telefono, clave, rol in usuarios:
            con.execute(
                "INSERT INTO usuarios (nombre, documento, correo, telefono, clave, rol) VALUES (?, ?, ?, ?, ?, ?)",
                (nombre, documento, correo, telefono, hash_clave(clave), rol),
            )

        equipos = [
            ("Portátil Lenovo ThinkPad", "portatil"),
            ("Portátil Dell Latitude", "portatil"),
            ("Cámara Canon EOS", "camara"),
            ("Proyector Epson", "proyector"),
            ("Tablet Samsung", "tablet"),
        ]
        con.executemany("INSERT INTO equipos (nombre, tipo) VALUES (?, ?)", equipos)

        # Un préstamo activo para cada estudiante
        con.execute(
            "INSERT INTO prestamos (usuario_id, equipo_id, fecha_inicio, fecha_limite) "
            "VALUES (2, 1, '2026-11-16', '2026-11-19')"
        )
        con.execute(
            "INSERT INTO prestamos (usuario_id, equipo_id, fecha_inicio, fecha_limite) "
            "VALUES (3, 3, '2026-11-16', '2026-11-18')"
        )
        con.execute("UPDATE equipos SET disponible = 0 WHERE id IN (1, 3)")

    con.commit()
    con.close()
