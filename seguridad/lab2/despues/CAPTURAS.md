# Lab 2 · Capturas del estado corregido (después)

Guardar las imágenes en `seguridad/lab2/despues/capturas/`. Todas se toman desde `~/presta-ucp`, en la rama `lab2/top5-correcciones`. **No volver a ejecutar `verificar.sh`**: las capturas 3 a 6 leen el `curl.txt` que ya quedó generado.

| Evidencia | Archivo | Comando | Qué mostrar |
|---|---|---|---|
| 1 | `01-pytest-antes.png` | `grep -E '::test_t\|passed\|failed' seguridad/lab2/antes/evidencias/pytest.txt \| grep -v '^FAILED'` | Las pruebas `test_t1` a `test_t5` con código original: 9 FAILED y el resumen `9 failed, 17 passed` |
| 2 | `02-pytest-despues.png` | `.venv/bin/python -m pytest -v tests/test_lab2_top5.py` (en vivo) | Las 13 pruebas del top 5 en PASSED |
| 3 | `03-t2-rol.png` | `sed -n '23,25p' seguridad/lab2/despues/evidencias/curl.txt \| fold -w 150` | El registro con `"rol":"admin"` queda como `"rol":"estudiante"` |
| 4 | `04-t3-secreto.png` | `sed -n '27,42p' seguridad/lab2/despues/evidencias/curl.txt \| fold -w 150` | `SECRET_KEY = os.environ.get("JWT_SECRET")`, el token forjado con `HTTP 401` y `['exp', 'rol', 'sub']` |
| 5 | `05-t4-bola.png` | `sed -n '44,46p' seguridad/lab2/despues/evidencias/curl.txt \| fold -w 150` | Ana pide `/prestamos/2` y recibe `Préstamo no encontrado` |
| 6 | `06-t5-t1.png` | `sed -n '48,50p;56,58p' seguridad/lab2/despues/evidencias/curl.txt \| fold -w 150` | Beto recibe `Solo el administrador puede hacer esto` y el `UNION` devuelve `[]` |
| 7 | `07-semgrep-despues.png` | `sed -n '36,70p' seguridad/lab2/despues/evidencias/semgrep.txt` | `3 Code Findings`, sin `jwt-python-hardcoded-secret` |
| 8 | `08-diff-codigo.png` | `git diff bdf1baa bc09098 -- app/main.py app/auth.py` | Los cambios del código (rojo lo que se quitó, verde lo que se puso) |
| 9 | `09-pull-request.png` | Navegador, en la página del PR en GitHub | El título y la descripción del PR |
