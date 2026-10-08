#!/usr/bin/env python3
"""Review and apply a Bicep deployment with explicit subscription and private reports."""
import argparse
from datetime import date
import hashlib
import ipaddress
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from uuid import UUID

import foundry

ROOT = Path(__file__).resolve().parents[1]
FIELDS = ("tenant_id subscription_id resource_group location account_name vault_name "
          "create_resource_group use_existing_account use_existing_vault allow_public_access "
          "allowed_ips reader_object_id budget_amount budget_start budget_emails deployments").split()


def validate(data):
    foundry.require(isinstance(data, dict) and set(data) == set(FIELDS), "Invalid provision manifest fields")
    foundry.validate_profile({k: data[k] for k in ("tenant_id", "subscription_id", "vault_name")})
    for key in ("resource_group", "account_name", "location"):
        foundry.require(isinstance(data[key], str) and
                        re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_-]{0,62}", data[key]), f"Invalid {key}")
    for key in ("create_resource_group", "use_existing_account", "use_existing_vault", "allow_public_access"):
        foundry.require(type(data[key]) is bool, f"Invalid {key}")
    foundry.require(isinstance(data["allowed_ips"], list), "Invalid IP list")
    for ip in data["allowed_ips"]:
        network = ipaddress.ip_network(ip, strict=True)
        foundry.require(network.version == 4 and network.is_global, "Only public IPv4 ranges are supported")
    if not (data["use_existing_account"] and data["use_existing_vault"]):
        foundry.require(data["allow_public_access"] or data["allowed_ips"],
                        "New resources need approved public access or an IP allowlist")
    foundry.require(isinstance(data["reader_object_id"], str) and isinstance(data["budget_start"], str),
                    "Invalid reader or budget date")
    if data["reader_object_id"]:
        UUID(data["reader_object_id"])
    foundry.require(type(data["budget_amount"]) is int and data["budget_amount"] >= 0,
                    "Invalid budget amount")
    foundry.require(isinstance(data["budget_emails"], list), "Invalid budget email list")
    if data["budget_amount"]:
        start = date.fromisoformat(data["budget_start"])
        foundry.require(start.day == 1 and data["budget_emails"], "Budget needs month start and recipients")
        foundry.require(all(isinstance(email, str) and re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email)
                            for email in data["budget_emails"]), "Invalid budget recipients")
    foundry.require(isinstance(data["deployments"], list), "Invalid deployments")
    names = set()
    for model in data["deployments"]:
        foundry.require(isinstance(model, dict) and set(model) ==
                        {"model", "version", "deployment", "sku", "capacity", "allow_global"},
                        "Invalid deployment fields")
        for field in ("model", "version", "deployment"):
            foundry.require(isinstance(model[field], str) and
                            re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}", model[field]),
                            f"Invalid deployment {field}")
        foundry.require(model["sku"] in ("DataZoneStandard", "GlobalStandard", "Standard"), "Unsupported SKU")
        foundry.require(type(model["allow_global"]) is bool, "Invalid global consent")
        foundry.require(model["sku"] != "GlobalStandard" or model["allow_global"],
                        "Global processing requires explicit consent per model")
        foundry.require(type(model["capacity"]) is int and model["capacity"] > 0, "Invalid capacity")
        foundry.require(model["deployment"] not in names, "Duplicate deployment")
        names.add(model["deployment"])
    return data


def parameters(data):
    mapping = {
        "resource_group": "resourceGroupName", "location": "location", "account_name": "accountName",
        "vault_name": "vaultName", "create_resource_group": "createResourceGroup",
        "use_existing_account": "useExistingAccount", "use_existing_vault": "useExistingVault",
        "allow_public_access": "allowPublicAccess", "allowed_ips": "allowedIPs",
        "reader_object_id": "readerObjectId", "budget_amount": "budgetAmount",
        "budget_start": "budgetStart", "budget_emails": "budgetEmails", "deployments": "deployments"}
    values = {target: {"value": data[source]} for source, target in mapping.items()}
    values["operationTag"] = {"value": manifest_id(data)}
    return {"$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentParameters.json#",
            "contentVersion": "1.0.0.0",
            "parameters": values}


def manifest_id(data):
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()[:24]


def preflight(data):
    sub = data["subscription_id"]
    account = foundry.azure(["account", "show", "--subscription", sub, "--query", "{id:id,tenant:tenantId}"])
    foundry.require(account == {"id": sub, "tenant": data["tenant_id"]}, "Wrong subscription/tenant")
    resources = foundry.azure(["resource", "list", "--subscription", sub])
    for kind, name, reuse in (
        ("Microsoft.CognitiveServices/accounts", data["account_name"], data["use_existing_account"]),
        ("Microsoft.KeyVault/vaults", data["vault_name"], data["use_existing_vault"]),
    ):
        matches = [r for r in resources if r["type"].lower() == kind.lower() and r["name"] == name]
        foundry.require((bool(matches) if reuse else
                         not matches or all(r.get("tags", {}).get("copilot-foundry-id") == manifest_id(data)
                                            for r in matches)),
                        "Existing/new resource selection does not match inventory or ownership")
        if matches:
            foundry.require(len(matches) == 1 and matches[0]["resourceGroup"].lower() ==
                            data["resource_group"].lower() and matches[0]["location"] == data["location"],
                            "Resource group or location mismatch")
    existing = []
    if any(r["type"].lower() == "microsoft.cognitiveservices/accounts" and
           r["name"] == data["account_name"] for r in resources):
        existing = foundry.azure(["cognitiveservices", "account", "deployment", "list",
                                  "--subscription", sub, "--resource-group", data["resource_group"],
                                  "--name", data["account_name"]])
    by_name = {m["name"]: m for m in existing}
    for item in data["deployments"]:
        if item["deployment"] in by_name:
            actual = by_name[item["deployment"]]
            foundry.require({key: actual["properties"]["model"].get(key) for key in ("format", "name", "version")} == {
                "format": "OpenAI", "name": item["model"], "version": item["version"]} and
                actual["sku"]["name"] == item["sku"] and actual["sku"]["capacity"] == item["capacity"],
                "Existing deployment differs; refuse implicit update")
    catalog = foundry.azure(["cognitiveservices", "model", "list", "--subscription", sub,
                            "--location", data["location"]])
    usages = foundry.azure(["rest", "--method", "get", "--subscription", sub, "--url",
                            f"https://management.azure.com/subscriptions/{sub}/providers/"
                            f"Microsoft.CognitiveServices/locations/{data['location']}/usages?api-version=2025-06-01"])
    needed = {}
    for item in data["deployments"]:
        foundry.require(any(r["model"]["name"] == item["model"] and r["model"]["version"] == item["version"] and
                            any(s["name"] == item["sku"] for s in r["model"].get("skus") or [])
                            for r in catalog), "Model/version/SKU unavailable")
        key = f"OpenAI.{item['sku']}.{item['model']}"
        needed[key] = needed.get(key, 0) + (0 if item["deployment"] in by_name else item["capacity"])
    for key, capacity in needed.items():
        row = next((r for r in usages["value"] if r["name"]["value"] == key), None)
        foundry.require(row is not None and row["limit"] - row["currentValue"] >= capacity,
                        "Insufficient model quota")
    if data["budget_amount"]:
        budgets = foundry.azure(["rest", "--method", "get", "--subscription", sub, "--url",
                                f"https://management.azure.com/subscriptions/{sub}/providers/"
                                "Microsoft.Consumption/budgets?api-version=2024-08-01"])
        existing_budget = next((r for r in budgets["value"]
                                if r["name"] == data["account_name"] + "-client-budget"), None)
        if existing_budget:
            foundry.require(existing_budget["properties"]["amount"] == data["budget_amount"],
                            "Budget differs; refuse implicit update")


def fingerprint(data):
    content = json.dumps(data, sort_keys=True).encode()
    for path in sorted((ROOT / "infra").glob("*.bicep")):
        content += path.read_bytes()
    return hashlib.sha256(content).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("plan", "apply"))
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--report", type=Path, required=True, help="Private new report outside this repository")
    parser.add_argument("--approval", type=Path, help="Previously reviewed plan report")
    parser.add_argument("--confirm", help="Type the exact subscription ID to authorize applying")
    args = parser.parse_args()
    try:
        data = validate(json.loads(args.manifest.read_text()))
        foundry.require(not args.report.resolve().is_relative_to(ROOT), "Reports must be outside the repository")
        foundry.require(not args.report.exists(), "Report exists; use a new operation path")
        if args.action == "apply":
            foundry.require(args.approval is not None and args.confirm == data["subscription_id"],
                            "Apply requires a reviewed --approval and --confirm SUBSCRIPTION")
            approval = json.loads(args.approval.read_text())
            foundry.require(approval["fingerprint"] == fingerprint(data), "Manifest or templates changed; re-plan")
        preflight(data)
        with tempfile.TemporaryDirectory(prefix="foundry-bicep-") as temp:
            parameter_file = Path(temp) / "parameters.json"
            parameter_file.write_text(json.dumps(parameters(data)))
            common = ["deployment", "sub", "--subscription", data["subscription_id"],
                      "--location", data["location"], "--name", "copilot-foundry-" + manifest_id(data),
                      "--template-file", str(ROOT / "infra/main.bicep"), "--parameters", "@" + str(parameter_file)]
            # The first two words form a command group; insert the operation after them.
            validation = foundry.azure([*common[:2], "validate", *common[2:]])
            properties = validation.get("properties", {})
            foundry.require(not validation.get("error") and not properties.get("error") and
                            properties.get("provisioningState") == "Succeeded",
                            "ARM validation did not confirm success")
            preview = foundry.azure([*common[:2], "what-if", *common[2:], "--no-pretty-print"])
            foundry.require(preview.get("status") == "Succeeded", "What-if did not succeed")
            changes = preview.get("changes")
            foundry.require(isinstance(changes, list), "What-if omitted the change list")
            foundry.require(all(c["changeType"] in ("Create", "NoChange", "Ignore") for c in changes),
                            "What-if includes destructive, modifying or unsupported changes; inspect manually")
            digest = hashlib.sha256(json.dumps(changes, sort_keys=True).encode()).hexdigest()
            if args.action == "apply":
                foundry.require(approval["changes_digest"] == digest, "Azure state changed; re-plan")
            report = {"fingerprint": fingerprint(data), "changes_digest": digest, "changes": changes,
                      "status": "review_required", "warnings": [
                          "Identifiers are private. Budget alerts do not stop spending.",
                          "Global deployments may process outside your region.",
                          "New Key Vault purge protection cannot simply be disabled."]}
            foundry.write_new(args.report, json.dumps(report, indent=2) + "\n", 0o600)
            if args.action == "apply":
                report["status"] = "apply_started"
                args.report.write_text(json.dumps(report, indent=2) + "\n")
                result = foundry.azure([*common[:2], "create", *common[2:]])
                foundry.require(result.get("properties", {}).get("provisioningState") == "Succeeded",
                                "Deployment not confirmed; inspect the ARM operation before retrying")
                report["status"] = "applied"
                args.report.write_text(json.dumps(report, indent=2) + "\n")
        print(f"{report['status']}: private report at {args.report}")
        return 0
    except (ValueError, KeyError, OSError, RuntimeError, subprocess.TimeoutExpired) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
