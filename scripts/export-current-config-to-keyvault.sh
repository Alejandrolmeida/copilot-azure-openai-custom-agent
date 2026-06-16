#!/usr/bin/env bash
set -euo pipefail

# Export the local Copilot + Azure OpenAI configuration to Azure Key Vault.
#
# The API key is stored as one Key Vault secret. Non-secret runtime settings are
# stored as a separate JSON secret so another machine can bootstrap after az login.

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

AZURE_KEYVAULT_NAME="${AZURE_KEYVAULT_NAME:-}"
AZURE_KEYVAULT_CONFIG_SECRET_NAME="${AZURE_KEYVAULT_CONFIG_SECRET_NAME:-copilot-azure-config}"
AZURE_KEYVAULT_SECRET_NAME="${AZURE_KEYVAULT_SECRET_NAME:-azure-openai-api-key}"
AZURE_OPENAI_BASE_URL="${AZURE_OPENAI_BASE_URL:-}"
AZURE_OPENAI_MODEL="${AZURE_OPENAI_MODEL:-}"
AZURE_OPENAI_MAX_COMPLETION_TOKENS="${AZURE_OPENAI_MAX_COMPLETION_TOKENS:-16384}"
COPILOT_PROVIDER_MODEL_ID="${COPILOT_PROVIDER_MODEL_ID:-gpt-5.5}"
COPILOT_PROVIDER_WIRE_API="${COPILOT_PROVIDER_WIRE_API:-responses}"
COPILOT_PROVIDER_MAX_PROMPT_TOKENS="${COPILOT_PROVIDER_MAX_PROMPT_TOKENS:-1000000}"
COPILOT_PROVIDER_MAX_OUTPUT_TOKENS="${COPILOT_PROVIDER_MAX_OUTPUT_TOKENS:-$AZURE_OPENAI_MAX_COMPLETION_TOKENS}"

require_var() {
  local name="$1"
  local value="${!name:-}"
  if [[ -z "$value" ]]; then
    echo "ERROR: $name is required" >&2
    exit 2
  fi
}

require_var AZURE_KEYVAULT_NAME
require_var AZURE_OPENAI_BASE_URL
require_var AZURE_OPENAI_MODEL

if ! command -v az >/dev/null 2>&1; then
  echo "ERROR: Azure CLI is required. Install it and run az login." >&2
  exit 2
fi

if ! az account show >/dev/null 2>&1; then
  echo "Azure CLI is not logged in. Starting az login..." >&2
  az login >/dev/null
fi

if [[ -n "${AZURE_SUBSCRIPTION_ID:-}" ]]; then
  az account set --subscription "$AZURE_SUBSCRIPTION_ID"
fi

api_key="${COPILOT_PROVIDER_API_KEY:-${AZURE_OPENAI_API_KEY:-}}"
if [[ -n "$api_key" ]]; then
  az keyvault secret set \
    --vault-name "$AZURE_KEYVAULT_NAME" \
    --name "$AZURE_KEYVAULT_SECRET_NAME" \
    --value "$api_key" \
    --output none
elif [[ "${SKIP_API_KEY_EXPORT:-false}" != "true" ]]; then
  echo "ERROR: set AZURE_OPENAI_API_KEY or COPILOT_PROVIDER_API_KEY, or use SKIP_API_KEY_EXPORT=true" >&2
  exit 2
fi

config_json="$({
  AZURE_KEYVAULT_SECRET_NAME="$AZURE_KEYVAULT_SECRET_NAME" \
  AZURE_OPENAI_BASE_URL="$AZURE_OPENAI_BASE_URL" \
  AZURE_OPENAI_MODEL="$AZURE_OPENAI_MODEL" \
  AZURE_OPENAI_MAX_COMPLETION_TOKENS="$AZURE_OPENAI_MAX_COMPLETION_TOKENS" \
  COPILOT_PROVIDER_MODEL_ID="$COPILOT_PROVIDER_MODEL_ID" \
  COPILOT_PROVIDER_WIRE_API="$COPILOT_PROVIDER_WIRE_API" \
  COPILOT_PROVIDER_MAX_PROMPT_TOKENS="$COPILOT_PROVIDER_MAX_PROMPT_TOKENS" \
  COPILOT_PROVIDER_MAX_OUTPUT_TOKENS="$COPILOT_PROVIDER_MAX_OUTPUT_TOKENS" \
  COPILOT_MODEL="${COPILOT_MODEL:-$COPILOT_PROVIDER_MODEL_ID}" \
  COPILOT_CONTEXT_TIER="${COPILOT_CONTEXT_TIER:-long_context}" \
  COPILOT_REASONING_EFFORT="${COPILOT_REASONING_EFFORT:-max}" \
  COPILOT_SUBAGENT_EFFORT_LEVEL="${COPILOT_SUBAGENT_EFFORT_LEVEL:-max}" \
  COPILOT_SUBAGENT_CONTEXT_TIER="${COPILOT_SUBAGENT_CONTEXT_TIER:-long_context}" \
  python3 - <<'PY'
import json
import os

keys = [
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
]

print(json.dumps({key: os.environ[key] for key in keys if os.environ.get(key)}, separators=(",", ":")))
PY
})"

az keyvault secret set \
  --vault-name "$AZURE_KEYVAULT_NAME" \
  --name "$AZURE_KEYVAULT_CONFIG_SECRET_NAME" \
  --value "$config_json" \
  --output none

cat <<EOF
Configuration exported to Azure Key Vault.

Bootstrap variables for another machine:
AZURE_KEYVAULT_NAME=$AZURE_KEYVAULT_NAME
AZURE_KEYVAULT_CONFIG_SECRET_NAME=$AZURE_KEYVAULT_CONFIG_SECRET_NAME
AZURE_KEYVAULT_SECRET_NAME=$AZURE_KEYVAULT_SECRET_NAME
AZURE_SUBSCRIPTION_ID=${AZURE_SUBSCRIPTION_ID:-}

Next machine flow:
  az login
  export AZURE_KEYVAULT_NAME=$AZURE_KEYVAULT_NAME
  export AZURE_KEYVAULT_CONFIG_SECRET_NAME=$AZURE_KEYVAULT_CONFIG_SECRET_NAME
  export AZURE_SUBSCRIPTION_ID=${AZURE_SUBSCRIPTION_ID:-}
  ./scripts/install-from-keyvault.sh
EOF