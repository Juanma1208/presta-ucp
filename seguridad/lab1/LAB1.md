# Lab 1 · Modelo de amenazas · PrestaUCP

- **Aplicación:** PrestaUCP, una API para gestionar el préstamo de equipos de la universidad, desarrollada con FastAPI, SQLite y PyJWT (`app/main.py`, `app/auth.py` y `app/db.py`).
- **Alcance:** se modeló toda la aplicación, incluyendo el registro, inicio de sesión, catálogo de equipos, préstamos y devoluciones.
- **Archivos entregados:** `modelo.json`, que contiene el modelo realizado en OWASP Threat Dragon, e `informe.pdf`, correspondiente al reporte exportado desde la herramienta.

## 1. ¿En qué se está trabajando?

El modelo de amenazas incluye los principales componentes de la aplicación y las relaciones entre ellos.

| Tipo | Elementos |
|---|---|
| Actores | Visitante anónimo (sin token), estudiante (token JWT) y administrador (token JWT con rol `admin`) |
| Procesos | Autenticación (`POST /registro` y `POST /login`, implementada en `auth.py`) y la API de PrestaUCP (gestión de equipos y préstamos) |
| Almacenes | Base de datos SQLite `presta.db` (usuarios con nombre, documento, correo, teléfono, hash de la contraseña y rol; equipos; préstamos) y los registros generados por el servidor (`uvicorn`) |
| Flujos | Se identificaron 9 flujos. Cada uno especifica el protocolo utilizado, si la comunicación está cifrada y si atraviesa una red pública. Los flujos entre los usuarios y la aplicación utilizan **HTTP sin cifrar**, mientras que la comunicación con la base de datos y los logs es local. |
| Límites de confianza | **L1:** Internet ↔ Servidor. **L2:** Aplicación ↔ Almacenamiento (base de datos y logs almacenados en el volumen de Docker). |

Como la aplicación no consume servicios externos, únicamente se definieron estos dos límites de confianza.

## 2. ¿Qué puede salir mal?

Se analizó cada elemento del diagrama utilizando la metodología STRIDE y se identificaron **17 amenazas**. Todas quedaron registradas en `modelo.json` junto con su descripción, el `archivo:línea` donde aparecen, la valoración de impacto y probabilidad, y la mitigación propuesta.

| ID | Elemento | STRIDE | Amenaza | I × P | Severidad |
|---|---|---|---|---|---|
| T-01 | Autenticación | E | Cualquier usuario puede registrarse como administrador mediante asignación masiva. | 3 × 3 = 9 | High |
| T-02 | Autenticación | S | El secreto utilizado para firmar los JWT está fijo en el código fuente del repositorio. | 3 × 3 = 9 | High |
| T-07 | API PrestaUCP | I | Vulnerabilidad BOLA: un estudiante puede consultar el préstamo de otro usuario y acceder a sus datos personales. | 3 × 3 = 9 | High |
| T-08 | API PrestaUCP | E | Cualquier estudiante puede registrar devoluciones, incluso de préstamos que no le pertenecen. | 3 × 3 = 9 | High |
| T-17 | Flujo Visitante → API | T | Inyección SQL en la búsqueda de equipos. | 3 × 3 = 9 | High |
| T-03 | Autenticación | S | Los tokens no tienen expiración ni existe un mecanismo de cierre de sesión. | 3 × 2 = 6 | Medium |
| T-04 | Autenticación | S | El inicio de sesión no limita intentos y permite contraseñas débiles. | 3 × 2 = 6 | Medium |
| T-05 | Autenticación | I | El login permite identificar si un correo electrónico ya está registrado. | 2 × 3 = 6 | Medium |
| T-06 | Autenticación | I | El registro devuelve el hash de la contraseña en la respuesta. | 2 × 3 = 6 | Medium |
| T-09 | API PrestaUCP | T | El estudiante puede decidir la duración del préstamo (**lógica de negocio**). | 2 × 3 = 6 | Medium |
| T-11 | API PrestaUCP | I | La aplicación expone trazas completas de error y tiene CORS abierto. | 2 × 3 = 6 | Medium |
| T-13 | SQLite | I | Las contraseñas se almacenan con MD5 sin sal y los datos personales no están cifrados. | 3 × 2 = 6 | Medium |
| T-14 | Flujo Visitante → Autenticación | I | Contraseñas, tokens y datos personales viajan sin cifrado. | 3 × 2 = 6 | Medium |
| T-15 | Administrador | S | Existe una cuenta de administrador por defecto con una contraseña débil. | 3 × 2 = 6 | Medium |
| T-10 | API PrestaUCP | T | Dos solicitudes simultáneas pueden superar el límite de préstamos permitido (**lógica de negocio**). | 2 × 2 = 4 | Medium |
| T-12 | API PrestaUCP | D | No existe limitación de peticiones ni paginación. | 2 × 2 = 4 | Medium |
| T-16 | Logs del servidor | R | No queda evidencia de quién solicita o devuelve un préstamo. | 2 × 2 = 4 | Medium |

**Cobertura del análisis:** se identificaron amenazas pertenecientes a las seis categorías de STRIDE (S: 4, T: 3, R: 1, I: 6, D: 1 y E: 2).

### Amenazas de lógica de negocio

Se identificaron dos amenazas que corresponden a reglas del negocio y que no serían detectadas por herramientas automáticas: **T-09** y **T-10**.

La más evidente es **T-09**. La política del sistema indica que un préstamo puede durar como máximo tres días, pero esa restricción únicamente aparece documentada en el README. En el código, el modelo `PrestamoNuevo` define `dias: int = 3` (`main.py:58`), pero el endpoint `pedir_prestamo` utiliza directamente el valor enviado por el cliente (`main.py:143`) sin validarlo. Como consecuencia, un estudiante puede solicitar un préstamo enviando `"dias": 365` y conservar un equipo durante un año. Desde el punto de vista técnico el código funciona correctamente; el problema es que el servidor no aplica la regla del negocio.

La amenaza **T-10** es menos evidente. Antes de crear un préstamo, el método `pedir_prestamo` verifica que el equipo esté disponible y que el estudiante tenga menos de dos préstamos activos (`main.py:125-151`). Si dos solicitudes llegan prácticamente al mismo tiempo, ambas pueden superar las validaciones antes de que alguna registre el préstamo en la base de datos, permitiendo que el mismo equipo quede asignado a dos personas.

### Criterio de valoración

El impacto se calificó con valor **3** cuando la amenaza permitía exponer datos personales, tomar control de cuentas o tomar el control de la aplicación. Se asignó **2** cuando el daño era limitado, como la retención de equipos o la exposición de información técnica, y **1** para afectaciones menores.

La probabilidad recibió un valor **3** cuando bastaba con enviar una petición sin autenticación o utilizando un token de un estudiante. Se asignó **2** cuando era necesario cumplir una condición adicional, como robar un token, estar en la misma red, ejecutar peticiones concurrentes o acceder directamente a la base de datos. Finalmente, se utilizó **1** cuando la explotación requería acceso al servidor.

## 3. ¿Qué se va a hacer al respecto? Top 5

Cinco amenazas obtuvieron un riesgo de **9**, por lo que todas fueron priorizadas. El orden se definió considerando la facilidad de explotación: las tres primeras pueden ejecutarse sin autenticación, mientras que las dos restantes requieren un token válido de estudiante.

| ID | Amenaza | STRIDE | I × P | Requisito de seguridad | ASVS 5.0 | Verificación |
|---|---|---|---|---|---|---|
| **T1 (T-17)** | Inyección SQL en `GET /equipos?buscar=` (`main.py:108`) | T | 3 × 3 = 9 | Todas las consultas utilizan parámetros (`?`) y el comodín `%` forma parte del parámetro, no de la consulta SQL. | V1 | Se verifica enviando `?buscar=' UNION SELECT id, correo, clave, rol FROM usuarios--`, comprobando que no se devuelven correos ni hashes y que una búsqueda con apóstrofos funciona correctamente. También puede verificarse con la regla `tainted-sql-string` de Semgrep. |
| **T2 (T-01)** | Registro como administrador (`main.py:43`, `main.py:69-78`) | E | 3 × 3 = 9 | El rol enviado por el cliente se ignora y todas las cuentas nuevas se crean como `estudiante`. | V15, V8 | Se registra un usuario enviando `"rol": "admin"` y se comprueba que el rol asignado continúa siendo estudiante y que `POST /equipos` responde `403`. |
| **T3 (T-02)** | Secreto del JWT embebido en el código (`auth.py:8`) | S | 3 × 3 = 9 | El secreto se obtiene desde una variable de entorno, es aleatorio, tiene al menos 32 bytes y todos los tokens incluyen expiración (`exp`). | V13, V9 | Se verifica que un token firmado con `presta-ucp-2026` sea rechazado con `401` y que un token expirado también sea inválido. Además, se revisa el historial de Git y las reglas `p/secrets` de Semgrep. |
| **T4 (T-07)** | BOLA en `GET /prestamos/{id}` (`main.py:166-182`) | I | 3 × 3 = 9 | La consulta únicamente devuelve préstamos pertenecientes al usuario autenticado, salvo para el administrador. Los préstamos ajenos responden `404`, igual que los inexistentes. | V8 | Se comprueba que Ana no pueda consultar el préstamo de Beto (`404`) y que la respuesta no exponga información personal, mientras que Ana sí puede acceder a sus propios préstamos. |
| **T5 (T-08)** | Registro de devoluciones por cualquier estudiante (`main.py:186-199`) | E | 3 × 3 = 9 | El endpoint `POST /prestamos/{id}/devolver` requiere el rol de administrador mediante `solo_admin`. | V8 | Se verifica que un estudiante reciba `403` al intentar registrar una devolución y que el equipo siga prestado, y que únicamente el administrador pueda realizar la operación con éxito. |

## 4. ¿Se hizo un buen trabajo?

1. **Aspectos fuera del alcance.** No se modeló la infraestructura de producción, como el proxy inverso con TLS, el servidor físico o virtual y las copias de seguridad, ya que actualmente la aplicación solo se ejecuta localmente mediante Docker sobre `127.0.0.1`. Tampoco se incluyeron los procesos de recuperación o cambio de contraseña, debido a que aún no existen en la aplicación.

2. **Amenaza que más sorprendió.** La amenaza **T-02** fue la más llamativa. Aunque inicialmente parecía un problema de configuración, al estar el repositorio disponible públicamente cualquier persona puede obtener el secreto utilizado para firmar los JWT y generar un token con privilegios de administrador sin conocer ninguna contraseña. Esto hace que controles como `solo_admin` pierdan efectividad, ya que la aplicación confía en el rol contenido dentro del token.
