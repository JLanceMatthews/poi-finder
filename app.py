import os, time, requests
import pandas as pd
import streamlit as st
from math import radians, sin, cos, asin, sqrt
import os
import time
import requests
import pandas as pd
import streamlit as st
from math import radians, sin, cos, asin, sqrt


# --- secrets / env ---
MAPBOX_TOKEN   = st.secrets.get("MAPBOX_TOKEN", os.getenv("MAPBOX_TOKEN", ""))
GOOGLE_API_KEY = st.secrets.get("GOOGLE_API_KEY", os.getenv("GOOGLE_API_KEY", ""))

st.title("POI Finder")
if not MAPBOX_TOKEN or not GOOGLE_API_KEY:
    st.info("Add MAPBOX_TOKEN and GOOGLE_API_KEY in Settings → Secrets after deploy.")

def miles_to_meters(m): return int(m*1609.34)
def haversine(lat1, lon1, lat2, lon2):
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon, dlat = lon2-lon1, lat2-lat1
    a = sin(dlat/2)**2 + cos(lat1)*cos(lat2)*sin(dlon/2)**2
    return 3956*2*asin(sqrt(a))  # miles
# === API Keys ===
MAPBOX_TOKEN   = st.secrets.get("MAPBOX_TOKEN", os.getenv("MAPBOX_TOKEN", ""))
GOOGLE_API_KEY = st.secrets.get("GOOGLE_API_KEY", os.getenv("GOOGLE_API_KEY", ""))

st.title("POI Finder")

# Show a friendly message if keys are missing and stop the script
if not MAPBOX_TOKEN or not GOOGLE_API_KEY:
    st.warning("⚠️ Add MAPBOX_TOKEN and GOOGLE_API_KEY in ☰ → Settings → Secrets, then click Rerun.")
    st.stop()


def geocode(address):
    url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{address}.json"
    r = requests.get(url, params={"access_token": MAPBOX_TOKEN})
    r.raise_for_status()
    lon, lat = r.json()["features"][0]["center"]
    return lat, lon

def places(lat, lon, radii):
    rows = []
    for rmi in radii:
        params = {"key": GOOGLE_API_KEY, "location": f"{lat},{lon}", "radius": miles_to_meters(rmi), "type": "establishment"}
        url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
        while True:
            res = requests.get(url, params=params).json()
            for p in res.get("results", []):
                plat = p["geometry"]["location"]["lat"]
                plon = p["geometry"]["location"]["lng"]
                rows.append({
                    "name": p.get("name"),
                    "category": ", ".join(p.get("types", [])),
                    "address": p.get("vicinity"),
                    "lat": plat, "lon": plon,
                    "radius_miles": rmi,
                    "distance_miles": round(haversine(lat, lon, plat, plon), 2),
                    "google_place_id": p.get("place_id"),
                })
            tok = res.get("next_page_token")
            if not tok: break
            params = {"key": GOOGLE_API_KEY, "pagetoken": tok}
            time.sleep(2)
    return pd.DataFrame(rows)

address = st.text_input("Address", "4900 W University Dr, Prosper, TX")
radii = st.multiselect("Radii (miles)", [1,3,5], default=[1,3,5])

if st.button("Run POI Search"):
    try:
        lat, lon = geocode(address)
        st.map(pd.DataFrame([{"lat": lat, "lon": lon}]))
        df = places(lat, lon, radii)
        st.success(f"Found {len(df)} POIs")
        st.dataframe(df, use_container_width=True)
        st.download_button("Download CSV", df.to_csv(index=False).encode("utf-8"),
                           "pois_by_radius.csv", "text/csv")
    except Exception as e:
        st.error(f"Error: {e}")
import os, streamlit as st
