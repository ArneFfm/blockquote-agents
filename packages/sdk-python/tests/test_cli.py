import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

from blockquote_agents import BlockquoteError, Response
from blockquote_agents.cli import main


class CliTest(unittest.TestCase):
    def test_module_help_and_invalid_arguments_are_offline(self):
        for args in ([], ["--help"]):
            result = subprocess.run([sys.executable, "-m", "blockquote_agents", *args],
                                    cwd=Path(__file__).resolve().parents[1],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0)
            self.assertIn("BLOCKQUOTE_API_KEY", result.stdout)
        result = subprocess.run([sys.executable, "-m", "blockquote_agents", "read", "id", "--refresh"],
                                cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)

    def test_commands_forward_options_and_preserve_response(self):
        response = Response({"id": "scan-id"}, 202, {"Retry-After": "5"})
        with patch("blockquote_agents.cli.Blockquote") as factory, patch.dict(os.environ, {
            "BLOCKQUOTE_API_KEY": "test-key", "BLOCKQUOTE_TURNSTILE_TOKEN": "test-token"
        }):
            client = factory.return_value
            for args, method in [(["scan", "https://example.com", "--refresh", "--idempotency-key", "key-1"], client.start_scan),
                                 (["read", "scan-id"], client.get_scan),
                                 (["compare", "old", "new"], client.compare_scans)]:
                method.return_value = response
                output = io.StringIO()
                with contextlib.redirect_stdout(output):
                    self.assertEqual(main(args), 0)
                self.assertEqual(json.loads(output.getvalue()), {
                    "data": {"id": "scan-id"}, "status": 202, "headers": {"Retry-After": "5"}
                })
            factory.assert_called_with(api_key="test-key")
            client.start_scan.assert_called_once_with("https://example.com", refresh=True,
                                                     idempotency_key="key-1", turnstile_token="test-token")
            client.get_scan.assert_called_once_with("scan-id")
            client.compare_scans.assert_called_once_with(from_id="old", to_id="new")

    def test_http_errors_retain_retry_guidance_and_other_errors_hide_secrets(self):
        for error in [BlockquoteError(Response({"error": "quota"}, 429, {"Retry-After": "60"})),
                      ValueError("invalid header with secret-test-token")]:
            with patch("blockquote_agents.cli.Blockquote") as factory:
                factory.return_value.get_scan.side_effect = error
                output = io.StringIO()
                with contextlib.redirect_stderr(output):
                    self.assertEqual(main(["read", "scan-id"]), 1)
                payload = json.loads(output.getvalue())
                if isinstance(error, BlockquoteError):
                    self.assertEqual(payload["status"], 429)
                    self.assertEqual(payload["retryAfter"], "60")
                    self.assertEqual(payload["data"], {"error": "quota"})
                else:
                    self.assertNotIn("secret-test-token", output.getvalue())
                factory.return_value.get_scan.assert_called_once()


if __name__ == "__main__":
    unittest.main()
