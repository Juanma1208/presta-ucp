# Lab 2 · Verificación ASVS 5.0 · PrestaUCP (estado inicial)

- **Aplicación:** PrestaUCP (FastAPI + SQLite + PyJWT), el proyecto del equipo. Corre en `127.0.0.1:8000` con `docker compose up -d --build`.
- **Referencias:** las rutas `app/...:N` son relativas a la raíz del repositorio. Los logs están en `antes/evidencias/` y se citan como `ev`.
- **Niveles:** cada requisito lleva su nivel de ASVS 5.0 entre paréntesis. Esta tabla describe la app **antes** de cualquier corrección.

| # | Capítulo | Qué verificar | Requisito ASVS | Estado | Evidencia |
|---|---|---|---|---|---|
| 1 | V6 Autenticación | Contraseñas de mínimo 8 caracteres, sin reglas de composición, contra una lista de comunes | 6.2.1, 6.2.4 (L1) | No cumple | El registro acepta la contraseña «1» (`ev/curl.txt`). No hay validación de longitud (`app/main.py:69`) |
| 2 | V6 / V11 | Contraseñas con un hash lento y con sal (Argon2id, bcrypt, scrypt, PBKDF2) | 11.4.2 (L2) | No cumple | `hash_clave` usa `hashlib.md5` sin sal (`app/auth.py:15`). Semgrep lo marca como `insecure-hash-algorithm-md5` |
| 3 | V6 | Límite de intentos o protección contra fuerza bruta en el login | 6.3.1 (L1) | No cumple | 12 logins fallidos seguidos dan 12 respuestas 401 y ningún 429 (`ev/curl.txt`). `login` no cuenta intentos (`app/main.py:82`) |
| 4 | V6 | El login y la recuperación no revelan si el usuario existe | 6.3.8 (L3) | No cumple | Un correo inexistente da 404 «El usuario no existe» y un correo real con clave mala da 401 (`app/main.py:86-89`, `ev/curl.txt`) |
| 5 | V7 Sesiones | La sesión expira y el cierre de sesión la invalida en el servidor | 7.2.2, 7.4.1 (L1) | No cumple | El token no tiene `exp` (`app/auth.py:22-24`) y no hay logout. Un token sirve para siempre |
| 6 | V7 | Cookie de sesión con `Secure`, `HttpOnly` y `SameSite` (si usan cookies) | 3.3.1 (L1) | No aplica | La API no usa cookies: la sesión va en la cabecera `Authorization` |
| 7 | V9 Tokens | La firma del token se verifica con una lista fija de algoritmos | 9.1.2 (L1) | Cumple en parte | `jwt.decode` fija `algorithms=["HS256"]` (`app/auth.py:29`), pero el secreto está en el código (ver fila 17), así que la firma no protege nada |
| 8 | V9 | El token tiene `exp`, y se validan emisor y audiencia | 9.2.1 (L1) | No cumple | El token solo tiene `sub` y `rol`, sin `exp` ni `aud` (`ev/curl.txt`) |
| 9 | V8 Autorización | Cada consulta a un objeto filtra por el dueño o por el permiso (BOLA) | 8.2.2 (L1) | No cumple | `ver_prestamo` consulta solo por `id` (`app/main.py:166-182`). Ana obtiene el préstamo de Beto con su documento, correo y teléfono (`ev/curl.txt`) |
| 10 | V8 | Los campos sensibles (rol, saldo, estado) no se pueden escribir desde el cliente | 15.3.3 (L2) | No cumple | El registro acepta `"rol": "admin"` (`app/main.py:43`, `app/main.py:69`). La cuenta nueva queda como admin (`ev/curl.txt`) |
| 11 | V8 | La autorización se aplica en el servidor, no solo ocultando botones | 8.3.1 (L1) | No cumple | `devolver` solo exige token, no el rol admin (`app/main.py:186`). Beto marca como devuelto el préstamo de otro (`ev/curl.txt`) |
| 12 | V4 APIs | Las respuestas no devuelven más campos de los necesarios | 15.3.1 (L1) | No cumple | `registrar` devuelve la fila completa, incluido el hash de la contraseña (`app/main.py:77-78`, `ev/curl.txt`) |
| 13 | V4 / V2 | Paginación con límite máximo; límites de tamaño en las peticiones | 2.4.1 (L2), 2.2.1 (L1) | No cumple | `/equipos` devuelve todas las filas (`app/main.py:106-109`), sin paginación ni límite de tamaño (amenaza T-12 del Lab 1). Además, el servidor no aplica la regla de negocio de máximo 3 días (2.2.1): `PrestamoNuevo` acepta cualquier `dias` (`app/main.py:58`) y `pedir_prestamo` lo usa tal cual (`app/main.py:143`). Ana pide un préstamo con `"dias": 365` y recibe `"fecha_limite":"2027-11-19"` (`ev/curl.txt`, amenaza T-09 del Lab 1) |
| 14 | V1 Codificación | Consultas parametrizadas en todo acceso a datos | 1.2.4 (L1) | No cumple | `listar_equipos` arma el SQL con un f-string (`app/main.py:108`). Un `UNION` devuelve correos, hashes y roles (`ev/curl.txt`) |
| 15 | V1 | Salida escapada según el contexto (HTML, JS, URL) | 1.2.1 (L1) | No aplica | La API solo devuelve JSON, que FastAPI serializa y escapa. No arma HTML |
| 16 | V11 Criptografía | Datos sensibles en reposo con cifrado autenticado (o justificación) | 11.3.2 (L1) | No cumple | El documento, el correo y el teléfono se guardan en texto plano en `presta.db` (`app/db.py`) |
| 17 | V11 / V13 | Ninguna llave, secreto o contraseña en el código ni en el historial de git | 13.3.1 (L2) | No cumple | `SECRET_KEY = "presta-ucp-2026"` está en el código (`app/auth.py:8`) y en el historial. Un token forjado con ese secreto es aceptado como admin (`ev/curl.txt`). Semgrep: `jwt-python-hardcoded-secret` |
| 18 | V12 Comunicación | TLS en todo tráfico externo; HSTS en producción | 12.2.1 (L1) | No cumple | Solo HTTP (uvicorn en el puerto 8000, `docker-compose.yml`), sin TLS ni HSTS |
| 19 | V13 Configuración | Debug apagado, sin trazas al usuario, cabeceras de seguridad | 13.4.2, 3.4.x (L2) | No cumple | `FastAPI(debug=True)` (`app/main.py:25`): un error devuelve la traza de Python. CORS con `allow_origins=["*"]` (`app/main.py:31`). Sin CSP ni `nosniff` (`ev/curl.txt`) |
| 20 | V16 Registro | Se registran los fallos de autenticación y de autorización, sin datos sensibles | 16.3.1, 16.3.2 (L2) | No cumple | Solo existe el log de acceso de uvicorn, sin el usuario. Los 401 y los accesos a objetos ajenos no se registran como eventos de seguridad |
| 21 | Lab 1 · T1 | Inyección SQL en `/equipos?buscar=`: consultas parametrizadas | 1.2.4 (L1) | No cumple | Igual que la fila 14 (`app/main.py:108`) |
| 22 | Lab 1 · T2 | Asignación masiva: el registro ignora el rol que envía el cliente | 15.3.3 (L2) | No cumple | Igual que la fila 10 (`app/main.py:43`, `app/main.py:69`) |
| 23 | Lab 1 · T3 | Secreto del JWT fuera del código y tokens con `exp` | 13.3.1, 9.2.1 | No cumple | Igual que las filas 8 y 17 (`app/auth.py:8`, `app/auth.py:22`) |
| 24 | Lab 1 · T4 | BOLA en `/prestamos/{id}`: filtrar por el dueño | 8.2.2 (L1) | No cumple | Igual que la fila 9 (`app/main.py:166`) |
| 25 | Lab 1 · T5 | Devolver exige el rol admin | 8.3.1 (L1) | No cumple | Igual que la fila 11 (`app/main.py:186`) |

**Resumen del estado inicial:** 0 Cumple · 1 Cumple en parte · 2 No aplica · 22 No cumple.

## Estado después de las correcciones

> Pendiente: se completa en la etapa «después». La tabla tendrá las columnas `# · Requisito · Antes · Después · Control y evidencia`, con una fila por cada requisito que cambie. El antes y el después se obtienen con los mismos comandos (`antes/evidencias/curl.txt` y `despues/evidencias/curl.txt`, generados con `verificar.sh`).

## ¿Se hizo un buen trabajo? (sección 5)

1. **Cumplimiento.** La versión revisada no cumple **ninguno de los 25** requisitos. Una fila cumple en parte (7: el algoritmo del JWT está fijo, pero el secreto está en el código), 2 no aplican (6 y 15) y 22 no se cumplen. *Pendiente: cuántos cumple después del PR y qué queda como riesgo residual.*
2. **Lo que solo encontró la revisión humana.** BOLA en `/prestamos/{id}` (Ana ve el documento y el teléfono de Beto), la asignación masiva del rol (cualquiera se registra como admin), la devolución de préstamos ajenos sin ser admin, los días del préstamo que fija el estudiante, el hash que devuelve el registro y el login que revela si el correo existe. Ni Semgrep ni ZAP marcaron ninguno, porque el código es válido y la respuesta es un 200 normal. Tampoco vieron la **inyección SQL** de `/equipos?buscar=`, a pesar de ser una falla técnica clásica: se encontró leyendo `app/main.py:108` y se confirmó con un `UNION` que devuelve correos y hashes. En el Lab 1 se esperaba que Semgrep la detectara con `tainted-sql-string` (verificación de T1), y no fue así: la herramienta prevista falló y la falla solo apareció con la revisión manual. También hubo un hallazgo que el Lab 1 no tenía: el bloqueo de SQLite (364 errores `database is locked`) que provocó el escaneo activo de ZAP.
3. **El falso positivo que más tiempo costó** fue `Storable and Cacheable Content` de ZAP. Hubo que revisar qué páginas había escaneado para ver que eran públicas (`/docs`, `/openapi.json`) y que las respuestas con datos personales (`/prestamos`, `/me`) nunca llegaron al escaneo porque el baseline no tenía token. Semgrep no tuvo falsos positivos: sus 4 hallazgos son fallas reales. Lo que más tiempo costó en realidad fue el escaneo activo de ZAP, que dejó la base bloqueada con 364 errores `database is locked` y obligó a cambiar al baseline.
