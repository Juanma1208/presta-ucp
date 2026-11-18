# Lab 1 · Modelo de amenazas · PrestaUCP

- **Aplicación:** PrestaUCP, una API para el préstamo de equipos de la universidad, hecha en FastAPI + SQLite + PyJWT (`app/main.py`, `app/auth.py`, `app/db.py`).
- **Alcance:** toda la aplicación: registro, login, catálogo de equipos, préstamos y devoluciones.
- **Archivos:** `modelo.json` es el modelo de OWASP Threat Dragon e `informe.pdf` es el reporte generado desde Threat Dragon.

## 1. ¿En qué se está trabajando?

| Tipo | Elementos |
|---|---|
| Actores | Visitante anónimo (sin token), estudiante (token JWT) y administrador (token JWT con rol admin) |
| Procesos | Autenticación (`POST /registro` y `POST /login`, con `auth.py`) y API PrestaUCP (equipos y préstamos) |
| Almacenes | SQLite `presta.db` (usuarios con nombre, documento, correo, teléfono, hash de la clave y rol; equipos; préstamos) y logs del servidor (uvicorn) |
| Flujos | 9 flujos, cada uno con su protocolo, si va cifrado y si pasa por una red pública. Los flujos de los actores usan **HTTP sin cifrar** por una red pública. Los flujos hacia la base y los logs son locales |
| Límites de confianza | **L1** Internet \| servidor · **L2** aplicación \| almacenamiento (la base y los logs viven en el volumen de Docker) |

La app no usa proveedores externos, por eso solo tiene estos dos límites.

## 2. ¿Qué puede salir mal?

Se recorrió cada elemento del diagrama con STRIDE y salieron **17 amenazas**. Todas están registradas en `modelo.json`, cada una con su descripción, el `archivo:línea` donde ocurre, la justificación de I × P y la mitigación.

| ID | Elemento | STRIDE | Amenaza | I × P | Severidad |
|---|---|---|---|---|---|
| T-01 | Autenticación | E | Cualquiera se registra como administrador (asignación masiva) | 3 × 3 = 9 | High |
| T-02 | Autenticación | S | El secreto del JWT está fijo en el código del repositorio público | 3 × 3 = 9 | High |
| T-07 | API PrestaUCP | I | BOLA: un estudiante ve el préstamo de otro con sus datos personales | 3 × 3 = 9 | High |
| T-08 | API PrestaUCP | E | Cualquier estudiante registra devoluciones, incluso de préstamos ajenos | 3 × 3 = 9 | High |
| T-17 | Flujo Visitante → API | T | Inyección SQL en la búsqueda de equipos | 3 × 3 = 9 | High |
| T-03 | Autenticación | S | Tokens sin expiración ni cierre de sesión | 3 × 2 = 6 | Medium |
| T-04 | Autenticación | S | Login sin límite de intentos y con contraseñas débiles | 3 × 2 = 6 | Medium |
| T-05 | Autenticación | I | El login revela si un correo está registrado | 2 × 3 = 6 | Medium |
| T-06 | Autenticación | I | El registro devuelve el hash de la contraseña | 2 × 3 = 6 | Medium |
| T-09 | API PrestaUCP | T | El estudiante decide cuántos días dura el préstamo (**negocio**) | 2 × 3 = 6 | Medium |
| T-11 | API PrestaUCP | I | Errores con traza completa y CORS abierto | 2 × 3 = 6 | Medium |
| T-13 | SQLite | I | Contraseñas en MD5 sin sal y datos personales sin cifrar | 3 × 2 = 6 | Medium |
| T-14 | Flujo Visitante → Autenticación | I | Contraseñas, tokens y datos personales viajan sin cifrar | 3 × 2 = 6 | Medium |
| T-15 | Administrador | S | Cuenta de administrador por defecto con contraseña débil | 3 × 2 = 6 | Medium |
| T-10 | API PrestaUCP | T | Dos peticiones simultáneas se saltan el límite de préstamos (**negocio**) | 2 × 2 = 4 | Medium |
| T-12 | API PrestaUCP | D | Sin límite de peticiones ni paginación | 2 × 2 = 4 | Medium |
| T-16 | Logs del servidor | R | No queda registro de quién pidió o devolvió un préstamo | 2 × 2 = 4 | Medium |

**Cobertura:** están las 6 categorías de STRIDE (S: 4, T: 3, R: 1, I: 6, D: 1, E: 2).

**Lógica de negocio:** hay 2 amenazas de este tipo, T-09 y T-10, y ninguna herramienta automática las encontraría. La más clara es **T-09**. La regla del préstamo es «máximo 3 días», pero esa regla solo está en el README. En el código, `PrestamoNuevo` tiene `dias: int = 3` (`main.py:58`) y `pedir_prestamo` usa el valor que envía el cliente sin revisarlo (`main.py:143`). Por eso un estudiante que envía `"dias": 365` se queda con un portátil un año. El código funciona y no tiene un patrón peligroso: lo que falla es que el servidor no aplica la regla del negocio.

**T-10** es menos evidente. `pedir_prestamo` primero revisa que el equipo esté disponible y que el estudiante tenga menos de 2 préstamos, y después inserta el préstamo (`main.py:125-151`). Si llegan dos peticiones al mismo tiempo, las dos pasan las validaciones antes de que alguna guarde el cambio, y el mismo equipo queda prestado a dos personas.

**Criterio de calificación:** el impacto es 3 si hay exposición de datos personales, toma de cuentas o control de la app; 2 si el daño es acotado (equipos retenidos, información técnica expuesta); y 1 si es menor. La probabilidad es 3 si basta con una petición sin token o con un token normal; 2 si hace falta una condición adicional (robar un token, estar en la misma red, enviar peticiones en paralelo o llegar a la base); y 1 si se necesita acceso al servidor.

## 3. ¿Qué se va a hacer al respecto? Top 5

Cinco amenazas tienen riesgo 9 y todas entraron al top 5. Para el orden se tuvo en cuenta qué tan fácil es explotarlas: las tres primeras no necesitan sesión, mientras que T4 y T5 necesitan el token de cualquier estudiante.

| ID | Amenaza | STRIDE | I × P | Requisito de seguridad (verificable) | ASVS 5.0 | Cómo se verifica |
|---|---|---|---|---|---|---|
| T1 (T-17) | Inyección SQL en `GET /equipos?buscar=` (`main.py:108`) | T | 3 × 3 = 9 | Todas las consultas usan parámetros `?`. En la búsqueda, el `%` va dentro del parámetro (`LIKE ?`) y no se pega al SQL | V1 | Prueba: `?buscar=' UNION SELECT id, correo, clave, rol FROM usuarios--` no devuelve correos ni hashes, y una búsqueda con apóstrofo funciona. Herramienta: Semgrep (`tainted-sql-string`) |
| T2 (T-01) | Cualquiera se registra como administrador (`main.py:43`, `main.py:69-78`) | E | 3 × 3 = 9 | El registro no usa el rol que envía el cliente: toda cuenta nueva queda como `estudiante` | V15, V8 | Prueba: registrarse con `"rol": "admin"` deja la cuenta como estudiante, y con ese token `POST /equipos` responde 403 |
| T3 (T-02) | Secreto del JWT fijo en el código (`auth.py:8`) | S | 3 × 3 = 9 | El secreto se lee de una variable de entorno, es aleatorio y tiene al menos 32 bytes. Los tokens tienen `exp` | V13, V9 | Prueba: un token firmado con `presta-ucp-2026` responde 401, y un token vencido también. Herramienta: Semgrep `p/secrets` y revisión del historial de git |
| T4 (T-07) | BOLA en `GET /prestamos/{id}` (`main.py:166-182`) | I | 3 × 3 = 9 | La consulta filtra por el dueño del préstamo (el admin puede ver todos). Un préstamo ajeno responde 404 igual que uno inexistente | V8 | Prueba: Ana pide `/prestamos/2` (de Beto), recibe 404 y la respuesta no tiene el documento ni el teléfono de Beto. Ana sigue viendo `/prestamos/1` |
| T5 (T-08) | Cualquier estudiante registra devoluciones (`main.py:186-199`) | E | 3 × 3 = 9 | `POST /prestamos/{id}/devolver` exige el rol admin con `solo_admin`, igual que `POST /equipos` | V8 | Prueba: Ana hace la devolución y recibe 403, y el equipo sigue prestado. El admin la hace y recibe 200 |

## 4. ¿Se hizo un buen trabajo?

1. **Qué quedó fuera del modelo.** El despliegue en producción (proxy con TLS, servidor, copias de seguridad de la base), porque hoy la app solo corre en Docker en `127.0.0.1`. Tampoco se modeló el cambio y la recuperación de contraseña, porque la app no los tiene. Esas partes se deben modelar cuando existan.
2. **Qué amenaza sorprendió.** T-02. El secreto del JWT parecía un detalle de configuración, pero como el repositorio es público, cualquiera puede leerlo y firmar un token de administrador sin conocer ninguna contraseña. Además, deja sin efecto los demás controles de acceso: `solo_admin` revisa el rol que viene en el token, y ese rol lo puede escribir el atacante.
