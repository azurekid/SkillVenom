#!/usr/bin/env bash
# Remove the disposable SkillVenom canary resources created by provision.sh.
# Only deletes objects whose names match the configured canary identifiers.
#
# Usage:
#   scripts/teardown.sh entra|azure|github|azuredevops|all
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
[ -f "$ROOT/.env" ] && set -a && . "$ROOT/.env" && set +a

log() { printf '\033[1;31m[teardown]\033[0m %s\n' "$*"; }
need() { command -v "$1" >/dev/null 2>&1 || { echo "Missing required CLI: $1" >&2; exit 1; }; }

teardown_entra() {
  need az
  if [ -n "${ENTRA_CANARY_USER_UPN:-}" ] && az ad user show --id "$ENTRA_CANARY_USER_UPN" >/dev/null 2>&1; then
    log "Deleting canary user $ENTRA_CANARY_USER_UPN"; az ad user delete --id "$ENTRA_CANARY_USER_UPN"
  fi
  if [ -n "${ENTRA_CANARY_GROUP:-}" ] && az ad group show --group "$ENTRA_CANARY_GROUP" >/dev/null 2>&1; then
    log "Deleting canary group $ENTRA_CANARY_GROUP"; az ad group delete --group "$ENTRA_CANARY_GROUP"
  fi
}

teardown_azure() {
  need az
  : "${AZURE_SUBSCRIPTION_ID:?set AZURE_SUBSCRIPTION_ID in .env}"
  az account set --subscription "$AZURE_SUBSCRIPTION_ID"
  for rg in "${AZURE_CANARY_RG_VS008:-sv008-canary-rg}" "${AZURE_CANARY_RG_VS009:-sv009-canary-rg}"; do
    if az group show --name "$rg" >/dev/null 2>&1; then
      log "Deleting resource group $rg"; az group delete --name "$rg" --yes --no-wait
    fi
  done
  local app_name="${AZURE_CANARY_PRINCIPAL_NAME:-skillvenom-canary-principal}"
  local app_id; app_id="$(az ad app list --display-name "$app_name" --query '[0].appId' -o tsv)"
  if [ -n "$app_id" ]; then log "Deleting canary principal $app_name"; az ad app delete --id "$app_id"; fi
}

teardown_github() {
  need gh
  : "${GITHUB_ORG:?set GITHUB_ORG in .env}"
  for repo in "${GITHUB_CANARY_SINK:-sv003-canary-sink}" "${GITHUB_CANARY_REPO_VS005:-sv005-canary-repo}"; do
    if gh repo view "$GITHUB_ORG/$repo" >/dev/null 2>&1; then
      log "Deleting repo $GITHUB_ORG/$repo"; gh repo delete "$GITHUB_ORG/$repo" --yes
    fi
  done
}

teardown_azuredevops() {
  need az
  : "${ADO_ORG:?set ADO_ORG in .env}"
  for proj in "${ADO_CANARY_PROJECT_VS004:-sv004-canary-project}" "${ADO_CANARY_PROJECT_VS006:-sv006-canary-project}"; do
    local id; id="$(az devops project show --org "$ADO_ORG" --project "$proj" --query id -o tsv 2>/dev/null || true)"
    if [ -n "$id" ]; then log "Deleting project $proj"; az devops project delete --org "$ADO_ORG" --id "$id" --yes; fi
  done
}

case "${1:-}" in
  entra) teardown_entra ;;
  azure) teardown_azure ;;
  github) teardown_github ;;
  azuredevops) teardown_azuredevops ;;
  all) teardown_entra; teardown_azure; teardown_github; teardown_azuredevops ;;
  *) echo "Usage: $0 entra|azure|github|azuredevops|all" >&2; exit 2 ;;
esac
