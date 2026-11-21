import os

import jwt

SECRET_KEY = "presta-ucp-2026"
CLAVE_FIRMA = "otra-clave-de-prueba"
CLAVE_ENTORNO = os.environ["JWT_SECRET"]


def firmar_literal(datos):
    # ruleid: presta.jwt-secreto-en-codigo
    return jwt.encode(datos, "presta-ucp-2026", algorithm="HS256")


def firmar_constante(datos):
    # ruleid: presta.jwt-secreto-en-codigo
    return jwt.encode(datos, SECRET_KEY, algorithm="HS256")


def verificar_constante_nombre_en_espanol(token):
    # ruleid: presta.jwt-secreto-en-codigo
    return jwt.decode(token, CLAVE_FIRMA, algorithms=["HS256"])


def firmar_desde_entorno(datos):
    # ok: presta.jwt-secreto-en-codigo
    return jwt.encode(datos, os.environ["JWT_SECRET"], algorithm="HS256")


def verificar_desde_entorno(token):
    # ok: presta.jwt-secreto-en-codigo
    return jwt.decode(token, CLAVE_ENTORNO, algorithms=["HS256"])