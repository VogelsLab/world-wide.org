"""
Geocode the lines contained in the "locations.txt" file by making using of the Google Maps API
"""

import requests
import json
import time
import csv

# Google Maps API key
API_KEY = "blah"

# Google Maps API endpoint
API_URL = "https://maps.googleapis.com/maps/api/geocode/json"

# Open the locations file
with open("locations.txt", "r") as f:
    # Create a CSV writer to write the results to
    with open("locations_geocoded.csv", "w") as csvfile:
        writer = csv.writer(csvfile)
        # Write the header
        writer.writerow(["address", "latitude", "longitude"])
        # For each line in the file
        for line in f:
            # Strip the line
            line = line.strip()
            # Create the parameters
            params = {
                "address": line,
                "key": API_KEY
            }
            # Make the request
            r = requests.get(API_URL, params=params)
            # Get the JSON response
            json_response = r.json()
            # If the JSON response contains a status of "OK"
            if json_response["status"] == "OK":
                # Get the latitude and longitude
                latitude = json_response["results"][0]["geometry"]["location"]["lat"]
                longitude = json_response["results"][0]["geometry"]["location"]["lng"]
                # Write the address, latitude, and longitude to the CSV file
                writer.writerow([line, latitude, longitude])
            # Otherwise
            else:
                # Write the address and "null" to the CSV file
                writer.writerow([line, "null", "null"])
            # Wait for 1 second
            time.sleep(1)