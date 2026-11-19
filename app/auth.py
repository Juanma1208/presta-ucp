"""Contraseñas y tokens de sesión."""
import hashlib
import os
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

# T3 (Lab 1) · ASVS 13.3.1: el secreto se lee del entorno, nunca del código.
SECRET_KEY = os.environ.get("JWT_SECRET", "")
if len(SECRET_KEY.encode()) < 32:
    raise RuntimeError("Defina JWT_SECRET con un valor aleatorio de al menos 32 bytes (ver .env.example)")
ALGORITMO = "HS256"
# T3 (Lab 1) · ASVS 9.2.1: los tokens vencen.
DURACION_TOKEN = timedelta(minutes=int(os.environ.get("JWT_MINUTOS", "60")))

bearer = HTTPBearer()


def hash_clave(clave: str) -> str:
    return hashlib.md5(clave.encode()).hexdigest()


def verificar_clave(clave: str, hash_guardado: str) -> bool:
    return hash_clave(clave) == hash_guardado


def crear_token(usuario_id: int, rol: str) -> str:
    datos = {"sub": str(usuario_id), "rol": rol, "exp": datetime.now(timezone.utc) + DURACION_TOKEN}
    return jwt.encode(datos, SECRET_KEY, algorithm=ALGORITMO)


def usuario_actual(credenciales: HTTPAuthorizationCredentials = Depends(bearer)) -> dict:
    try:
        datos = jwt.decode(
            credenciales.credentials, SECRET_KEY, algorithms=[ALGORITMO], options={"require": ["exp", "sub"]}
        )
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")
    return {"id": int(datos["sub"]), "rol": datos["rol"]}


def solo_admin(usuario: dict = Depends(usuario_actual)) -> dict:
    if usuario["rol"] != "admin":
        raise HTTPException(status_code=403, detail="Solo el administrador puede hacer esto")
    return usuario
