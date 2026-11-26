#!/usr/bin/env bash
# Ergänzt fehlende Variablen in .env mit zufälligen Werten.
# Vorhandene Werte werden nie überschrieben, und es werden keine Werte ausgegeben.
set -euo pipefail

cd "$(dirname "$0")/.."
ENV_FILE=".env"

if [ ! -f "$ENV_FILE" ]; then
  : > "$ENV_FILE"
fi
chmod 600 "$ENV_FILE"

# Zeilenumbruch am Dateiende sicherstellen, bevor angehängt wird
if [ -s "$ENV_FILE" ] && [ "$(tail -c1 "$ENV_FILE" | wc -l)" -eq 0 ]; then
  echo >> "$ENV_FILE"
fi

add_if_missing() {
  local name="$1" value="$2"
  if grep -qE "^${name}=.+" "$ENV_FILE"; then
    echo "vorhanden:  ${name}"
  else
    sed -i.bak -E "/^${name}=\s*$/d" "$ENV_FILE" && rm -f "${ENV_FILE}.bak"
    echo "${name}=${value}" >> "$ENV_FILE"
    echo "ergänzt:    ${name}"
  fi
}

add_if_missing POSTGRES_PASSWORD "$(openssl rand -hex 24)"
add_if_missing LITELLM_MASTER_KEY "sk-$(openssl rand -hex 24)"
add_if_missing TUTOR_API_TOKEN "$(openssl rand -hex 24)"

for name in AI_HUB_BASE_URL AI_HUB_API_KEY; do
  if ! grep -qE "^${name}=.+" "$ENV_FILE"; then
    echo "FEHLT:      ${name} (bitte selbst in .env eintragen)"
  fi
done
