import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, patch
from subprocess import CompletedProcess


spec = importlib.util.spec_from_file_location(
    "foundry", Path(__file__).resolve().parents[1] / "scripts/foundry.py")
foundry = importlib.util.module_from_spec(spec)
spec.loader.exec_module(foundry)

SUBSCRIPTION = "00000000-0000-0000-0000-000000000001"
TENANT = "00000000-0000-0000-0000-000000000002"
PROFILE = {"tenant_id": TENANT, "subscription_id": SUBSCRIPTION, "vault_name": "kv-example"}
MODELS = ("gpt-5.6-sol", "gpt-6-sol", "gpt-6.1-sol", "gpt-6-astra", "gpt-6-luna")


def config():
    return {
        "schema_version": 1, "subscription_id": SUBSCRIPTION,
        "resource_group": "rg-example", "account_name": "oai-example",
        "endpoint": "https://oai-example.openai.azure.com/",
        "models": {model: {"deployment": model + "-test", "max_prompt_tokens": 64000,
                           "max_output_tokens": 8000} for model in MODELS},
    }


class LoginTests(unittest.TestCase):
    def auth_error(self):
        return foundry.AzureCommandError(["keyvault", "show"], 1,
                                         "ERROR: AADSTS50173: revoked private-data")

    def test_authentication_classification_and_output_suppression(self):
        for message in ("AADSTS50173: private-data", "AADSTS700082: private-data",
                        "Please run 'az login' to setup account."):
            error = foundry.AzureCommandError(["keyvault", "show"], 1, message)
            self.assertTrue(error.authentication_required)
            self.assertNotIn("private-data", str(error))
        error = foundry.AzureCommandError(["account", "show"], 1,
                                         "The subscription 'example' doesn't exist in cloud 'AzureCloud'.")
        self.assertTrue(error.authentication_required)
        for message in ("(Forbidden) private-data", "(ResourceNotFound) private-data",
                        "Connection timeout", "AADSTS53003: blocked by policy"):
            self.assertFalse(foundry.AzureCommandError(
                ["keyvault", "show"], 1, message).authentication_required)

    def test_valid_session_does_not_login(self):
        with patch.object(foundry, "load_config", return_value=config()) as load, \
                patch.object(foundry.subprocess, "run") as run:
            self.assertEqual(foundry.load_config_for_run(PROFILE), config())
        load.assert_called_once_with(PROFILE)
        run.assert_not_called()

    def test_revoked_session_logs_into_profile_tenant_and_revalidates(self):
        with patch.object(foundry, "load_config", side_effect=[self.auth_error(), config()]) as load, \
                patch.object(foundry.sys.stdin, "isatty", return_value=True), \
                patch.object(foundry.sys, "stderr", new_callable=io.StringIO), \
                patch.object(foundry.subprocess, "run", return_value=CompletedProcess([], 0)) as run:
            self.assertEqual(foundry.load_config_for_run(PROFILE), config())
        self.assertEqual(load.call_count, 2)
        run.assert_called_once()
        command = run.call_args.args[0]
        self.assertEqual(command[:4], ["az", "login", "--tenant", TENANT])
        self.assertIn("--use-device-code", command)
        self.assertEqual(run.call_args.kwargs["env"]["AZURE_CORE_LOGIN_EXPERIENCE_V2"], "off")
        self.assertNotIn("capture_output", run.call_args.kwargs)

    def test_noninteractive_session_failure_prints_manual_command(self):
        with patch.object(foundry, "load_config", side_effect=self.auth_error()), \
                patch.object(foundry.sys.stdin, "isatty", return_value=False), \
                patch.object(foundry.subprocess, "run") as run:
            with self.assertRaisesRegex(RuntimeError, "Run in WSL: az login --tenant " + TENANT):
                foundry.load_config_for_run(PROFILE)
        run.assert_not_called()

    def test_permission_error_does_not_login(self):
        error = foundry.AzureCommandError(["keyvault", "show"], 1, "(Forbidden) private-data")
        with patch.object(foundry, "load_config", side_effect=error), \
                patch.object(foundry.subprocess, "run") as run:
            with self.assertRaises(foundry.AzureCommandError):
                foundry.load_config_for_run(PROFILE)
        run.assert_not_called()

    def test_failed_login_stops_and_repeated_auth_failure_does_not_loop(self):
        for returncode in (0, 1):
            with self.subTest(returncode=returncode), \
                    patch.object(foundry, "load_config", side_effect=self.auth_error()) as load, \
                    patch.object(foundry.sys.stdin, "isatty", return_value=True), \
                    patch.object(foundry.sys, "stderr", new_callable=io.StringIO), \
                    patch.object(foundry.subprocess, "run", return_value=CompletedProcess([], returncode)) as run:
                with self.assertRaises(RuntimeError):
                    foundry.load_config_for_run(PROFILE)
            run.assert_called_once()
            self.assertEqual(load.call_count, 2 if returncode == 0 else 1)


class TemporaryAccessTests(unittest.TestCase):
    IP = "8.8.8.8"

    def account(self, action="Deny", ips=(), etag="etag-1"):
        return {
            "etag": etag,
            "properties": {"networkAcls": {
                "defaultAction": action, "bypass": "None",
                "ipRules": [{"value": ip} for ip in ips], "virtualNetworkRules": [],
            }},
        }

    def test_ip_lookup_requires_public_ipv4_without_prompting(self):
        with patch("builtins.input") as prompt, \
                patch.object(foundry.subprocess, "run",
                             return_value=CompletedProcess([], 0, self.IP + "\n", "")) as run:
            self.assertEqual(foundry.session_ip(), self.IP)
        prompt.assert_not_called()
        self.assertEqual(run.call_args.args[0][-1], "https://ifconfig.me/ip")
        self.assertIn("--ipv4", run.call_args.args[0])
        self.assertIn("--disable", run.call_args.args[0])
        self.assertEqual(run.call_args.kwargs["timeout"], 15)
        for response in ("127.0.0.1", "10.1.2.3", "not-an-ip",
                         "2001:4860:4860::8888", self.IP + "\n1.1.1.1"):
            with self.subTest(response=response), \
                    patch.object(foundry.subprocess, "run",
                                 return_value=CompletedProcess([], 0, response, "")):
                with self.assertRaises(ValueError):
                    foundry.session_ip()
        with patch.object(foundry.subprocess, "run",
                          return_value=CompletedProcess([], 22, "", "private upstream error")):
            with self.assertRaisesRegex(ValueError, "Could not discover public IPv4") as error:
                foundry.session_ip()
        self.assertNotIn("private upstream error", str(error.exception))

    def test_failed_ip_lookup_does_not_read_key_or_change_network_rules(self):
        with patch.object(foundry.sys, "argv",
                          ["foundry.py", "run", "foundry6", "--temporary-ip-access",
                           "--model", "gpt-6-sol"]), \
                patch.object(foundry, "read_profile", return_value=PROFILE), \
                patch.object(foundry, "load_config_for_run", return_value=config()), \
                patch.object(foundry, "deployment_limits", return_value=(64000, 8000, 100000)), \
                patch.object(foundry, "session_ip", side_effect=ValueError("IP lookup failed")), \
                patch.object(foundry, "secret") as key, \
                patch.object(foundry, "set_network_rules") as update, \
                patch.object(foundry.sys, "stderr", new_callable=io.StringIO):
            with self.assertRaises(SystemExit) as error:
                foundry.main()
        self.assertEqual(error.exception.code, 1)
        key.assert_not_called()
        update.assert_not_called()

    def test_network_patch_checks_account_identity_etag_and_confirms_rules(self):
        resource = (f"/subscriptions/{SUBSCRIPTION}/resourceGroups/rg-example"
                    "/providers/Microsoft.CognitiveServices/accounts/oai-example")
        account = {
            "id": resource, "kind": "OpenAI", "etag": "etag-1",
            "properties": {"publicNetworkAccess": "Enabled",
                           "endpoint": config()["endpoint"], "provisioningState": "Succeeded",
                           "networkAcls": self.account()["properties"]["networkAcls"]},
        }
        updated = json.loads(json.dumps(account))
        updated["etag"] = "etag-2"
        updated["properties"]["networkAcls"]["ipRules"] = [{"value": self.IP}]
        with patch.object(foundry, "azure", side_effect=[account, None, updated]) as azure:
            foundry.set_network_rules(PROFILE, config(), "Deny", [self.IP], "etag-1")
        self.assertEqual(azure.call_count, 3)
        args = azure.call_args_list[1].args[0]
        self.assertIn(f"If-Match=etag-1", args)
        self.assertIn(SUBSCRIPTION, args)
        self.assertEqual(json.loads(args[args.index("--body") + 1])["properties"]["networkAcls"]
                         ["ipRules"], [{"value": self.IP}])
        with patch.object(foundry, "azure", return_value=account) as azure:
            with self.assertRaisesRegex(ValueError, "concurrently"):
                foundry.set_network_rules(PROFILE, config(), "Deny", [self.IP], "etag-old")
        azure.assert_called_once()

    def test_network_rejects_unexpected_rules(self):
        for action, ips in (("Allow", ()), ("Deny", (self.IP,))):
            with self.subTest(action=action, ips=ips), \
                    self.assertRaises(ValueError):
                foundry.require_network_rules(self.account(action, ips), "Deny", 0)

    def test_temporary_access_cleans_up_on_success_and_child_failure(self):
        for failure in (False, True):
            state = self.account()
            def read(*_):
                return "url", state
            def update(_profile, _config, action, ips, expected):
                self.assertEqual(state["etag"], expected)
                state["properties"]["networkAcls"]["defaultAction"] = action
                state["properties"]["networkAcls"]["ipRules"] = [{"value": ip} for ip in ips]
                state["etag"] += "x"
                return state
            with self.subTest(failure=failure), \
                    patch.object(foundry, "account_network", side_effect=read), \
                    patch.object(foundry, "set_network_rules", side_effect=update) as patch_rules, \
                    patch.object(foundry.sys, "stderr", new_callable=io.StringIO):
                if failure:
                    with self.assertRaisesRegex(OSError, "launch failed"):
                        with foundry.temporary_ip_access(PROFILE, config(), self.IP):
                            raise OSError("launch failed")
                else:
                    with foundry.temporary_ip_access(PROFILE, config(), self.IP):
                        self.assertEqual(state["properties"]["networkAcls"]["ipRules"],
                                         [{"value": self.IP}])
                self.assertEqual([call.args[3] for call in patch_rules.call_args_list],
                                 [[self.IP], []])
                self.assertEqual(state["properties"]["networkAcls"]["ipRules"], [])

    def test_concurrent_change_does_not_overwrite_and_reports_cleanup_failure(self):
        initial = self.account()
        changed = self.account("Deny", ("1.1.1.1",), "etag-2")
        with patch.object(foundry, "account_network", side_effect=[("url", initial),
                                                                     ("url", changed)]), \
                patch.object(foundry, "set_network_rules") as update:
            with self.assertRaisesRegex(ValueError, "manual cleanup required"):
                with foundry.temporary_ip_access(PROFILE, config(), self.IP):
                    pass
        update.assert_called_once()
        with patch.object(foundry, "account_network",
                          side_effect=[("url", initial),
                                       ("url", self.account("Deny", (self.IP,)))]), \
                patch.object(foundry, "set_network_rules",
                             side_effect=ValueError("concurrently")) as update:
            with self.assertRaisesRegex(ValueError, "concurrently"):
                with foundry.temporary_ip_access(PROFILE, config(), self.IP):
                    pass
        self.assertEqual(update.call_count, 2)

    def test_child_interrupt_terminates_process_and_removes_rule(self):
        child = MagicMock()
        child.__enter__.return_value = child
        child.wait.side_effect = [KeyboardInterrupt(), None]
        child.poll.return_value = None
        with patch.object(foundry, "account_network",
                          side_effect=[("url", self.account()),
                                       ("url", self.account("Deny", (self.IP,), "etag-2"))]), \
                patch.object(foundry, "set_network_rules") as update, \
                patch.object(foundry.subprocess, "Popen", return_value=child), \
                patch.object(foundry.signal, "signal"), \
                patch.object(foundry.sys, "stderr", new_callable=io.StringIO):
            with self.assertRaises(KeyboardInterrupt):
                foundry.run_with_temporary_ip(PROFILE, config(), ["copilot"], {}, self.IP)
        child.terminate.assert_called_once()
        self.assertEqual([call.args[3] for call in update.call_args_list], [[self.IP], []])

    def test_access_commands_validate_expected_state_before_updating(self):
        for action, before, after in (("prepare", "Allow", "Deny"),
                                      ("close", "Deny", "Allow"),
                                      ("revoke", "Deny", "Deny")):
            ips = (self.IP,) if action == "revoke" else ()
            with self.subTest(action=action), \
                    patch.object(foundry.sys, "argv",
                                 ["foundry.py", "access", "foundry6", action]), \
                    patch.object(foundry, "read_profile", return_value=PROFILE), \
                    patch.object(foundry, "load_config_for_run", return_value=config()), \
                    patch.object(foundry, "account_network",
                                 return_value=("url", self.account(before, ips))), \
                    patch.object(foundry, "set_network_rules") as update, \
                    patch("builtins.print"):
                foundry.main()
                self.assertEqual(update.call_args.args[2:4], (after, []))
        with patch.object(foundry.sys, "argv", ["foundry.py", "access", "foundry6", "close"]), \
                patch.object(foundry, "read_profile", return_value=PROFILE), \
                patch.object(foundry, "load_config_for_run", return_value=config()), \
                patch.object(foundry, "account_network",
                             return_value=("url", self.account("Deny", (self.IP,)))), \
                patch.object(foundry, "set_network_rules") as update, \
                patch.object(foundry.sys, "stderr", new_callable=io.StringIO):
            with self.assertRaises(SystemExit) as error:
                foundry.main()
        self.assertEqual(error.exception.code, 1)
        update.assert_not_called()

    def test_non_foundry6_cannot_request_temporary_access(self):
        with patch.object(foundry.sys, "argv",
                          ["foundry.py", "run", "foundry1", "--temporary-ip-access",
                           "--model", "gpt-6-sol"]), \
                patch.object(foundry, "read_profile") as profile, \
                patch.object(foundry.sys, "stderr", new_callable=io.StringIO):
            with self.assertRaises(SystemExit) as error:
                foundry.main()
        self.assertEqual(error.exception.code, 1)
        profile.assert_not_called()


class ProfileTests(unittest.TestCase):
    def test_selector_lists_only_configured_models_and_retries(self):
        data = config()
        data["models"] = {model: data["models"][model]
                          for model in ("gpt-6.1-sol", "gpt-6-luna")}
        with patch("builtins.input", side_effect=["", "0", "3", "wrong", "2"]), \
                patch.object(foundry.sys, "stderr", new_callable=io.StringIO) as stderr:
            self.assertEqual(foundry.select_model("foundry2", data), "gpt-6-luna")
        self.assertIn("1. gpt-6.1-sol", stderr.getvalue())
        self.assertIn("2. gpt-6-luna", stderr.getvalue())
        self.assertNotIn("gpt-6-astra", stderr.getvalue())
        self.assertEqual(stderr.getvalue().count("Seleccion no valida"), 4)

    def test_selector_all_five_choices(self):
        for index, model in enumerate(MODELS, 1):
            with self.subTest(model=model), patch("builtins.input", return_value=str(index)), \
                    patch.object(foundry.sys, "stderr", new_callable=io.StringIO):
                self.assertEqual(foundry.select_model("foundry1", config()), model)

    def test_noninteractive_launch_requires_model_before_azure(self):
        with patch.object(foundry.sys, "argv", ["foundry.py", "run", "foundry1"]), \
                patch.object(foundry.sys.stdin, "isatty", return_value=False), \
                patch.object(foundry, "load_config") as load, \
                patch.object(foundry.sys, "stderr", new_callable=io.StringIO) as stderr:
            with self.assertRaises(SystemExit) as error:
                foundry.main()
        self.assertEqual(error.exception.code, 1)
        self.assertIn("Specify --model", stderr.getvalue())
        load.assert_not_called()

    def test_cancel_does_not_read_api_key_or_launch(self):
        for cancellation in ("q", EOFError(), KeyboardInterrupt()):
            with self.subTest(cancellation=type(cancellation).__name__), \
                    patch.object(foundry.sys, "argv", ["foundry.py", "run", "foundry1"]), \
                    patch.object(foundry.sys.stdin, "isatty", return_value=True), \
                    patch.object(foundry.Path, "read_text", return_value=json.dumps(PROFILE)), \
                    patch.object(foundry, "load_config", return_value=config()), \
                    patch("builtins.input", side_effect=[cancellation]), \
                    patch.object(foundry, "secret") as secret, \
                    patch.object(foundry.os, "execvpe") as execute, \
                    patch.object(foundry.sys, "stderr", new_callable=io.StringIO):
                with self.assertRaises(SystemExit) as error:
                    foundry.main()
                self.assertEqual(error.exception.code, 130)
                secret.assert_not_called()
                execute.assert_not_called()

    def test_interactive_and_explicit_model_launch_preserve_resume(self):
        for explicit in (False, True):
            arguments = ["foundry.py", "run", "foundry3"]
            if explicit:
                arguments += ["--model", "gpt-6.1-sol"]
            arguments += ["--", "--resume", "session-example"]
            with self.subTest(explicit=explicit), \
                    patch.object(foundry.sys, "argv", arguments), \
                    patch.object(foundry.sys.stdin, "isatty", return_value=not explicit), \
                    patch.object(foundry.Path, "read_text", return_value=json.dumps(PROFILE)), \
                    patch.object(foundry, "load_config", return_value=config()), \
                    patch.object(foundry, "deployment_limits", return_value=(56250, 18750, 300000)), \
                    patch("builtins.input", return_value="3") as selection, \
                    patch.object(foundry, "secret", return_value="test-key") as secret, \
                    patch.object(foundry.os, "execvpe") as execute, \
                    patch.object(foundry.sys, "stderr", new_callable=io.StringIO):
                foundry.main()
                secret.assert_called_once_with(PROFILE, foundry.KEY_SECRET)
                executable, command, env = execute.call_args.args
                self.assertEqual(executable, "copilot")
                self.assertEqual(command, foundry.copilot_command(
                    "gpt-6.1-sol", ["--resume", "session-example"]))
                self.assertEqual(env["COPILOT_PROVIDER_WIRE_MODEL"], "gpt-6.1-sol-test")
                self.assertEqual(selection.call_count, 0 if explicit else 1)

    def test_direct_resume_forms(self):
        for options, expected in (
            (["--resume=session-example"], "--resume=session-example"),
            (["--resume", "session-example"], "--resume=session-example"),
            (["--resume"], "--resume"),
        ):
            with self.subTest(options=options), \
                    patch.object(foundry.sys, "argv",
                                 ["foundry.py", "run", "foundry1", *options]), \
                    patch.object(foundry.sys.stdin, "isatty", return_value=True), \
                    patch.object(foundry.Path, "read_text", return_value=json.dumps(PROFILE)), \
                    patch.object(foundry, "load_config", return_value=config()), \
                    patch.object(foundry, "deployment_limits", return_value=(56250, 18750, 300000)), \
                    patch("builtins.input", return_value="3"), \
                    patch.object(foundry, "secret", return_value="test-key"), \
                    patch.object(foundry.os, "execvpe") as execute, \
                    patch.object(foundry.sys, "stderr", new_callable=io.StringIO):
                foundry.main()
                self.assertEqual(execute.call_args.args[1],
                                 foundry.copilot_command("gpt-6.1-sol", [expected]))

    def test_direct_resume_rejects_diagnostics_and_duplicate_session(self):
        for options in (["--print-config"], ["--smoke-test"],
                        ["--", "--resume=other"], ["--", "--continue"],
                        ["--", "--session-id=other"]):
            with self.subTest(options=options), \
                    patch.object(foundry.sys, "argv",
                                 ["foundry.py", "run", "foundry1", "--model",
                                  "gpt-6-sol", "--resume=session-example", *options]), \
                    patch.object(foundry, "load_config") as load, \
                    patch.object(foundry.sys, "stderr", new_callable=io.StringIO):
                with self.assertRaises(SystemExit) as error:
                    foundry.main()
                self.assertEqual(error.exception.code, 1)
                load.assert_not_called()

    def test_profile_rejects_secret_and_path_traversal(self):
        with self.assertRaises(ValueError):
            foundry.validate_profile({**PROFILE, "api_key": "not-a-real-key"})
        with self.assertRaises(ValueError):
            foundry.profile_name("../foundry1")

    def test_config_subscription_and_schema(self):
        foundry.validate_config(config(), SUBSCRIPTION)
        with self.assertRaises(ValueError):
            foundry.validate_config(config(), TENANT)
        for value in (False, 0, -1, "64000"):
            data = config()
            data["models"]["gpt-6-sol"]["max_prompt_tokens"] = value
            with self.assertRaises(ValueError):
                foundry.validate_config(data, SUBSCRIPTION)

    def test_endpoint_rejects_external_hosts_and_redirect_targets(self):
        for endpoint in ("http://oai-example.openai.azure.com", "https://example.com",
                         "https://oai.openai.azure.com.evil.test", "https://user@example.openai.azure.com",
                         "https://oai.openai.azure.com/path", "https://oai.openai.azure.com?q=1"):
            with self.assertRaises(ValueError):
                foundry.resource_host(endpoint)
        self.assertIsNone(foundry.NoRedirect().redirect_request(None, None, 302, "", {}, ""))

    def test_model_switch_updates_wire_model_and_cleans_credentials(self):
        parent = {"PATH": "/bin", "COPILOT_PROVIDER_BEARER_TOKEN": "old",
                  "COPILOT_PROVIDER_HEADERS": "old", "COPILOT_PROVIDER_API_KEY_COMMAND": "old",
                  "OPENAI_API_KEY": "old", "COPILOT_MODEL": "old"}
        for model in MODELS:
            env = foundry.provider_env(parent, config(), model, "test-key")
            self.assertEqual(env["COPILOT_PROVIDER_WIRE_MODEL"], model + "-test")
            self.assertEqual(env["COPILOT_PROVIDER_MODEL_ID"], model)
            self.assertEqual(env["COPILOT_MODEL"], model)
            self.assertNotIn("COPILOT_PROVIDER_BEARER_TOKEN", env)
            self.assertNotIn("COPILOT_PROVIDER_HEADERS", env)
            self.assertNotIn("COPILOT_PROVIDER_API_KEY_COMMAND", env)
            self.assertNotIn("OPENAI_API_KEY", env)
            self.assertEqual(parent["COPILOT_MODEL"], "old")

    def test_no_cli_override_of_provider_settings(self):
        for option in ("--model=x", "--model", "--secret-env-vars=x", "--context"):
            with self.assertRaises(ValueError):
                foundry.copilot_command("gpt-6-sol", [option])
        command = foundry.copilot_command("gpt-6-sol", ["-p", "OK"])
        self.assertIn("--secret-env-vars=COPILOT_PROVIDER_API_KEY", command)

    def test_new_models_preserve_individual_limits(self):
        data = config()
        limits = {"gpt-6-astra": (922000, 128000), "gpt-6-luna": (256000, 32000)}
        for model, (prompt, output) in limits.items():
            data["models"][model]["max_prompt_tokens"] = prompt
            data["models"][model]["max_output_tokens"] = output
        foundry.validate_config(data, SUBSCRIPTION)
        for model, (prompt, output) in limits.items():
            env = foundry.provider_env({}, data, model, "test-key")
            self.assertEqual(env["COPILOT_PROVIDER_MAX_PROMPT_TOKENS"], str(prompt))
            self.assertEqual(env["COPILOT_PROVIDER_MAX_OUTPUT_TOKENS"], str(output))

    @patch.object(foundry, "azure")
    def test_quota_bounds_selected_deployment(self, azure):
        data = config()
        data["models"]["gpt-6-sol"]["max_prompt_tokens"] = 922000
        data["models"]["gpt-6-sol"]["max_output_tokens"] = 128000
        azure.return_value = {
            "name": "gpt-6-sol-test",
            "properties": {
                "model": {"name": "gpt-6-sol"}, "provisioningState": "Succeeded",
                "rateLimits": [{"key": "request", "count": 300.0, "renewalPeriod": 60.0},
                               {"key": "token", "count": 300000.0, "renewalPeriod": 60.0}],
            },
        }
        limits = foundry.deployment_limits(PROFILE, data, "gpt-6-sol")
        self.assertEqual(limits, (56250, 18750, 300000))
        self.assertIn("--deployment-name", azure.call_args.args[0])
        env = foundry.provider_env({}, data, "gpt-6-sol", "test-key", limits[:2])
        self.assertEqual(env["COPILOT_PROVIDER_MAX_PROMPT_TOKENS"], "56250")
        self.assertEqual(env["COPILOT_PROVIDER_MAX_OUTPUT_TOKENS"], "18750")
        self.assertEqual(data["models"]["gpt-6-sol"]["max_prompt_tokens"], 922000)
        with self.assertRaisesRegex(ValueError, "at least 1200000 TPM"):
            foundry.deployment_limits(PROFILE, data, "gpt-6-sol", full_context=True)
        azure.return_value["properties"]["rateLimits"][1]["count"] = 1200000.0
        self.assertEqual(foundry.deployment_limits(
            PROFILE, data, "gpt-6-sol", full_context=True), (922000, 128000, 1200000))

    @patch.object(foundry, "azure")
    def test_quota_preflight_fails_closed(self, azure):
        valid = {
            "name": "gpt-6-sol-test",
            "properties": {"model": {"name": "gpt-6-sol"},
                           "provisioningState": "Succeeded",
                           "rateLimits": [{"key": "token", "count": 300000.0,
                                           "renewalPeriod": 60.0}]},
        }
        for change in (
            {"name": "wrong"},
            {"properties": {**valid["properties"], "model": {"name": "other"}}},
            {"properties": {**valid["properties"], "provisioningState": "Failed"}},
            {"properties": {**valid["properties"], "rateLimits": []}},
            {"properties": {**valid["properties"], "rateLimits": [
                {"key": "token", "count": 1000, "renewalPeriod": 60}]}},
        ):
            with self.subTest(change=change):
                azure.return_value = {**valid, **change}
                with self.assertRaises(ValueError):
                    foundry.deployment_limits(PROFILE, config(), "gpt-6-sol")

    def test_run_rejects_unavailable_quota_before_key_read(self):
        with patch.object(foundry.sys, "argv",
                          ["foundry.py", "run", "foundry1", "--model", "gpt-6-sol"]), \
                patch.object(foundry.Path, "read_text", return_value=json.dumps(PROFILE)), \
                patch.object(foundry, "load_config", return_value=config()), \
                patch.object(foundry, "deployment_limits",
                             side_effect=ValueError("Cannot determine deployment TPM")), \
                patch.object(foundry, "secret") as secret, \
                patch.object(foundry.os, "execvpe") as execute, \
                patch.object(foundry.sys, "stderr", new_callable=io.StringIO) as stderr:
            with self.assertRaises(SystemExit) as error:
                foundry.main()
            self.assertEqual(error.exception.code, 1)
            self.assertIn("Cannot determine deployment TPM", stderr.getvalue())
            secret.assert_not_called()
            execute.assert_not_called()

    def test_existing_three_model_profiles_remain_valid(self):
        data = config()
        del data["models"]["gpt-6-astra"]
        del data["models"]["gpt-6-luna"]
        self.assertEqual(foundry.validate_config(data, SUBSCRIPTION), data)

    def test_install_preserves_existing_files(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            profile = home / "foundry1.json"
            profile.write_text(json.dumps(PROFILE))
            foundry.install(profile, home)
            foundry.install(profile, home)
            launcher = home / ".local/bin/Copilot-foundry1"
            lowercase = home / ".local/bin/copilot-foundry1"
            self.assertEqual(lowercase.read_text(), launcher.read_text())
            self.assertEqual(lowercase.stat().st_mode & 0o777, 0o700)
            launcher.write_text("user launcher\n")
            with self.assertRaises(ValueError):
                foundry.install(profile, home)
            self.assertEqual(launcher.read_text(), "user launcher\n")
            self.assertEqual((home / ".config/copilot-foundry/foundry1.json").stat().st_mode & 0o777, 0o600)

    def test_install_preserves_conflicting_lowercase_launcher(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            profile = home / "foundry1.json"
            profile.write_text(json.dumps(PROFILE))
            launcher = home / ".local/bin/copilot-foundry1"
            launcher.parent.mkdir(parents=True)
            launcher.write_text("existing command\n")
            with self.assertRaises(ValueError):
                foundry.install(profile, home)
            self.assertEqual(launcher.read_text(), "existing command\n")
            self.assertFalse((home / ".local/bin/Copilot-foundry1").exists())

    @patch.object(foundry, "azure")
    def test_tenant_mismatch_stops_before_reading_secrets(self, azure):
        azure.return_value = {"id": SUBSCRIPTION, "tenant": SUBSCRIPTION}
        with self.assertRaises(ValueError):
            foundry.load_config(PROFILE)
        self.assertEqual(azure.call_count, 1)

    @patch.object(foundry, "azure")
    def test_endpoint_mismatch_fails_closed(self, azure):
        azure.side_effect = [
            {"id": SUBSCRIPTION, "tenant": TENANT},
            {"id": f"/subscriptions/{SUBSCRIPTION}/resourceGroups/rg/providers/Microsoft.KeyVault/vaults/kv-example",
             "tenant": TENANT},
            json.dumps(config()),
            {"id": f"/subscriptions/{SUBSCRIPTION}/resourceGroups/rg/providers/Microsoft.CognitiveServices/accounts/oai",
             "kind": "OpenAI", "endpoint": "https://different.openai.azure.com"},
        ]
        with self.assertRaises(ValueError):
            foundry.load_config(PROFILE)
        self.assertEqual(azure.call_count, 4)

    @patch.object(foundry.subprocess, "run")
    def test_secret_errors_do_not_echo_output(self, run):
        run.return_value.returncode = 1
        run.return_value.stderr = "sensitive-output"
        with self.assertRaisesRegex(RuntimeError, "exit 1") as error:
            foundry.secret(PROFILE, foundry.KEY_SECRET)
        self.assertNotIn("sensitive-output", str(error.exception))


if __name__ == "__main__":
    unittest.main()
