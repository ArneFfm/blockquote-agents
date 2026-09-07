---
name: report-comparison
description: Compare two completed Blockquote scans of one URL and explain score changes, changed checks, and resolved or new recommendations. Use after a deployment, when checking a regression, or when asked whether an edit improved a Blockquote report. Reads existing reports without starting scans.
---

# Compare Blockquote reports

Use this skill to compare stored reports. It does not start scans or edit pages.
Blockquote measures AI citability signals, not actual citations or search rank.

## Choose the reports

Use two completed scan IDs for the same submitted URL.
Set `from` to the baseline and `to` to the report after the change.
Check `baseline.scannedAt` and `current.scannedAt` before attributing a difference to a deployment.
A cached report does not prove that the deployed change was scanned.

If IDs are unavailable, send `url` to compare its two newest completed scans.
Send either `from` and `to`, or `url`. Do not combine both forms.
This endpoint does not compare different pages.

## Read the comparison

Use the connected MCP tool `compare_scans` with these arguments:

```json
{"from":"BASELINE_SCAN_ID","to":"CURRENT_SCAN_ID","view":"json"}
```

Replace both placeholder IDs with real report IDs. The remote MCP endpoint is
`https://mcp.blockquote.io/mcp`. `view` accepts `json` or `markdown` and defaults to `json`.

The REST equivalent needs no account for public report reads:

```sh
curl --get 'https://blockquote.io/api/v1/compare' \
  --data-urlencode 'from=BASELINE_SCAN_ID' \
  --data-urlencode 'to=CURRENT_SCAN_ID'
```

Send `Accept: text/markdown` for a formatted comparison.
An optional API key uses `Authorization: Bearer bq_…` and needs the `read` scope.
Keep keys in the client's credential store or environment. Never put keys in shared commands.

## Interpret the evidence

1. Check `methodologyChanged` first. When true, the scoring rules differ and score deltas are null.
2. Read `score.current`, `score.previous`, and `score.delta`. A null delta is not zero improvement.
3. Read `categories` for category changes and `checks.changed` for changed verdicts.
4. Separate `recommendations.resolved`, `recommendations.added`, and `recommendations.stillOpen`.
5. Respect `gated` and each recommendation's `locked` flag. Do not invent withheld fix content.

Report the two scan IDs, scan times, comparable score change, and the main changed checks.
Link the reports as `https://blockquote.io/scan/SCAN_ID`.
Describe a score change as a measured signal, not proof of more traffic or citations.
If methodology changed, report that limitation before discussing individual checks.

## Handle missing evidence

- `404 not_enough_scans`: fewer than two completed scans exist for the URL. Report the missing baseline or current scan.
- `400 scan_not_done`: a selected report is pending or failed. Read it with `get_scan` to distinguish those states.
- `400 url_mismatch`: the reports describe different submitted URLs. Select a matching pair.
- `404`: a requested report is unavailable. Check the ID instead of creating a replacement without user intent.
- `429`: honor `Retry-After`. Do not loop until the service accepts the request.

Read the [product skill](https://blockquote.io/.well-known/agent-skills/blockquote/SKILL.md)
when the task also requires a new scan or account setup.
