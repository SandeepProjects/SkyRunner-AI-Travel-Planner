import os
import requests
from dotenv import load_dotenv

load_dotenv()

def search_flights(query: str) -> str:
    api_key = (os.getenv("AVIATIONSTACK_API_KEY") or "").strip(" ;\"'")
    if not api_key:
        return "AVIATIONSTACK_API_KEY is missing. Add it to your .env file."

    url = "http://api.aviationstack.com/v1/flights"

    params = {
        "access_key": api_key,
        "limit": 5,
    }

    try:
        response = requests.get(url, params=params, timeout=20)
        response.raise_for_status()

        data = response.json()

        if "error" in data:
            return f"AviationStack API error: {data['error']}"

        flights = data.get("data", [])

        if not flights:
            return f"No flight results found for: {query}"

        results = []

        for flight in flights:
            airline = flight.get("airline", {}).get("name", "Unknown airline")
            flight_number = flight.get("flight", {}).get("iata", "Unknown flight number")
            departure_airport = flight.get("departure", {}).get("airport", "Unknown departure")
            arrival_airport = flight.get("arrival", {}).get("airport", "Unknown arrival")
            status = flight.get("flight_status", "Unknown status")

            results.append(
                f"Airline: {airline}\n"
                f"Flight: {flight_number}\n"
                f"From: {departure_airport}\n"
                f"To: {arrival_airport}\n"
                f"Status: {status}\n"
            )

        return "\n---\n".join(results)

    except requests.exceptions.RequestException as error:
        return f"Flight search failed: {error}"