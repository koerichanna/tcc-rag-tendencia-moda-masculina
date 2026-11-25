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

# Apaga as imagens que nenhum contêiner usa (versões antigas dos dois ambientes) ANTES de baixar
# a nova. O prune simples só removia imagens sem tag, e as antigas (tag = SHA) lotaram o disco de
# 30 GB em 25/11/2026. A versão anterior deste ambiente continua no GHCR para o rollback.
docker image prune -a -f > /dev/null
livre_mb=$(df -Pm / | awk 'NR==2 {print $4}')
if [ "$livre_mb" -lt 3000 ]; then
  echo "ERRO: só ${livre_mb} MB livres no disco; o deploy precisa de pelo menos 3000 MB"
  exit 1
fi

# Backup: scripts na versão deste deploy e cron diário às 06h UTC (03h de Brasília)
for script in backup.sh restaurar.sh; do
  git show "$TAG:deploy/$script" > "$DIR/$script"
  chmod 700 "$DIR/$script"
done
mkdir -p "$DIR/backups"
printf '%s\n' "# Backup diario dos bancos (instalado pelo deploy.sh do projeto-moda)" \
  "0 6 * * * root $DIR/backup.sh >> $DIR/backups/backup.log 2>&1" > /etc/cron.d/projeto-moda-backup
chmod 644 /etc/cron.d/projeto-moda-backup
# Guarda o estado atual antes de atualizar (e de rodar migrations). Falha aqui não trava o deploy.
"$DIR/backup.sh" "$AMBIENTE" || echo "AVISO: backup antes do deploy falhou"

compose() {
  docker compose -p "moda-$AMBIENTE" --env-file "$ENV_FILE" -f "$COMPOSE_FILE" "$@"
}

compose pull --quiet
compose up -d --wait --quiet-pull 2>&1 | tail -n 5
# idempotente: atualiza a base de tendências sem duplicar nem apagar o que veio da API
compose exec -T backend python ingestion.py </dev/null

echo "Deploy de $TAG em $AMBIENTE concluido"
