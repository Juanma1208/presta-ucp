#!/usr/bin/env bash
# Lab 2 · Pruebas con curl contra PrestaUCP para la revisión ASVS.
# Uso:  bash seguridad/lab2/verificar.sh antes      (o despues)
# Requiere la app recién levantada:  docker compose down -v && docker compose up -d --build
# Solo contra 127.0.0.1 (Ley 1273 de 2009).
set -u
ETQ=${1:?Indica la etapa: antes o despues}
B=http://127.0.0.1:8000
J='Content-Type: application/json'
DIR="$(cd "$(dirname "$0")" && pwd)/$ETQ/evidencias"
mkdir -p "$DIR"

paso() { printf '\n==================== %s ====================\n' "$1"; }
run()  { printf '$ %s\n' "$*"; eval "$@"; printf '\n'; }
token() { curl -s -X POST $B/login -H "$J" -d "{\"correo\":\"$1\",\"clave\":\"$2\"}" | python3 -c 'import sys,json; print(json.load(sys.stdin).get("token",""))'; }

{
echo "# Verificación «$ETQ» contra $B"
echo "# Fecha: $(date '+%Y-%m-%d %H:%M:%S %z') · Maquina: $(hostname) · Usuario: $USER · Commit: $(git -C "$DIR" rev-parse --short HEAD)"

ANA="Authorization: Bearer $(token ana@presta.edu.co ana12345)"
BETO="Authorization: Bearer $(token beto@presta.edu.co beto12345)"

paso "Fila 1 y 3 · Contrasena debil y login sin limite de intentos (ASVS 6.2.1, 6.3.1)"
run "curl -s -X POST $B/registro -H '$J' -d '{\"nombre\":\"Prueba\",\"documento\":\"111\",\"correo\":\"debil@presta.edu.co\",\"telefono\":\"300\",\"clave\":\"1\"}'"
echo '## Login repetido 12 veces con clave incorrecta: ningun 429'
run "for i in \$(seq 12); do curl -s -o /dev/null -w '%{http_code} ' -X POST $B/login -H '$J' -d '{\"correo\":\"ana@presta.edu.co\",\"clave\":\"mala\"}'; done; echo"

paso "Fila 2 y 12 · El registro devuelve el hash MD5 de la contrasena (ASVS 11.4.2, 15.3.1)"
echo "MD5 de '1' = $(printf 1 | md5sum | cut -d' ' -f1)  (si coincide con el campo clave de arriba, la contrasena se guarda en MD5)"

paso "Fila 4 · El login distingue correo inexistente de clave incorrecta (ASVS 6.3.8)"
run "curl -s -o /dev/null -w 'correo que no existe -> HTTP %{http_code}\n' -X POST $B/login -H '$J' -d '{\"correo\":\"nadie@x.co\",\"clave\":\"x\"}'"
run "curl -s -o /dev/null -w 'correo real, clave mala -> HTTP %{http_code}\n' -X POST $B/login -H '$J' -d '{\"correo\":\"ana@presta.edu.co\",\"clave\":\"x\"}'"

paso "Fila 10 · Asignacion masiva: el registro acepta el campo rol (ASVS 15.3.3) [T2 del Lab 1]"
run "curl -s -X POST $B/registro -H '$J' -d '{\"nombre\":\"Intruso\",\"documento\":\"222\",\"correo\":\"intruso@presta.edu.co\",\"telefono\":\"301\",\"clave\":\"clave1234\",\"rol\":\"admin\"}'"

paso "Fila 7 y 17 · El secreto del JWT esta en el codigo (ASVS 9.1.2, 13.3.1) [T3 del Lab 1]"
run "grep -n 'SECRET_KEY' app/auth.py"
echo '## Token forjado con ese secreto, con rol admin, aceptado por una ruta de administrador'
run "python3 -c \"import jwt; print(jwt.encode({'sub':'999','rol':'admin','exp':4102444800},'presta-ucp-2026',algorithm='HS256'))\" > /tmp/tok.txt; curl -s -o /dev/null -w 'POST /equipos con token forjado -> HTTP %{http_code}\n' -X POST $B/equipos -H '$J' -H \"Authorization: Bearer \$(cat /tmp/tok.txt)\" -d '{\"nombre\":\"x\",\"tipo\":\"y\"}'"

paso "Fila 8 · El token no tiene expiracion (ASVS 9.2.1) [T3 del Lab 1]"
run "python3 -c \"import jwt; t='$(token ana@presta.edu.co ana12345)'; print(sorted(jwt.decode(t,options={'verify_signature':False}).keys()))\""

paso "Fila 9 · BOLA: Ana consulta el prestamo de Beto (ASVS 8.2.2) [T4 del Lab 1]"
run "curl -s $B/prestamos/2 -H '$ANA'"

paso "Fila 11 · Devolver un prestamo no exige rol admin (ASVS 8.3.1) [T5 del Lab 1]"
run "curl -s -X POST $B/prestamos/2/devolver -H '$BETO'"

paso "Fila 13 · Lado de negocio: el estudiante fija los dias del prestamo (ASVS 2.2.1) [T-09 del Lab 1]"
run "curl -s -X POST $B/prestamos -H '$J' -H '$ANA' -d '{\"equipo_id\":2,\"dias\":365}'"

paso "Fila 14 · Inyeccion SQL en la busqueda de equipos (ASVS 1.2.4) [T1 del Lab 1]"
run "curl -s \"$B/equipos?buscar=%27%20UNION%20SELECT%20id,correo,clave,rol%20FROM%20usuarios--\""

paso "Fila 19 · Cabeceras de respuesta, CORS abierto y servidor (ASVS 13.4.x, 3.4.x)"
run "curl -s -i $B/salud -H 'Origin: https://malo.example' | tr -d '\r' | sed '/^$/q'"

paso "Fila 19 · Debug encendido: un error devuelve la traza de Python (ASVS 13.4.2)"
run "curl -s -X POST $B/registro -H '$J' -d '{\"nombre\":\"Dup\",\"documento\":\"1\",\"correo\":\"ana@presta.edu.co\",\"telefono\":\"1\",\"clave\":\"clave1234\"}' | head -c 400; echo"

paso "Controles que SI estan bien (para que la tabla no quede toda en No cumple)"
run "curl -s -o /dev/null -w 'Ana (estudiante) crea equipo -> HTTP %{http_code} (403 = bien)\n' -X POST $B/equipos -H '$J' -H '$ANA' -d '{\"nombre\":\"x\",\"tipo\":\"y\"}'"
run "curl -s -o /dev/null -w 'GET /prestamos sin token -> HTTP %{http_code} (401/403 = bien)\n' $B/prestamos"
run "curl -s \"$B/equipos?buscar=Canon\""
} 2>&1 | tee "$DIR/curl.txt"
