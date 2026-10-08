#!/usr/bin/env python3
"""Generate a private, key-free VS Code import request from validated profiles."""
import argparse
import json
from pathlib import Path
import sys

import foundry


def group(name, config):
    foundry.require(config["schema_version"] == 2,
                    "VS Code generation needs v2 capability metadata; migrate explicitly")
    models = []
    for model, settings in foundry.primary_models(config).items():
        models.append({
            "id": settings["deployment"], "name": f"{model} ({name})",
            "url": foundry.resource_host(config["endpoint"]) + "/openai/v1/" +
                   ("responses" if settings["wire_api"] == "responses" else "chat/completions"),
            "toolCalling": settings["tool_calling"], "vision": settings["vision"],
            "contextWindow": settings["context_window"],
            "maxOutputTokens": settings["max_output_tokens"],
            "maxInputTokens": settings["max_prompt_tokens"],
        })
    apis = {settings["wire_api"] for settings in foundry.primary_models(config).values()}
    foundry.require(apis == {"responses"},
                    "Automated editor import is verified for Responses only; use the secure dialog for other APIs")
    return {"name": name, "vendor": "customendpoint", "apiType": next(iter(apis)), "models": models}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("profiles", nargs="+")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        foundry.require(not args.output.resolve().is_relative_to(Path(__file__).resolve().parents[1]),
                        "Write private import requests outside the repository")
        foundry.require(len(set(args.profiles)) == len(args.profiles), "Duplicate profiles")
        entries = []
        for name in args.profiles:
            profile = foundry.read_profile(name)
            config = foundry.load_config(profile)
            entries.append({"profile": profile, "group": group("Foundry-" + name, config)})
        foundry.write_new(args.output, json.dumps({"schema_version": 1, "profiles": entries}, indent=2) + "\n", 0o600)
        print("Private import request written without API keys. Review it before importing in VS Code.")
        return 0
    except (ValueError, KeyError, OSError, RuntimeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
