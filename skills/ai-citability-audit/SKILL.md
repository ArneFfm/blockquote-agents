---
name: ai-citability-audit
description: Audit a page for AI citability with Blockquote (blockquote.io) and fix it. Use when a page must be citable by ChatGPT, Perplexity or Google AI Overviews, when asked to raise a Blockquote score, when diagnosing why an answer engine does not cite a page, or when adding JSON-LD, llms.txt, a TL;DR or quotable structure for that purpose. Drives a scan, read the ranked fixes, apply the smallest one, re-scan loop over Blockquote's MCP server or its REST API.
---

# AI Citability Audit

Blockquote scores one public URL from 0 to 100 for AI citability. The score answers
one question: how likely are ChatGPT, Perplexity and Google AI Overviews to cite this
page? A scan runs 34 checks in three weighted categories. 29 checks are deterministic.
5 use a language model against a fixed rubric; the playbook below marks those
"LLM-judged".

Work one check at a time:

**scan → read the ranked fixes → apply the smallest fix for the top recommendation → re-scan.**

Do not rewrite the page. Each recommendation carries a copy-paste payload. Apply it,
then take the next one.

This skill is served from https://blockquote.io/.well-known/agent-skills/ai-citability-audit/SKILL.md.
Fetch it fresh rather than working from a memorised copy.

## Step 1 — Scan the page

The scan needs no account. Blockquote's MCP server accepts a stateless JSON-RPC call,
so plain `curl` is enough:

```bash
curl -s -X POST https://mcp.blockquote.io/mcp \
  -H 'content-type: application/json' \
  -H 'accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call",
       "params":{"name":"start_scan","arguments":{"url":"https://example.com"}}}'
```

The answer is one Server-Sent Event. The tool payload is the JSON string in
`result.content[0].text`:

```json
{
  "scanId": "u4h7hxswu0lq",
  "status": "pending",
  "cached": false,
  "reportUrl": "https://blockquote.io/scan/u4h7hxswu0lq",
  "next": "Scan dispatched. Poll get_scan with scanId \"u4h7hxswu0lq\" every ~8 seconds until status is done."
}
```

If the MCP server is already connected as a tool provider, call `start_scan` directly
instead of shelling out. Setup: https://blockquote.io/docs/ai-agents.

Four rules the scan enforces:

- The URL must be HTTPS and reachable from the public internet. An `http://` URL is
  refused with `invalid_url`. A page on localhost cannot be scanned — scan a deployed
  preview URL instead.
- Anonymous callers get 1 scan per day and 3 per month from one network. MCP and
  REST share those counters.
- A URL scanned inside the 24-hour cache window answers from the cache. It returns
  `"status": "done"` and `"cached": true` at once, with the stored scan id.
- `POST /api/v1/scan` over REST refuses an anonymous caller with `turnstile_failed`,
  because the browser form is behind Cloudflare Turnstile. The MCP route above is the
  no-account path. The REST route needs a Pro or Agency plan — an API key
  (`Authorization: Bearer bq_…`) or that plan's signed-in session. A free session is
  refused the same way, except on the `refresh: true` path of step 5.

## Step 2 — Fetch the report

Poll until the report arrives. A scan takes about 15 to 45 seconds. A pending scan
answers `{"id": "…", "status": "pending"}`. A failed scan answers
`{"id": "…", "status": "error", "error": "…"}` with HTTP 500 — stop and report that
string. The finished report carries no `status` field, so stop when the body carries
`score`.

Over MCP, `get_scan` with the default `view` `summary` sets `status` to `done` instead,
which is what the `next` string of step 1 asks you to wait for. `view` `full` and `view`
`markdown` carry no `status` field — poll with the default, then re-read with the view
you want.

Reading a report needs no account and spends no scan quota:

```bash
SCAN_ID=u4h7hxswu0lq   # the scanId from step 1
curl -s "https://blockquote.io/api/v1/scan/$SCAN_ID"
```

Three shapes of the same report:

| What you want | Call |
|---|---|
| The full report as JSON | `GET /api/v1/scan/{id}` |
| The full report as one Markdown document | `GET /api/v1/scan/{id}` with `Accept: text/markdown` |
| The report wrapped in an instruction prompt | `GET /api/v1/scan/{id}/ai-instructions` |

The Markdown document is the best single input when you plan the work yourself. The
`ai-instructions` document is the best input when you apply the fixes straight away —
it states the apply order and the verification step.

Over MCP, `get_scan` with `view` `full` returns the JSON report, and `view` `markdown`
returns the Markdown document. The default `view` `summary` returns the score, the
category scores and the top recommendations only — it carries no check results. No
`view` returns the ai-instructions document; the MCP prompt `fix_top_issues` plays that
role.

## Step 3 — Read the report

The report carries a score, three category scores, 34 check results and a ranked
recommendation list.

**Score.** Each category scores 0 to 100. The overall score weights them: schema 40%,
structure 30%, citability 30%.

**Category score.** Every check has a `weight` from 1 to 5 inside its category and a
`score` from 0 to 1. The category score is the weighted mean of its check scores,
rescaled to 0 to 100: the mean of the 0-to-1 scores, times 100, rounded. A check
marked `notApplicable` leaves both sides of that mean — an FAQPage check on a
navigational page neither helps nor hurts.

**Check result.** One entry per check:

```json
{
  "id": "schema-jsonld-present",
  "category": "schema",
  "weight": 5,
  "pass": false,
  "score": 0,
  "evidence": "No JSON-LD blocks found in the document.",
  "fix": { "kind": "jsonld", "title": "…", "payload": "…", "guidance": "…" }
}
```

`pass` is the hard verdict. `score` is the graded one — a graded check can score 0.6
and still fail its threshold, so read `score` when you rank near-misses. `evidence`
states what the scan found. `notApplicable: true` means the check did not apply.

**Recommendations.** `report.recommendations` is the work list, highest `priority`
first. Each entry names its `checkId` and carries `fix.payload`: the exact JSON-LD
block or the content edit to make. `fix.kind` is `jsonld` or `content`. That payload is
what you apply — the playbook below tells you what the check is about.

**What a free caller sees.** All 34 check results, and fix content for the first 3
recommendations. The rest come back as `{"locked": true}` with only `checkId`,
`category`, `priority` and `summary`, and the report sets `"gated": true` whenever it
withheld anything. A Pro or
Agency API key unlocks the complete fix list. Never guess a locked payload — read the
check id in the playbook below and fix it from there.

## Step 4 — Fix playbook

One line per check: the id you will see in a report, what it measures and the fix.
The catalogue is also published at https://blockquote.io/checks, one anchor per check
id (for example https://blockquote.io/checks#schema-jsonld-present).

The block below is generated from Blockquote's check catalogue
(`packages/types/src/check-catalog.ts`) and a test pins it there. Do not edit it by
hand.

<!-- generated:playbook:start -->

### Schema — 40% of the score

- `schema-jsonld-present` — JSON-LD present. Whether the page embeds any JSON-LD structured data at all. **Fix:** Add a <script type="application/ld+json"> block describing the page (Article, Organization, …) to the <head>.
- `schema-organization` — Organization schema. Whether an Organization (or publisher) entity is declared in structured data. **Fix:** Add Organization JSON-LD with name, url, and logo, and reference it as the page's publisher.
- `schema-article` — Article schema. Whether content pages declare an Article/BlogPosting entity with headline and dates. **Fix:** Add Article JSON-LD with headline, datePublished, dateModified, and author.
- `schema-faqpage` — FAQPage schema. Whether pages with question-and-answer content declare FAQPage markup. **Fix:** Mirror the on-page questions and answers in FAQPage JSON-LD (only content that is visible on the page).
- `schema-author` — Author schema. Whether structured data names a Person (or Organization) as the content's author. **Fix:** Add an author Person to the Article JSON-LD with name and, ideally, url or sameAs.
- `schema-breadcrumb` — Breadcrumb schema. Whether BreadcrumbList markup describes where the page sits in the site. **Fix:** Add BreadcrumbList JSON-LD mirroring the visible breadcrumb trail.
- `schema-sitemap` — Sitemap coverage. Whether the site serves a sitemap.xml and it includes the scanned URL. **Fix:** Serve /sitemap.xml, include this URL with an accurate lastmod, and reference it in robots.txt.
- `schema-llms-txt` — llms.txt present. Whether the site serves an llms.txt file with meaningful sections. **Fix:** Serve /llms.txt (llmstxt.org format): a one-line summary, key pages, and access policy.
- `schema-robots-llm-access` — LLM crawler access. Whether robots.txt allows the major AI crawlers (GPTBot, ClaudeBot, PerplexityBot, …). **Fix:** Allow the AI crawlers you want citations from in robots.txt (and block only what you mean to block).
- `schema-canonical` — Canonical URL. Whether the page declares a canonical URL that matches where it is served. **Fix:** Add <link rel="canonical"> pointing at the page's one true HTTPS URL.
- `schema-open-graph` — Open Graph tags. Whether og:title, og:description, and og:image are present and non-empty. **Fix:** Add complete Open Graph meta tags with an absolute 1200×630 og:image URL.
- `schema-knowledge-graph` — Knowledge graph sameAs. Whether the publisher entity links out to its profiles via sameAs. **Fix:** Add a sameAs array of official profile URLs to the Organization or Person JSON-LD.
- `schema-date-freshness` — Publication date. Whether the page carries a machine-readable publication/modification date, and how old it is. **Fix:** Declare datePublished and keep dateModified current in the Article JSON-LD.
- `schema-meta-description` — Meta description. Whether a meta description exists and is a useful length. **Fix:** Write a 120–160 character meta description that states what the page answers.
- `schema-image-alt-text` — Image alt text. Whether content images carry descriptive alt attributes. **Fix:** Give every meaningful content image a specific, descriptive alt attribute.
- `schema-jsonld-validity` — JSON-LD validity. Whether every JSON-LD block on the page parses as valid JSON. **Fix:** Fix the JSON syntax (trailing commas, unescaped quotes) so every block parses.
- `schema-date-consistency` — Date consistency. Whether dates in structured data agree with the dates shown on the page. **Fix:** Make visible dates and JSON-LD dates identical, including the timezone story.

### Structure — 30% of the score

- `content-tldr` — TL;DR or summary block. Whether the page opens with a short summary of its key points. **Fix:** Add a 2–4 sentence TL;DR near the top that states the page's core claims.
- `content-direct-answer` — Direct answer near the top. Whether the page answers its main question within the first paragraphs. **Fix:** State the direct answer in the first ~100 words, then elaborate below it.
- `content-question-h2` — Question-style H2 structure. Whether section headings are phrased as the questions readers actually ask. **Fix:** Rephrase key H2/H3 headings as full questions ("How does … work?").
- `content-definition-opener` — Definition-led opener. Whether the page opens by defining its subject in one clean sentence. **Fix:** Open with "<Subject> is …" — one self-contained defining sentence.
- `content-lists-tables` — Lists and tables. Whether the content uses lists or tables where it enumerates or compares. **Fix:** Turn step sequences and comparisons into ordered lists or small tables.
- `content-subheading-frequency` — Subheading frequency. Whether long stretches of prose are broken up by subheadings. **Fix:** Add a descriptive subheading roughly every 150–300 words.
- `content-client-rendered` — Client-side rendering. Whether the raw HTML this scan fetched carries the page's content, or only a script-driven shell that fills it in after load. **Fix:** Server-render or statically prerender the route so its content ships inside the first HTML response.
- `content-extractable-scope` — Extractable content scope. Whether the primary heading, and the bulk of the text, sit outside <header>, <footer>, <nav> and <aside>. **Fix:** Move the H1 and the body copy into <main> or <article>; keep header, footer, nav and aside for site furniture.

### Citability — 30% of the score

- `citability-fact-density` — Fact density. LLM-judged: how many concrete, checkable facts the content carries per unit of text. **Fix:** Replace vague claims with numbers, dates, names, and specific outcomes.
- `citability-author-byline` — Author byline. Whether a visible byline names who wrote the page. **Fix:** Add a visible byline with the author's name (and link it to an author page).
- `citability-original-data` — Original data or unique claims. LLM-judged: whether the page contributes information that does not exist elsewhere. **Fix:** Publish something only you have: your own measurements, benchmarks, or documented experience.
- `citability-direct-paragraphs` — Direct paragraphs. LLM-judged: whether paragraphs make their point in the first sentence. **Fix:** Rewrite paragraph openers to state the conclusion first, evidence second.
- `citability-citation-density` — Citation density. Whether the content links out to credible sources for its claims. **Fix:** Link claims to primary sources; a handful of authoritative external links beats none.
- `citability-emphasis` — Emphasis and scannability. Whether key phrases are emphasized (bold/strong) at a healthy rate. **Fix:** Bold the decision-relevant phrases — sparingly, roughly a handful per section.
- `citability-word-count` — Word count. Whether the main content is substantial enough to be a citable treatment. **Fix:** Grow the page toward a complete treatment of its question (typically 1,000+ words).
- `citability-pronoun-clarity` — Pronoun clarity. LLM-judged: whether sentences remain unambiguous when quoted out of context. **Fix:** Replace ambiguous pronouns with their nouns in key sentences.
- `citability-quote-extractability` — Quote extractability. LLM-judged: whether the page contains self-contained sentences worth quoting verbatim. **Fix:** Write a few deliberate, self-contained key sentences that survive being quoted alone.

<!-- generated:playbook:end -->

## Step 5 — Re-scan and compare

Re-scan the URL after you deploy the fix, then compare the two scans:

```bash
curl -s 'https://blockquote.io/api/v1/compare?url=https://example.com/'
```

`url` compares the two newest stored scans of that page. `from` and `to` compare two
named scan ids. `Accept: text/markdown` returns the same comparison as one Markdown
section. Over MCP the tool is `compare_scans`.

The comparison names the score delta, the per-category deltas, every check whose
verdict flipped, and the recommendations split into `resolved`, `added` and
`stillOpen`:

```json
{
  "score": { "current": 17, "previous": 16, "delta": 1 },
  "categories": [{ "category": "citability", "score": 25, "previous": 20, "delta": 5 }],
  "checks": { "changed": [{ "checkId": "citability-quote-extractability", "from": "fail", "to": "pass" }], "unchanged": 33 },
  "recommendations": { "resolved": [], "added": [], "stillOpen": [] }
}
```

`methodologyChanged: true` means the two reports were produced under different scoring
versions. Read the delta as indicative when you see it, not as the effect of your edit.

One limit to plan around: a repeat scan of the same URL is answered from the 24-hour
cache, so an anonymous caller cannot verify a fix on the same URL the same day.
Three ways out, in order of cost:

1. Scan the deployed preview URL of the fixed page. A different URL is a different scan.
2. Wait for the cache to expire.
3. Send `refresh: true` from any signed-in account, which skips the cache. An agent
   needs a Pro or Agency API key to do this unattended, because a free account gets no
   API keys.

Report progress in this shape:

```
## Blockquote score: {score}/100  [was {previous}/100]
Fixed: {check ids that flipped to pass}
Still open: {check ids}
Next: {top recommendation checkId} — {one-line plan}
```

## Step 6 — What Blockquote does not measure

Blockquote does not measure keyword rank, backlinks or Core Web Vitals.

It scores one page at a time, from that page's served HTML plus the site's
`sitemap.xml`, `llms.txt` and `robots.txt`. It does not crawl a whole site, it does not
render JavaScript, and it does not report whether an assistant actually cited the page.
A rising score means the page is easier to cite. It is not proof of a citation.

## Limits and plans

- **Anonymous**: 1 scan per day and 3 per month from one network, no account. Full
  score, all 34 check results, top 1 fix.
- **Free account**: 1 scan per day, 30 per month. Full score, all 34 check results, top
  3 fixes, scan history, plus `refresh: true` to skip the 24-hour cache.
- **Pro** and **Agency**: the complete fix list, weekly monitoring of a URL, and API
  keys for agents and scripts. Details: https://blockquote.io/pricing.md.

The REST surface is described by https://blockquote.io/api/v1/openapi.json. The product's
own summary for agents is https://blockquote.io/llms.txt.
