# Blockquote integration instructions

Use the product skills in `skills/` for Blockquote workflows.

- Read https://blockquote.io/auth.md before account-scoped calls.
- Use https://mcp.blockquote.io/mcp for anonymous scans. These consume real quotas.
- Use https://blockquote.io/api/v1/sandbox for synthetic reports without writes or quota use.
- Keep API keys in environment variables. Never commit credentials or include them in reports.
- Honor Retry-After and rate-limit headers. Do not retry failed mutations automatically.
- Apply only evidence-backed page fixes. Do not invent prices, credentials, or review claims.
- Re-scan the deployed page to verify a fix. Local changes do not prove a score increase.
- Stage only files you changed.

Run the SDK checks in README.md before changing SDK behavior.
