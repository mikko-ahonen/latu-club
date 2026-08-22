#!/usr/bin/env bash
#
# Compare the times published on an Eventilla event page against a committed
# baseline, so we notice when Helsingin Latu ja Polku changes a schedule and
# latu.club goes stale.
#
# Usage: scripts/check-eventilla-times.sh [EVENT_CODE ...]
#        (no arguments = every baseline in tests/eventilla-times/)
#
# Exit codes:
#   0  every checked event matches its baseline
#   1  at least one event's times differ from the baseline
#   2  a page could not be fetched or yielded no times at all
#
# Refresh a baseline after an intentional change:
#   scripts/check-eventilla-times.sh --update AJ5PA

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BASELINE_DIR="$REPO_ROOT/tests/eventilla-times"
UPDATE=0

if [[ "${1:-}" == "--update" ]]; then
  UPDATE=1
  shift
fi

# Pull the human-readable "klo ..." times out of an event page. Script and
# style bodies are dropped first: Eventilla ships ~500KB of JS, and stray
# digits in there would otherwise show up as phantom times.
extract_times() {
  sed -e 's/<script[^>]*>/\n<script>/gI' -e 's/<style[^>]*>/\n<style>/gI' \
  | awk 'BEGIN{IGNORECASE=1}
         /<script>/{s=1} /<\/script>/{s=0;next}
         /<style>/{t=1} /<\/style>/{t=0;next}
         !s && !t' \
  | sed -e 's/<[^>]*>/ /g' \
  | sed -e 's/&nbsp;/ /g' -e 's/&amp;/\&/g' -e 's/&ndash;/-/g' -e 's/–/-/g' \
  | tr -s ' \t\n' ' ' \
  | grep -oE 'klo [0-9]{1,2}([.:][0-9]{2})?( ?- ?[0-9]{1,2}([.:][0-9]{2})?)?' \
  | sed -e 's/ *- */-/' -e 's/:/./' \
  | sort -u
}

fetch() {
  curl -sS -L --max-time 60 --retry 3 --retry-delay 5 --retry-all-errors \
       -A 'latu.club schedule monitor (+https://latu.club)' \
       -w '%{http_code}' -o "$2" "$1"
}

if [[ $# -gt 0 ]]; then
  EVENTS=("$@")
else
  EVENTS=()
  for f in "$BASELINE_DIR"/*.expected; do
    [[ -e "$f" ]] || continue
    EVENTS+=("$(basename "$f" .expected)")
  done
fi

if [[ ${#EVENTS[@]} -eq 0 ]]; then
  echo "No events to check (no baselines in $BASELINE_DIR)." >&2
  exit 2
fi

STATUS=0
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

for event in "${EVENTS[@]}"; do
  url="https://ssl.eventilla.com/event/$event"
  baseline="$BASELINE_DIR/$event.expected"

  code="$(fetch "$url" "$TMP/$event.html")"
  if [[ "$code" != "200" ]]; then
    echo "ERROR $event: HTTP $code from $url" >&2
    STATUS=2
    continue
  fi

  extract_times < "$TMP/$event.html" > "$TMP/$event.times"

  # No times at all means the page stopped rendering them server-side, not
  # that the schedule was emptied. Treat it as a broken check, not a change.
  if [[ ! -s "$TMP/$event.times" ]]; then
    echo "ERROR $event: no times found in $url (page structure changed?)" >&2
    STATUS=2
    continue
  fi

  if [[ $UPDATE -eq 1 ]]; then
    cp "$TMP/$event.times" "$baseline"
    echo "UPDATED $event ($(wc -l < "$baseline" | tr -d ' ') times) -> $baseline"
    continue
  fi

  if [[ ! -f "$baseline" ]]; then
    echo "ERROR $event: no baseline at $baseline (run with --update)" >&2
    STATUS=2
    continue
  fi

  if diff -q "$baseline" "$TMP/$event.times" >/dev/null; then
    echo "OK $event: times unchanged"
  else
    echo "CHANGED $event: times differ from baseline ($url)"
    diff -u --label "baseline/$event" --label "live/$event" \
         "$baseline" "$TMP/$event.times"
    [[ $STATUS -eq 2 ]] || STATUS=1
  fi
done

exit $STATUS
