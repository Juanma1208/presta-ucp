# Swagger UI servido por la app

- Paquete: `swagger-ui-dist@5.34.1` (npm, publicado el 2026-10-30), licencia Apache 2.0 (`LICENSE`, `NOTICE`).
- Integridad del paquete verificada contra npm: `sha512-VSr8fXfI93obYaQicLJbLUKGRxDojj/SfRJDDLCioGTUBj4BK/Nj4eE9jCeCAnJxVLi7iS+08PbiZLyrQKBkJQ==`
- Se sirve desde `/static/swagger/` en lugar del CDN para que `/docs` no cargue scripts de otro dominio (alertas ZAP 90003 y 10017) y la CSP pueda ser `script-src 'self'`.
- `docs-init.js` es propio: reemplaza el `<script>` en línea que genera FastAPI.
