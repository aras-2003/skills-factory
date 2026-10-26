#!/usr/bin/env python3
"""Exercise local Supabase REST authorization without logging local keys."""

from __future__ import annotations

import json
import os
import secrets
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid


def cli_env() -> dict[str, str]:
    result = subprocess.run(
        ["supabase", "status", "--output", "env"],
        check=True,
        text=True,
        capture_output=True,
    )
    values: dict[str, str] = {}
    for line in result.stdout.splitlines():
        if "=" not in line:
            continue
        name, value = line.split("=", 1)
        values[name.strip()] = value.strip().strip('"').strip("'")
    return values


def request(
    url: str,
    *,
    api_key: str,
    bearer: str,
    method: str = "GET",
    body: dict[str, object] | None = None,
) -> tuple[int, bytes]:
    headers = {
        "apikey": api_key,
        "Authorization": f"Bearer {bearer}",
        "Accept": "application/json",
    }
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
        headers["Prefer"] = "return=minimal"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as error:
        return error.code, error.read()


def expect_denied(status: int, role: str, operation: str) -> None:
    if status not in (401, 403):
        raise AssertionError(f"{role} {operation} should be denied; HTTP {status}")


def main() -> int:
    env = cli_env()
    api_url = env.get("API_URL") or env.get("SUPABASE_URL")
    anon_key = env.get("ANON_KEY") or env.get("SUPABASE_ANON_KEY")
    service_key = env.get("SERVICE_ROLE_KEY") or env.get("SUPABASE_SERVICE_ROLE_KEY")
    if not api_url or not anon_key or not service_key:
        raise RuntimeError("local Supabase status did not provide the expected API variables")

    rest_url = api_url.rstrip("/") + "/rest/v1/accounts?select=account_id&limit=1"
    status, _ = request(rest_url, api_key=anon_key, bearer=anon_key)
    expect_denied(status, "anon", "SELECT")

    identity = uuid.uuid4().hex
    email = f"sf-grant-{identity}@example.com"
    password = secrets.token_urlsafe(32)
    signup_url = api_url.rstrip("/") + "/auth/v1/signup"
    signup_status, signup_body = request(
        signup_url,
        api_key=anon_key,
        bearer=anon_key,
        method="POST",
        body={"email": email, "password": password},
    )
    if signup_status not in (200, 201):
        raise AssertionError(f"local synthetic user setup failed; HTTP {signup_status}")
    signup = json.loads(signup_body or b"{}")
    access_token = signup.get("access_token")
    if not access_token:
        token_url = api_url.rstrip("/") + "/auth/v1/token?grant_type=password"
        token_status, token_body = request(
            token_url,
            api_key=anon_key,
            bearer=anon_key,
            method="POST",
            body={"email": email, "password": password},
        )
        if token_status != 200:
            raise AssertionError(f"local synthetic login failed; HTTP {token_status}")
        access_token = json.loads(token_body).get("access_token")
    if not access_token:
        raise AssertionError("local Auth did not issue an authenticated access token")

    status, _ = request(rest_url, api_key=anon_key, bearer=access_token)
    expect_denied(status, "authenticated", "SELECT")
    unauthorized_write_url = api_url.rstrip("/") + "/rest/v1/accounts"
    status, _ = request(
        unauthorized_write_url,
        api_key=anon_key,
        bearer=anon_key,
        method="POST",
        body={"provider": f"unauthorized-{identity}"},
    )
    expect_denied(status, "anon", "INSERT")
    status, _ = request(
        unauthorized_write_url,
        api_key=anon_key,
        bearer=access_token,
        method="POST",
        body={"provider": f"unauthorized-authenticated-{identity}"},
    )
    expect_denied(status, "authenticated", "INSERT")

    permitted_value = f"iteration-04-{identity}"
    status, _ = request(
        unauthorized_write_url,
        api_key=service_key,
        bearer=service_key,
        method="POST",
        body={"provider": permitted_value},
    )
    if status not in (201, 204):
        raise AssertionError(f"service_role INSERT should succeed; HTTP {status}")
    permitted_url = (
        api_url.rstrip("/")
        + "/rest/v1/accounts?select=provider&provider=eq."
        + urllib.parse.quote(permitted_value, safe="")
    )
    status, body = request(permitted_url, api_key=service_key, bearer=service_key)
    if status != 200 or permitted_value.encode("utf-8") not in body:
        raise AssertionError(f"service_role could not read its synthetic test row; HTTP {status}")

    updated_value = permitted_value + "-updated"
    account_filter = (
        api_url.rstrip("/")
        + "/rest/v1/accounts?provider=eq."
        + urllib.parse.quote(permitted_value, safe="")
    )
    status, _ = request(
        account_filter,
        api_key=service_key,
        bearer=service_key,
        method="PATCH",
        body={"provider": updated_value},
    )
    if status not in (200, 204):
        raise AssertionError(f"service_role UPDATE should succeed; HTTP {status}")
    updated_account_url = (
        api_url.rstrip("/")
        + "/rest/v1/accounts?select=provider&provider=eq."
        + urllib.parse.quote(updated_value, safe="")
    )
    status, body = request(updated_account_url, api_key=service_key, bearer=service_key)
    if status != 200 or updated_value.encode("utf-8") not in body:
        raise AssertionError(f"service_role UPDATE did not persist its synthetic value; HTTP {status}")
    status, _ = request(
        updated_account_url,
        api_key=service_key,
        bearer=service_key,
        method="DELETE",
    )
    expect_denied(status, "service_role", "DELETE")

    source_title = f"iteration-04-source-{identity}"
    source_url = api_url.rstrip("/") + "/rest/v1/sources"
    status, _ = request(
        source_url,
        api_key=service_key,
        bearer=service_key,
        method="POST",
        body={"title": source_title, "source_type": "iteration-04-regression"},
    )
    if status not in (201, 204):
        raise AssertionError(f"service_role INSERT should succeed on an append-only table; HTTP {status}")
    source_filter = source_url + "?title=eq." + urllib.parse.quote(source_title, safe="")
    status, body = request(source_filter, api_key=service_key, bearer=service_key)
    if status != 200 or source_title.encode("utf-8") not in body:
        raise AssertionError(f"service_role could not read its append-only test row; HTTP {status}")

    status, _ = request(
        source_filter,
        api_key=service_key,
        bearer=service_key,
        method="PATCH",
        body={"title": source_title + "-updated"},
    )
    expect_denied(status, "service_role", "UPDATE on append-only source")
    status, _ = request(
        source_filter,
        api_key=service_key,
        bearer=service_key,
        method="DELETE",
    )
    expect_denied(status, "service_role", "DELETE")

    print("PASS: client reads/writes denied; service_role SELECT/INSERT/UPDATE and append-only boundaries verified.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as error:
        # Never print response bodies or local API keys.
        print(f"FAIL: {type(error).__name__}: {error}")
        sys.exit(1)
