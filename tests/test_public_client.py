import copy
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from zipfile import ZipFile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import check_public
import foundry
import provision
import seed_vault
import vscode_config

ROOT = Path(__file__).resolve().parents[1]


def example(name="config"):
    return json.loads((ROOT / "examples" / f"{name}.example.json").read_text())


class ContractTests(unittest.TestCase):
    def test_all_public_examples_validate_offline(self):
        profile = foundry.validate_profile(example("profile"))
        foundry.validate_config(example(), profile["subscription_id"])
        provision.validate(example("provision"))

    def test_arbitrary_profile_and_model_not_a_fixed_catalog(self):
        self.assertEqual(foundry.profile_name("research-team"), "research-team")
        for bad in ("../team", "/tmp/team", "team/other", "UPPER", ""):
            with self.assertRaises(ValueError):
                foundry.profile_name(bad)
        config = example()
        config["models"]["future-compatible-model"] = config["models"].pop("gpt-5-mini")
        foundry.validate_config(config, config["subscription_id"])

    def test_limits_and_metadata_reject_invalid_values(self):
        for key, value in (("context_window", 10), ("max_prompt_tokens", True),
                           ("tool_calling", "yes"), ("role", "unexpected"),
                           ("wire_api", "unknown"), ("source", "https://example.com"),
                           ("verified_at", "not-a-date")):
            with self.subTest(key=key):
                config = example()
                config["models"]["gpt-5-mini"][key] = value
                with self.assertRaises((ValueError, TypeError)):
                    foundry.validate_config(config, config["subscription_id"])

    def test_key_reference_names_cannot_collide(self):
        profile = example("profile")
        profile.update(key_secret="same", config_secret="same")
        with self.assertRaises(ValueError):
            foundry.validate_profile(profile)

    def test_auxiliaries_not_in_selection(self):
        config = example()
        config["models"]["example-auxiliary"] = {
            **config["models"]["gpt-5-mini"], "deployment": "auxiliary", "role": "auxiliary"}
        foundry.validate_config(config, config["subscription_id"])
        self.assertEqual(list(foundry.primary_models(config)), ["gpt-5-mini"])
        with patch("builtins.input", return_value="1"), patch("sys.stderr", new=io.StringIO()) as stderr:
            self.assertEqual(foundry.select_model("team", config), "gpt-5-mini")
            self.assertNotIn("example-auxiliary", stderr.getvalue())

    def test_v2_does_not_force_reasoning_effort(self):
        config = example()
        cmd = foundry.copilot_command("gpt-5-mini", [], config["models"]["gpt-5-mini"])
        self.assertNotIn("--reasoning-effort", cmd)
        env = foundry.provider_env({}, config, "gpt-5-mini", "canary")
        self.assertEqual(env["COPILOT_PROVIDER_WIRE_API"], "responses")

    def test_vscode_group_contains_no_key_and_uses_deployment(self):
        group = vscode_config.group("Foundry-team", example())
        self.assertNotIn("apiKey", group)
        self.assertEqual(group["models"][0]["id"], "coding")
        self.assertEqual(group["models"][0]["maxInputTokens"], 272000)
        config = example()
        config["models"]["gpt-5-mini"]["wire_api"] = "completions"
        with self.assertRaises(ValueError):
            vscode_config.group("Foundry-team", config)

    def test_symlink_install_cannot_escape_private_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "real").mkdir()
            (root / "link").symlink_to(root / "real")
            with self.assertRaises(ValueError):
                foundry.write_new(root / "link" / "config", "data", 0o600)


class ProvisionTests(unittest.TestCase):
    def test_plan_and_approved_apply_use_same_preview(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            manifest = root / "input.json"
            plan = root / "plan.json"
            applied = root / "applied.json"
            data = example("provision")
            manifest.write_text(json.dumps(data))
            preview = {"status": "Succeeded", "changes": [{"changeType": "Create", "resourceId": "example"}]}
            with patch.object(provision, "preflight"), \
                    patch.object(foundry, "azure", side_effect=[
                        {"properties": {"provisioningState": "Succeeded"}}, preview]) as azure, \
                    patch.object(sys, "argv", ["provision.py", "plan", str(manifest), "--report", str(plan)]), \
                    patch("sys.stdout", new=io.StringIO()):
                self.assertEqual(provision.main(), 0)
                self.assertEqual(azure.call_count, 2)
            self.assertEqual(json.loads(plan.read_text())["status"], "review_required")
            self.assertEqual(plan.stat().st_mode & 0o777, 0o600)
            with patch.object(provision, "preflight"), \
                    patch.object(foundry, "azure", side_effect=[
                        {"properties": {"provisioningState": "Succeeded"}}, preview,
                        {"properties": {"provisioningState": "Succeeded"}}]) as azure, \
                    patch.object(sys, "argv", ["provision.py", "apply", str(manifest), "--report", str(applied),
                                              "--approval", str(plan), "--confirm", data["subscription_id"]]), \
                    patch("sys.stdout", new=io.StringIO()):
                self.assertEqual(provision.main(), 0)
                calls = [call.args[0] for call in azure.call_args_list]
                self.assertEqual([call[2] for call in calls], ["validate", "what-if", "create"])
                self.assertTrue(all("--subscription" in call for call in calls))
            self.assertEqual(json.loads(applied.read_text())["status"], "applied")

    def test_unsafe_preview_never_applies(self):
        for change in ("Modify", "Delete", "Unsupported", "Deploy"):
            with self.subTest(change=change), tempfile.TemporaryDirectory() as folder:
                manifest = Path(folder) / "input.json"
                manifest.write_text(json.dumps(example("provision")))
                with patch.object(provision, "preflight"), \
                        patch.object(foundry, "azure", side_effect=[
                            {"properties": {"provisioningState": "Succeeded"}},
                            {"status": "Succeeded", "changes": [{"changeType": change}]}]) as azure, \
                        patch.object(sys, "argv", ["provision.py", "plan", str(manifest),
                                                  "--report", str(Path(folder) / "report.json")]), \
                        patch("sys.stderr", new=io.StringIO()):
                    self.assertEqual(provision.main(), 1)
                    self.assertEqual(azure.call_count, 2)

    def test_apply_without_consent_never_contacts_azure(self):
        with tempfile.TemporaryDirectory() as folder:
            manifest = Path(folder) / "input.json"
            manifest.write_text(json.dumps(example("provision")))
            with patch.object(provision, "preflight") as preflight, \
                    patch.object(sys, "argv", ["provision.py", "apply", str(manifest),
                                              "--report", str(Path(folder) / "report.json")]), \
                    patch("sys.stderr", new=io.StringIO()):
                self.assertEqual(provision.main(), 1)
                preflight.assert_not_called()

    def test_explicit_consent_for_global_and_network(self):
        data = example("provision")
        data["use_existing_account"] = False
        with self.assertRaises(ValueError):
            provision.validate(data)
        data["allow_public_access"] = True
        data["deployments"] = [{"model": "example", "version": "2026-01-01",
                                "deployment": "coding", "sku": "GlobalStandard",
                                "capacity": 1, "allow_global": False}]
        with self.assertRaises(ValueError):
            provision.validate(data)
        data["deployments"][0]["allow_global"] = True
        self.assertEqual(provision.validate(data), data)

    def test_budget_and_capacity_require_explicit_values(self):
        data = example("provision")
        data["budget_amount"] = True
        with self.assertRaises(ValueError):
            provision.validate(data)
        data["budget_amount"] = 25
        with self.assertRaises(ValueError):
            provision.validate(data)
        data.update(budget_start="2026-10-01", budget_emails=["alerts@example.com"])
        provision.validate(data)
        params = provision.parameters(data)["parameters"]
        self.assertEqual(params["budgetAmount"]["value"], 25)
        self.assertNotIn("tenant_id", params)
        self.assertEqual(len(params["operationTag"]["value"]), 24)

    def test_plan_hash_covers_changes(self):
        data = example("provision")
        before = provision.fingerprint(data)
        data["location"] = "westeurope"
        self.assertNotEqual(before, provision.fingerprint(data))

    @patch.object(foundry, "azure")
    def test_no_unapproved_account_adoption(self, azure):
        data = example("provision")
        data["use_existing_account"] = False
        azure.side_effect = [
            {"id": data["subscription_id"], "tenant": data["tenant_id"]},
            [{"type": "Microsoft.CognitiveServices/accounts", "name": data["account_name"],
              "location": data["location"], "resourceGroup": data["resource_group"], "tags": {}}]]
        with self.assertRaises(ValueError):
            provision.preflight(data)
        self.assertEqual(azure.call_count, 2)


class SecretTests(unittest.TestCase):
    @patch.object(foundry, "azure")
    @patch.object(foundry, "validate_resource")
    @patch.object(foundry, "validate_identity")
    def test_initialization_refuses_existing_secret(self, identity, resource, azure):
        azure.return_value = [foundry.KEY_SECRET]
        with patch.object(seed_vault, "put_secret") as put:
            with self.assertRaises(ValueError):
                seed_vault.seed(example("profile"), example())
            put.assert_not_called()

    @patch.object(foundry, "azure")
    def test_secret_put_uses_https_body_not_argv(self, azure):
        azure.return_value = "synthetic-access-token"
        response = unittest.mock.MagicMock()
        response.__enter__.return_value.status = 200
        opener = unittest.mock.MagicMock()
        opener.open.return_value = response
        with patch.object(seed_vault.urllib.request, "build_opener", return_value=opener):
            seed_vault.put_secret(example("profile"), "example-secret", "synthetic-value")
        request = opener.open.call_args.args[0]
        self.assertEqual(json.loads(request.data)["value"], "synthetic-value")
        self.assertNotIn("synthetic-value", str(azure.call_args))
        self.assertNotIn("synthetic-value", request.full_url)

    @patch.object(foundry, "validate_identity")
    @patch.object(foundry, "validate_resource")
    @patch.object(foundry, "azure")
    @patch.object(foundry, "load_config")
    def test_metadata_update_preserves_key(self, load, azure, resource, identity):
        load.return_value = example()
        azure.return_value = [foundry.KEY_SECRET, foundry.CONFIG_SECRET]
        with patch.object(seed_vault, "put_secret") as put:
            seed_vault.seed(example("profile"), example(), update_config_only=True)
            self.assertEqual(put.call_count, 1)
            self.assertEqual(put.call_args.args[1], foundry.CONFIG_SECRET)

    def test_metadata_update_cannot_redirect_key(self):
        original = example()
        changed = copy.deepcopy(original)
        changed["endpoint"] = "https://different.openai.azure.com"
        with patch.object(foundry, "validate_identity"), patch.object(foundry, "validate_resource"), \
                patch.object(foundry, "load_config", return_value=original), \
                patch.object(foundry, "azure", return_value=[foundry.KEY_SECRET, foundry.CONFIG_SECRET]), \
                patch.object(seed_vault, "put_secret") as put:
            with self.assertRaises(ValueError):
                seed_vault.seed(example("profile"), changed, update_config_only=True)
            put.assert_not_called()


class PublicationTests(unittest.TestCase):
    def test_privacy_findings_never_include_matched_values(self):
        private_id = "a" * 8 + "-" + "-".join(["a" * 4] * 3) + "-" + "a" * 12
        result = check_public.findings(private_id)
        self.assertEqual(result, [(1, "non-synthetic-identity")])
        self.assertNotIn(private_id, str(result))

    def test_public_examples_have_no_privacy_matches(self):
        for file in (ROOT / "examples").glob("*.json"):
            self.assertFalse(check_public.findings(file.read_text()), file.name)

    def test_architecture_word_is_allowlisted_and_inspected(self):
        relative = check_public.ARCHITECTURE_DOC
        self.assertIn(relative, check_public.public_files())
        self.assertEqual(check_public.inspect_architecture_doc(ROOT / relative), [])

    def test_word_rejects_unexpected_parts_and_private_content(self):
        original = ROOT / check_public.ARCHITECTURE_DOC
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "test.docx"
            with ZipFile(original) as source, ZipFile(target, "w") as dest:
                for name in source.namelist():
                    content = source.read(name)
                    if name == "word/document.xml":
                        content = content.replace(b"</w:body>", b"<w:p><w:r><w:t>"
                                                  b"person@" + b"company.invalid"
                                                  b"</w:t></w:r></w:p></w:body>")
                    dest.writestr(name, content)
            self.assertTrue(any("personal-email" in error
                                for error in check_public.inspect_architecture_doc(target)))
            with ZipFile(original) as source, ZipFile(target, "w") as dest:
                for name in source.namelist():
                    content = source.read(name)
                    if name == "word/document.xml":
                        content = content.replace(
                            b"</w:body>",
                            b"<w:p><w:r><w:t>person@</w:t></w:r>"
                            b"<w:r><w:t>company.invalid</w:t></w:r></w:p></w:body>",
                        )
                    dest.writestr(name, content)
            self.assertTrue(any("personal-email" in error
                                for error in check_public.inspect_architecture_doc(target)))
            with ZipFile(target, "a") as archive:
                archive.writestr("word/embeddings/customer-data.bin", b"private")
            with self.assertRaisesRegex(ValueError, "Unexpected"):
                check_public.inspect_architecture_doc(target)


if __name__ == "__main__":
    unittest.main()
