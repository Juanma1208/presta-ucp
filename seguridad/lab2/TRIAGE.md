# Lab 2 · Triage SAST y DAST · PrestaUCP (estado inicial)

## SAST: Semgrep

Conjuntos de reglas: `p/python`, `p/secrets` y `p/owasp-top-ten`, excluyendo `seguridad/` y `.venv/`. El reporte está en `antes/evidencias/semgrep.sarif` y la consola en `antes/evidencias/semgrep.txt`.

- **`semgrep.sarif`:** 4 hallazgos, 2 de severidad ERROR y 2 WARNING.
- **Salida en pantalla (`semgrep.txt`, captura `09-semgrep.png`):** 2 hallazgos, los dos ERROR marcados como «Blocking». Los WARNING solo quedan en el SARIF.

### Hallazgos de severidad ERROR

| Regla | Archivo:línea | ¿Verdadero o falso positivo? | Por qué | Fila ASVS relacionada |
|---|---|---|---|---|
| `python.jwt.security.jwt-hardcode.jwt-python-hardcoded-secret` | `app/auth.py:24` | Verdadero positivo | El secreto del JWT está escrito en el código (`app/auth.py:8`). Se explotó: con ese secreto se forja un token de admin y `POST /equipos` lo acepta con HTTP 201 (`antes/evidencias/curl.txt`, captura `05-secreto-jwt.png`) | 17, 23 (13.3.1) |
| `dockerfile.security.missing-user.missing-user` | `Dockerfile:9` | Verdadero positivo | El Dockerfile no tiene `USER`, así que uvicorn corre como `root` dentro del contenedor. Si alguien logra ejecutar código aprovechando otra falla, lo hace como root | 19 |

### Hallazgos WARNING del SARIF (también se revisaron)

| Regla | Archivo:línea | ¿Verdadero o falso positivo? | Por qué | Fila ASVS relacionada |
|---|---|---|---|---|
| `python.lang.security.insecure-hash-algorithms-md5.insecure-hash-algorithm-md5` | `app/auth.py:15` | Verdadero positivo | `hash_clave` usa MD5 sin sal. El registro devuelve `c4ca4238a0b923820dcc509a6f75849b`, que es el MD5 de «1» y se revierte en segundos con tablas en línea (`antes/evidencias/curl.txt`, captura `04-registro-hash-rol.png`) | 2 (11.4.2) |
| `python.fastapi.security.wildcard-cors.wildcard-cors` | `app/main.py:31` | Verdadero positivo | `allow_origins=["*"]`: cualquier sitio puede llamar a la API desde el navegador de un usuario. Se confirmó con `curl`: una petición con `Origin: https://malo.example` recibe `access-control-allow-origin: *` (captura `08-debug-cors.png`) | 19 |

No hubo falsos positivos en Semgrep: los 4 hallazgos son fallas reales.

### Lo que Semgrep no encontró y la revisión manual sí

| Falla | Dónde | Fila ASVS | Por qué la herramienta no la ve |
|---|---|---|---|
| Inyección SQL en la búsqueda | `app/main.py:108` | 14, 21 | El f-string con el parámetro no coincidió con ninguna regla de `p/python`; se encontró a mano y con `curl` |
| BOLA en `/prestamos/{id}` | `app/main.py:166` | 9, 24 | La consulta está parametrizada. Le falta filtrar por el dueño, y eso es una regla de negocio |
| Asignación masiva del rol | `app/main.py:43`, `69` | 10, 22 | Guardar un campo del cliente es código válido para la herramienta |
| Devolver sin rol admin | `app/main.py:186` | 11, 25 | La herramienta no sabe qué rol debería exigir la función |
| El estudiante fija los días del préstamo (T-09 del Lab 1) | `app/main.py:58`, `143` | 13 (2.2.1) | Es una regla de negocio, no un patrón de código |
| El registro devuelve el hash | `app/main.py:77` | 12 | La herramienta no sabe qué campos son sensibles |
| Login que revela si el usuario existe | `app/main.py:86-89` | 4 | Depende del mensaje, no de un patrón |

## DAST: ZAP

Primero se intentó el escaneo de API (`zap-api-scan.py`) sobre `/openapi.json` con un token de administrador. Ese escaneo se quedó trabado: las peticiones en paralelo del escaneo activo provocaron **364 errores `database is locked`** en la app (`antes/evidencias/log-bloqueo-db.txt`). Cuando una petición falla a mitad de camino, la conexión a SQLite no se cierra (`app/main.py:69-78`), la base queda bloqueada y las siguientes escrituras fallan. Esto es un hallazgo real de denegación de servicio. Está relacionado con la amenaza T-12 del Lab 1 (D, sin límite de peticiones) y con la fila 13 de ASVS, pero su causa es otra: T-12 trata de peticiones sin límite, y aquí el problema son las conexiones a SQLite que no se cierran cuando una petición falla. **El modelo del Lab 1 no tenía esta amenaza**, así que es un hallazgo nuevo del Lab 2.

Por eso se usó el escaneo pasivo (`zap-baseline.py`) sobre `http://127.0.0.1:8000/docs`, la única página HTML de la app. El resultado fue **FAIL 0 · WARN 9 · PASS 59**. El reporte está en `antes/evidencias/zap.html` y la consola en `antes/evidencias/zap.txt`.

### Alertas Medium (no hubo High)

| Alerta ZAP | Riesgo | ¿Verdadero o falso positivo? | Por qué | Fila ASVS |
|---|---|---|---|---|
| Content Security Policy (CSP) Header Not Set [10038] | Medium | Verdadero positivo | La app no envía `Content-Security-Policy` en ninguna respuesta | 19 |
| Missing Anti-clickjacking Header [10020] | Medium | Verdadero positivo | No hay `X-Frame-Options` ni `frame-ancestors`, así que `/docs` se puede meter en un iframe de otro sitio | 19 |
| Sub Resource Integrity Attribute Missing [90003] | Medium | Verdadero positivo, de bajo impacto | `/docs` carga el JavaScript y el CSS de Swagger UI desde `cdn.jsdelivr.net` sin atributo `integrity`. Si el CDN fuera comprometido, el código cambiado se ejecutaría en la página de documentación. Es la página por defecto de FastAPI, y en producción se puede desactivar con `docs_url=None` | 19 |

### Alertas Low e Informational

| Alerta ZAP | Riesgo | ¿Verdadero o falso positivo? | Por qué | Fila ASVS |
|---|---|---|---|---|
| X-Content-Type-Options Header Missing [10021] | Low | Verdadero positivo | Falta `nosniff` | 19 |
| Cross-Origin-Embedder / Opener / Resource-Policy [90004] | Low | Verdadero positivo, de prioridad baja | Faltan estas cabeceras de aislamiento | 19 |
| Permissions Policy Header Not Set [10063] | Low | Verdadero positivo, de prioridad baja | La app no usa cámara ni ubicación; es una capa extra | 19 |
| Cross-Domain JavaScript Source File Inclusion [10017] | Low | Verdadero positivo | Es la misma causa de la alerta SRI: `/docs` carga scripts de otro dominio | 19 |
| Storable and Cacheable Content [10049] | Informational | Falso positivo para lo escaneado | Las páginas escaneadas son públicas. Las respuestas con datos personales (`/prestamos`, `/me`) sí deberían llevar `Cache-Control: no-store`, pero el baseline no tenía token para verlas | 16 |
| Modern Web Application [10109] | Informational | Falso positivo | Solo informa que `/docs` usa JavaScript | — |

### Lo que ZAP no encontró

El baseline es pasivo y no tenía token, así que solo vio cabeceras de `/docs`. No detectó la inyección SQL, BOLA en `/prestamos/{id}`, la asignación masiva del rol, la devolución sin rol admin, el secreto del JWT ni los días del préstamo. Todas esas salieron de la revisión con ASVS y de los `curl` de `antes/evidencias/curl.txt`. El único hallazgo «de comportamiento» que dejó ZAP fue indirecto: el bloqueo de la base durante el primer intento.

## ¿Por qué Semgrep y ZAP encontraron cosas distintas?

En esta app **no hubo ninguna coincidencia**. Semgrep encontró 4 fallas reales en el código y la configuración (secreto del JWT, MD5, CORS abierto y contenedor como root), y ZAP encontró 3 alertas Medium y 6 Low, todas de cabeceras y de la página `/docs`. Ninguna herramienta vio lo que encontró la otra, porque cada una revisa la aplicación desde un lugar distinto y con información distinta.

| | SAST (Semgrep) | DAST (ZAP baseline) |
|---|---|---|
| **Qué revisa** | El código fuente (`app/`) y el `Dockerfile`, sin ejecutarlos | La app corriendo en `127.0.0.1:8000`, sin ver el código |
| **Cómo busca** | Compara el código con patrones conocidos: una llamada a `md5`, un string pasado a `jwt.encode`, `allow_origins=["*"]`, un Dockerfile sin `USER` | Pide páginas y revisa las respuestas: cabeceras, códigos de estado y contenido |
| **Qué información tiene** | Todo el código, incluidas las rutas que piden token | Solo lo que alcanza desde afuera: sin token, sin cargas de ataque (el baseline es pasivo) y con una sola página HTML (`/docs`) |
| **Qué encontró aquí** | `app/auth.py:8-24` (secreto), `app/auth.py:15` (MD5), `app/main.py:31` (CORS), `Dockerfile:9` (root) | CSP, anti-clickjacking, SRI, `nosniff`, `Permissions-Policy` y COEP/COOP/CORP ausentes; scripts de otro dominio en `/docs` |

### Por qué Semgrep vio el secreto, el MD5, el CORS y el root, y ZAP no

- Las cuatro fallas **están escritas** en un archivo: `SECRET_KEY = "presta-ucp-2026"`, `hashlib.md5(...)`, `allow_origins=["*"]` y un `Dockerfile` que termina sin `USER`. Son patrones fijos, y Semgrep los reconoce leyendo el texto.
- Desde afuera ninguna se ve. El secreto y el algoritmo del hash nunca viajan en una respuesta, y el usuario con el que corre el proceso tampoco.
- El CORS sí se puede ver desde afuera, pero solo si la petición trae la cabecera `Origin`. El baseline no la envía, así que la respuesta nunca incluyó `access-control-allow-origin`. Se confirmó a mano con `curl -H 'Origin: https://malo.example'`.

### Por qué ZAP vio las cabeceras y Semgrep no

- Una cabecera que falta es una **ausencia**. Semgrep busca patrones que *están* en el código, y no tiene una regla que diga «esta respuesta debería tener una CSP y no la tiene».
- Las alertas de SRI y de scripts de otro dominio vienen de la página de Swagger UI que FastAPI genera sola. Ese HTML no está en `app/`, sino dentro de la librería, así que Semgrep nunca lo leyó. Solo existe en la **respuesta real**, que es justo lo que revisa ZAP.
- El bloqueo de la base (`database is locked`, 364 errores) tampoco lo podía ver Semgrep: aparece solo cuando llegan muchas peticiones a la vez y alguna falla. Lo dejó ver el primer intento de escaneo activo de ZAP, aunque de forma indirecta: no fue una alerta, sino el log de la app.

### Lo que ninguna de las dos vio

La inyección SQL (`app/main.py:108`), BOLA en `/prestamos/{id}` (`app/main.py:166`), la asignación masiva del rol (`app/main.py:43`, `69`), la devolución sin rol admin (`app/main.py:186`), los días del préstamo que decide el estudiante (`app/main.py:143`), el hash que devuelve el registro (`app/main.py:77`), el login que revela si el usuario existe (`app/main.py:86-89`) y el `debug=True` que muestra la traza (`app/main.py:25`).

Casi todas son **fallas de autorización o de lógica de negocio**. El código es válido y la respuesta HTTP es un 200 normal. Para saber que algo está mal hay que conocer una regla del negocio: «un préstamo es de su dueño», «el rol lo asigna el sistema», «devolver es tarea del administrador». Ninguna herramienta conoce esas reglas, por eso las encontraron la revisión con ASVS y los `curl` de `antes/evidencias/curl.txt`.

La inyección SQL es el caso más llamativo, porque es una falla técnica clásica. Semgrep no la marcó, probablemente porque en FastAPI el parámetro `buscar` llega como argumento de la función y no desde `request.args`, como en Flask, y las reglas de `p/python` no siguieron el dato hasta el f-string. ZAP tampoco la vio, porque el baseline no envía cargas y el escaneo activo tuvo que detenerse por el bloqueo de la base.

### Conclusión

Las dos herramientas **se complementan, no se repiten**. SAST encuentra lo que se ve en el código (secretos, algoritmos, configuración escrita) y DAST lo que se ve con la app corriendo (cabeceras, páginas generadas por la librería y el comportamiento bajo carga). Lo que depende del negocio solo lo encuentra una persona. Con más configuración, cada una podría cubrir parte de lo que ve la otra: un escaneo activo de ZAP con token (`zap-api-scan.py` sobre `/openapi.json`), una vez corregido el bloqueo de SQLite, probablemente detectaría la inyección SQL y la traza de Python, y una regla propia de Semgrep podría marcar los f-strings dentro de `con.execute()`. Aun así, ninguna de las dos detectaría BOLA, la asignación masiva del rol ni la devolución sin rol admin.

## Después de las correcciones

> Pendiente: se completa en la etapa «después», repitiendo Semgrep y ZAP con los mismos comandos sobre la versión corregida y comparando los resultados (`despues/evidencias/`).
