from typing import Any

import pytest

from server import (
    READER_ROLE_ID,
    ConfigurationError,
    Settings,
    assign_role,
    inspect_assignments,
    require_allowed_target,
)

PRINCIPAL = "11111111-1111-1111-1111-111111111111"
SCOPE = "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/sv008-canary-rg"
SETTINGS = Settings(
    allowed_principal_id=PRINCIPAL,
    allowed_scope=SCOPE,
    write_confirmation=f"ASSIGN Reader TO {PRINCIPAL} ON {SCOPE}",
)


class FakeRbacClient:
    def __init__(self, has_reader: bool = False) -> None:
        self.has_reader = has_reader
        self.created: list[tuple[str, str, str]] = []

    def list_assignments(self, scope: str, principal_id: str) -> list[dict[str, Any]]:
        if self.has_reader:
            return [{"id": "existing", "role_definition_id": f"/x/{READER_ROLE_ID}"}]
        return []

    def create_assignment(
        self, scope: str, principal_id: str, role_definition_id: str
    ) -> dict[str, Any]:
        self.created.append((scope, principal_id, role_definition_id))
        self.has_reader = True
        return {"id": "new-assignment", "role_definition_id": role_definition_id}


def test_inspect_is_read_only() -> None:
    client = FakeRbacClient()
    result = inspect_assignments(client, SETTINGS, PRINCIPAL, SCOPE)
    assert result["assignments"] == []
    assert client.created == []


def test_assign_requires_server_arming() -> None:
    client = FakeRbacClient()
    unarmed = Settings(
        allowed_principal_id=PRINCIPAL, allowed_scope=SCOPE, write_confirmation="nope"
    )
    with pytest.raises(ConfigurationError, match="not armed"):
        assign_role(client, unarmed, PRINCIPAL, SCOPE)
    assert client.created == []


def test_assign_rejects_non_allowlisted_principal() -> None:
    client = FakeRbacClient()
    with pytest.raises(ConfigurationError, match="outside"):
        assign_role(client, SETTINGS, "99999999-9999-9999-9999-999999999999", SCOPE)
    assert client.created == []


def test_assign_rejects_broad_scope() -> None:
    sub_scope = "/subscriptions/00000000-0000-0000-0000-000000000000"
    broad = Settings(
        allowed_principal_id=PRINCIPAL,
        allowed_scope=sub_scope,
        write_confirmation=f"ASSIGN Reader TO {PRINCIPAL} ON {sub_scope}",
    )
    with pytest.raises(ConfigurationError, match="resource-group"):
        require_allowed_target(broad, PRINCIPAL, sub_scope)


def test_assign_writes_reader_and_is_idempotent() -> None:
    client = FakeRbacClient(has_reader=False)
    result = assign_role(client, SETTINGS, PRINCIPAL, SCOPE)
    assert result["status"] == "assigned"
    assert len(client.created) == 1
    assert client.created[0][2].endswith(READER_ROLE_ID)

    again = assign_role(client, SETTINGS, PRINCIPAL, SCOPE)
    assert again["status"] == "unchanged"
    assert len(client.created) == 1
