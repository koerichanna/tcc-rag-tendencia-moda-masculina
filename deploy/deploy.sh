#!/usr/bin/env bash
# Executado na VM pelo pipeline (az vm run-command), sem SSH.
# Uso: deploy.sh <production|staging> <sha-do-commit>
set -euo pipefail
# o run-command devolve só o fim da saída: junta stderr no stdout e deixa o docker quieto
exec 2>&1

AMBIENTE="$1"
TAG="$2"
DIR=/opt/projeto-moda
ENV_FILE="$DIR/.env.$AMBIENTE"
COMPOSE_FILE="$DIR/compose.$AMBIENTE.yml"

cd "$DIR/repo"
git fetch --quiet origin
git show "$TAG:docker-compose.prod.yml" > "$COMPOSE_FILE"

sed -i "s/^IMAGE_TAG=.*/IMAGE_TAG=$TAG/" "$ENV_FILE"

compose() {
  docker compose -p "moda-$AMBIENTE" --env-file "$ENV_FILE" -f "$COMPOSE_FILE" "$@"
}

compose pull --quiet
compose up -d --wait --quiet-pull 2>&1 | tail -n 5
compose exec -T backend python ingestion.py --se-vazio </dev/null
docker image prune -f >/dev/null

echo "Deploy de $TAG em $AMBIENTE concluido"
