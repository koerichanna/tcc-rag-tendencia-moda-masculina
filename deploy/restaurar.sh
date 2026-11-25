#!/usr/bin/env bash
# Restaura um backup gerado pelo backup.sh.
# Uso: restaurar.sh <production|staging> <arquivo.dump>
# Antes de restaurar, faz um backup do estado atual (se a restauração for engano, dá para voltar).
# O ChromaDB não precisa de backup: o deploy.sh o reconstrói com o ingestion.py.
set -euo pipefail

AMBIENTE="${1:?informe o ambiente: production ou staging}"
ARQUIVO="${2:?informe o arquivo .dump}"
BASE_DIR="${BASE_DIR:-/opt/projeto-moda}"
[[ -f "$ARQUIVO" ]] || ARQUIVO="$BASE_DIR/backups/$ARQUIVO"
[[ -f "$ARQUIVO" ]] || { echo "arquivo não encontrado: $2"; exit 1; }

echo "1/4 backup do estado atual"
"$(dirname "$0")/backup.sh" "$AMBIENTE"

echo "2/4 parando o backend"
docker stop "moda-$AMBIENTE-backend-1" > /dev/null

echo "3/4 restaurando $(basename "$ARQUIVO")"
docker cp "$ARQUIVO" "moda-$AMBIENTE-db-1:/tmp/restaurar.dump"
docker exec "moda-$AMBIENTE-db-1" sh -c \
  'pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists --no-owner --single-transaction /tmp/restaurar.dump; s=$?; rm -f /tmp/restaurar.dump; exit $s'

echo "4/4 subindo o backend"
docker start "moda-$AMBIENTE-backend-1" > /dev/null
echo "Restauracao de $AMBIENTE concluida"
