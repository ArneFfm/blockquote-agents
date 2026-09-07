import io
import json
import unittest
from email.message import Message
from unittest.mock import Mock
from urllib.error import HTTPError
from blockquote_agents import Blockquote, BlockquoteError


class Raw(io.BytesIO):
    status = 202
    headers = Message()
    headers["Retry-After"] = "3"


class ClientTest(unittest.TestCase):
    def test_wire_contract(self):
        client = Blockquote(api_key="test-key")
        client._opener = Mock()
        client._opener.open.side_effect = lambda *args, **kwargs: Raw(b'{"id":"scan-id"}')
        result = client.start_scan("https://example.com", refresh=True, idempotency_key="request-1")
        request = client._opener.open.call_args.args[0]
        self.assertEqual(request.full_url, "https://blockquote.io/api/v1/scan")
        self.assertEqual(json.loads(request.data), {"url": "https://example.com", "refresh": True})
        self.assertEqual(request.get_header("Authorization"), "Bearer test-key")
        self.assertEqual(request.get_header("Idempotency-key"), "request-1")
        self.assertEqual(result.headers.get("Retry-After"), "3")
        client.get_scan("a/b")
        self.assertTrue(client._opener.open.call_args.args[0].full_url.endswith("/scan/a%2Fb"))
        client.compare_scans(from_id="a", to_id="b")
        self.assertTrue(client._opener.open.call_args.args[0].full_url.endswith("/compare?from=a&to=b"))

    def test_http_error_preserves_payload_and_retry(self):
        for body in (b'{"error":"quota"}', b'upstream unavailable'):
            client = Blockquote()
            client._opener = Mock()
            headers = Message()
            headers["Retry-After"] = "60"
            client._opener.open.side_effect = HTTPError("https://blockquote.io", 429, "Limited", headers, io.BytesIO(body))
            with self.assertRaises(BlockquoteError) as caught:
                client.get_scan("id")
            self.assertEqual(caught.exception.status, 429)
            self.assertEqual(caught.exception.retry_after, "60")
            self.assertIn(caught.exception.data, ({"error": "quota"}, "upstream unavailable"))
            self.assertEqual(client._opener.open.call_count, 1)
            self.assertIsNone(client._opener.open.call_args.args[0].get_header("Authorization"))

    def test_invalid_inputs(self):
        with self.assertRaises(ValueError):
            Blockquote(base_url="http://example.com")
        with self.assertRaises(ValueError):
            Blockquote().get_scan("..")
        with self.assertRaises(ValueError):
            Blockquote().compare_scans(url="example.com", from_id="a")


if __name__ == "__main__":
    unittest.main()
