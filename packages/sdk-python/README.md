# Blockquote Python SDK and CLI

Official client for [Blockquote](https://blockquote.io). Requires Python 3.10 or later. No runtime dependencies.

```sh
pip install blockquote-agents
```

```python
import os
import uuid
from blockquote_agents import Blockquote, BlockquoteError

client = Blockquote(api_key=os.getenv("BLOCKQUOTE_API_KEY"))
started = client.start_scan("https://example.com", idempotency_key=str(uuid.uuid4()))
print(started.data, started.headers.get("Retry-After"))
# Wait for Retry-After, then read the returned id.
report = client.get_scan(started.data["id"])
comparison = client.compare_scans(from_id="BASELINE_ID", to_id="NEW_ID")
```

Each call returns a `Response` with `data`, `status`, and HTTP `headers`.
`BlockquoteError` retains `data`, `status`, `headers`, and `retry_after`. Network errors pass through.
Requests time out after 30 seconds. Set `timeout` in the constructor to change this.
The client does not retry or poll automatically. Scans can return a cached result or pending status.
Reuse an idempotency key only when you repeat the same scan request.

Public report reads need no key. Account access uses an optional bearer key from [your account](https://blockquote.io/account).
Keys require Pro or Agency. Unattended scan creation can require a paid key with the `scan` scope.
Human verification still applies where required. Pass `turnstile_token` when available; the SDK does not obtain or bypass verification.
Pass `refresh=True` to request a fresh scan with account authentication. Scan quotas still apply.
Read access and comparison output follow your account plan.

See the [API reference](https://blockquote.io/api/docs) and [OpenAPI document](https://blockquote.io/api/v1/openapi.json).

Run tests from this package directory:

```sh
python3 -m unittest discover -s tests
```

## Command line

The package installs the `blockquote` command. `python -m blockquote_agents` runs the same CLI.

```sh
python -m pip install --upgrade blockquote-agents
blockquote --help
blockquote read SCAN_ID
blockquote scan https://example.com --idempotency-key UNIQUE_REQUEST_ID
blockquote compare BASELINE_ID NEW_ID
```

Set `BLOCKQUOTE_API_KEY` for account access. Set `BLOCKQUOTE_TURNSTILE_TOKEN` only when you have a human verification token.
Use `--refresh` with `scan` to request a fresh scan. Authentication and quota rules remain the same.
The CLI prints JSON with `data`, `status`, and `headers`. It does not poll or retry.
HTTP failures print server data, headers, status, and `retryAfter` to stderr with exit code 1.
Other request failures print only their error type to avoid exposing credentials. Invalid arguments exit with code 2.
