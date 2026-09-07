#!/usr/bin/env node
import { parseArgs } from "node:util";
import { Blockquote, BlockquoteError } from "./index.js";

const help = `Usage: blockquote <command>
  scan <https-url> [--refresh] [--idempotency-key <key>]
  read <scan-id>
  compare <from-id> <to-id>
  --help

Set BLOCKQUOTE_API_KEY for account access. Public report reads need no key.
Scan creation can require a paid API key or human verification.
Set BLOCKQUOTE_TURNSTILE_TOKEN for a token obtained through human verification.
Responses are JSON with data, status, and headers. Scans are asynchronous.
Read the returned scan id after Retry-After. No automatic retries are made.
`;

try {
  const { values, positionals } = parseArgs({
    allowPositionals: true,
    options: {
      help: { type: "boolean", short: "h" },
      refresh: { type: "boolean" },
      "idempotency-key": { type: "string" },
    },
  });
  if (values.help || positionals.length === 0) {
    process.stdout.write(help);
  } else {
    const [command, first, second] = positionals;
    const client = new Blockquote({ apiKey: process.env.BLOCKQUOTE_API_KEY });
    let result;
    if (command === "scan" && first && positionals.length === 2) {
      result = await client.startScan(first, {
        refresh: values.refresh,
        idempotencyKey: values["idempotency-key"],
        turnstileToken: process.env.BLOCKQUOTE_TURNSTILE_TOKEN,
      });
    } else if (
      command === "read" &&
      first &&
      positionals.length === 2 &&
      !values.refresh &&
      !values["idempotency-key"]
    ) {
      result = await client.getScan(first);
    } else if (
      command === "compare" &&
      first &&
      second &&
      positionals.length === 3 &&
      !values.refresh &&
      !values["idempotency-key"]
    ) {
      result = await client.compareScans({ from: first, to: second });
    } else {
      throw new Error("Invalid command or arguments. Run blockquote --help.");
    }
    console.log(
      JSON.stringify({ ...result, headers: Object.fromEntries(result.headers) }, null, 2),
    );
  }
} catch (error) {
  console.error(
    JSON.stringify(
      error instanceof BlockquoteError
        ? {
            error: error.message,
            status: error.status,
            data: error.data,
            headers: Object.fromEntries(error.headers),
            retryAfter: error.retryAfter,
          }
        : { error: error.message },
    ),
  );
  process.exitCode = 1;
}
