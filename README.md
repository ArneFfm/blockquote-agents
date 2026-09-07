# Blockquote agent integrations

Official integrations for [Blockquote](https://blockquote.io), an AI citability audit for public pages.

## Install

- Skills: `npx skills add ArneFfm/blockquote-agents`
- JavaScript SDK: `npm install https://github.com/ArneFfm/blockquote-agents/releases/download/v0.1.0/blockquote-agents-0.1.0.tgz`
- CLI: `python -m pip install --upgrade blockquote-agents`, then `blockquote --help`.
- Python SDK: `pip install blockquote-agents`

npm registry publication is pending account two-factor verification. Python is published on [PyPI](https://pypi.org/project/blockquote-agents/).

The portable Agent Plugins manifest is `plugin.json`. Its `mcp.json` connects to the product MCP server.
The three product skills cover API access, the scan/fix/re-scan workflow, and comparisons of completed reports.

- [blockquote](skills/blockquote/SKILL.md): product API and MCP access.
- [ai-citability-audit](skills/ai-citability-audit/SKILL.md): scan a page and apply evidence-backed fixes.
- [report-comparison](skills/report-comparison/SKILL.md): compare reports without starting scans.

Install comparison only: `npx skills add ArneFfm/blockquote-agents --skill report-comparison`.

## Interfaces

- Product MCP: https://mcp.blockquote.io/mcp
- Documentation MCP: https://mcp.blockquote.io/docs/mcp
- API reference: https://blockquote.io/api/v1/docs
- Markdown API reference: https://blockquote.io/api/v1/docs.md
- Authentication: https://blockquote.io/auth.md
- Isolated fixture sandbox: https://blockquote.io/api/v1/sandbox
- Documentation keyword search: https://blockquote.io/ask?query=API

Anonymous MCP scans use real network quotas. The fixture sandbox performs no live scans or writes.
Account-scoped access uses a user-created API key. Blockquote has no OAuth authorization server or unattended registration.

## SDKs

See [JavaScript and CLI](packages/sdk-js/README.md) and [Python](packages/sdk-python/README.md).
Each client preserves HTTP status, error payloads, rate-limit headers, and retry guidance.
No client retries automatically.

## Checks

```sh
node --test packages/sdk-js/test.js
PYTHONPATH=packages/sdk-python python3 -m unittest discover -s packages/sdk-python/tests -p 'test_*.py'
```
