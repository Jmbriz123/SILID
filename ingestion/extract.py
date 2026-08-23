import logging
from datetime import datetime, timezone
import requests
from ingestion.config import CITIES
#configuration of the logging system
logging.basicConfig(
    level=logging.INFO,
     format="%(asctime)s - %(levelname)s - %(message)s"
     )
#create logger for this module
logger = logging.getLogger(__name__)
BASE_URL = "https://api.open-meteo.com/v1/forecast" #target endpoint URL for Open-Meteo-API

def fetch_city_weather(city_key: str, city_meta: dict) -> dict:
    """ Fetch hourly forecast and observed variables for a single city"""
    
    #prepare variable containing API/query parameters
    api_parameters = {
        "latitude": city_meta["latitude"],
        "longitude": city_meta["longitude"],
        "hourly": [
            "temperature_2m",  #standard ambient air temperature measured 2 meters above the ground (the meteorological standard)
            "relative_humidity_2m", #Measures atmospheric moisture relative to temperature. It is critical for forecasting fog, dew, agricultural drying conditions, or HVAC load calculations.
            "apparent_temperature", # The "feels-like" temperature. It factors in humidity and wind to reflect how heat is actually experienced by humans, which is essential for consumer-facing dashboards or heat-index monitoring
            "precipitation_probability", #The likelihood (0–100%) that measurable rain will fall during that hour. Essential for predictive alerts and likelihood scoring
            "precipitation", #The total liquid water equivalent of all moisture (rain, snow, sleet, hail) falling during the hour.
            "rain", #Specifically measures liquid rainfall. Isolating rain from total precipitation prevents misinterpreting frozen or mixed precipitation types when modeling tropical or varied climates.
            "wind_speed_10m" #Standardized wind speed measured 10 meters above the surface. This is critical for maritime tracking, storm warnings, drone operations, or wind energy generation models.
        ],
        "timezone": city_meta["timezone"]
    }
    
    #actual fetching of data using API
    try:
        response = requests.get(BASE_URL, params=api_parameters, timeout=10)
        response.raise_for_status() #raise exception if the server returned an HTTP error status
        
        return {
            "city_key": city_key,
            "city_name":city_meta["name"],
            "ingested_at": datetime.now(timezone.utc).isoformat(),
            "raw_payload": response.json()
        }
    except requests.raise_for_status as e:
        logger.error(f"API extraction failed for {city_key}: {e} ")

def run_extraction_batch() -> list[dict]:
    """
    Iterate over configured cities and extract API payloads
    """
    records = []
    for city_key, city_meta in CITIES.items():
        logger.info("Extracting Open-Meteo API ppayloads")
        records.append(fetch_city_weather(city_key, city_meta))

    return records

if __name__ == "__main__":
    data = run_extraction_batch()
    logger.info(f"Extracted {len(data)} city payloads successfully")
