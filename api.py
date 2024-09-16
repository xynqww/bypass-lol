from flask import Flask, request, jsonify
import re
import requests
import time

app = Flask(__name__)

# Correct regex pattern for the content key
key_regex = r'let content = "([^"]+)";'

def fetch(url, headers):
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        return None

def bypass_link(url):
    try:
        hwid = url.split("HWID=")[-1]
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
            response_text = fetch(url, headers)
            if response_text is None:
                return None, "Failed to fetch URL"

            if i == len(endpoints) - 1:
                match = re.search(key_regex, response_text)
                if match:
                    end_time = time.time()
                    time_taken = end_time - start_time
                    return match.group(1), time_taken
                else:
                    return None, "Failed to find content key"
    except Exception as e:
        return None, str(e)

@app.route("/")
def home():
    return jsonify({"message": "Invalid Endpoint"})

@app.route("/api/fluxus")
def bypass():
    url = request.args.get("url")
    if url and url.startswith("https://flux.li/android/external/start.php?HWID="):
        content, error = bypass_link(url)
        if content:
            return jsonify({"key": content, "time_taken": error, "credit": "FeliciaXxx"})
        else:
            return jsonify({"error": error}), 500
    else:
        return jsonify({"message": "Please Enter Fluxus Link!"})

if __name__ == "__main__":
    app.run()
