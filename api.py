from flask import Flask, request, jsonify
import re, requests, time, logging

app = Flask(__name__)

# Debug logging
logging.basicConfig(level=logging.DEBUG)

# Regex to match the content key
key_regex = r'let content = "([^"]+)";'

# Fetch function
def fetch(url, headers):
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching {url}: {e}")
        return None

# Bypass function
def bypass_link(url):
    try:
        hwid = url.split("HWID=")[-1]
        if not hwid:
            return None, "Invalid HWID"

        start_time = time.time()
        endpoints = [
            {"url": f"https://flux.li/android/external/start.php?HWID={hwid}", "referer": ""},
            {"url": "https://flux.li/android/external/check1.php?hash={hash}", "referer": "https://linkvertise.com"},
            {"url": "https://flux.li/android/external/main.php?hash={hash}", "referer": "https://linkvertise.com"}
        ]

        for i, endpoint in enumerate(endpoints):
            response_text = fetch(endpoint["url"], {'Referer': endpoint["referer"], 'User-Agent': 'Mozilla'})
            if response_text is None:
                return None, "Failed to fetch URL"
            if i == len(endpoints) - 1:
                match = re.search(key_regex, response_text)
                if match:
                    return match.group(1), time.time() - start_time
                else:
                    return None, "Content key not found"
    except Exception as e:
        logging.error(f"Error in bypass_link: {e}")
        return None, str(e)

@app.route("/api/fluxus")
def bypass():
    url = request.args.get("url")
    if url and url.startswith("https://flux.li/android/external/start.php?HWID="):
        content, error = bypass_link(url)
        if content:
            return jsonify({"key": content, "time_taken": error})
        else:
            return jsonify({"error": error}), 500
    else:
        return jsonify({"error": "Invalid URL"}), 400

if __name__ != "__main__":
    # Ensure this runs on serverless platforms
    app = app
