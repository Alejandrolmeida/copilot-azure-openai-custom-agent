#!/usr/bin/env bash
set -euo pipefail

# Generic GitHub Copilot CLI wrapper for Azure OpenAI / Azure AI Foundry.
#
# Usage:
#   cp examples/.env.example .env
#   edit .env
#   ./examples/copilot-azure-wrapper.sh --print-config
#   ./examples/copilot-azure-wrapper.sh
#
# This script intentionally contains no real endpoint or API key.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ -z "${ENV_FILE:-}" && ! -f "$ROOT_DIR/.env" && -f "$ROOT_DIR/private/.env" ]]; then
  ENV_FILE="$ROOT_DIR/private/.env"
else
  ENV_FILE="${ENV_FILE:-$ROOT_DIR/.env}"
fi

if [[ -f "$ENV_FILE" ]]; then
  # shellcheck disable=SC1090
  set -a
  source "$ENV_FILE"
  set +a
fi

load_config_from_keyvault() {
  if [[ -z "${AZURE_KEYVAULT_CONFIG_SECRET_NAME:-}" ]]; then
    return 0
  fi

  if [[ -z "${AZURE_KEYVAULT_NAME:-}" ]]; then
    echo "ERROR: AZURE_KEYVAULT_NAME is required when AZURE_KEYVAULT_CONFIG_SECRET_NAME is set" >&2
    exit 2
  fi

  if ! command -v az >/dev/null 2>&1; then
    echo "ERROR: Azure CLI is required to load configuration from Azure Key Vault" >&2
    exit 2
  fi

  local az_args=(keyvault secret show --vault-name "$AZURE_KEYVAULT_NAME" --name "$AZURE_KEYVAULT_CONFIG_SECRET_NAME" --query value -o tsv)
  if [[ -n "${AZURE_SUBSCRIPTION_ID:-}" ]]; then
    az_args+=(--subscription "$AZURE_SUBSCRIPTION_ID")
  fi

  local config_json
  config_json="$(az "${az_args[@]}")"

  # shellcheck disable=SC1090
  source <(CONFIG_JSON="$config_json" python3 - <<'PY'
import json
import os
import shlex

allowed_keys = {
    "AZURE_OPENAI_BASE_URL",
    "AZURE_OPENAI_MODEL",
    "AZURE_OPENAI_MAX_COMPLETION_TOKENS",
    "AZURE_KEYVAULT_SECRET_NAME",
    "COPILOT_PROVIDER_MODEL_ID",
    "COPILOT_PROVIDER_WIRE_API",
    "COPILOT_PROVIDER_MAX_PROMPT_TOKENS",
    "COPILOT_PROVIDER_MAX_OUTPUT_TOKENS",
    "COPILOT_MODEL",
    "COPILOT_CONTEXT_TIER",
    "COPILOT_REASONING_EFFORT",
    "COPILOT_SUBAGENT_EFFORT_LEVEL",
    "COPILOT_SUBAGENT_CONTEXT_TIER",
}

data = json.loads(os.environ["CONFIG_JSON"])
if not isinstance(data, dict):
    raise SystemExit("Key Vault configuration secret must contain a JSON object")

for key in sorted(allowed_keys):
    value = data.get(key)
    if value is None or value == "":
        continue
    print(f"export {key}={shlex.quote(str(value))}")
PY
  )
}

load_config_from_keyvault

AZURE_OPENAI_BASE_URL="${AZURE_OPENAI_BASE_URL:-}"
AZURE_OPENAI_MODEL="${AZURE_OPENAI_MODEL:-}"
AZURE_OPENAI_MAX_COMPLETION_TOKENS="${AZURE_OPENAI_MAX_COMPLETION_TOKENS:-16384}"

if [[ -z "$AZURE_OPENAI_BASE_URL" ]]; then
  echo "ERROR: AZURE_OPENAI_BASE_URL is required" >&2
  exit 2
fi

if [[ -z "$AZURE_OPENAI_MODEL" ]]; then
  echo "ERROR: AZURE_OPENAI_MODEL is required" >&2
  exit 2
fi

# Copilot CLI's Azure provider expects only the resource host, not /openai/v1.
AZURE_OPENAI_RESOURCE_URL="${AZURE_OPENAI_BASE_URL%%/openai/v1*}"
AZURE_OPENAI_RESOURCE_URL="${AZURE_OPENAI_RESOURCE_URL%/}"

load_api_key() {
  if [[ -n "${COPILOT_PROVIDER_API_KEY:-}" ]]; then
    return 0
  fi

  if [[ -n "${AZURE_OPENAI_API_KEY:-}" ]]; then
    export COPILOT_PROVIDER_API_KEY="$AZURE_OPENAI_API_KEY"
    return 0
  fi

  # Optional Azure Key Vault loading. Requires Azure CLI login and env vars.
  if [[ -n "${AZURE_KEYVAULT_NAME:-}" && -n "${AZURE_KEYVAULT_SECRET_NAME:-}" ]]; then
    local az_args=(keyvault secret show --vault-name "$AZURE_KEYVAULT_NAME" --name "$AZURE_KEYVAULT_SECRET_NAME" --query value -o tsv)
    if [[ -n "${AZURE_SUBSCRIPTION_ID:-}" ]]; then
      az_args+=(--subscription "$AZURE_SUBSCRIPTION_ID")
    fi
    export COPILOT_PROVIDER_API_KEY="$(az "${az_args[@]}")"
    return 0
  fi

  echo "ERROR: provide AZURE_OPENAI_API_KEY, COPILOT_PROVIDER_API_KEY, or Azure Key Vault env vars" >&2
  exit 2
}

configure_subagents() {
  local settings_file="${COPILOT_HOME:-$HOME/.copilot}/settings.json"
  mkdir -p "$(dirname "$settings_file")"

  python - "$settings_file" <<'PY'
import json
import os
import sys
from pathlib import Path

settings_path = Path(sys.argv[1])
try:
    data = json.loads(settings_path.read_text()) if settings_path.exists() else {}
except json.JSONDecodeError:
    backup_path = settings_path.with_suffix(settings_path.suffix + ".bak")
    backup_path.write_text(settings_path.read_text())
    data = {}

model = os.environ.get("COPILOT_PROVIDER_MODEL_ID") or os.environ.get("COPILOT_MODEL") or "gpt-5.5"
effort = os.environ.get("COPILOT_SUBAGENT_EFFORT_LEVEL", "max")
context = os.environ.get("COPILOT_SUBAGENT_CONTEXT_TIER", "long_context")

agent_names = {
    "explore",
    "task",
    "general-purpose",
    "code-review",
    "research",
}

agents_dir = Path.cwd() / ".github" / "agents"
if agents_dir.is_dir():
    for agent_file in agents_dir.glob("*.agent.md"):
        agent_names.add(agent_file.name.removesuffix(".agent.md"))

agents = data.setdefault("subagents", {}).setdefault("agents", {})
for name in sorted(agent_names):
    agents[name] = {
        "model": model,
        "effortLevel": effort,
        "contextTier": context,
    }

settings_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
PY
}

export COPILOT_PROVIDER_TYPE="azure"
export COPILOT_PROVIDER_BASE_URL="$AZURE_OPENAI_RESOURCE_URL"
export COPILOT_PROVIDER_WIRE_API="${COPILOT_PROVIDER_WIRE_API:-responses}"
export COPILOT_PROVIDER_MODEL_ID="${COPILOT_PROVIDER_MODEL_ID:-gpt-5.5}"
export COPILOT_PROVIDER_WIRE_MODEL="${COPILOT_PROVIDER_WIRE_MODEL:-$AZURE_OPENAI_MODEL}"
export COPILOT_MODEL="${COPILOT_MODEL:-$COPILOT_PROVIDER_MODEL_ID}"
export COPILOT_PROVIDER_MAX_PROMPT_TOKENS="${COPILOT_PROVIDER_MAX_PROMPT_TOKENS:-1000000}"
export COPILOT_PROVIDER_MAX_OUTPUT_TOKENS="${COPILOT_PROVIDER_MAX_OUTPUT_TOKENS:-$AZURE_OPENAI_MAX_COMPLETION_TOKENS}"

if [[ "${1:-}" == "--print-config" || "${1:-}" == "--show-config" ]]; then
  cat <<EOF
Copilot CLI Azure custom provider configuration

Azure source variables:
  AZURE_OPENAI_BASE_URL=$AZURE_OPENAI_BASE_URL
  AZURE_OPENAI_MODEL=$AZURE_OPENAI_MODEL
  AZURE_OPENAI_MAX_COMPLETION_TOKENS=$AZURE_OPENAI_MAX_COMPLETION_TOKENS

Copilot CLI BYOK provider variables:
  COPILOT_PROVIDER_TYPE=$COPILOT_PROVIDER_TYPE
  COPILOT_PROVIDER_BASE_URL=$COPILOT_PROVIDER_BASE_URL
  COPILOT_PROVIDER_WIRE_API=$COPILOT_PROVIDER_WIRE_API
  COPILOT_PROVIDER_MODEL_ID=$COPILOT_PROVIDER_MODEL_ID
  COPILOT_PROVIDER_WIRE_MODEL=$COPILOT_PROVIDER_WIRE_MODEL
  COPILOT_MODEL=$COPILOT_MODEL
  COPILOT_PROVIDER_MAX_PROMPT_TOKENS=$COPILOT_PROVIDER_MAX_PROMPT_TOKENS
  COPILOT_PROVIDER_MAX_OUTPUT_TOKENS=$COPILOT_PROVIDER_MAX_OUTPUT_TOKENS

Secret handling:
  Runtime configuration can be loaded from Azure Key Vault secret: ${AZURE_KEYVAULT_CONFIG_SECRET_NAME:-<not configured>}
  COPILOT_PROVIDER_API_KEY is loaded from env, .env, or Azure Key Vault and is not printed.
EOF
  exit 0
fi

load_api_key

if [[ "${COPILOT_CONFIGURE_SUBAGENTS:-true}" == "true" ]]; then
  configure_subagents
fi

exec copilot \
  --model "$COPILOT_MODEL" \
  --context "${COPILOT_CONTEXT_TIER:-long_context}" \
  --effort "${COPILOT_REASONING_EFFORT:-max}" \
  "$@"
