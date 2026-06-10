# Deferred review items from PR #56 (timezone decoding)

Items raised by review bots on PR #56, judged not worth fixing now. Recorded here with rationale so they can be revisited deliberately instead of churned on.

## Non-finite `utcoffset` values (NaN/Infinity) pass `_validate_utcoffset_seconds`

Raised by cubic (P2). A payload with `"utcoffset": NaN` or `Infinity` passes the numeric type check and fails later inside `datetime.timedelta(...)`. Verified behavior: the failure is already loud — the decoder machinery wraps it into `KajsonDecoderError` ("function 'json_decode_datetime' failed: cannot convert float NaN..."). Standard JSON forbids NaN/Infinity literals anyway; only Python's permissive `json` parser produces them. Fixing would only sharpen the error message for a payload no conforming producer can emit. Revisit only if we ever add a strict-JSON mode or see such payloads in the wild.

## `ZoneInfo(name)` resolution priority vs wire `utcoffset`

Raised by cubic (P2). `_decode_tzinfo` resolves the tzinfo name through `ZoneInfo` before considering the `utcoffset` field. If someone constructs `datetime.timezone(timedelta(hours=5), "Europe/Paris")` — a fixed offset deliberately labeled with an IANA key whose offset doesn't match — decoding yields `ZoneInfo("Europe/Paris")` and the instant shifts. This priority is the documented, deliberate design: names win so genuine `ZoneInfo` payloads keep DST semantics (and survive tz-database rule updates as zone semantics rather than frozen offsets). The colliding-label case is pathological. A cross-check (compare the zone's offset at the decoded wall time against the wire offset, fall back to fixed offset on mismatch) is possible but interacts badly with tz-database version drift, where the mismatch is legitimate and the named zone is the better answer. Revisit only with a concrete real-world report.
