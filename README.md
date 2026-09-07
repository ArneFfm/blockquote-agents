# Blockquote agent integrations

Official integrations for [Blockquote](https://blockquote.io), an AI citability audit for public pages.

## Install

- Skills: `npx skills add ArneFfm/blockquote-agents`
- JavaScript SDK: `npm install https://github.com/ArneFfm/blockquote-agents/releases/download/v0.1.0/blockquote-agents-0.1.0.tgz`
- CLI: Run `blockquote --help` after installing the JavaScript package.
- Python SDK from source: `pip install "git+https://github.com/ArneFfm/blockquote-agents.git#subdirectory=packages/sdk-python"`

npm registry publication is pending account two-factor verification. Python is available from source and the release wheel.

The portable Agent Plugins manifest is `plugin.json`. Its `mcp.json` connects to the product MCP server.
The two product skills cover API access and the scan/fix/re-scan workflow.

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
python3 -m unittest discover -s packages/sdk-python/tests -p 'test_*.py'
```
