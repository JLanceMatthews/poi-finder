import requests
import csv
import time
from math import radians, cos, sin, asin, sqrt

# === CONFIG ===
MAPBOX_TOKEN = "pk.eyJ1IjoiamxhbmNlLW1yZWlzIiwiYSI6ImNtZXZxanU0ajAyM3AybG9laXlxM28ycG4ifQ.50B_jHsWFPg-kwP7UzU2hg"
GOOGLE_API_KEY = "AIzaSyChTvFt4qBSSQzQtlmQo6VTS1S-1_XMfj8"
ADDRESS = "4900 W University Dr, Prosper, TX"
RADIUS_MILES = [1, 3, 5]

# === HELPERS ===
def miles_to_meters(miles):
    return int(miles * 1609.34)

def haversine(lat1, lon1, lat2, lon2):
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    return 3956 * c  # miles

# === STEP 1: GEOCODE ===
geo_url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{ADDRESS}.json?access_token={MAPBOX_TOKEN}"
resp = requests.get(geo_url)
data = resp.json()
center = data['features'][0]['center']
subject_lon, subject_lat = center[0], center[1]

# === STEP 2: QUERY GOOGLE PLACES ===
all_pois = []
for radius in RADIUS_MILES:
    meters = miles_to_meters(radius)
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {
        "key": GOOGLE_API_KEY,
        "location": f"{subject_lat},{subject_lon}",
        "radius": meters,
        "type": "establishment"
    }
    print(f"Querying {radius}-mile radius...")
    while True:
        res = requests.get(url, params=params)
        results = res.json().get("results", [])
        for place in results:
            poi = {
                "name": place.get("name"),
                "category": ', '.join(place.get("types", [])),
                "lat": place["geometry"]["location"]["lat"],
                "lon": place["geometry"]["location"]["lng"],
                "address": place.get("vicinity"),
                "radius_miles": radius,
                "distance": round(haversine(subject_lat, subject_lon, place["geometry"]["location"]["lat"], place["geometry"]["location"]["lng"]), 2)
            }
            all_pois.append(poi)

        if "next_page_token" in res.json():
            params["pagetoken"] = res.json()["next_page_token"]
            time.sleep(2)
        else:
            break

# === STEP 3: EXPORT TO CSV ===
with open("pois_by_radius.csv", "w", newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=["name", "category", "address", "lat", "lon", "radius_miles", "distance"])
    writer.writeheader()
    for poi in all_pois:
        writer.writerow(poi)

print("✅ POIs exported to pois_by_radius.csv")
