# Deferred review items from PR #56 (timezone decoding)

Items raised by review bots on PR #56, judged not worth fixing now. Recorded here with rationale so they can be revisited deliberately instead of churned on.

## Non-finite `utcoffset` values (NaN/Infinity) pass `_validate_utcoffset_seconds`

Raised by cubic (P2). A payload with `"utcoffset": NaN` or `Infinity` passes the numeric type check and fails later inside `datetime.timedelta(...)`. Verified behavior: the failure is already loud — the decoder machinery wraps it into `KajsonDecoderError` ("function 'json_decode_datetime' failed: cannot convert float NaN..."). Standard JSON forbids NaN/Infinity literals anyway; only Python's permissive `json` parser produces them. Fixing would only sharpen the error message for a payload no conforming producer can emit. Revisit only if we ever add a strict-JSON mode or see such payloads in the wild.

## ~~`ZoneInfo(name)` resolution priority vs wire `utcoffset`~~ — RESOLVED, cross-check implemented

Originally deferred (raised by cubic as the pathological `timezone(timedelta(hours=5), "Europe/Paris")` case). The /review adversarial pass then showed the collision class is realistic, not pathological: single-segment tzdata keys (`CET`, `EET`, `WET`, `MET`, `EST`, `MST`, `HST`) are exactly the abbreviations developers pass as fixed-offset labels, and — independently of any collision — fold-1 DST fall-back datetimes silently decoded one hour off because the resolved zone defaults to fold=0. Both were verified silent instant corruption, so the cross-check is now implemented in `json_decode_datetime`: the wire offset is authoritative; on mismatch the decoder first tries `fold=1` (ambiguous wall time), then falls back to a fixed offset with the name preserved (mislabeled name or tz-rule drift — the instant wins over zone semantics, since re-encoding keeps the name and identity is recoverable).

## Keyless `ZoneInfo` (from_file) leaks file paths into the wire format

`str()` of a `ZoneInfo.from_file(...)` instance (no key) is its repr, which embeds the local file path — the encoded payload discloses host paths and produces a grotesque tzinfo name. It decodes fine via the offset fallback (instant preserved). Pre-existing wart, rare advanced usage; fixing raises design questions (raise at encode time? store offset only?). Also pre-existing: the bare-ZoneInfo encoder writes `{"zone": null}` for keyless instances, which can never decode. Revisit if anyone actually uses `ZoneInfo.from_file` with kajson.

## Cosmetic error messages for two malformed-payload paths

A bare timezone payload missing `"utcoffset"` surfaces the raw `KeyError` text; a time string without the `.%f` fraction surfaces `list index out of range`. Both are correctly wrapped in `KajsonDecoderError` (loud, no raw exceptions escape) — only the message quality is poor. Not worth dedicated guards for payloads no real producer emits.
