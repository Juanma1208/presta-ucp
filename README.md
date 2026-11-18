# PrestaUCP

API para el préstamo de equipos de la universidad (portátiles, cámaras, proyectores y tablets). Los estudiantes se registran, consultan el catálogo y piden equipos prestados por unos días. El administrador agrega equipos y registra las devoluciones.

Proyecto integrador del curso de Desarrollo Seguro.

## Stack

- Python 3.12 y FastAPI
- SQLite (`sqlite3` de Python)
- Tokens JWT con PyJWT
- Pruebas con pytest
- Docker Compose

## Cómo ejecutarla

Con Docker (solo escucha en `127.0.0.1`):

```bash
docker compose up -d --build
```

O en local, con un entorno virtual:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

La documentación de la API queda en http://127.0.0.1:8000/docs y la especificación OpenAPI en http://127.0.0.1:8000/openapi.json.

## Pruebas

```bash
pytest
```

## Rutas

| Método | Ruta | Descripción |
|---|---|---|
| POST | `/registro` | Crear una cuenta |
| POST | `/login` | Iniciar sesión y obtener el token |
| GET | `/me` | Ver mis datos |
| GET | `/equipos?buscar=` | Catálogo de equipos, con búsqueda por nombre |
| POST | `/equipos` | Agregar un equipo (administrador) |
| POST | `/prestamos` | Pedir un equipo prestado |
| GET | `/prestamos` | Ver mis préstamos (el administrador ve todos) |
| GET | `/prestamos/{id}` | Ver el detalle de un préstamo |
| POST | `/prestamos/{id}/devolver` | Registrar la devolución |

Las rutas protegidas usan la cabecera `Authorization: Bearer <token>`.

## Reglas

- Cada estudiante puede tener máximo 2 préstamos activos.
- Un préstamo dura 3 días por defecto.
- Solo se presta un equipo disponible.

## Usuarios de prueba

Se crean automáticamente la primera vez que arranca la app.

| Correo | Contraseña | Rol |
|---|---|---|
| `admin@presta.edu.co` | `admin123` | admin |
| `ana@presta.edu.co` | `ana12345` | estudiante |
| `beto@presta.edu.co` | `beto12345` | estudiante |
