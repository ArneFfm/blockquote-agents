# Blockquote JavaScript SDK and CLI

Official client for [Blockquote](https://blockquote.io). Requires Node.js 20 or later. No runtime dependencies.

```sh
npm install https://github.com/ArneFfm/blockquote-agents/releases/download/v0.1.0/blockquote-agents-0.1.0.tgz
npm exec -- blockquote --help
npm exec -- blockquote read SCAN_ID
```

npm registry publication is pending. Install the official release archive above.

```js
import { Blockquote, BlockquoteError } from "blockquote-agents";

const client = new Blockquote({ apiKey: process.env.BLOCKQUOTE_API_KEY });
const started = await client.startScan("https://example.com", {
  idempotencyKey: crypto.randomUUID(),
});
console.log(started.data, started.headers.get("retry-after"));
// Wait for Retry-After, then read the returned id.
const report = await client.getScan(started.data.id);
const comparison = await client.compareScans({ from: "BASELINE_ID", to: "NEW_ID" });
```

Each call returns `{ data, status, headers }`. `headers` is a standard `Headers` object.
`BlockquoteError` retains `data`, `status`, `headers`, and `retryAfter`. Network errors pass through.
Requests time out after 30 seconds. Pass `signal` in method options to control cancellation.
The client does not retry or poll automatically. Scans can return a cached result or pending status.
Reuse an idempotency key only when you repeat the same scan request.

Public report reads need no key. Account access uses an optional bearer key from [your account](https://blockquote.io/account).
Keys require Pro or Agency. Unattended scan creation can require a paid key with the `scan` scope.
Human verification still applies where required. The SDK accepts `turnstileToken`; it does not obtain or bypass verification.
Pass `refresh: true` to request a fresh scan with account authentication. Scan quotas still apply.
Read access and comparison output follow your account plan.

The CLI reads `BLOCKQUOTE_API_KEY` and optional `BLOCKQUOTE_TURNSTILE_TOKEN` from the environment.
It prints response data, status, and headers as JSON. Failures go to stderr with exit code 1.

```sh
npm exec -- blockquote scan https://example.com --idempotency-key UNIQUE_REQUEST_ID
npm exec -- blockquote read SCAN_ID
npm exec -- blockquote compare BASELINE_ID NEW_ID
npm test
```

See the [API reference](https://blockquote.io/api/docs) and [OpenAPI document](https://blockquote.io/api/v1/openapi.json).
