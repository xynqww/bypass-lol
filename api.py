from flask import Flask, request, jsonify
import re
import requests
import time
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Updated regex pattern to match the expected format of the content key
key_regex = r'let content = "([^"]+)";'

def fetch(url, headers):
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to fetch URL: {url}. Error: {e}")
        raise Exception(f"Failed to fetch URL: {url}. Error: {e}")

def bypass_link(url):
    try:
        hwid = url.split("HWID=")[-1]
        if not hwid:
            raise Exception("Invalid HWID in URL")

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
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x66) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
            }
            logging.debug(f"Fetching URL: {url}")
            response_text = fetch(url, headers)
            logging.debug(f"Response from {url}: {response_text[:1000]}")  # Log part of the response

            if i == len(endpoints) - 1:
                match = re.search(key_regex, response_text)
                if match:
                    end_time = time.time()
                    time_taken = end_time - start_time
                    return match.group(1), time_taken
                else:
                    logging.error("Failed to find content key with regex")
                    raise Exception("Failed to find content key")
    except Exception as e:
        logging.error(f"Failed to bypass link. Error: {e}")
        raise Exception(f"Failed to bypass link. Error: {e}")

@app.route("/")
def home():
    return jsonify({"message": "Invalid Endpoint"})

@app.route("/api/fluxus")
def bypass():
    url = request.args.get("url")
    if url and url.startswith("https://flux.li/android/external/start.php?HWID="):
        try:
            content, time_taken = bypass_link(url)
            return jsonify({"key": content, "time_taken": time_taken, "credit": "FeliciaXxx"})
        except Exception as e:
            logging.error(f"Error in bypass route: {e}")
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify({"message": "Please Enter Fluxus Link!"})

if __name__ == "__main__":
    app.run(debug=True)
