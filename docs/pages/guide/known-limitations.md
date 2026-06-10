# Known Limitations

This page documents edge cases that kajson knowingly does not handle perfectly, and why we don't plan to fix them. Each one was weighed deliberately: the failure modes are loud (no silent data corruption), the triggering inputs are ones no real producer emits, and a fix would add complexity or raise design questions disproportionate to the benefit. They are recorded here so they can be revisited deliberately if circumstances change, instead of being rediscovered and churned on.

## Non-finite `utcoffset` values (NaN / Infinity) are rejected late

A datetime/timezone payload with `"utcoffset": NaN` or `Infinity` passes the decoder's numeric type check and only fails when constructing the `datetime.timedelta`. The failure is loud — it surfaces as a `KajsonDecoderError` (e.g. "function 'json_decode_datetime' failed: cannot convert float NaN...") — but the error message points at the timedelta conversion rather than naming the invalid wire value directly.

**Why we don't plan to fix it:** standard JSON forbids `NaN` and `Infinity` literals; only Python's permissive `json` parser can even produce these values. Rejecting them earlier would only sharpen the error message for a payload that no conforming JSON producer can emit. Revisit only if kajson ever grows a strict-JSON mode or such payloads show up in the wild.

## Keyless `ZoneInfo` instances (`ZoneInfo.from_file`) leak file paths into the wire format

A `ZoneInfo` built with `ZoneInfo.from_file(...)` has no IANA key, so `str()` of it falls back to its repr — which embeds the local file path. When such a tzinfo is attached to a datetime, the encoded payload discloses a host filesystem path and carries a grotesque tzinfo name. The instant is still preserved: decoding succeeds through the fixed-offset fallback. Relatedly, encoding a bare keyless `ZoneInfo` object (not attached to a datetime) writes `{"zone": null}`, which can never decode.

**Why we don't plan to fix it:** this is rare, advanced usage, and any fix raises design questions with no obviously right answer — should encoding raise instead? Should the payload store only the offset and silently drop the zone identity? Revisit if anyone actually uses `ZoneInfo.from_file` with kajson in practice.

## Rough error messages on some malformed-payload paths

Two malformed payloads produce correctly-wrapped but poorly-worded errors: a bare timezone payload missing its `"utcoffset"` field surfaces the raw `KeyError` text, and a time string missing its `.%f` fractional part surfaces a `list index out of range` message. In both cases the exception is a `KajsonDecoderError` — the failure is loud and no raw exception escapes — only the message quality is poor.

**Why we don't plan to fix it:** these payloads are never produced by kajson itself or any real producer; they only arise from hand-crafted or corrupted input. Dedicated validation guards just to improve the wording aren't worth the added code.

## A `time` with a named zone requires a timezone database to decode

A `datetime.time` carrying a named zone (`ZoneInfo`) has no defined UTC offset without a date, so its payload carries only the zone name — there is no offset to fall back on. Decoding it therefore requires a timezone database. This is a structural property of bare times, not a bug; in practice it always works because kajson depends on `tzdata`. See the [encoder reference](../api/encoder.md) for details on the wire format.
