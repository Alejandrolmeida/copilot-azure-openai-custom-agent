#!/usr/bin/env python3
"""Explicitly initialize a configured vault; no secret travels in process arguments."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import urllib.error
import urllib.request

import foundry


def put_secret(profile, name, value):
    token = foundry.azure(["account", "get-access-token", "--subscription",
                          profile["subscription_id"], "--resource", "https://vault.azure.net",
                          "--query", "accessToken"])
    foundry.require(isinstance(token, str) and token, "Missing Key Vault access token")
    request = urllib.request.Request(
        f"https://{profile['vault_name']}.vault.azure.net/secrets/{name}?api-version=7.4",
        data=json.dumps({"value": value}).encode(), method="PUT",
        headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"})
    try:
        with urllib.request.build_opener(foundry.NoRedirect).open(request, timeout=60) as response:
            foundry.require(response.status == 200, "Secret write did not succeed")
    except urllib.error.HTTPError as error:
        raise RuntimeError(f"Key Vault write failed: HTTP {error.code}; response suppressed") from None
    finally:
        token = None


def seed(profile, config, update_config_only=False):
    foundry.validate_identity(profile)
    foundry.validate_resource(profile, config)
    names = foundry.azure(["keyvault", "secret", "list", "--subscription", profile["subscription_id"],
                          "--vault-name", profile["vault_name"], "--query", "[].name"])
    key_name = profile.get("key_secret", foundry.KEY_SECRET)
    config_name = profile.get("config_secret", foundry.CONFIG_SECRET)
    if update_config_only:
        foundry.require(key_name in names and config_name in names, "Existing key/config secrets are required")
        previous = foundry.load_config(profile)
        foundry.require(all(previous[field] == config[field] for field in
                            ("subscription_id", "account_name", "resource_group")) and
                        foundry.resource_host(previous["endpoint"]) == foundry.resource_host(config["endpoint"]),
                        "Config-only update must not redirect an existing key to another account")
        put_secret(profile, config_name, json.dumps(config))
        return
    foundry.require(key_name not in names and config_name not in names,
                    "Target secrets already exist or import is partial; inspect, do not overwrite")
    key = foundry.azure(["cognitiveservices", "account", "keys", "list",
                        "--subscription", profile["subscription_id"],
                        "--resource-group", config["resource_group"], "--name", config["account_name"],
                        "--query", "key1"])
    foundry.require(isinstance(key, str) and key.strip(), "No account key returned")
    try:
        put_secret(profile, key_name, key)
    finally:
        key = None
    put_secret(profile, config_name, json.dumps(config))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("profile_file", type=Path)
    parser.add_argument("config_file", type=Path)
    parser.add_argument("--confirm-write", action="store_true")
    parser.add_argument("--update-config-only", action="store_true",
                        help="Update metadata after review; preserve the existing API key")
    args = parser.parse_args()
    try:
        foundry.require(args.confirm_write, "Use --confirm-write after reviewing identity and permissions")
        profile = foundry.validate_profile(json.loads(args.profile_file.read_text()))
        config = foundry.validate_config(json.loads(args.config_file.read_text()), profile["subscription_id"])
        seed(profile, config, args.update_config_only)
        print("Approved vault write completed without logging values. Remove any temporary write role you approved.")
    except KeyboardInterrupt:
        print("ERROR: Interrupted; inspect partial vault state before retrying.", file=sys.stderr)
        return 130
    except (ValueError, KeyError, OSError, RuntimeError, subprocess.TimeoutExpired) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
