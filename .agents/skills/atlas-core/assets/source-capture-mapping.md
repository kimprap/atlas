# Source capture mapping

Owners map one complete transport result into `source-capture.schema.json` before calling `source.normalize_capture`. Python accepts only that canonical record and never parses harness framing.

| Transport shape | `requested_url` | `final_url` | `content_type` | `method` | `complete` | `notes` | `text` |
|---|---|---|---|---|---|---|---|
| GitHub `file_read` | Original requested HTTP(S) GitHub URL | Exact resolved HTTP(S) file URL reported by the tool, or the requested URL when no redirect occurred | Reported textual media type; use `text/plain` only when the tool identifies decoded file text without a media type | `github-file-read` | `true` only for the complete file with no omitted range | Tool-provided nonsecret notes in order | Exact decoded file characters returned for the complete file |
| OMP native reader | Original requested HTTP(S) URL | Structured `finalUrl` | Structured textual `contentType` | Structured retrieval `method` | `true` only when structured `truncated` is false and every omitted range has been read | Structured notes in order | Exact source body supplied separately from reader-rendered metadata; never split a rendered prefix |
| Generic HTTP or browser | Original requested HTTP(S) URL | Final response/page HTTP(S) URL after redirects | Final textual response/page media type | `http`, `browser`, or another explicit transport method | `true` only after the complete textual representation is available | Explicit retrieval notes in order | Exact extracted readable text, including original newline and Unicode characters |

All eight keys are required and no aliases are accepted. `requested_url` and `final_url` are normalized by the canonical URL owner; `content_type` must be textual; `complete` must be `true`; and `text` must be nonempty valid Unicode encodable as UTF-8. Mapping failure is terminal no-write. Do not recursively inspect arbitrary objects, guess provider fields, parse human-readable wrappers, substitute cached text, or add provider-specific runtime hooks.
