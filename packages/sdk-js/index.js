/** HTTP failures retain the server response and retry guidance. */
export class BlockquoteError extends Error {
  constructor(response) {
    super(`Blockquote HTTP ${response.status}`);
    this.name = "BlockquoteError";
    Object.assign(this, response);
    this.retryAfter = response.headers.get("retry-after");
  }
}

export class Blockquote {
  constructor({
    apiKey,
    baseUrl = "https://blockquote.io/api/v1",
    fetch: fetcher = globalThis.fetch,
  } = {}) {
    const base = new URL(baseUrl);
    if (base.protocol !== "https:" || base.username || base.password || base.search || base.hash) {
      throw new TypeError("baseUrl must be an HTTPS URL without credentials, query, or fragment");
    }
    this.baseUrl = base.href.replace(/\/$/, "");
    this.apiKey = apiKey;
    this.fetch = fetcher;
  }

  async request(path, { body, idempotencyKey, signal } = {}) {
    const headers = { Accept: "application/json" };
    if (this.apiKey) headers.Authorization = `Bearer ${this.apiKey}`;
    if (body !== undefined) headers["Content-Type"] = "application/json";
    if (idempotencyKey) headers["Idempotency-Key"] = idempotencyKey;
    const raw = await this.fetch(`${this.baseUrl}${path}`, {
      method: body === undefined ? "GET" : "POST",
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
      signal: signal ?? AbortSignal.timeout(30_000),
      redirect: "error",
    });
    const text = await raw.text();
    let data;
    try {
      data = JSON.parse(text);
    } catch {
      data = text;
    }
    const response = { data, status: raw.status, headers: raw.headers };
    if (!raw.ok) throw new BlockquoteError(response);
    return response;
  }

  startScan(url, { refresh, turnstileToken, idempotencyKey, signal } = {}) {
    return this.request("/scan", {
      body: { url, refresh, turnstileToken },
      idempotencyKey,
      signal,
    });
  }

  getScan(id, { signal } = {}) {
    if (typeof id !== "string" || !id.trim() || id === "." || id === "..")
      throw new TypeError("A scan id is required");
    return this.request(`/scan/${encodeURIComponent(id)}`, { signal });
  }

  compareScans({ from, to, url, signal } = {}) {
    if (url ? from !== undefined || to !== undefined : !from || !to) {
      throw new TypeError("Use url or both from and to");
    }
    const query = new URLSearchParams(url ? { url } : { from, to });
    return this.request(`/compare?${query}`, { signal });
  }
}
