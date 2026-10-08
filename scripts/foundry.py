#!/usr/bin/env python3
"""Explicit subscription/model profiles for Copilot, with credentials in Key Vault."""

import argparse
from contextlib import contextmanager
from datetime import date
import ipaddress
import json
import math
import os
from pathlib import Path
import re
import shlex
import shutil
import signal
import subprocess
import sys
import urllib.error
import urllib.request
from urllib.parse import urlsplit
from uuid import UUID


CONFIG_SECRET = "copilot-foundry-config"
KEY_SECRET = "azure-openai-api-key"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def profile_name(value):
    require(isinstance(value, str) and re.fullmatch(r"[a-z][a-z0-9_-]{0,39}", value),
            "Invalid profile name")
    return value


def validate_profile(data):
    required = {
        "tenant_id", "subscription_id", "vault_name"
    }
    require(isinstance(data, dict) and required <= set(data) and
            set(data) <= required | {"config_secret", "key_secret"},
            "Invalid profile fields")
    for field in ("tenant_id", "subscription_id"):
        require(isinstance(data[field], str), f"Invalid {field}")
        require(str(UUID(data[field])) == data[field], f"Invalid {field}")
    require(isinstance(data["vault_name"], str) and
            re.fullmatch(r"[a-z][a-z0-9-]{1,22}[a-z0-9]", data["vault_name"]),
            "Invalid vault name")
    for field in ("config_secret", "key_secret"):
        if field in data:
            require(isinstance(data[field], str) and
                    re.fullmatch(r"[A-Za-z0-9-]{1,127}", data[field]), f"Invalid {field}")
    require(data.get("config_secret", CONFIG_SECRET) != data.get("key_secret", KEY_SECRET),
            "Configuration and API key secrets must be distinct")
    return data


def resource_host(value):
    require(isinstance(value, str), "Invalid endpoint")
    url = urlsplit(value)
    require(url.scheme == "https" and url.hostname and
            url.hostname.endswith(".openai.azure.com") and
            not url.username and not url.password and url.port is None and
            url.path in ("", "/") and not url.query and not url.fragment,
            "Expected an HTTPS Azure OpenAI resource host")
    return f"https://{url.hostname}"


def validate_config(data, subscription):
    require(isinstance(data, dict) and set(data) == {
        "schema_version", "subscription_id", "resource_group", "account_name",
        "endpoint", "models"
    }, "Unsupported configuration fields")
    require(type(data["schema_version"]) is int and data["schema_version"] in (1, 2),
            "Unsupported configuration version")
    require(data["subscription_id"] == subscription, "Configuration subscription mismatch")
    for field in ("resource_group", "account_name"):
        require(isinstance(data[field], str) and
                re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}", data[field]),
                f"Invalid {field}")
    resource_host(data["endpoint"])
    require(isinstance(data["models"], dict) and bool(data["models"]), "Empty model map")
    deployments = set()
    for model, settings in data["models"].items():
        require(isinstance(model, str) and
                re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", model), "Invalid model ID")
        fields = {
            "deployment", "max_prompt_tokens", "max_output_tokens"
        }
        if data["schema_version"] == 2:
            fields |= {"context_window", "wire_api", "tool_calling", "vision",
                       "role", "source", "verified_at"}
        require(isinstance(settings, dict) and set(settings) == fields, "Invalid model settings")
        deployment = settings["deployment"]
        require(isinstance(deployment, str) and
                re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}", deployment),
                "Invalid deployment name")
        require(deployment not in deployments, "Models must use distinct deployments")
        deployments.add(deployment)
        for field in ("max_prompt_tokens", "max_output_tokens"):
            require(type(settings[field]) is int and settings[field] > 0,
                    f"Invalid {field}")
        if data["schema_version"] == 2:
            require(type(settings["context_window"]) is int and
                    settings["context_window"] >= settings["max_prompt_tokens"] +
                    settings["max_output_tokens"], "Input plus output exceeds context")
            require(settings["wire_api"] in ("responses", "completions"), "Invalid wire API")
            require(all(type(settings[key]) is bool for key in ("vision", "tool_calling")),
                    "Capabilities must be booleans")
            require(settings["role"] in ("primary", "auxiliary"), "Invalid model role")
            require(isinstance(settings["source"], str), "Invalid source URL")
            source = urlsplit(settings["source"])
            require(source.scheme == "https" and source.hostname in
                    ("ai.azure.com", "learn.microsoft.com") and not source.username and
                    not source.password and not source.query and not source.fragment,
                    "Expected a Microsoft model documentation URL")
            require(isinstance(settings["verified_at"], str), "Invalid verification date")
            date.fromisoformat(settings["verified_at"])
    require(any(settings.get("role", "primary") == "primary"
                for settings in data["models"].values()), "No primary models configured")
    return data


class AzureCommandError(RuntimeError):
    def __init__(self, args, returncode, stderr):
        # Keep only a code and a boolean, never credential operation output.
        match = re.search(r"\bAADSTS[0-9]+\b", stderr)
        if match:
            self.code = match.group(0)
        else:
            match = re.search(r'(?:"code"\s*:\s*"|\()([A-Za-z][A-Za-z0-9]+)(?:"|\))', stderr)
            self.code = match.group(1) if match else None
        self.authentication_required = self.code in {
            "AADSTS50173", "AADSTS70008", "AADSTS700082", "AADSTS700084",
            "AADSTS70043", "AADSTS50076", "AADSTS50079",
        } or "please run 'az login'" in stderr.lower() or (
            args[:2] == ["account", "show"] and
            re.search(r"subscription .+ (?:doesn't|does not) exist", stderr, re.I) is not None)
        reason = f", code {self.code}" if self.code else ""
        super().__init__(f"Azure command {' '.join(args[:2])} failed (exit {returncode}{reason})")


def azure(args):
    result = subprocess.run(
        ["az", *args, "-o", "json", "--only-show-errors"],
        capture_output=True, text=True, timeout=120,
        env={**os.environ, "AZURE_EXTENSION_USE_DYNAMIC_INSTALL": "no"},
    )
    if result.returncode:
        raise AzureCommandError(args, result.returncode, result.stderr)
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        raise RuntimeError("Azure returned invalid JSON; raw output suppressed") from None


def secret(profile, name):
    value = azure(["keyvault", "secret", "show", "--subscription",
                   profile["subscription_id"], "--vault-name", profile["vault_name"],
                   "--name", name, "--query", "value"])
    require(isinstance(value, str) and bool(value.strip()), f"Empty secret: {name}")
    return value


def validate_identity(profile):
    subscription = profile["subscription_id"]
    account = azure(["account", "show", "--subscription", subscription,
                     "--query", "{id:id,tenant:tenantId}"])
    require(account == {"id": subscription, "tenant": profile["tenant_id"]},
            "Authenticated subscription/tenant mismatch")
    vault = azure(["keyvault", "show", "--subscription", subscription,
                   "--name", profile["vault_name"], "--query",
                   "{id:id,tenant:properties.tenantId}"])
    require(vault["id"].lower().startswith(f"/subscriptions/{subscription}/") and
            vault["tenant"] == profile["tenant_id"], "Vault subscription/tenant mismatch")

def validate_resource(profile, config):
    subscription = profile["subscription_id"]
    resource = azure(["cognitiveservices", "account", "show", "--subscription", subscription,
                      "--resource-group", config["resource_group"],
                      "--name", config["account_name"], "--query",
                      "{id:id,endpoint:properties.endpoint,kind:kind}"])
    require(resource["id"].lower().startswith(f"/subscriptions/{subscription}/") and
            resource["kind"] == "OpenAI" and
            resource_host(resource["endpoint"]) == resource_host(config["endpoint"]),
            "Endpoint does not match the approved Azure resource")

def load_config(profile):
    validate_identity(profile)
    config = validate_config(json.loads(secret(profile, profile.get("config_secret", CONFIG_SECRET))),
                             profile["subscription_id"])
    validate_resource(profile, config)
    return config


def load_config_for_run(profile):
    try:
        # Cached account metadata alone cannot detect revoked tokens.
        # load_config also checks ARM and Key Vault online.
        return load_config(profile)
    except AzureCommandError as error:
        if not error.authentication_required:
            raise
        login = ["az", "login", "--tenant", profile["tenant_id"],
                 "--scope", "https://management.core.windows.net//.default",
                 "--use-device-code", "--output", "none"]
        if not sys.stdin.isatty():
            raise RuntimeError(
                f"Azure session missing or expired ({error.code or 'login required'}). "
                f"Run in WSL: {shlex.join(login)}") from None
        print(f"Sesion de Azure ausente o caducada ({error.code or 'login requerido'}). "
              f"Iniciando sesion en el tenant {profile['tenant_id']}...", file=sys.stderr)
        # Device-code instructions and MFA use the terminal. Disable the
        # subscription picker for this process only; resource calls always
        # specify the profile subscription explicitly.
        result = subprocess.run(
            login, stdout=subprocess.DEVNULL, timeout=600,
            env={**os.environ, "AZURE_CORE_LOGIN_EXPERIENCE_V2": "off",
                 "AZURE_EXTENSION_USE_DYNAMIC_INSTALL": "no"})
        if result.returncode:
            raise RuntimeError("Azure login failed; Copilot was not started")
        # Retry once and validate tenant, subscription, vault and resource.
        return load_config(profile)


def account_network(profile, config):
    subscription = profile["subscription_id"]
    resource_id = (f"/subscriptions/{subscription}/resourceGroups/{config['resource_group']}"
                   f"/providers/Microsoft.CognitiveServices/accounts/{config['account_name']}")
    url = f"https://management.azure.com{resource_id}?api-version=2024-10-01"
    account = azure(["rest", "--method", "get", "--url", url, "--subscription", subscription])
    require(account["id"].lower() == resource_id.lower() and
            account["kind"] == "OpenAI" and
            account["properties"]["publicNetworkAccess"] == "Enabled" and
            resource_host(account["properties"]["endpoint"]) == resource_host(config["endpoint"]) and
            account["properties"]["provisioningState"] == "Succeeded",
            "Foundry6 account identity or state changed; no network update made")
    return url, account


def network_rules(account):
    return account["properties"].get("networkAcls")


def require_network_rules(account, action, count):
    rules = network_rules(account)
    require(isinstance(rules, dict) and rules.get("defaultAction") == action and
            rules.get("bypass") == "None" and
            isinstance(rules.get("ipRules"), list) and len(rules["ipRules"]) == count and
            not rules.get("virtualNetworkRules"),
            "Foundry6 network rules changed; refusing to overwrite them")
    return rules


def set_network_rules(profile, config, action, ips, expected):
    url, account = account_network(profile, config)
    require(account["etag"] == expected, "Foundry6 was modified concurrently; no update made")
    rules = {"defaultAction": action, "bypass": "None",
             "ipRules": [{"value": ip} for ip in ips], "virtualNetworkRules": []}
    azure(["rest", "--method", "patch", "--url", url,
           "--subscription", profile["subscription_id"],
           "--headers", f"If-Match={expected}",
           "--body", json.dumps({"properties": {"networkAcls": rules}})])
    _, updated = account_network(profile, config)
    require(network_rules(updated) == rules, "Foundry6 network update was not confirmed")
    return updated


def session_ip():
    require(sys.stdin.isatty(), "An interactive terminal is required for temporary IP access")
    value = input("Indica tu IP publica IPv4 actual: ").strip()
    try:
        ip = ipaddress.IPv4Address(value)
    except ipaddress.AddressValueError:
        raise ValueError("Invalid public IPv4 address") from None
    require(ip.is_global, "Expected a public IPv4 address")
    return str(ip)


@contextmanager
def temporary_ip_access(profile, config, ip):
    _, account = account_network(profile, config)
    require_network_rules(account, "Deny", 0)
    attempted = False
    try:
        attempted = True
        set_network_rules(profile, config, "Deny", [ip], account["etag"])
        print("Acceso temporal a Foundry6 activado para esta IP.", file=sys.stderr)
        yield
    finally:
        if attempted:
            _, account = account_network(profile, config)
            require_network_rules(account, "Deny", 1)
            rules = network_rules(account)
            require(rules["ipRules"][0]["value"] == ip,
                    "Foundry6 IP rule changed; manual cleanup required")
            set_network_rules(profile, config, "Deny", [], account["etag"])
            print("Acceso temporal a Foundry6 retirado.", file=sys.stderr)


def run_with_temporary_ip(profile, config, command, env, ip):
    with temporary_ip_access(profile, config, ip):
        with subprocess.Popen(command, env=env) as child:
            def stop_on_term(signum, frame):
                child.terminate()
                raise KeyboardInterrupt

            previous = signal.signal(signal.SIGTERM, stop_on_term)
            try:
                return child.wait()
            finally:
                signal.signal(signal.SIGTERM, previous)
                if child.poll() is None:
                    child.terminate()
                    try:
                        child.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        child.kill()
                        child.wait()


def provider_env(parent, config, model, key, limits=None):
    require(model in config["models"], "Model not configured in this profile")
    settings = config["models"][model]
    env = {k: v for k, v in parent.items() if not k.startswith("COPILOT_PROVIDER_")}
    for name in ("OPENAI_API_KEY", "AZURE_OPENAI_API_KEY", "ANTHROPIC_API_KEY",
                 "OPENAI_BASE_URL", "AZURE_OPENAI_BASE_URL", "AZURE_OPENAI_MODEL",
                 "COPILOT_MODEL", "COPILOT_CONTEXT_TIER", "COPILOT_REASONING_EFFORT"):
        env.pop(name, None)
    env.update({
        "COPILOT_PROVIDER_TYPE": "azure",
        "COPILOT_PROVIDER_BASE_URL": resource_host(config["endpoint"]),
        "COPILOT_PROVIDER_WIRE_API": settings.get("wire_api", "responses"),
        "COPILOT_PROVIDER_MODEL_ID": model,
        "COPILOT_PROVIDER_WIRE_MODEL": settings["deployment"],
        "COPILOT_PROVIDER_API_KEY": key,
        "COPILOT_PROVIDER_MAX_PROMPT_TOKENS": str(
            limits[0] if limits else settings["max_prompt_tokens"]),
        "COPILOT_PROVIDER_MAX_OUTPUT_TOKENS": str(
            limits[1] if limits else settings["max_output_tokens"]),
        "COPILOT_MODEL": model,
    })
    return env


def deployment_limits(profile, config, model, full_context=False):
    settings = config["models"][model]
    deployed = azure(["cognitiveservices", "account", "deployment", "show",
                      "--subscription", profile["subscription_id"],
                      "--resource-group", config["resource_group"],
                      "--name", config["account_name"],
                      "--deployment-name", settings["deployment"]])
    require(isinstance(deployed, dict), "Selected deployment has invalid metadata")
    properties = deployed.get("properties", {})
    require(isinstance(properties, dict) and
            isinstance(properties.get("model"), dict),
            "Selected deployment has invalid metadata")
    require(deployed.get("name") == settings["deployment"] and
            properties.get("model", {}).get("name") == model and
            properties.get("provisioningState") == "Succeeded",
            "Selected deployment differs from profile or is not ready")
    rates = properties.get("rateLimits", [])
    require(isinstance(rates, list), "Cannot determine deployment TPM; refusing to start")
    token_rates = [rate["count"] for rate in rates
                   if isinstance(rate, dict) and rate.get("key") == "token" and
                   rate.get("renewalPeriod") == 60 and
                   type(rate.get("count")) in (int, float) and
                   math.isfinite(rate["count"]) and rate["count"] > 0]
    require(len(token_rates) == 1 and int(token_rates[0]) == token_rates[0],
            "Cannot determine deployment TPM; refusing to start")
    tpm = int(token_rates[0])
    if full_context:
        prompt = settings["max_prompt_tokens"]
        output = settings["max_output_tokens"]
        minimum = (8 * (prompt + output) + 6) // 7
        require(tpm >= minimum,
                f"Full context needs at least {minimum} TPM; deployment has {tpm}")
        return prompt, output, tpm
    budget = tpm // 4
    output = min(settings["max_output_tokens"], budget // 4)
    prompt = min(settings["max_prompt_tokens"], budget - output)
    require(prompt >= 4096 and output >= 1024,
            "Deployment TPM is too low for a Copilot session")
    return prompt, output, tpm


def copilot_command(model, extra, settings=None):
    protected = ("--model", "--context", "--reasoning-effort", "--secret-env-vars", "--effort")
    require(not any(arg.split("=", 1)[0] in protected for arg in extra),
            "Provider/model settings cannot be overridden after --")
    defaults = ["--context", "default"]
    if settings is None:
        defaults += ["--reasoning-effort", "medium"]
    return ["copilot", "--model", model, *defaults,
            "--secret-env-vars=COPILOT_PROVIDER_API_KEY", *extra]


def select_model(name, config):
    models = [model for model, settings in config["models"].items()
              if settings.get("role", "primary") == "primary"]
    print(f"\n{name} | {resource_host(config['endpoint'])}", file=sys.stderr)
    for index, model in enumerate(models, 1):
        print(f"  {index}. {model}", file=sys.stderr)
    while True:
        print("Selecciona modelo (numero; q para cancelar): ", end="",
              file=sys.stderr, flush=True)
        choice = input().strip()
        if choice.lower() == "q":
            raise KeyboardInterrupt
        if choice in {str(index) for index in range(1, len(models) + 1)}:
            return models[int(choice) - 1]
        print("Seleccion no valida. Introduce uno de los numeros de la lista.",
              file=sys.stderr)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def smoke_test(config, model, key):
    settings = config["models"][model]
    responses = settings.get("wire_api", "responses") == "responses"
    limit = min(1024, settings["max_output_tokens"])
    payload = ({"model": settings["deployment"], "input": "Reply exactly OK.",
                "max_output_tokens": limit, "store": False} if responses else
               {"model": settings["deployment"], "messages": [{"role": "user", "content": "Reply exactly OK."}],
                "max_completion_tokens": limit})
    request = urllib.request.Request(
        resource_host(config["endpoint"]) + "/openai/v1/" + ("responses" if responses else "chat/completions"),
        data=json.dumps(payload).encode(),
        headers={"api-key": key, "Content-Type": "application/json"},
    )
    try:
        with urllib.request.build_opener(NoRedirect).open(request, timeout=120) as response:
            data = json.load(response)
            request_id = response.headers.get("apim-request-id")
    except urllib.error.HTTPError as error:
        raise RuntimeError(f"Inference failed: HTTP {error.code}") from None
    text = "".join(
        part.get("text", "") for item in data.get("output", [])
        for part in item.get("content", []) if part.get("type") == "output_text"
    ) if responses else next(iter(data.get("choices", [])), {}).get("message", {}).get("content", "")
    finished = (data.get("status") == "completed" if responses else
                next(iter(data.get("choices", [])), {}).get("finish_reason") == "stop")
    require(finished and isinstance(text, str) and text.strip() == "OK" and data.get("usage"),
            "Smoke test did not complete with expected text and usage")
    return {"model": model, "status": "completed", "request_id": request_id,
            "response_id": data.get("id"), "usage": data["usage"], "text": text}


def write_new(path, content, mode):
    require(not any(parent.is_symlink() for parent in path.parents), "Symlinked parent directory")
    if path.exists() or path.is_symlink():
        require(not path.is_symlink() and path.read_text() == content,
                f"Refusing to replace existing file: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode)
    with os.fdopen(fd, "w") as file:
        file.write(content)


def install(profile_file, home):
    name = profile_name(profile_file.stem)
    data = validate_profile(json.loads(profile_file.read_text()))
    target = home / ".config/copilot-foundry" / f"{name}.json"
    script = shlex.quote(str(Path(__file__).resolve()))
    python = shlex.quote(sys.executable)
    generic = f'#!/bin/sh\nexec {python} {script} run "$@"\n'
    alias = f'#!/bin/sh\nexec {python} {script} run {name} "$@"\n'
    # Preflight all conflicts before installing anything.
    files = [(target, json.dumps(data, indent=2) + "\n", 0o600),
             (home / ".local/bin/copilot-foundry", generic, 0o700),
             (home / ".local/bin" / f"Copilot-{name}", alias, 0o700),
             (home / ".local/bin" / f"copilot-{name}", alias, 0o700)]
    for path, content, _ in files:
        if path.exists() or path.is_symlink():
            require(not path.is_symlink() and path.read_text() == content,
                    f"Refusing to replace existing file: {path}")
    for path, content, mode in files:
        write_new(path, content, mode)
    return {"profile": name, "config": str(target),
            "launcher": str(home / ".local/bin" / f"Copilot-{name}")}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    installer = commands.add_parser("install")
    installer.add_argument("profile_file", type=Path)
    configure = commands.add_parser("configure", help="Install a profile for an existing configured vault")
    configure.add_argument("profile")
    configure.add_argument("--tenant")
    configure.add_argument("--subscription")
    configure.add_argument("--vault")
    doctor = commands.add_parser("doctor", help="Read-only checks; no API key or inference")
    doctor.add_argument("profile")
    catalog = commands.add_parser("catalog", help="Inspect regional model metadata without inference")
    catalog.add_argument("--subscription", required=True)
    catalog.add_argument("--location", required=True)
    catalog.add_argument("--model")
    runner = commands.add_parser("run")
    runner.add_argument("profile")
    runner.add_argument("--model",
                        help="Modelo; si se omite, abre el selector en una terminal")
    runner.add_argument("--full-context", action="store_true",
                        help="Use model context limits only when deployment TPM leaves 12.5%% headroom")
    runner.add_argument("--resume", nargs="?", const="",
                        help="Reanudar una sesion por ID o abrir el selector de sesiones")
    runner.add_argument("--temporary-ip-access", action="store_true",
                        help="Foundry6 only: allow this IP while Copilot is running")
    access = commands.add_parser("access", help="Manage the Foundry6 test firewall")
    access.add_argument("profile", choices=["foundry6"])
    access.add_argument("action", choices=["prepare", "close", "revoke"])
    mode = runner.add_mutually_exclusive_group()
    mode.add_argument("--print-config", action="store_true")
    mode.add_argument("--smoke-test", action="store_true")
    args_list = sys.argv[1:]
    if "--" in args_list:
        index = args_list.index("--")
        args_list, extra = args_list[:index], args_list[index + 1:]
    else:
        extra = []
    args = parser.parse_args(args_list)
    try:
        if args.command == "catalog":
            require(not extra, "Unexpected catalog arguments")
            require(str(UUID(args.subscription)) == args.subscription, "Invalid subscription")
            require(re.fullmatch(r"[a-z0-9]+", args.location), "Invalid location")
            rows = azure(["cognitiveservices", "model", "list", "--subscription", args.subscription,
                          "--location", args.location])
            models = [{"model": row["model"]["name"], "version": row["model"]["version"],
                       "skus": row["model"].get("skus", []),
                       "capabilities": row["model"].get("capabilities", {})}
                      for row in rows if not args.model or row["model"]["name"] == args.model]
            require(bool(models), "No matching models in this regional catalog")
            print(json.dumps(models, indent=2))
            return
        if args.command == "install":
            require(not extra, "Unexpected install arguments")
            print(json.dumps(install(args.profile_file, Path.home()), indent=2))
            return
        if args.command == "configure":
            require(not extra, "Unexpected configure arguments")
            name = profile_name(args.profile)
            def choose(values, label):
                require(sys.stdin.isatty(), f"Specify {label} without a terminal")
                require(bool(values), f"No choices available for {label}")
                for index, (display, _) in enumerate(values, 1):
                    print(f"{index}. {display}")
                value = input(label + " (number): ").strip()
                require(value in {str(index) for index in range(1, len(values) + 1)},
                        "Invalid selection; no files changed")
                return values[int(value) - 1][1]
            subscription = args.subscription
            if subscription is None:
                accounts = azure(["account", "list", "--query", "[?state=='Enabled'].{id:id,name:name}"])
                subscription = choose([(a["name"], a["id"]) for a in accounts], "--subscription")
            account = azure(["account", "show", "--subscription", subscription,
                             "--query", "{id:id,tenant:tenantId}"])
            tenant = args.tenant or account["tenant"]
            require(account == {"id": subscription, "tenant": tenant}, "Tenant mismatch")
            vault = args.vault
            if vault is None:
                vaults = azure(["keyvault", "list", "--subscription", subscription, "--query", "[].name"])
                vault = choose([(v, v) for v in vaults], "--vault")
            profile = validate_profile({
                "tenant_id": tenant, "subscription_id": subscription, "vault_name": vault})
            load_config(profile)
            import tempfile
            with tempfile.TemporaryDirectory() as folder:
                path = Path(folder) / (name + ".json")
                path.write_text(json.dumps(profile))
                print(json.dumps(install(path, Path.home()), indent=2))
            return
        if args.command == "doctor":
            require(not extra, "Unexpected doctor arguments")
            profile = read_profile(args.profile)
            config = load_config(profile)
            require(shutil.which("copilot") is not None, "Copilot CLI is not installed")
            help_result = subprocess.run(["copilot", "--help"], capture_output=True, text=True,
                                         check=True, timeout=30)
            require("--secret-env-vars" in help_result.stdout and "--reasoning-effort" in help_result.stdout,
                    "CLI lacks required protection or reasoning flags")
            deployed = azure(["cognitiveservices", "account", "deployment", "list", "--subscription",
                              profile["subscription_id"], "--resource-group", config["resource_group"],
                              "--name", config["account_name"]])
            actual = {d["name"]: d["properties"] for d in deployed}
            for model, settings in config["models"].items():
                require(settings["deployment"] in actual and
                        actual[settings["deployment"]]["model"]["name"] == model and
                        actual[settings["deployment"]]["provisioningState"] == "Succeeded",
                        "Deployment identity or readiness differs from configuration")
            print(json.dumps({"identity": "verified", "endpoint": "verified",
                              "primary_model_count": len(primary_models(config)),
                              "api_key_read": False, "inference_performed": False}, indent=2))
            return
        if args.command == "access":
            require(not extra, "Unexpected access arguments")
            profile = read_profile(args.profile)
            config = load_config_for_run(profile)
            _, account = account_network(profile, config)
            if args.action == "prepare":
                require_network_rules(account, "Allow", 0)
                set_network_rules(profile, config, "Deny", [], account["etag"])
            elif args.action == "close":
                require_network_rules(account, "Deny", 0)
                set_network_rules(profile, config, "Allow", [], account["etag"])
            else:
                require_network_rules(account, "Deny", 1)
                set_network_rules(profile, config, "Deny", [], account["etag"])
            print(f"Foundry6 test access: {args.action} completed")
            return
        name = profile_name(args.profile)
        require(not args.temporary_ip_access or name == "foundry6",
                "Temporary IP access is enabled only for foundry6")
        require(not args.temporary_ip_access or not args.print_config,
                "Temporary IP access requires launching Copilot or a smoke test")
        if args.resume is not None:
            require(not any(arg.split("=", 1)[0] in ("--resume", "-r", "--continue",
                                                     "--session-id") for arg in extra),
                    "Specify session selection only once")
            extra = [("--resume=" + args.resume) if args.resume else "--resume", *extra]
        require(args.model is not None or sys.stdin.isatty(),
                "Specify --model when running without an interactive terminal")
        require(not extra or not (args.print_config or args.smoke_test),
                "Copilot arguments are only valid when launching Copilot")
        require(not args.full_context or not args.smoke_test,
                "--full-context cannot be combined with --smoke-test")
        profile = read_profile(name)
        config = load_config_for_run(profile)
        model = args.model if args.model is not None else select_model(name, config)
        require(model in config["models"], "Model not configured in this profile")
        require(config["models"][model].get("role", "primary") == "primary",
                "Auxiliary models are not selectable as the session model")
        command = copilot_command(model, extra, config["models"][model] if config["schema_version"] == 2 else None)
        require(config["models"][model].get("tool_calling", True), "Primary model lacks tool calling")
        limits = None if args.smoke_test else deployment_limits(
            profile, config, model, args.full_context)
        if args.print_config:
            print(json.dumps({"profile": name, "subscription": profile["subscription_id"],
                              "endpoint": resource_host(config["endpoint"]),
                              "model": model, **config["models"][model],
                              "context_mode": "full" if args.full_context else "conservative",
                              "deployment_tpm": limits[2],
                              "effective_max_prompt_tokens": limits[0],
                              "effective_max_output_tokens": limits[1]}, indent=2))
            return
        ip = session_ip() if args.temporary_ip_access else None
        key = secret(profile, profile.get("key_secret", KEY_SECRET))
        if args.smoke_test:
            if ip is None:
                result = smoke_test(config, model, key)
            else:
                with temporary_ip_access(profile, config, ip):
                    result = smoke_test(config, model, key)
            print(json.dumps(result, indent=2))
            return
        env = provider_env(os.environ, config, model, key, limits[:2])
        print(f"{name}: {model} -> {config['models'][model]['deployment']} "
              f"({resource_host(config['endpoint'])}); context {limits[0]} input / "
              f"{limits[1]} output tokens, quota {limits[2]} TPM", file=sys.stderr)
        if ip is not None:
            sys.exit(run_with_temporary_ip(profile, config, command, env, ip))
        os.execvpe("copilot", command, env)
    except (KeyboardInterrupt, EOFError):
        print("\nCancelado; no se ha iniciado Copilot.", file=sys.stderr)
        sys.exit(130)
    except subprocess.CalledProcessError:
        print("ERROR: Dependency command failed; output suppressed", file=sys.stderr)
        sys.exit(1)
    except (ValueError, KeyError, OSError, RuntimeError, subprocess.TimeoutExpired) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        sys.exit(1)


def read_profile(name):
    return validate_profile(json.loads(
        (Path.home() / ".config/copilot-foundry" / (profile_name(name) + ".json")).read_text()))


def primary_models(config):
    return {name: value for name, value in config["models"].items()
            if value.get("role", "primary") == "primary"}


if __name__ == "__main__":
    main()
