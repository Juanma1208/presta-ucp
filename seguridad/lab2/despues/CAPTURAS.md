# Lab 2 · Capturas del estado corregido (después)

Guardar las imágenes en `seguridad/lab2/despues/capturas/`. Todas se toman desde `~/presta-ucp`, en la rama `lab2/top5-correcciones`. **No volver a ejecutar `verificar.sh`**: las capturas que leen `curl.txt` usan el que ya quedó generado (commit `4d9c740`).

## Pruebas automáticas

| # | Archivo | Comando | Qué mostrar |
|---|---|---|---|
| 1 | `01-pytest-top5-antes.png` | `grep -E '::test_t\|passed\|failed' seguridad/lab2/antes/evidencias/pytest.txt \| grep -v '^FAILED'` | Las pruebas `test_t1` a `test_t5` con el código original: 9 FAILED y el resumen `9 failed, 17 passed` |
| 2 | `02-pytest-config-antes.png` | `grep -E '::test_\|passed\|failed' seguridad/lab2/despues/evidencias/pytest-config-antes.txt \| grep -v '^FAILED'` | Las pruebas de las filas 2 y 19 antes de corregirlas: `10 failed, 1 passed` |
| 3 | `03-pytest-despues.png` | `.venv/bin/python -m pytest -v` (en vivo) | Las 37 pruebas en PASSED |

## La app corregida (`despues/evidencias/curl.txt`)

| # | Archivo | Comando | Qué mostrar |
|---|---|---|---|
| 4 | `04-t2-rol-y-hash.png` | `sed -n '23,25p' seguridad/lab2/despues/evidencias/curl.txt \| fold -w 150` | `"rol":"estudiante"` y `"clave":"pbkdf2_sha256$600000$…"` (ya no MD5) |
| 5 | `05-t3-secreto.png` | `sed -n '27,42p' seguridad/lab2/despues/evidencias/curl.txt \| fold -w 150` | `os.environ.get("JWT_SECRET")`, el token forjado con `HTTP 401` y `['exp', 'rol', 'sub']` |
| 6 | `06-t4-bola.png` | `sed -n '44,46p' seguridad/lab2/despues/evidencias/curl.txt \| fold -w 150` | Ana pide `/prestamos/2` y recibe `Préstamo no encontrado` |
| 7 | `07-t5-t1.png` | `sed -n '48,50p;56,58p' seguridad/lab2/despues/evidencias/curl.txt \| fold -w 150` | Beto recibe `Solo el administrador puede hacer esto` y el `UNION` devuelve `[]` |
| 8 | `08-cabeceras-debug.png` | `sed -n '60,81p' seguridad/lab2/despues/evidencias/curl.txt \| cut -c1-150` | Sin `access-control-allow-origin` ni `server`, con CSP, `x-frame-options`, `nosniff`…, y el correo repetido con `409` sin traza |
| 9 | `09-no-root.png` | `docker compose exec api id` | `uid=10001(app)`: el contenedor ya no corre como root |

## Escaneos

| # | Archivo | Comando o lugar | Qué mostrar |
|---|---|---|---|
| 10 | `10-semgrep-despues.png` | `sed -n '1,30p' seguridad/lab2/despues/evidencias/semgrep.txt` | El comando y `Findings: 0 (0 blocking)` |
| 11 | `11-zap-despues.png` | Navegador: `\\wsl.localhost\Ubuntu\home\juanm\presta-ucp\seguridad\lab2\despues\evidencias\zap.html` | Summary of Alerts con High 0 y Medium 0, y la tabla Alerts |

## Código y entrega

| # | Archivo | Comando o lugar | Qué mostrar |
|---|---|---|---|
| 12 | `12-docs-funciona.png` | Navegador: `http://127.0.0.1:8000/docs` | Swagger UI cargando bien, servido desde la propia app |
| 13 | `13-diff-codigo.png` | `git diff bdf1baa 4d9c740 -- app/main.py app/auth.py` | Los cambios del código (rojo lo que se quitó, verde lo que se puso) |
| 14 | `14-pull-request.png` | Navegador, en la página del PR en GitHub | El título y la descripción del PR |
