import json
import os
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

UNIVERSE_ID = "4614743437"
PLACE_ID = "13234175149"
DATA_FILE = Path("data.json")
THRESHOLDS = [50, 75, 100]
ROBLOX_API_KEY = os.getenv("ROBLOX_API_KEY", "").strip()
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "").strip()


def request_json(url, method="GET", payload=None, headers=None):
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    request_headers = {"User-Agent": "GameStats/1.0"}
    if body is not None:
        request_headers["Content-Type"] = "application/json"
    if headers:
        request_headers.update(headers)
    req = urllib.request.Request(url, data=body, headers=request_headers, method=method)
    with urllib.request.urlopen(req, timeout=25) as response:
        return json.loads(response.read().decode("utf-8"))


def get_public_stats():
    url = f"https://games.roblox.com/v1/games?universeIds={UNIVERSE_ID}"
    result = request_json(url)
    games = result.get("data", [])
    if not games:
        raise RuntimeError("Roblox returned no game data for this universe.")
    game = games[0]
    votes = {}
    try:
        votes = request_json(f"https://games.roblox.com/v1/games/{UNIVERSE_ID}/votes")
    except Exception as exc:
        print(f"Vote endpoint unavailable; using game details only: {exc}")
    return {
        "name": game.get("name", "Click For Free"),
        "ccu": int(game.get("playing", 0)),
        "visits": int(game.get("visits", 0)),
        "favorites": game.get("favoritedCount"),
        "likes": votes.get("upVotes", game.get("upVotes")),
        "dislikes": votes.get("downVotes", game.get("downVotes")),
    }


def query_metric(metric, start_time, end_time):
    url = f"https://apis.roblox.com/analytics-query-api/v1/universes/{UNIVERSE_ID}/metrics"
    headers = {"x-api-key": ROBLOX_API_KEY}
    payload = {
        "metric": metric,
        "granularity": "OneDay",
        "startTime": start_time,
        "endTime": end_time,
    }
    result = request_json(url, method="POST", payload=payload, headers=headers)
    if result.get("done") is False and result.get("path"):
        poll_url = "https://apis.roblox.com/analytics-query-api/" + result["path"].lstrip("/")
        for _ in range(12):
            time.sleep(5)
            result = request_json(poll_url, headers=headers)
            if result.get("done") is True:
                break
    if result.get("error"):
        raise RuntimeError(f"{metric}: {result['error']}")
    values = result.get("response", {}).get("values", [])
    if not values:
        return []
    points = values[0].get("dataPoints", [])
    return [{"time": p.get("time"), "value": p.get("value")} for p in points if p.get("time")]


def refresh_analytics(data):
    if not ROBLOX_API_KEY:
        data.setdefault("analytics", {})["enabled"] = False
        print("ROBLOX_API_KEY not configured; private analytics skipped.")
        return
    now = datetime.now(timezone.utc)
    start = (now - timedelta(days=35)).replace(hour=0, minute=0, second=0, microsecond=0)
    end = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    start_time = start.isoformat(timespec="seconds").replace("+00:00", "Z")
    end_time = end.isoformat(timespec="seconds").replace("+00:00", "Z")
    analytics = data.setdefault("analytics", {})
    for metric in ["DailyRevenue", "DailyActiveUsers", "ForwardD1Retention", "ForwardD7Retention", "ForwardD30Retention"]:
        try:
            analytics[metric] = query_metric(metric, start_time, end_time)
            print(f"Updated {metric}: {len(analytics[metric])} points")
        except Exception as exc:
            print(f"Could not update {metric}: {exc}")
    analytics["enabled"] = any(analytics.get(key) for key in [
        "DailyRevenue", "DailyActiveUsers", "ForwardD1Retention",
        "ForwardD7Retention", "ForwardD30Retention"
    ])


def send_discord_alert(threshold, ccu, game_name):
    if not DISCORD_WEBHOOK_URL:
        print("Discord webhook not configured; skipping notification.")
        return
    content = (
        f"🚀 **CCU MILESTONE REACHED!**\n"
        f"**Game:** {game_name}\n"
        f"**Current players:** {ccu}\n"
        f"**Milestone:** {threshold} CCU\n"
        f"https://www.roblox.com/games/{PLACE_ID}"
    )
    request_json(DISCORD_WEBHOOK_URL, method="POST", payload={"content": content})


def main():
    if DATA_FILE.exists():
        data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    else:
        data = {}
    public = get_public_stats()
    now = datetime.now(timezone.utc)
    data["current"] = public
    data["updatedAt"] = now.isoformat(timespec="seconds").replace("+00:00", "Z")

    history = data.setdefault("ccuHistory", [])
    history.append({"time": data["updatedAt"], "ccu": public["ccu"]})
    cutoff = now - timedelta(days=7)
    data["ccuHistory"] = [
        point for point in history
        if point.get("time") and datetime.fromisoformat(point["time"].replace("Z", "+00:00")) >= cutoff
    ][-2500:]

    alerts = data.setdefault("alerts", {"thresholds": THRESHOLDS, "active": []})
    previous = set(alerts.get("active", []))
    current = {target for target in THRESHOLDS if public["ccu"] >= target}
    for target in THRESHOLDS:
        if target in current and target not in previous:
            send_discord_alert(target, public["ccu"], public["name"])
    alerts["thresholds"] = THRESHOLDS
    alerts["active"] = sorted(current)

    # Pull private analytics once per UTC day to keep API usage modest.
    last_analytics_date = data.get("analyticsUpdatedDate")
    today = now.date().isoformat()
    if last_analytics_date != today:
        refresh_analytics(data)
        data["analyticsUpdatedDate"] = today

    DATA_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"{public['name']}: {public['ccu']} concurrent players; saved dashboard data.")


if __name__ == "__main__":
    main()
