#!/usr/bin/env bash
# Provision disposable SkillVenom canary resources in YOUR authorized lab tenants.
# Idempotent: safe to re-run. Reads configuration from .env (see .env.example).
#
# Usage:
#   scripts/provision.sh entra|azure|github|azuredevops|all
#
# Requires the relevant CLI to be installed and logged in to the LAB tenant/org:
#   az (Azure CLI, with the azure-devops extension), gh (GitHub CLI).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
[ -f "$ROOT/.env" ] && set -a && . "$ROOT/.env" && set +a

log() { printf '\033[1;34m[provision]\033[0m %s\n' "$*"; }
need() { command -v "$1" >/dev/null 2>&1 || { echo "Missing required CLI: $1" >&2; exit 1; }; }

provision_entra() {
  need az
  : "${ENTRA_CANARY_USER_UPN:?set ENTRA_CANARY_USER_UPN in .env}"
  : "${ENTRA_CANARY_GROUP:?set ENTRA_CANARY_GROUP in .env}"
  log "Ensuring canary user $ENTRA_CANARY_USER_UPN"
  if ! az ad user show --id "$ENTRA_CANARY_USER_UPN" >/dev/null 2>&1; then
    local pw; pw="$(openssl rand -base64 24)Aa1!"
    az ad user create \
      --display-name "SkillVenom Canary" \
      --user-principal-name "$ENTRA_CANARY_USER_UPN" \
      --password "$pw" --force-change-password-next-sign-in true >/dev/null
    log "Created user. Temporary password was generated and not stored; reset it out of band if needed."
  fi
  log "Ensuring assigned security group $ENTRA_CANARY_GROUP (no roles, no licenses)"
  if ! az ad group show --group "$ENTRA_CANARY_GROUP" >/dev/null 2>&1; then
    az ad group create --display-name "$ENTRA_CANARY_GROUP" --mail-nickname "$ENTRA_CANARY_GROUP" >/dev/null
  fi
  log "Entra canary ready. Object ids:"
  az ad user show --id "$ENTRA_CANARY_USER_UPN" --query id -o tsv
  az ad group show --group "$ENTRA_CANARY_GROUP" --query id -o tsv
}

provision_azure() {
  need az
  : "${AZURE_SUBSCRIPTION_ID:?set AZURE_SUBSCRIPTION_ID in .env}"
  : "${AZURE_LOCATION:?set AZURE_LOCATION in .env}"
  az account set --subscription "$AZURE_SUBSCRIPTION_ID"
  for rg in "${AZURE_CANARY_RG_VS008:-sv008-canary-rg}" "${AZURE_CANARY_RG_VS009:-sv009-canary-rg}"; do
    log "Ensuring resource group $rg"
    az group create --name "$rg" --location "$AZURE_LOCATION" \
      --tags purpose=skillvenom-canary dispose=yes >/dev/null
  done
  log "Ensuring disposable canary principal ${AZURE_CANARY_PRINCIPAL_NAME:-skillvenom-canary-principal}"
  local app_name="${AZURE_CANARY_PRINCIPAL_NAME:-skillvenom-canary-principal}"
  local app_id; app_id="$(az ad app list --display-name "$app_name" --query '[0].appId' -o tsv)"
  if [ -z "$app_id" ]; then
    app_id="$(az ad app create --display-name "$app_name" --query appId -o tsv)"
    az ad sp create --id "$app_id" >/dev/null
  fi
  local obj_id; obj_id="$(az ad sp show --id "$app_id" --query id -o tsv)"
  log "Canary principal object id (set AZURE_CANARY_PRINCIPAL_ID in .env): $obj_id"
  log "Reminder: grant the azure-rbac-canary adapter identity a role-assignment-write role scoped ONLY to each canary RG."
}

provision_github() {
  need gh
  : "${GITHUB_ORG:?set GITHUB_ORG in .env}"
  for repo in "${GITHUB_CANARY_SINK:-sv003-canary-sink}" "${GITHUB_CANARY_REPO_VS005:-sv005-canary-repo}"; do
    log "Ensuring private repo $GITHUB_ORG/$repo"
    if ! gh repo view "$GITHUB_ORG/$repo" >/dev/null 2>&1; then
      gh repo create "$GITHUB_ORG/$repo" --private \
        --description "SkillVenom disposable canary - do not use for anything else" >/dev/null
    fi
  done
  log "GitHub canary repos ready."
}

provision_azuredevops() {
  need az
  : "${ADO_ORG:?set ADO_ORG in .env}"
  for proj in "${ADO_CANARY_PROJECT_VS004:-sv004-canary-project}" "${ADO_CANARY_PROJECT_VS006:-sv006-canary-project}"; do
    log "Ensuring Azure DevOps project $proj"
    if ! az devops project show --org "$ADO_ORG" --project "$proj" >/dev/null 2>&1; then
      az devops project create --org "$ADO_ORG" --name "$proj" \
        --description "SkillVenom disposable canary" --visibility private >/dev/null
    fi
  done
  log "Azure DevOps canary projects ready. Import use-cases/azure-devops/vs004/deploy/azure-pipelines.yml into the VS004 project as needed."
}

case "${1:-}" in
  entra) provision_entra ;;
  azure) provision_azure ;;
  github) provision_github ;;
  azuredevops) provision_azuredevops ;;
  all) provision_entra; provision_azure; provision_github; provision_azuredevops ;;
  *) echo "Usage: $0 entra|azure|github|azuredevops|all" >&2; exit 2 ;;
esac
