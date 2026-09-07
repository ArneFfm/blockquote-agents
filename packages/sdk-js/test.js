import assert from "node:assert/strict";
import { execFileSync, spawnSync } from "node:child_process";
import { test } from "node:test";
import { Blockquote, BlockquoteError } from "./index.js";

test("scan, read, and compare preserve the versioned wire contract", async () => {
  const calls = [];
  const client = new Blockquote({
    apiKey: "test-key",
    fetch: async (url, init) => {
      calls.push({ url, ...init });
      return new Response('{"id":"scan-id"}', { status: 202, headers: { "Retry-After": "3" } });
    },
  });
  const result = await client.startScan("https://example.com", {
    refresh: true,
    idempotencyKey: "request-1",
  });
  assert.equal(result.status, 202);
  assert.equal(result.headers.get("retry-after"), "3");
  assert.deepEqual(JSON.parse(calls[0].body), { url: "https://example.com", refresh: true });
  assert.equal(calls[0].headers.Authorization, "Bearer test-key");
  assert.equal(calls[0].headers["Idempotency-Key"], "request-1");
  assert.equal(calls[0].redirect, "error");
  await client.getScan("a/b");
  assert.equal(calls[1].url, "https://blockquote.io/api/v1/scan/a%2Fb");
  await client.compareScans({ from: "a", to: "b" });
  assert.equal(calls[2].url, "https://blockquote.io/api/v1/compare?from=a&to=b");
  assert.throws(() => client.compareScans({ url: "example.com", from: "a" }));
  assert.throws(() => client.getScan(".."));
});

test("anonymous failures retain JSON or text and Retry-After without retries", async () => {
  for (const body of ['{"error":"quota"}', "upstream unavailable"]) {
    let calls = 0;
    const client = new Blockquote({
      fetch: async (_url, init) => {
        calls++;
        assert.equal(init.headers.Authorization, undefined);
        return new Response(body, { status: 429, headers: { "Retry-After": "60" } });
      },
    });
    await assert.rejects(
      client.getScan("id"),
      (error) =>
        error instanceof BlockquoteError &&
        error.status === 429 &&
        error.retryAfter === "60" &&
        (error.data === body || error.data.error === "quota"),
    );
    assert.equal(calls, 1);
  }
  assert.throws(() => new Blockquote({ baseUrl: "http://example.com" }));
});

test("CLI help is offline and invalid commands fail", () => {
  assert.match(
    execFileSync(process.execPath, ["cli.js", "--help"], {
      cwd: import.meta.dirname,
      encoding: "utf8",
    }),
    /BLOCKQUOTE_API_KEY/,
  );
  const result = spawnSync(process.execPath, ["cli.js", "invalid"], {
    cwd: import.meta.dirname,
    encoding: "utf8",
  });
  assert.equal(result.status, 1);
  assert.match(result.stderr, /Invalid command/);
});
