#!/usr/bin/env python3
"""Collect current conditions at Rastila beach for latu.club.

Writes three files:

  archive/conditions.csv        append-only record of every reading ever taken,
                                never trimmed - the permanent history
  data/conditions.json          latest reading of each source (Hugo .Site.Data)
  data/conditions_history.json  current season only, for the front-page chart,
                                regenerated from the archive on every run

A season runs from 1 August to 31 July, so "fall 2026 - spring 2027" is the
2026-2027 season. Only the season file feeds the page; the archive keeps
everything so older seasons stay available for comparison.

Water temperature is recorded from both sources on every run:

  sensor  UIRAS (Forum Virium Helsinki), a real sensor on the Rastila pier
          at -0.2 m depth
  model   Open-Meteo Marine, a model grid cell out in Vartiokylanlahti; it
          read ~1.2 C below the sensor on a summer afternoon

`preferred` names the one the site should show. Air comes from Ilmatieteen
laitos, Helsinki Kumpula (fmisid 101004) - the nearest station reporting a
full set of values, since Vuosaari is a manual cloud-observation station and
returns NaN for temperature.

Only stdlib, so the job needs no pip install.

Usage:
  python3 scripts/fetch_conditions.py [--out DIR] [--archive PATH]
  python3 scripts/fetch_conditions.py --backfill    # seed archive, then append

Exits non-zero only if no source at all could be read.
"""

import argparse
import csv
import json
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from xml.etree import ElementTree

LAT, LON = 60.207977, 25.114849
STATION = "Rastilan uimaranta"
FMISID = 101004  # Helsinki Kumpula

UIRAS = "https://iot.fvh.fi/opendata/uiras/uiras_latest.geojson"
MARINE = (
    f"https://marine-api.open-meteo.com/v1/marine?latitude={LAT}&longitude={LON}"
    "&current=sea_surface_temperature&timezone=Europe%2FHelsinki"
)
FMI = (
    "https://opendata.fmi.fi/wfs?service=WFS&version=2.0.0&request=getFeature"
    f"&storedquery_id=fmi::observations::weather::simple&fmisid={FMISID}"
    "&parameters=t2m,ws_10min,wd_10min,rh"
)
# Backfill sources. Everything is requested in UTC so the three series line up
# on a shared hourly key without any timezone arithmetic.
MARINE_PAST = (
    f"https://marine-api.open-meteo.com/v1/marine?latitude={LAT}&longitude={LON}"
    "&hourly=sea_surface_temperature&past_days={days}&forecast_days=1&timezone=UTC"
)
AIR_PAST = (
    f"https://api.open-meteo.com/v1/forecast?latitude={LAT}&longitude={LON}"
    "&hourly=temperature_2m&past_days={days}&forecast_days=1&timezone=UTC"
)

UA = "latu.club conditions collector (+https://latu.club)"
NS = {"BsWfs": "http://xml.fmi.fi/schema/wfs/2.0"}


def get(url, as_json=False):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as res:
        raw = res.read()
    return json.loads(raw) if as_json else raw.decode("utf-8", "replace")


def uiras_feature():
    geo = get(UIRAS, as_json=True)
    for f in geo.get("features", []):
        if (f.get("properties") or {}).get("name") == STATION:
            return f
    raise ValueError(f'no UIRAS sensor named "{STATION}"')


def water_sensor():
    props = uiras_feature()["properties"]
    m = props.get("measurement") or {}
    temp = m.get("temp_water")
    if not isinstance(temp, (int, float)):
        raise ValueError("sensor reported no temp_water")
    return {
        "temperature_c": temp,
        "measured_at": m.get("time"),
        "station": STATION,
        "depth_m": props.get("installation depth"),
        "modelled": False,
        "source": "UIRAS / Forum Virium Helsinki",
        "source_url": "https://uiras.fvh.io/",
    }


def water_model():
    j = get(MARINE, as_json=True)
    temp = (j.get("current") or {}).get("sea_surface_temperature")
    if not isinstance(temp, (int, float)):
        raise ValueError("Open-Meteo returned no sea_surface_temperature")
    return {
        "temperature_c": temp,
        "measured_at": j["current"].get("time"),
        "station": "Vartiokylanlahti (mallinnettu)",
        "depth_m": None,
        "modelled": True,
        "source": "Open-Meteo Marine",
        "source_url": "https://open-meteo.com/en/docs/marine-weather-api",
    }


def air():
    """Parse FMI's flat 'simple' feed, keeping the newest real value per name.

    Missing observations come through as NaN, and the feed is oldest-first.
    """
    root = ElementTree.fromstring(get(FMI))
    newest = {}
    for el in root.iterfind(".//BsWfs:BsWfsElement", NS):
        time = el.findtext("BsWfs:Time", namespaces=NS)
        name = el.findtext("BsWfs:ParameterName", namespaces=NS)
        raw = el.findtext("BsWfs:ParameterValue", namespaces=NS)
        try:
            value = float(raw)
        except (TypeError, ValueError):
            continue
        if value != value:  # NaN
            continue
        if name not in newest or time > newest[name]["time"]:
            newest[name] = {"time": time, "value": value}
    if not newest:
        raise ValueError("FMI returned no usable observations")

    def at(k):
        return newest[k]["value"] if k in newest else None

    return {
        "temperature_c": at("t2m"),
        "wind_speed_ms": at("ws_10min"),
        "wind_direction_deg": at("wd_10min"),
        "humidity_pct": at("rh"),
        "measured_at": newest.get("t2m", next(iter(newest.values())))["time"],
        "station": "Helsinki Kumpula",
        "source": "Ilmatieteen laitos, avoin data",
        "source_url": "https://www.ilmatieteenlaitos.fi/avoin-data",
    }


def hour_key(iso):
    """Normalise any of the three time formats to a UTC 'YYYY-MM-DDTHH' key."""
    text = iso.replace("Z", "+00:00")
    dt = datetime.fromisoformat(text)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H")


def hourly_map(url, field, days):
    j = get(url.format(days=days), as_json=True)
    h = j.get("hourly") or {}
    out = {}
    for t, v in zip(h.get("time", []), h.get(field, [])):
        if isinstance(v, (int, float)):
            out[hour_key(t)] = v
    return out


def backfill(days):
    """Seed history from each source's own archive.

    The sensor's 3-hourly series sets the timestamps; the two Open-Meteo
    series are matched to it by UTC hour. Without this the charts would start
    empty and take weeks of hourly runs to become readable.
    """
    props = uiras_feature()["properties"]
    # The summary feed carries only the latest reading; the archive lives in
    # the per-device file it links to.
    href = ((props.get("links") or {}).get("geojson") or {}).get("href")
    if not href:
        raise ValueError("UIRAS feature carried no device-file link")
    device = get(href, as_json=True)
    feature = (device.get("features") or [device])[0]
    data = (feature.get("properties") or {}).get("data") or {}
    # h3 is the 3-hourly series (~30 days); raw only reaches back 7.
    series = data.get("h3") or data.get("raw") or []
    if not series:
        raise ValueError("UIRAS device file carried no h3 or raw series")

    air_by_hour = hourly_map(AIR_PAST, "temperature_2m", days)
    sea_by_hour = hourly_map(MARINE_PAST, "sea_surface_temperature", days)

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    points = []
    for row in series:
        t = row.get("time")
        temp = row.get("temp_water")
        if not t or not isinstance(temp, (int, float)):
            continue
        dt = datetime.fromisoformat(t.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        if dt < cutoff:
            continue
        key = hour_key(t)
        points.append({
            "t": dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
            "water_sensor": temp,
            "water_model": sea_by_hour.get(key),
            "air": air_by_hour.get(key),
        })
    points.sort(key=lambda p: p["t"])
    return points


FIELDS = ["t", "water_sensor", "water_model", "air"]


def season_start(now):
    """First day of the season `now` falls in.

    Seasons run 1 August - 31 July, so an autumn-to-spring swimming season
    lands in one season rather than being split across two calendar years.
    """
    year = now.year if now.month >= 8 else now.year - 1
    return datetime(year, 8, 1, tzinfo=timezone.utc)


def season_label(start):
    return f"{start.year}-{start.year + 1}"


def read_archive(path):
    """Every row ever recorded, keyed by timestamp so re-runs cannot duplicate."""
    rows = {}
    try:
        with path.open(encoding="utf-8", newline="") as fh:
            for row in csv.DictReader(fh):
                t = (row.get("t") or "").strip()
                if not t:
                    continue
                point = {"t": t}
                for key in FIELDS[1:]:
                    raw = (row.get(key) or "").strip()
                    try:
                        point[key] = float(raw)
                    except ValueError:
                        point[key] = None
                rows[t] = point
    except OSError:
        pass  # first run
    return rows


def write_archive(path, rows):
    """Rewrite the archive sorted by time.

    Sorted output keeps the file deterministic, so a re-run that adds nothing
    produces no diff and the workflow skips the commit.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS)
        writer.writeheader()
        for t in sorted(rows):
            writer.writerow({k: ("" if rows[t].get(k) is None else rows[t].get(k))
                             for k in FIELDS})


def thin(points, limit):
    """Even sample down to `limit` points, always keeping first and last.

    A full season at hourly cadence is ~6500 points; sending all of them to the
    browser would bloat the page for a chart only a few hundred pixels wide.
    The archive keeps every reading regardless.
    """
    if limit <= 0 or len(points) <= limit:
        return points
    step = len(points) / limit
    picked = [points[int(i * step)] for i in range(limit)]
    if picked[-1] is not points[-1]:
        picked[-1] = points[-1]
    return picked


def load(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data", type=Path,
                    help="directory holding conditions.json and conditions_history.json")
    ap.add_argument("--archive", default=Path("archive/conditions.csv"), type=Path,
                    help="append-only record of every reading; never trimmed")
    ap.add_argument("--backfill", action="store_true",
                    help="seed the archive from each source's own archive first")
    ap.add_argument("--backfill-days", default=14, type=int,
                    help="how far back --backfill reaches")
    ap.add_argument("--chart-points", default=1200, type=int,
                    help="cap on points written to the chart file (0 disables thinning)")
    args = ap.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    current_path = args.out / "conditions.json"
    history_path = args.out / "conditions_history.json"

    archive = read_archive(args.archive)
    print(f"Archive holds {len(archive)} readings.")

    if args.backfill:
        try:
            seeded = backfill(args.backfill_days)
            added = 0
            for point in seeded:
                # Existing rows win, so a backfill never overwrites a live reading.
                if point["t"] not in archive:
                    archive[point["t"]] = point
                    added += 1
            print(f"Backfilled {added} new points ({len(seeded)} fetched).")
        except (urllib.error.URLError, OSError, ValueError) as e:
            print(f"WARN: backfill failed: {e}", file=sys.stderr)

    results = {}
    for label, fn in (("sensor", water_sensor), ("model", water_model), ("air", air)):
        try:
            results[label] = fn()
        except (urllib.error.URLError, OSError, ValueError, ElementTree.ParseError) as e:
            print(f"WARN: {label}: {e}", file=sys.stderr)
            results[label] = None

    if not any(results.values()):
        print("ERROR: no source could be read; leaving the existing files alone.",
              file=sys.stderr)
        return 1

    previous = load(current_path, {})

    # Retain the last known value for a source that failed, so the file never
    # carries a hole; `preferred` still only points at a source that reported.
    sensor = results["sensor"] or (previous.get("water") or {}).get("sensor")
    model = results["model"] or (previous.get("water") or {}).get("model")
    preferred = "sensor" if results["sensor"] else (
        "model" if results["model"] else ("sensor" if sensor else "model"))

    difference = None
    if results["sensor"] and results["model"]:
        # A widening gap hints the sensor has drifted, iced over, or come loose.
        difference = round(results["sensor"]["temperature_c"]
                           - results["model"]["temperature_c"], 2)

    now = datetime.now(timezone.utc)
    start = season_start(now)
    current = {
        "updated_at": now.isoformat().replace("+00:00", "Z"),
        "season": season_label(start),
        "water": {
            "preferred": preferred,
            "sensor": sensor,
            "model": model,
            "difference_c": difference,
        },
        "air": results["air"] or previous.get("air"),
    }

    # Only genuinely fresh values enter the record; retained ones would draw a
    # flat line that looks like real data.
    stamp = current["updated_at"]
    archive[stamp] = {
        "t": stamp,
        "water_sensor": results["sensor"]["temperature_c"] if results["sensor"] else None,
        "water_model": results["model"]["temperature_c"] if results["model"] else None,
        "air": results["air"]["temperature_c"] if results["air"] else None,
    }
    write_archive(args.archive, archive)

    # The page shows this season only; the archive above keeps every season.
    cutoff = start.isoformat().replace("+00:00", "Z")
    season = sorted((row for t, row in archive.items() if t >= cutoff),
                    key=lambda row: row["t"])
    season = thin(season, args.chart_points)

    current_path.write_text(json.dumps(current, indent=2, ensure_ascii=False) + "\n",
                            encoding="utf-8")
    history_path.write_text(json.dumps(season, ensure_ascii=False) + "\n", encoding="utf-8")

    shown = current["water"][preferred] or {}
    print(f"Wrote {args.archive} ({len(archive)} readings, all seasons)")
    print(f"Wrote {current_path} and {history_path} "
          f"(season {current['season']}, {len(season)} points)")
    print(f"  water sensor: {(sensor or {}).get('temperature_c', '?')} C")
    print(f"  water model:  {(model or {}).get('temperature_c', '?')} C")
    print(f"  preferred:    {preferred} -> {shown.get('temperature_c', '?')} C, diff {difference}")
    a = current["air"] or {}
    print(f"  air:          {a.get('temperature_c', '?')} C, {a.get('wind_speed_ms', '?')} m/s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
