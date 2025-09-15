# AI Agent - Services Finder in the Area

This project is a **Streamlit-based AI agent** that helps users find nearby services like EV charging stations, coffee shops, and pizza places. It leverages **Azure OpenAI LLM** to interpret user queries and dynamically fetch locations on a map. Different service types are marked with distinct icons and colors.

## Features
- Find **EV Charging Stations** (Tesla / Non-Tesla)
- Find **Coffee Shops** (brown coffee icon)
- Find **Pizza Places** (red pizza icon)
- Multi-skill AI agent using **LLM** to interpret natural language queries
- Interactive **Folium map** with markers and Google Directions links
- Adjustable search radius

![EV AI Agent Screenshot](services%20finder%20output.png)

## How It Works
1. User enters a query like:  
   `"Find Tesla chargers and coffee shops near San Ramon, CA"`.
2. The **LLM interprets** the query to identify:
   - Service type (Charging Station, Coffee Shop, Pizza Place)
   - Location
   - Charger type (if relevant)
3. Fetches the service locations via:
   - **OpenChargeMap API** for EV chargers
   - **Overpass API (OpenStreetMap)** for Coffee/Pizza shops
4. Displays services on a **Folium map** with different icons.

## Getting Started

### Prerequisites
- Python 3.10+
- Streamlit
- Folium
- Requests
- Geopy

### Installation
```bash
git clone <YOUR_REPO_URL>
cd <REPO_FOLDER>
pip install -r requirements.txt
