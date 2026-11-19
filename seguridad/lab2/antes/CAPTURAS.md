# Lab 2 · Capturas del estado inicial (antes)

Guardar las imágenes en `seguridad/lab2/antes/capturas/` con el nombre indicado. Antes de empezar, levantar la app limpia:

```bash
cd ~/presta-ucp
docker compose down -v && docker compose up -d --build
```

| Evidencia | Archivo sugerido | Qué mostrar |
|---|---|---|
| Evidencia 1 | `01-estructura.png` | Terminal con `ls -R seguridad/lab2`: las carpetas `antes/` y `despues/` y los archivos generados |
| Evidencia 2 | `02-app-docs.png` | Navegador en `http://127.0.0.1:8000/docs`, con la lista de rutas de PrestaUCP |
| Evidencia 3 | `03-curl-script.png` | Terminal ejecutando `bash seguridad/lab2/verificar.sh antes` (app recién levantada). Que se vea el inicio y algunos bloques |
| Evidencia 4 | `04-registro-hash-rol.png` | Del `curl.txt`: la respuesta del registro con `"rol":"admin"` y el campo `"clave"` con el hash MD5 (filas 2, 10 y 12) |
| Evidencia 5 | `05-secreto-jwt.png` | Del `curl.txt`: el `grep SECRET_KEY app/auth.py` y la línea `POST /equipos con token forjado -> HTTP 201` (filas 7 y 17) |
| Evidencia 6 | `06-bola.png` | Del `curl.txt`: Ana pidiendo `/prestamos/2` y la respuesta con el documento y el teléfono de Beto (fila 9) |
| Evidencia 7 | `07-devolver-sql.png` | Del `curl.txt`: la devolución hecha por Beto (fila 11) y la inyección SQL que devuelve correos y hashes (fila 14) |
| Evidencia 8 | `08-debug-cors.png` | Del `curl.txt`: la traza de Python del error y las cabeceras con `access-control-allow-origin: *` (fila 19) |
| Evidencia 9 | `09-semgrep.png` | Terminal con `cat seguridad/lab2/antes/evidencias/semgrep.txt` (o volver a correr el comando): los hallazgos de MD5, secreto del JWT, CORS y Dockerfile |
| Evidencia 10 | `10-zap.png` | Navegador abriendo `seguridad/lab2/antes/evidencias/zap.html`: el resumen de alertas (3 Medium: CSP, clickjacking y SRI) |
| Evidencia 11 | `11-zap-bloqueo.png` | Del `log-bloqueo-db.txt`: el conteo de 364 errores `database is locked` del primer intento (fila 13) |

Para abrir el `curl.txt` y sacar las capturas 4 a 8 cómodamente:

```bash
cat seguridad/lab2/antes/evidencias/curl.txt
```

Si prefieres capturas del navegador en vez del `curl.txt`, puedes repetir cada ataque desde `http://127.0.0.1:8000/docs` con el botón **Authorize** y un token.
