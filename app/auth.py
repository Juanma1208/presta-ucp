"""Contraseñas y tokens de sesión."""
import hashlib

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

SECRET_KEY = "presta-ucp-2026"
ALGORITMO = "HS256"

bearer = HTTPBearer()


def hash_clave(clave: str) -> str:
    return hashlib.md5(clave.encode()).hexdigest()


def verificar_clave(clave: str, hash_guardado: str) -> bool:
    return hash_clave(clave) == hash_guardado


def crear_token(usuario_id: int, rol: str) -> str:
    datos = {"sub": str(usuario_id), "rol": rol}
    return jwt.encode(datos, SECRET_KEY, algorithm=ALGORITMO)


def usuario_actual(credenciales: HTTPAuthorizationCredentials = Depends(bearer)) -> dict:
    try:
        datos = jwt.decode(credenciales.credentials, SECRET_KEY, algorithms=[ALGORITMO])
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")
    return {"id": int(datos["sub"]), "rol": datos["rol"]}


def solo_admin(usuario: dict = Depends(usuario_actual)) -> dict:
    if usuario["rol"] != "admin":
        raise HTTPException(status_code=403, detail="Solo el administrador puede hacer esto")
    return usuario
