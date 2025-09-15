# This Python script implements a multi-skill AI agent for finding EV charging stations, coffee shops, pizza shops, restaurants, and public restrooms.
#It uses Azure OpenAI GPT-4 to interpret natural language queries, Open Charge Map API for EV stations, and Overpass API (OpenStreetMap) for local amenities. 
#Results are displayed on an interactive Folium map with distinct icons and colors for each service type.

# pip install streamlit streamlit-folium geopy requests folium
# HOW TO RUN IN TERMINAL

# streamlit run roadly.py

import streamlit as st
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
import requests
import folium
import json

# ----------------- Azure OpenAI REST Setup -----------------
AZURE_OPENAI_KEY = "xxxxxxxxxxxxxxxxxxxx"
AZURE_OPENAI_ENDPOINT = "https://ai-xxxxxxxxx.openai.azure.com"  # e.g., https://YOUR_RESOURCE.openai.azure.com/
DEPLOYMENT_NAME = "gpt-4.1"  # e.g., gpt-4
API_VERSION = "2025-01-01-preview"

OPEN_CHARGE_MAP_KEY = "xxx-b6bf-xxx-xxx-xxxx"
# ev_ai_agent_rest_fixed.py



# ----------------- Helper Functions -----------------
def ask_azure_openai(prompt):
    url = f"{AZURE_OPENAI_ENDPOINT}/openai/deployments/{DEPLOYMENT_NAME}/chat/completions?api-version={API_VERSION}"
    headers = {"api-key": AZURE_OPENAI_KEY, "Content-Type": "application/json"}
    payload = {"messages": [{"role": "user", "content": prompt}], "temperature": 0.3}
    try:
        response = requests.post(url, headers=headers, json=payload)
        result = response.json()
        if "choices" in result and len(result["choices"]) > 0:
            return result["choices"][0]["message"]["content"]
        else:
            st.warning("No 'choices' in Azure response")
            st.json(result)
            return "{}"
    except Exception as e:
        st.warning(f"Azure API failed: {e}")
        return "{}"

def fetch_ev_stations(lat, lon, is_tesla=True, distance_km=20, max_results=10):
    connection_type = "27,30" if is_tesla else "2,32,25"
    url = "https://api.openchargemap.io/v3/poi/"
    params = {
        "output": "json",
        "latitude": lat,
        "longitude": lon,
        "distance": distance_km,
        "distanceunit": "KM",
        "maxresults": max_results,
        "key": OPEN_CHARGE_MAP_KEY,
        "connectiontypeid": connection_type
    }
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            stations = []
            for item in data:
                info = item.get("AddressInfo", {})
                if info.get("Latitude") and info.get("Longitude"):
                    stations.append({
                        "name": info.get("Title", "Unknown"),
                        "lat": info.get("Latitude"),
                        "lon": info.get("Longitude"),
                        "address": info.get("AddressLine1", "No address"),
                        "type": "charger"
                    })
            return stations
    except Exception as e:
        st.warning(f"Open Charge Map API failed: {e}")
    return []

def fetch_coffee_shops(lat, lon, radius=2000):
    query = f"""
    [out:json];
    node["amenity"="cafe"](around:{radius},{lat},{lon});
    out;
    """
    try:
        resp = requests.post("http://overpass-api.de/api/interpreter", data={"data": query}).json()
        cafes = []
        for e in resp.get("elements", []):
            cafes.append({
                "name": e["tags"].get("name", "Unnamed Cafe"),
                "lat": e["lat"],
                "lon": e["lon"],
                "address": e["tags"].get("addr:street", "No address"),
                "type": "cafe"
            })
        return cafes
    except Exception as e:
        st.warning(f"Overpass API failed (coffee shops): {e}")
        return []

def fetch_pizza_shops(lat, lon, radius=2000):
    query = f"""
    [out:json];
    node["amenity"="restaurant"]["cuisine"="pizza"](around:{radius},{lat},{lon});
    out;
    """
    try:
        resp = requests.post("http://overpass-api.de/api/interpreter", data={"data": query}).json()
        pizza_places = []
        for e in resp.get("elements", []):
            pizza_places.append({
                "name": e["tags"].get("name", "Unnamed Pizza Place"),
                "lat": e["lat"],
                "lon": e["lon"],
                "address": e["tags"].get("addr:street", "No address"),
                "type": "pizza"
            })
        return pizza_places
    except Exception as e:
        st.warning(f"Overpass API failed (pizza shops): {e}")
        return []

def show_map(location, services):
    m = folium.Map(location=[location.latitude, location.longitude], zoom_start=14)
    for s in services:
        popup_html = f"<b>{s['name']}</b><br>{s.get('address','')}<br>"
        popup_html += f'<a href="https://www.google.com/maps/dir/?api=1&destination={s["lat"]},{s["lon"]}" target="_blank">Get Directions</a>'

        if s.get("type") == "cafe":
            icon = folium.Icon(color="brown", icon="coffee", prefix="fa")
        elif s.get("type") == "pizza":
            icon = folium.Icon(color="red", icon="cutlery", prefix="fa")
        elif s.get("type") == "charger":
            icon = folium.Icon(color="green", icon="bolt", prefix="fa")
        else:
            icon = folium.Icon(color="blue", icon="info-sign")
        
        folium.Marker([s["lat"], s["lon"]], popup=popup_html, icon=icon).add_to(m)

    st_folium(m, width=700, height=500)

# ----------------- EV Agent -----------------
class EVAgent:
    def __init__(self):
        self.geolocator = Nominatim(user_agent="ev_ai_agent")

    def interpret_query(self, user_query):
        prompt = f"""
        You are an AI assistant. Interpret this query: "{user_query}"
        Extract:
        - service: Charging Station, Coffee Shop, Pizza Shop, Restaurant, Restroom
        - location: city/state/zipcode
        - charger_type: Tesla / Non-Tesla (if relevant)
        Return JSON strictly like:
        {{
          "service": "...",
          "location": "...",
          "charger_type": "..."
        }}
        """
        response = ask_azure_openai(prompt)
        try:
            return json.loads(response)
        except:
            return {"service": "Charging Station", "location": user_query, "charger_type": "Tesla"}

    def get_location(self, location_input):
        location = self.geolocator.geocode(location_input)
        if not location:
            class LocFallback:
                latitude = 34.285
                longitude = -118.872
                address = location_input
            location = LocFallback()
        return location

    def run(self, user_query, distance_km=20):
        llm_result = self.interpret_query(user_query)
        st.session_state['llm_result'] = llm_result

        location_input = llm_result.get("location") or user_query
        location = self.get_location(location_input)
        st.session_state['location'] = location

    # Fetch all service types
        services = []

    # EV Charging
        is_tesla = (llm_result.get("charger_type", "Tesla").lower() == "tesla")
        services += fetch_ev_stations(location.latitude, location.longitude, is_tesla, distance_km)

    # Coffee shops
        services += fetch_coffee_shops(location.latitude, location.longitude)

    # Pizza shops
        services += fetch_pizza_shops(location.latitude, location.longitude)

    # Optional: restaurants/restrooms (mock)
        services += [{"name": "Restaurant A", "lat": location.latitude + 0.002, "lon": location.longitude + 0.002,
                  "address": "Mock Address", "type": "restaurant"}]
        services += [{"name": "Public Restroom", "lat": location.latitude + 0.001, "lon": location.longitude + 0.001,
                  "address": "Mock Address", "type": "restroom"}]

        st.session_state['services'] = services
        return location, services

# ----------------- Streamlit UI -----------------
st.title("☕🍕🔋 EV AI Agent - Multi-skill")

user_query = st.text_input("Ask me (e.g., 'Find Tesla chargers and coffee shops near San Ramon, CA')")

distance_km = st.slider("Search radius (km)", 5, 50, 20, key="radius_slider")

if st.button("Run Agent", key="run_agent_button") and user_query:
    agent = EVAgent()
    agent.run(user_query, distance_km=distance_km)

if 'services' in st.session_state and st.session_state['services']:
    show_map(st.session_state['location'], st.session_state['services'])
