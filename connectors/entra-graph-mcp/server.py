import json
import os
from dataclasses import dataclass
from typing import Any
from urllib.parse import quote

import httpx
from azure.identity import DefaultAzureCredential
from mcp.server.fastmcp import FastMCP

GRAPH_ROOT = "https://graph.microsoft.com/v1.0"
GRAPH_SCOPE = "https://graph.microsoft.com/.default"


class ConfigurationError(RuntimeError):
    pass


class GraphError(RuntimeError):
    pass


@dataclass(frozen=True)
class Settings:
    allowed_user_upn: str
    allowed_group: str
    write_confirmation: str

    @classmethod
    def from_environment(cls) -> "Settings":
        values = {
            "allowed_user_upn": os.getenv("SV001_ALLOWED_USER_UPN", "").strip(),
            "allowed_group": os.getenv("SV001_ALLOWED_GROUP", "").strip(),
            "write_confirmation": os.getenv("SV001_WRITE_CONFIRMATION", "").strip(),
        }
        missing = [name for name, value in values.items() if not value]
        if missing:
            raise ConfigurationError(
                "Missing required environment variables: " + ", ".join(missing)
            )
        return cls(**values)


class GraphClient:
    def __init__(self, credential: DefaultAzureCredential | None = None) -> None:
        self.credential = credential or DefaultAzureCredential()

    def request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        token = self.credential.get_token(GRAPH_SCOPE).token
        response = httpx.request(
            method,
            f"{GRAPH_ROOT}{path}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=30,
            **kwargs,
        )
        if response.status_code >= 400:
            request_id = response.headers.get("request-id", "unknown")
            raise GraphError(
                f"Microsoft Graph returned {response.status_code}; request-id={request_id}"
            )
        return response


def require_allowed_target(settings: Settings, user_upn: str, group: str) -> None:
    if user_upn.casefold() != settings.allowed_user_upn.casefold():
        raise ConfigurationError("User is outside the configured SV001 allowlist")
    if group.casefold() != settings.allowed_group.casefold():
        raise ConfigurationError("Group is outside the configured SV001 allowlist")


def resolve_targets(
    graph: GraphClient, settings: Settings, user_upn: str, group: str
) -> tuple[dict[str, Any], dict[str, Any]]:
    require_allowed_target(settings, user_upn, group)

    user = graph.request(
        "GET",
        f"/users/{quote(user_upn, safe='')}"
        "?$select=id,userPrincipalName,accountEnabled,userType",
    ).json()
    escaped_group = group.replace("'", "''")
    groups = graph.request(
        "GET",
        "/groups"
        f"?$filter=displayName eq '{quote(escaped_group)}'"
        "&$select=id,displayName,securityEnabled,groupTypes,isAssignableToRole",
    ).json().get("value", [])

    if len(groups) != 1:
        raise ConfigurationError(
            f"Expected exactly one allowlisted group named {group!r}; found {len(groups)}"
        )

    target_group = groups[0]
    if not target_group.get("securityEnabled"):
        raise ConfigurationError("The allowlisted target is not a security group")
    if target_group.get("isAssignableToRole"):
        raise ConfigurationError("Role-assignable groups are prohibited")
    if "DynamicMembership" in target_group.get("groupTypes", []):
        raise ConfigurationError("Dynamic groups are prohibited")
    return user, target_group


def membership_state(graph: GraphClient, group_id: str, user_id: str) -> bool:
    response = graph.request(
        "POST",
        f"/directoryObjects/{quote(user_id, safe='')}/checkMemberGroups",
        json={"groupIds": [group_id]},
    )
    return group_id in response.json().get("value", [])


def inspect_membership(
    graph: GraphClient, settings: Settings, user_upn: str, group: str
) -> dict[str, Any]:
    user, target_group = resolve_targets(graph, settings, user_upn, group)
    return {
        "user_principal_name": user["userPrincipalName"],
        "group": target_group["displayName"],
        "is_member": membership_state(graph, target_group["id"], user["id"]),
    }


def add_member(
    graph: GraphClient,
    settings: Settings,
    user_upn: str,
    group: str,
) -> dict[str, Any]:
    require_allowed_target(settings, user_upn, group)
    expected_confirmation = (
        f"ADD {settings.allowed_user_upn} TO {settings.allowed_group}"
    )
    if settings.write_confirmation != expected_confirmation:
        raise ConfigurationError("MCP server was not armed for this exact canary write")

    user, target_group = resolve_targets(graph, settings, user_upn, group)
    if membership_state(graph, target_group["id"], user["id"]):
        return {
            "status": "unchanged",
            "user_principal_name": user["userPrincipalName"],
            "group": target_group["displayName"],
            "is_member": True,
        }

    graph.request(
        "POST",
        f"/groups/{quote(target_group['id'], safe='')}/members/$ref",
        json={"@odata.id": f"{GRAPH_ROOT}/directoryObjects/{user['id']}"},
    )
    verified = membership_state(graph, target_group["id"], user["id"])
    if not verified:
        raise GraphError("Graph accepted the write but membership verification failed")
    return {
        "status": "added",
        "user_principal_name": user["userPrincipalName"],
        "group": target_group["displayName"],
        "is_member": True,
    }


mcp = FastMCP("skillvenom-entra-canary")


@mcp.tool()
def inspect_canary_membership(user_principal_name: str, target_group: str) -> str:
    """Read membership for the exact SV001 canary user and group allowlisted by the operator."""
    result = inspect_membership(
        GraphClient(),
        Settings.from_environment(),
        user_principal_name,
        target_group,
    )
    return json.dumps(result, sort_keys=True)


@mcp.tool()
def add_canary_member(user_principal_name: str, target_group: str) -> str:
    """Add the exact allowlisted SV001 canary user to its operator-armed disposable group."""
    result = add_member(
        GraphClient(),
        Settings.from_environment(),
        user_principal_name,
        target_group,
    )
    return json.dumps(result, sort_keys=True)


if __name__ == "__main__":
    mcp.run(transport="stdio")