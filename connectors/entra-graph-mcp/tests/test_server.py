from dataclasses import dataclass
from typing import Any

import pytest

from server import ConfigurationError, Settings, add_member, inspect_membership


@dataclass
class FakeResponse:
    body: dict[str, Any]

    def json(self) -> dict[str, Any]:
        return self.body


class FakeGraphClient:
    def __init__(self, is_member: bool = False) -> None:
        self.is_member = is_member
        self.calls: list[tuple[str, str, dict[str, Any]]] = []

    def request(self, method: str, path: str, **kwargs: Any) -> FakeResponse:
        self.calls.append((method, path, kwargs))
        if path.startswith("/users/"):
            return FakeResponse(
                {
                    "id": "user-id",
                    "userPrincipalName": "vs001@azurehacking.com",
                    "accountEnabled": True,
                    "userType": "Member",
                }
            )
        if path.startswith("/groups?"):
            return FakeResponse(
                {
                    "value": [
                        {
                            "id": "group-id",
                            "displayName": "ai-venom",
                            "securityEnabled": True,
                            "groupTypes": [],
                            "isAssignableToRole": False,
                        }
                    ]
                }
            )
        if path.endswith("/checkMemberGroups"):
            return FakeResponse({"value": ["group-id"] if self.is_member else []})
        if path.endswith("/members/$ref"):
            self.is_member = True
            return FakeResponse({})
        raise AssertionError(f"Unexpected request: {method} {path}")


SETTINGS = Settings(
    allowed_user_upn="vs001@azurehacking.com",
    allowed_group="ai-venom",
    write_confirmation="ADD vs001@azurehacking.com TO ai-venom",
)


def test_inspect_membership_is_read_only() -> None:
    graph = FakeGraphClient(is_member=False)

    result = inspect_membership(
        graph, SETTINGS, "vs001@azurehacking.com", "ai-venom"
    )

    assert result["is_member"] is False
    assert all("/members/$ref" not in path for _, path, _ in graph.calls)


def test_add_member_requires_server_arming_before_graph_resolution() -> None:
    graph = FakeGraphClient()
    unarmed_settings = Settings(
        allowed_user_upn="vs001@azurehacking.com",
        allowed_group="ai-venom",
        write_confirmation="not-armed",
    )

    with pytest.raises(ConfigurationError, match="not armed"):
        add_member(
            graph,
            unarmed_settings,
            "vs001@azurehacking.com",
            "ai-venom",
        )

    assert graph.calls == []


def test_add_member_rejects_non_allowlisted_target() -> None:
    graph = FakeGraphClient()

    with pytest.raises(ConfigurationError, match="outside"):
        add_member(
            graph,
            SETTINGS,
            "someone@example.com",
            "ai-venom",
        )

    assert graph.calls == []


def test_add_member_writes_and_verifies() -> None:
    graph = FakeGraphClient(is_member=False)

    result = add_member(
        graph,
        SETTINGS,
        "vs001@azurehacking.com",
        "ai-venom",
    )

    assert result["status"] == "added"
    assert result["is_member"] is True
    assert sum(path.endswith("/members/$ref") for _, path, _ in graph.calls) == 1