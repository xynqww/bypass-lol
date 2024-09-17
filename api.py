from flask import Flask, request, jsonify
import re
import requests
import time
import logging

# Initialize Flask app
app = Flask(__name__)

# Set up logging for debugging
logging.basicConfig(level=logging.DEBUG)

# Correct regex pattern for the content key
key_regex = r'let content = "([^"]+)";'

# Function to fetch the URL
def fetch(url, headers):
    try:
        logging.debug(f"Fetching URL: {url}")
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an HTTPError for bad responses
        logging.debug(f"Response status code: {response.status_code}")
        return response.text
    except requests.exceptions.RequestException as e:
        logging.error(f"Error during fetch: {e}")
        return None

# Bypass function to process the link
def bypass_link(url):
    try:
        hwid = url.split("HWID=")[-1]
        logging.debug(f"Extracted HWID: {hwid}")
        
        if not hwid:
            return None, "Invalid HWID in URL"
        
        start_time = time.time()
        endpoints = [
            {
                "url": f"https://flux.li/android/external/start.php?HWID={hwid}",
                "referer": ""
            },
            {
                "url": "https://flux.li/android/external/check1.php?hash={hash}",
                "referer": "https://linkvertise.com"
            },
            {
                "url": "https://flux.li/android/external/main.php?hash={hash}",
                "referer": "https://linkvertise.com"
            }
        ]

        for i, endpoint in enumerate(endpoints):
            url = endpoint["url"]
            referer = endpoint["referer"]
            headers = {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'DNT': '1',
                'Connection': 'close',
                'Referer': referer,
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
            }
            logging.debug(f"Making request to: {url} with Referer: {referer}")
            response_text = fetch(url, headers)
            if response_text is None:
                logging.error("Failed to fetch URL")
                return None, "Failed to fetch URL"

            # If this is the last endpoint, search for the key using regex
            if i == len(endpoints) - 1:
                match = re.search(key_regex, response_text)
                if match:
                    end_time = time.time()
                    time_taken = end_time - start_time
                    logging.debug(f"Key found: {match.group(1)}")
                    logging.debug(f"Time taken: {time_taken} seconds")
                    return match.group(1), time_taken
                else:
                    logging.error("Failed to find content key")
                    return None, "Failed to find content key"
    except Exception as e:
        logging.exception("Exception occurred in bypass_link")
        return None, str(e)

@app.route("/")
def home():
    return jsonify({"message": "Invalid Endpoint"})

@app.route("/api/fluxus")
def bypass():
    url = request.args.get("url")
    logging.debug(f"Received URL for bypass: {url}")
    
    if url and url.startswith("https://flux.li/android/external/start.php?HWID="):
        content, error = bypass_link(url)
        if content:
            logging.debug(f"Bypass successful, key: {content}")
            return jsonify({"key": content, "time_taken": error, "credit": "FeliciaXxx"})
        else:
            logging.error(f"Bypass failed: {error}")
            return jsonify({"error": error}), 500
    else:
        logging.debug("Invalid Fluxus URL provided")
        return jsonify({"message": "Please Enter Fluxus Link!"})
