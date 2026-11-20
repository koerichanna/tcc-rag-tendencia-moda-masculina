#!/usr/bin/env bash
# Backup dos bancos PostgreSQL da VM (pg_dump em formato custom, já comprimido).
# Uso: backup.sh                  # produção e homologação
#      backup.sh production       # só um ambiente
# Roda todo dia pelo cron (/etc/cron.d/projeto-moda-backup, instalado pelo deploy.sh) e antes de
# cada deploy. Guarda os últimos $DIAS_BACKUP dias em $BASE_DIR/backups. Se existir
# $BASE_DIR/.env.backup com BACKUP_SAS_URL (URL de um contêiner do Azure Blob com token SAS), também
# envia uma cópia para fora da VM.
set -euo pipefail

BASE_DIR="${BASE_DIR:-/opt/projeto-moda}"
DESTINO="$BASE_DIR/backups"
DIAS_BACKUP="${DIAS_BACKUP:-7}"
AMBIENTES="${*:-production staging}"

umask 077  # os dumps têm hashes de senha: só o root lê
mkdir -p "$DESTINO"

enviar_para_azure() {
  local arquivo="$1" url
  [ -f "$BASE_DIR/.env.backup" ] || return 0
  url=$(grep -E '^BACKUP_SAS_URL=' "$BASE_DIR/.env.backup" | cut -d= -f2- || true)
  [ -n "$url" ] || return 0
  # https://conta.blob.core.windows.net/backups?sv=...  ->  .../backups/<arquivo>?sv=...
  curl -sSf -X PUT -H "x-ms-blob-type: BlockBlob" --data-binary "@$arquivo" \
    "${url%%\?*}/$(basename "$arquivo")?${url#*\?}" -o /dev/null
  echo "  cópia enviada ao Azure Blob"
}

falhas=0
for amb in $AMBIENTES; do
  db="moda-$amb-db-1"
  if ! docker inspect -f '{{.State.Running}}' "$db" 2>/dev/null | grep -q true; then
    echo "$amb: contêiner $db não está rodando, backup pulado"
    continue
  fi
  arquivo="$DESTINO/$amb-$(date +%Y%m%d-%H%M%S).dump"
  # as credenciais já estão no ambiente do contêiner do banco; nada de senha neste script
  if docker exec "$db" sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --format=custom' > "$arquivo.parcial" \
     && docker exec -i "$db" pg_restore --list < "$arquivo.parcial" > /dev/null; then
    mv "$arquivo.parcial" "$arquivo"
    echo "$amb: $(basename "$arquivo") ($(du -h "$arquivo" | cut -f1))"
    enviar_para_azure "$arquivo" || { echo "  AVISO: envio ao Azure Blob falhou"; falhas=1; }
  else
    rm -f "$arquivo.parcial"
    echo "$amb: ERRO no backup"
    falhas=1
  fi
  find "$DESTINO" -name "$amb-*.dump" -mtime +"$DIAS_BACKUP" -delete
done
exit "$falhas"
