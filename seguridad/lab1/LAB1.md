# Lab 1 · Modelo de amenazas · PrestaUCP

- **Aplicación:** PrestaUCP es una API para el préstamo de equipos de la universidad. Está hecha con FastAPI, SQLite y PyJWT (`app/main.py`, `app/auth.py` y `app/db.py`).
- **Alcance:** se modeló toda la aplicación: registro, inicio de sesión, catálogo de equipos, préstamos y devoluciones.
- **Archivos:** `modelo.json` es el modelo que se hizo en OWASP Threat Dragon e `informe.pdf` es el reporte que genera la herramienta.

## 1. ¿En qué se está trabajando?

Para encontrar amenazas primero hay que saber qué partes tiene la aplicación y cómo se comunican. Por eso el diagrama incluye estos elementos:

| Tipo | Elementos |
|---|---|
| Actores | Visitante anónimo (sin token), estudiante (con token JWT) y administrador (con token JWT y rol `admin`) |
| Procesos | Autenticación (`POST /registro` y `POST /login`, en `auth.py`) y la API de PrestaUCP (equipos y préstamos) |
| Almacenes | La base SQLite `presta.db` (usuarios con nombre, documento, correo, teléfono, hash de la contraseña y rol; equipos; préstamos) y los logs del servidor (`uvicorn`) |
| Flujos | Son 9 flujos, y cada uno indica su protocolo, si va cifrado y si pasa por una red pública. Los flujos entre los usuarios y la app van por **HTTP sin cifrar**, mientras que los que llegan a la base y a los logs son locales |
| Límites de confianza | **L1:** Internet ↔ servidor. **L2:** aplicación ↔ almacenamiento (la base y los logs están en el volumen de Docker) |

Solo hay dos límites de confianza porque la app no usa servicios externos. Si más adelante se conecta con otro sistema, habría que agregar un límite por cada uno.

## 2. ¿Qué puede salir mal?

Se recorrió cada elemento del diagrama con STRIDE y salieron **17 amenazas**. Todas están en `modelo.json` con su descripción, el `archivo:línea` donde ocurren, la calificación de impacto y probabilidad, y la mitigación.

| ID | Elemento | STRIDE | Amenaza | I × P | Severidad |
|---|---|---|---|---|---|
| T-01 | Autenticación | E | Cualquiera puede registrarse como administrador (asignación masiva) | 3 × 3 = 9 | High |
| T-02 | Autenticación | S | El secreto que firma los JWT está escrito en el código del repositorio | 3 × 3 = 9 | High |
| T-07 | API PrestaUCP | I | BOLA: un estudiante puede ver el préstamo de otro, con sus datos personales | 3 × 3 = 9 | High |
| T-08 | API PrestaUCP | E | Cualquier estudiante puede registrar devoluciones, incluso de préstamos ajenos | 3 × 3 = 9 | High |
| T-17 | Flujo Visitante → API | T | Inyección SQL en la búsqueda de equipos | 3 × 3 = 9 | High |
| T-03 | Autenticación | S | Los tokens no vencen y no hay cierre de sesión | 3 × 2 = 6 | Medium |
| T-04 | Autenticación | S | El login no limita los intentos y acepta contraseñas débiles | 3 × 2 = 6 | Medium |
| T-05 | Autenticación | I | El login deja saber si un correo está registrado | 2 × 3 = 6 | Medium |
| T-06 | Autenticación | I | El registro devuelve el hash de la contraseña | 2 × 3 = 6 | Medium |
| T-09 | API PrestaUCP | T | El estudiante decide cuántos días dura el préstamo (**lógica de negocio**) | 2 × 3 = 6 | Medium |
| T-11 | API PrestaUCP | I | Los errores muestran la traza completa y CORS está abierto | 2 × 3 = 6 | Medium |
| T-13 | SQLite | I | Las contraseñas están en MD5 sin sal y los datos personales no están cifrados | 3 × 2 = 6 | Medium |
| T-14 | Flujo Visitante → Autenticación | I | Contraseñas, tokens y datos personales viajan sin cifrar | 3 × 2 = 6 | Medium |
| T-15 | Administrador | S | Hay una cuenta de administrador por defecto con contraseña débil | 3 × 2 = 6 | Medium |
| T-10 | API PrestaUCP | T | Dos peticiones al mismo tiempo pueden saltarse el límite de préstamos (**lógica de negocio**) | 2 × 2 = 4 | Medium |
| T-12 | API PrestaUCP | D | No hay límite de peticiones ni paginación | 2 × 2 = 4 | Medium |
| T-16 | Logs del servidor | R | No queda registro de quién pidió o devolvió un préstamo | 2 × 2 = 4 | Medium |

**Cobertura:** hay amenazas de las seis letras de STRIDE (S: 4, T: 3, R: 1, I: 6, D: 1, E: 2).

### Amenazas de lógica de negocio

Dos amenazas, T-09 y T-10, no son errores de código sino reglas del negocio que el servidor no aplica. Por eso una herramienta automática no las encontraría: el código funciona bien, lo que falla es lo que permite hacer.

**T-09** es la más clara. La regla dice que un préstamo dura máximo tres días, pero esa regla solo está escrita en el README. En el código, `PrestamoNuevo` tiene `dias: int = 3` (`main.py:58`), aunque ese 3 es solo el valor por defecto: `pedir_prestamo` usa el número que mande el cliente sin revisarlo (`main.py:143`). Así, un estudiante que envía `"dias": 365` se queda con un portátil un año.

**T-10** cuesta más verla. Antes de crear el préstamo, `pedir_prestamo` revisa que el equipo esté disponible y que el estudiante tenga menos de dos préstamos activos, y después guarda el préstamo (`main.py:125-151`). El problema es que entre revisar y guardar pasa un momento. Si llegan dos peticiones al mismo tiempo, las dos pasan las validaciones antes de que alguna guarde, y el mismo equipo queda prestado a dos personas.

### Cómo se calificó

Para que las calificaciones no fueran a ojo, se definió un criterio y se aplicó igual en las 17 amenazas.

El **impacto** es 3 si la amenaza expone datos personales, permite tomar una cuenta o tomar el control de la aplicación; 2 si el daño es acotado, como retener equipos o mostrar información técnica; y 1 si es algo menor.

La **probabilidad** es 3 si basta una petición sin token o con el token de cualquier estudiante; 2 si hace falta algo más, como robar un token, estar en la misma red, enviar peticiones en paralelo o llegar a la base; y 1 si se necesita acceso al servidor.

## 3. ¿Qué se va a hacer al respecto? Top 5

Cinco amenazas tienen riesgo 9, así que todas entraron al top 5. Para ordenarlas se tuvo en cuenta qué tan fácil es explotarlas: las tres primeras no necesitan sesión, mientras que T4 y T5 necesitan el token de algún estudiante.

| ID | Amenaza | STRIDE | I × P | Requisito de seguridad | ASVS 5.0 | Cómo se verifica |
|---|---|---|---|---|---|---|
| **T1 (T-17)** | Inyección SQL en `GET /equipos?buscar=` (`main.py:108`) | T | 3 × 3 = 9 | Todas las consultas usan parámetros `?`. En la búsqueda, el `%` va dentro del parámetro y no pegado al SQL | V1 | Enviar `?buscar=' UNION SELECT id, correo, clave, rol FROM usuarios--` y comprobar que no devuelve correos ni hashes, y que una búsqueda con apóstrofo sigue funcionando. También con la regla `tainted-sql-string` de Semgrep |
| **T2 (T-01)** | Cualquiera se registra como administrador (`main.py:43`, `main.py:69-78`) | E | 3 × 3 = 9 | El registro ignora el rol que manda el cliente: toda cuenta nueva queda como `estudiante` | V15, V8 | Registrarse con `"rol": "admin"` y comprobar que la cuenta queda como estudiante y que con ese token `POST /equipos` responde `403` |
| **T3 (T-02)** | Secreto del JWT en el código (`auth.py:8`) | S | 3 × 3 = 9 | El secreto sale de una variable de entorno, es aleatorio y tiene al menos 32 bytes. Los tokens llevan `exp` | V13, V9 | Un token firmado con `presta-ucp-2026` recibe `401`, y un token vencido también. Además, revisar el historial de git y las reglas `p/secrets` de Semgrep |
| **T4 (T-07)** | BOLA en `GET /prestamos/{id}` (`main.py:166-182`) | I | 3 × 3 = 9 | La consulta filtra por el dueño del préstamo (el admin puede ver todos). Un préstamo ajeno responde `404`, igual que uno que no existe | V8 | Ana pide el préstamo de Beto, recibe `404` y la respuesta no trae sus datos personales. Ana sigue viendo sus propios préstamos |
| **T5 (T-08)** | Cualquier estudiante registra devoluciones (`main.py:186-199`) | E | 3 × 3 = 9 | `POST /prestamos/{id}/devolver` exige el rol admin con `solo_admin`, igual que `POST /equipos` | V8 | Un estudiante intenta devolver, recibe `403` y el equipo sigue prestado. El admin lo hace sin problema |

## 4. ¿Se hizo un buen trabajo?

1. **Qué quedó fuera del modelo.** No se modeló el despliegue en producción (el proxy con TLS, el servidor y las copias de seguridad de la base), porque hoy la app solo corre en Docker en `127.0.0.1`. Tampoco el cambio ni la recuperación de contraseña, porque la app todavía no los tiene. Cuando existan, habría que agregarlos al modelo.

2. **Qué amenaza sorprendió.** T-02. Al principio parecía un simple detalle de configuración, pero el repositorio es público, así que cualquiera puede leer el secreto y firmar un token de administrador sin saber ninguna contraseña. Lo más grave es que eso tumba los demás controles de acceso: `solo_admin` revisa el rol que viene en el token, y ese rol lo escribe el atacante.
