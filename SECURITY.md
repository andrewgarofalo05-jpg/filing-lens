# Security and privacy

Filing Lens is a single-user educational application. It binds to 127.0.0.1 by default.
Do not expose it directly to the internet or disable Streamlit's default XSRF protections.
It has no authentication or multi-tenant isolation and is not a hosted service template.

## Where information goes

| Information | Destination and retention |
| --- | --- |
| SEC name/email | SEC User-Agent; app session memory only; not in cache or exports |
| SEC URLs | SEC; public response bodies cached locally for 24 hours of reuse |
| Questions | App session memory; optional user-initiated JSON download |
| AI inputs | Question + up to three passages to local Ollama, only after clicking generate |
| Browser analytics | Streamlit usage telemetry disabled in repository config |
| API keys | None needed, collected or stored |

Cache entries are not automatically deleted at expiry: expiry means a subsequent access fetches
a new response. Delete `.cache/sec/` when you want to remove public cached data. Closing the
app stops the process; browser session cleanup is controlled by Streamlit. Ollama has its own
logging and retention settings; inspect those separately. Corporate proxies and network software
may also log SEC requests. Local Ollama requests bypass environment proxy configuration.

## Defensive boundaries

- Fixed HTTPS SEC hosts and narrow path allowlist; no user-supplied download URLs.
- Redirects disabled, TLS verification enabled, connection/read timeouts and 25 MB decoded cap.
- Requests paced process-wide, cache reuse, bounded transient-error retries, cooldown on blocks.
- Raw filing HTML never rendered; script/style/header elements removed before text extraction.
- Evidence and AI drafts rendered as plain text. No document instruction is executed.
- Local AI has no tools, shell, browsing or file permissions supplied by this app.
- Citation IDs must exist in retrieved evidence. Digits/currency/percent signs in draft claims
  are rejected. Neither check proves entailment or guarantees resistance to prompt injection.
- No pickle deserialization, uploaded documents, arbitrary model endpoints or remote generation.
- `.env`, private keys, Streamlit secrets, downloaded data and caches are ignored by Git.

SEC pacing is per process, not a distributed limiter. Use one instance and account for other
SEC clients sharing your network. The app respects blocks instead of rotating IPs or identities.
Ollama cloud models are filtered, but the app cannot audit a modified local server; for strict
offline assurance, disable Ollama cloud features or disconnect after model installation.

## Reporting issues

After publication, use the repository's **Security → Report a vulnerability** if enabled.
Until a private reporting channel is configured, do not post secrets or exploit details in a
public issue. Notify the repository owner privately. No response-time promise is made for this
student-maintained project. Security reporting setup is part of the release checklist.
