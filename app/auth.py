"""Contraseñas y tokens de sesión."""
import hashlib
import hmac
import os
import secrets
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


# Fila 2 · ASVS 11.4.2: hash lento y con sal. PBKDF2-HMAC-SHA256 con 600.000 iteraciones
# (valor recomendado por OWASP) y una sal aleatoria de 16 bytes por contraseña.
ITERACIONES = int(os.environ.get("PBKDF2_ITERACIONES", "600000"))


def hash_clave(clave: str) -> str:
    sal = secrets.token_bytes(16)
    resumen = hashlib.pbkdf2_hmac("sha256", clave.encode(), sal, ITERACIONES)
    return f"pbkdf2_sha256${ITERACIONES}${sal.hex()}${resumen.hex()}"


def verificar_clave(clave: str, hash_guardado: str) -> bool:
    try:
        algoritmo, iteraciones, sal, resumen = hash_guardado.split("$")
    except ValueError:
        return False
    if algoritmo != "pbkdf2_sha256":
        return False
    calculado = hashlib.pbkdf2_hmac("sha256", clave.encode(), bytes.fromhex(sal), int(iteraciones))
    return hmac.compare_digest(calculado.hex(), resumen)


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
