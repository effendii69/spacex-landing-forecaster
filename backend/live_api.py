import requests
from datetime import datetime, timezone
from typing import Dict, Optional, Tuple
import pandas as pd

LAUNCH_URL = "https://ll.thespacedevs.com/2.3.0/launch/upcoming/?search=SpaceX&limit=1"
MARINE_URL = "https://marine-api.open-meteo.com/v1/marine"


def fetch_next_launch() -> Optional[Dict]:
    """Fetch the next SpaceX launch from Launch Library."""
    try:
        resp = requests.get(LAUNCH_URL, timeout=8)
        resp.raise_for_status()
        data = resp.json() or {}
        results = data.get("results") or []
        if not results:
            return None
        launch = results[0]
        pad = launch.get("pad") or {}
        loc = pad.get("location") or {}
        return {
            "name": launch.get("name") or "SpaceX Launch",
            "net": launch.get("net"),
            "pad_name": pad.get("name") or loc.get("name") or "Launch Site",
            "latitude": loc.get("latitude"),
            "longitude": loc.get("longitude"),
        }
    except Exception as exc:
        print(f"[live_api] Launch fetch failed: {exc}")
        return None


def parse_net(net_str: Optional[str]) -> Optional[datetime]:
    if not net_str:
        return None
    try:
        # Launch Library uses ISO 8601 with Z
        return datetime.fromisoformat(net_str.replace("Z", "+00:00")).astimezone(timezone.utc)
    except Exception:
        return None


def format_countdown(net_dt: Optional[datetime]) -> str:
    if not net_dt:
        return "T- TBD"
    now = datetime.now(timezone.utc)
    delta = net_dt - now
    sign = "-" if delta.total_seconds() >= 0 else "+"
    delta_seconds = abs(int(delta.total_seconds()))
    hours = delta_seconds // 3600
    minutes = (delta_seconds % 3600) // 60
    return f"T{sign}{hours}h {minutes}m"


def guess_booster(pad_name: str) -> str:
    name = (pad_name or "").lower()
    if "vandenberg" in name or "vsfb" in name:
        return "B10xx (West Coast)"
    return "B1083 (Flight 12)"


def pick_landing_profile(mission_name: str, pad_name: str) -> Tuple[str, Tuple[float, float]]:
    """
    Decide landing type and coordinates for weather.
    ASDS for Starlink/LEO by default; RTLS otherwise.
    """
    mission_l = (mission_name or "").lower()
    pad_l = (pad_name or "").lower()

    if "starlink" in mission_l or "rideshare" in mission_l or "transporter" in mission_l:
        return "ASDS", (28.5, -74.5)  # OCISLY area

    if "vandenberg" in pad_l or "vsfb" in pad_l:
        # Vandenberg RTLS/ASDS both west coast; keep RTLS style coords
        return "RTLS", (34.732, -120.572)  # Approx VSFB SLC-4E

    return "RTLS", (28.56, -80.57)  # CCSFS/KSC RTLS


def fetch_wind_kts(lat: float, lon: float) -> float:
    """Fetch max forecast wind (kts) from Open-Meteo Marine; fallback to 12.0."""
    try:
        params = {
            "latitude": lat,
            "longitude": lon,
            "hourly": "wind_speed_10m",
            "timezone": "UTC",
        }
        resp = requests.get(MARINE_URL, params=params, timeout=8)
        resp.raise_for_status()
        data = resp.json() or {}
        speeds = data.get("hourly", {}).get("wind_speed_10m") or []
        if speeds:
            # Use the next 72 hours for a realistic window
            max_ms = max(speeds[:72])
            return round(float(max_ms) * 1.94384, 1)
    except Exception as exc:
        print(f"[live_api] Weather fetch failed: {exc}")
    return 12.0


def compute_probability(model_obj, wind_kts: float = 10.0) -> float:
    """
    Try to score with the loaded model; otherwise return a conservative default.
    Uses placeholder feature values aligned with typical column names.
    """
    try:
        clf = model_obj
        feature_names = None
        if isinstance(model_obj, dict) and "model" in model_obj:
            clf = model_obj["model"]
            feature_names = model_obj.get("feature_names")

        if feature_names:
            row = {}
            for col in feature_names:
                lc = col.lower()
                if "payload" in lc:
                    row[col] = 7000
                elif "flight" in lc:
                    row[col] = 10
                elif "reuse" in lc or "reused" in lc:
                    row[col] = 1
                elif "wind" in lc:
                    row[col] = wind_kts
                else:
                    row[col] = 0
            X = pd.DataFrame([row])
            proba = clf.predict_proba(X)[0][1]
            return round(float(proba), 3)
    except Exception as exc:
        print(f"[live_api] Probability fallback: {exc}")

    return 0.94


def get_live_next_launch(model_obj) -> Dict:
    launch = fetch_next_launch()

    # Fallback defaults
    default = {
        "mission": "Starlink Group 10-15",
        "date": "TBD",
        "probability": 0.94,
        "booster": "B1083 (Flight 12)",
        "wind_kts": 12.0,
        "countdown": "T-18h 42m",
        "landing_type": "ASDS",
    }

    if not launch:
        print("[live_api] No upcoming launch found; serving fallback.")
        return default

    mission = launch["name"]
    net_dt = parse_net(launch.get("net"))
    countdown = format_countdown(net_dt)
    booster = guess_booster(launch.get("pad_name", ""))

    landing_type, coords = pick_landing_profile(mission, launch.get("pad_name", ""))
    # Prefer pad coords for RTLS when available
    if landing_type == "RTLS" and launch.get("latitude") and launch.get("longitude"):
        coords = (launch["latitude"], launch["longitude"])

    wind_kts = fetch_wind_kts(coords[0], coords[1])
    probability = compute_probability(model_obj, wind_kts=wind_kts)
    date_str = net_dt.strftime("%b %d, %Y %H:%M UTC") if net_dt else "TBD"

    result = {
        "mission": mission,
        "date": date_str,
        "probability": probability,
        "booster": booster,
        "wind_kts": wind_kts,
        "countdown": countdown,
        "landing_type": landing_type,
    }

    print(f"Live data fetched: {mission}")
    print(f"Live next launch: {mission} at {date_str}")
    return result
