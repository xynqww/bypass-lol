from flask import Flask, request, jsonify
import requests
import re

app = Flask(__name__)

key_regex = r'let content = "([^"]+)";'

def fetch(url, headers):
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        return f"Failed to fetch URL: {url}. Error: {e}"

def bypass_link(url):
    hwid = url.split("HWID=")[-1]
    if not hwid:
        return "Invalid HWID in URL", None

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

    for endpoint in endpoints:
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
        if endpoint == endpoints[-1]:
            match = re.search(key_regex, response_text)
            if match:
                return match.group(1), None
            else:
                return "Failed to find content key", None
    return "Unhandled case", None

@app.route("/api/fluxus")
def bypass():
    url = request.args.get("url")
    if url and url.startswith("https://flux.li/android/external/start.php?HWID="):
        content, error = bypass_link(url)
        if error:
            return jsonify({"error": content}), 500
        return jsonify({"key": content, "credit": "FeliciaXxx"})
    else:
        return jsonify({"message": "Please Enter Fluxus Link!"})

if __name__ == "__main__":
    app.run()
