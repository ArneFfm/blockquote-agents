"""Official Blockquote client. Uses Python's standard library."""
import json
from dataclasses import dataclass
from urllib.error import HTTPError
from urllib.parse import quote, urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener


@dataclass
class Response:
    data: object
    status: int
    headers: object


class BlockquoteError(Exception):
    def __init__(self, response):
        super().__init__(f"Blockquote HTTP {response.status}")
        self.data = response.data
        self.status = response.status
        self.headers = response.headers
        self.retry_after = response.headers.get("Retry-After")


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class Blockquote:
    def __init__(self, api_key=None, base_url="https://blockquote.io/api/v1", timeout=30):
        base = urlsplit(base_url)
        if base.scheme != "https" or not base.netloc or base.username or base.password or base.query or base.fragment:
            raise ValueError("base_url must be an HTTPS URL without credentials, query, or fragment")
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self._opener = build_opener(_NoRedirect())

    def _request(self, path, body=None, idempotency_key=None):
        headers = {"Accept": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        if body is not None:
            headers["Content-Type"] = "application/json"
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key
        request = Request(self.base_url + path, headers=headers,
                          data=None if body is None else json.dumps(body).encode())
        try:
            raw = self._opener.open(request, timeout=self.timeout)
        except HTTPError as error:
            raw = error
        with raw:
            text = raw.read().decode("utf-8", errors="replace")
            try:
                data = json.loads(text)
            except ValueError:
                data = text
            response = Response(data, raw.status, raw.headers)
        if not 200 <= response.status < 300:
            raise BlockquoteError(response)
        return response

    def start_scan(self, url, *, refresh=None, turnstile_token=None, idempotency_key=None):
        body = {"url": url}
        if refresh is not None:
            body["refresh"] = refresh
        if turnstile_token is not None:
            body["turnstileToken"] = turnstile_token
        return self._request("/scan", body, idempotency_key)

    def get_scan(self, scan_id):
        if not isinstance(scan_id, str) or not scan_id.strip() or scan_id in (".", ".."):
            raise ValueError("A scan id is required")
        return self._request("/scan/" + quote(scan_id, safe=""))

    def compare_scans(self, *, from_id=None, to_id=None, url=None):
        if (url and (from_id is not None or to_id is not None)) or (not url and (not from_id or not to_id)):
            raise ValueError("Use url or both from_id and to_id")
        query = {"url": url} if url else {"from": from_id, "to": to_id}
        return self._request("/compare?" + urlencode(query))
