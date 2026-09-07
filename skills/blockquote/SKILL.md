---
name: blockquote
description: Score a public URL 0-100 for AI citability with Blockquote and get the fixes. Use when checking whether ChatGPT, Perplexity or Google AI Overviews can cite a page, when comparing a page before and after an edit, when watching a set of URLs for score changes, or when pulling a finished report into another tool as JSON or Markdown. Anonymous use needs no account.
---

# Blockquote — AI citability scoring

Blockquote scores a public HTTPS URL 0-100 for AI citability: how likely ChatGPT, Claude,
Perplexity and Google AI Overviews are to cite it. A scan runs 34 checks in three weighted
categories — schema 40%, structure 30%, citability 30%. 29 checks are deterministic. 5 use a
language model against a fixed rubric. A check that does not apply to the page is marked N/A and
leaves the score. Every failure carries a copy-paste fix, generated JSON-LD included.

A scan is asynchronous. Start it, poll for the result, then read the report by id. A scan takes
about 15-45 seconds. A report younger than 24 hours comes back from the cache at once.

## Two ways in

| Way in | Endpoint | Anonymous |
|---|---|---|
| Remote MCP server | `https://mcp.blockquote.io/mcp` — Streamable HTTP, stateless | Yes |
| REST API | `https://blockquote.io/api/v1/…` — OpenAPI 3.1 at `/api/v1/openapi.json` | Read only |

Call the versioned base `/api/v1/`. The unversioned `/api/` base answers the same routes and
stays, but every answer from it carries `Deprecation` and a `Link` naming `/api/v1` as its
successor.

Prefer MCP. It starts a scan without an account. Over REST, `POST /api/v1/scan` refuses an
anonymous caller with `403 turnstile_failed`: the browser form proves the caller is human with a
Cloudflare Turnstile token, and an agent cannot produce one. A Pro or Agency API key removes that
gate. Read routes such as `GET /api/v1/scan/{id}` stay open to everybody.

## Connect the MCP server

```bash
claude mcp add --transport http blockquote https://mcp.blockquote.io/mcp
```

Cursor (`~/.cursor/mcp.json`) and VS Code (`.vscode/mcp.json`) use the same shape:

```json
{
  "mcpServers": {
    "blockquote": {
      "url": "https://mcp.blockquote.io/mcp",
      "headers": { "Authorization": "Bearer bq_YOUR_KEY" }
    }
  }
}
```

Delete the `headers` line for anonymous use.

## MCP tools

| Tool | Arguments | Needs an API key |
|---|---|---|
| `start_scan` | `url`; `refresh` optional | No — `refresh` yes |
| `get_scan` | `scanId`; `view`: `summary` (default), `full`, `markdown` | No |
| `compare_scans` | `from` and `to`, or `url`; `view`: `json` (default), `markdown` | No |
| `list_checks` | `category` optional: `schema`, `structure`, `citability` | No |
| `explain_check` | `checkId` | No |
| `get_account` | none | Yes |
| `list_monitors` | none | Yes |
| `add_monitor` | `url` | Yes |
| `remove_monitor` | `id` | Yes |

### Prompts and resources

The server registers two prompts, two resources and one resource template:

| Name or URI | Kind | Purpose |
|---|---|---|
| `analyze_report` | Prompt | Rank every finding of one scan by score impact. Argument: `scanId`. |
| `fix_top_issues` | Prompt | Apply the top fixes to the project. Arguments: `scanId`, `maxFixes`. |
| `blockquote://checks` | Resource | The whole check catalog as JSON. |
| `blockquote://llms.txt` | Resource | The live product summary of blockquote.io. |
| `blockquote://scan/{scanId}/report.md` | Resource template | One finished report as Markdown. |

## Worked example — MCP

Any HTTP client reaches the endpoint. The server is stateless, so no session id is needed.

```bash
curl -X POST https://mcp.blockquote.io/mcp \
  -H "content-type: application/json" \
  -H "accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call",
       "params":{"name":"start_scan","arguments":{"url":"blockquote.io/llm-friendly"}}}'
```

The tool result carries the scan id:

```json
{
  "scanId": "mof4htesy950",
  "status": "pending",
  "cached": false,
  "reportUrl": "https://blockquote.io/scan/mof4htesy950",
  "next": "Scan dispatched. Poll get_scan with scanId \"mof4htesy950\" every ~8 seconds until status is done."
}
```

Poll every 8 seconds until `status` is `done`. The default `summary` view holds the score, the
category scores, the top recommendations and the pass/fail counts:

```bash
curl -X POST https://mcp.blockquote.io/mcp \
  -H "content-type: application/json" \
  -H "accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call",
       "params":{"name":"get_scan","arguments":{"scanId":"mof4htesy950"}}}'
```

Ask for `view: "markdown"` when you want the whole report — every check, its evidence and every
fix payload — as one document to reason over:

```bash
curl -X POST https://mcp.blockquote.io/mcp \
  -H "content-type: application/json" \
  -H "accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":3,"method":"tools/call",
       "params":{"name":"get_scan","arguments":{"scanId":"mof4htesy950","view":"markdown"}}}'
```

## Worked example — REST

Start a scan. This call needs a Pro or Agency key:

```bash
curl -X POST https://blockquote.io/api/v1/scan \
  -H "authorization: Bearer bq_YOUR_KEY" \
  -H "content-type: application/json" \
  -d '{"url":"https://example.com/blog/post"}'
```

A dispatched scan answers `202` with a `Location` header of `/api/v1/scan/{id}` and a `Retry-After`
header. A fresh cached report answers `200` with `status` `done` and `cached` true. Add
`"refresh": true` to skip the cache and read the live page again.

Read the result. These calls need no key:

```bash
# JSON report, or {"status":"pending"} while the scan runs
curl https://blockquote.io/api/v1/scan/mof4htesy950

# the same report as one Markdown document
curl -H "accept: text/markdown" https://blockquote.io/api/v1/scan/mof4htesy950

# live progress, until the scan reaches done or error
curl -N -H "accept: text/event-stream" https://blockquote.io/api/v1/scan/mof4htesy950/events
```

Other routes worth knowing:

| Route | Returns |
|---|---|
| `GET /api/v1/scan/{id}/ai-instructions` | The report wrapped in a ready-to-paste prompt for a coding agent. Markdown. |
| `GET /api/v1/compare?url=…` or `?from=…&to=…` | Score and category deltas, flipped checks, and resolved / new / open fixes. `Accept: text/markdown` works here too. |
| `GET /api/v1/account/usage` | Effective plan, its limits, and scans used today and this month. |
| `GET /api/v1/monitors`, `POST /api/v1/monitors`, `DELETE /api/v1/monitors/{id}` | The weekly watchlist. |
| `GET /api/v1/history`, `GET /api/v1/history/{urlHash}` | Stored scans per URL. Pro and Agency. |
| `GET /api/v1/openapi.json`, `GET /api/v1/docs` | The full specification and its reference UI. |

## What a report holds

`score` 0-100, one entry per category in `categories`, one entry per check in `checks` (34 of
them, each with `pass`, `notApplicable` and its evidence), and `recommendations` ordered by
priority.

Fix content is plan-gated. An anonymous or free caller keeps the fix on the first 3
recommendations. Every further entry comes back with `locked: true` and only `checkId`,
`category`, `priority` and `summary`, and the report sets `gated: true`. The score and all 34
check results stay complete at every tier. Pro and Agency callers get the whole fix list and
`gated: false`.

## Authentication

- **Anonymous** needs nothing. The caller is metered by IP.
- **API key**: `Authorization: Bearer bq_…`. Keys belong to the Pro and Agency plans and are
  created at `https://blockquote.io/account`. A key is shown exactly once — only its hash is
  stored. An account holds at most **5 keys you create yourself**; connected apps do not count
  against that number.
- **Scopes** are chosen at creation from `read`, `scan` and `monitors`, and default to `read` and
  `scan`. A key must carry `read`, because every readable route sits behind it. Scopes are fixed
  for the life of a key: to change them, create a new key. Three further scopes exist in the
  vocabulary and are never granted — `webhooks`, `billing` and `delete` — so the routes behind them refuse
  every key the account page issues today.
- Key management is session-only. No key, whatever its scope, can create or revoke a key.
- An invalid or revoked key answers `401 invalid_api_key`. It never degrades to anonymous.

## Limits, and the 429 body

| Caller | Scans |
|---|---|
| Anonymous, per IP | 1 per day, 3 per month |
| Free account | 1 per day, 30 per month |
| Pro | 30 per day, 200 per month |
| Agency | 60 per day, 500 per month |

Only a dispatched scan spends a slot; a cached report is free. The MCP endpoint carries a second,
independent ceiling of 120 requests per hour per IP, so the cheap tools cannot be hammered.

A refusal is `429` with this body:

```json
{
  "error": "rate_limited",
  "message": "Daily limit of 1 scans from this network reached.",
  "scope": "day",
  "limit": 1,
  "used": 1,
  "resetAt": "2026-08-24T00:00:00.000Z",
  "authenticated": false,
  "plan": null,
  "upgrade": "signup",
  "retryAfterSec": 1854
}
```

- `error` is `rate_limited` for an IP refusal and `quota_exceeded` for an account refusal.
- `scope` names the bucket that refused: `day` or `month`.
- `resetAt` is the exact UTC instant that bucket rolls over. Wait for it. Do not guess a delay.
- `plan` is null for an anonymous caller, because an anonymous caller has no plan.
- `retryAfterSec` is in the body on the anonymous path only. The `Retry-After` header rides every
  `429`, the account path included, so read the header rather than this field.

Every answer carries `RateLimit`, `RateLimit-Policy`, `RateLimit-Limit`, `RateLimit-Remaining` and
`RateLimit-Reset`, on the refusal and on the admitted answer alike. `RateLimit` and
`RateLimit-Policy` are Structured Field lists and name every bucket you are metered on. Read them
and throttle yourself before a refusal.

A `503` on `POST /api/v1/scan` carries `scan_budget_exhausted`: the account-wide daily scan budget
is spent. Retry after 00:00 UTC, not before.

## Monitoring and webhooks

A monitor re-scans one URL every week and mails a digest in any week the score moves. The
allowance is 0 URLs on the free plan, 5 on Pro and 25 on Agency. Manage monitors with
`add_monitor`, `list_monitors` and `remove_monitor` over MCP, or with `/api/v1/monitors` over REST.
A key needs the `monitors` scope to add or remove one, and `read` to list them. At the plan cap
the call is refused with `402` and the reason names the allowance.

Outbound webhooks deliver those weekly results and belong to the **Agency** plan. Configure the
endpoint at `POST /api/v1/webhooks` with the session cookie: `webhooks` is not a grantable scope, so
a key created since scopes shipped answers `403 insufficient_scope` there.

A delivery is a `POST` of JSON with three headers:

- `X-Blockquote-Signature: t=<unix-seconds>,v1=<hex>`
- `X-Blockquote-Event-Id`
- `X-Blockquote-Event-Type`

The signature is HMAC-SHA256 over the string `<t>.<raw body>`, keyed with the endpoint secret
(`whsec_…`), in lowercase hex — the scheme Stripe uses. Verify it against the raw bytes before
you parse them, and reject a stale `t`.

The payload carries `schema_version` `"1"`, `event` `"monitor.weekly_result"`, `event_id`,
`delivered_at`, the `monitor`, the `scan`, a `score` block with `current`, `previous` and
`delta`, one entry per category, and up to 3 recommendations. When the report schema changed
between the two runs, `previous` and `delta` are null: the older score came from different
checks, so the difference would be a false alarm.

Delivery times out after 10 seconds — answer `2xx` first and do the work afterwards. A `5xx`, a
`429` or a network error is retried; any other `4xx` is not. The delay starts at 30 seconds and
doubles up to a ceiling of one hour, for at most 6 retries, then the event goes to the
dead-letter queue.

## When not to use Blockquote

- Blockquote does not measure keyword rank, backlinks or Core Web Vitals. For those, use a
  classic SEO tool.
- It scans one URL at a time. It does not crawl a site and it has no bulk endpoint.
- It reads server-rendered HTML with no browser, so content that only a JavaScript runtime
  produces is invisible to it.
- It cannot reach a page behind a login, and it accepts public HTTPS URLs only.
- It reports; it does not edit your site. The fixes are text and JSON-LD for you or your agent to
  apply.
- Do not index `/api/*` or the MCP endpoint, and do not crawl `/scan/*`, `/account` or `/login`.

## Where to look next

- Check catalog, one anchor per check id: <https://blockquote.io/checks>
- The method behind the score: <https://blockquote.io/llm-friendly>
- Agent setup, keys and limits: <https://blockquote.io/docs/ai-agents>
- Webhook reference: <https://blockquote.io/docs/webhooks>
- Product summary for agents: <https://blockquote.io/llms.txt>
