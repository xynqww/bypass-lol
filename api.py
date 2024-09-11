from flask import Flask, request, jsonify, send_from_directory
import re
import requests
import time
import json
from bs4 import BeautifulSoup

app = Flask(__name__, static_folder='public')

# Serve index.html from /static for the root route
@app.route('/')
def serve_ui():
    return send_from_directory(app.static_folder, 'index.html')

# Regular expression for key extraction
key_regex = r'let content = "([^"]+)"'

# Function to fetch URL with headers
def fetch(url, headers):
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to fetch URL: {url}. Error: {e}")

# Function to bypass a Fluxus link
def bypass_fluxus(url):
    try:
        hwid = url.split("HWID=")[-1]
        if not hwid:
            raise Exception("Invalid HWID in URL")

        start_time = time.time()
        endpoints = [
            {"url": f"https://flux.li/android/external/start.php?HWID={hwid}", "referer": ""},
            {"url": "https://flux.li/android/external/check1.php?hash={hash}", "referer": "https://linkvertise.com"},
            {"url": "https://flux.li/android/external/main.php?hash={hash}", "referer": "https://linkvertise.com"}
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
            print(f"Fetching URL: {url}")  # Added logging
            response_text = fetch(url, headers)
            if endpoint == endpoints[-1]:
                match = re.search(key_regex, response_text)
                if match:
                    end_time = time.time()
                    time_taken = end_time - start_time
                    return match.group(1), time_taken
                else:
                    raise Exception("Failed to find content key")
    except Exception as e:
        print(f"Failed to bypass Fluxus link. Error: {e}")  # Added logging
        raise

# Function to get Paste Drop content
def bypass_paste_drop(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Referer': 'https://paste-drop.com/'
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        content = soup.find('span', id='content')
        return content.get_text().replace('\\', '') if content else None
    except Exception as e:
        raise Exception(f"Failed to get Paste Drop content. Error: {e}")

# Function to bypass SocialWolvez
def bypass_socialwolvez(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        script_tag = soup.find('script', {'id': '__NUXT_DATA__'})
        if script_tag and script_tag.string:
            data = json.loads(script_tag.string)
            extracted_url = data.get(5)
            extracted_name = data.get(6)
            if extracted_url and extracted_name:
                return extracted_url, extracted_name
            else:
                raise Exception("Required data not found in the JSON structure.")
        else:
            raise Exception("Script tag with JSON data not found.")
    except requests.RequestException as e:
        raise Exception(f"Failed to make request to the provided URL. Error: {e}")

# Function to bypass MBoost
def bypass_mboost(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        targeturl_regex = r'"targeturl":\s*"(.*?)"'
        match = re.search(targeturl_regex, response.text, re.MULTILINE)
        return match.group(1) if match else None
    except requests.RequestException as e:
        raise Exception(f"Error fetching MBoost URL. Error: {e}")

# Function to bypass MediaFire
def bypass_mediafire(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        download_button = soup.find('a', {'id': 'downloadButton'})
        return download_button.get('href') if download_button else None
    except Exception as e:
        raise Exception(f"Error fetching MediaFire URL. Error: {e}")

# Unified route for all bypasses
@app.route('/api/bypass', methods=['GET'])
def bypass():
    url = request.args.get('url')

    if not url:
        return jsonify({"status": "fail", "message": "URL parameter is missing"}), 400

    try:
        if "flux.li" in url:
            content, time_taken = bypass_fluxus(url)
            return jsonify({"status": "success", "result": {"key": content, "time_taken": time_taken}})
        elif "paste-drop.com" in url:
            content = bypass_paste_drop(url)
            if content:
                return jsonify({"status": "success", "result": content})
            else:
                return jsonify({"status": "fail", "message": "Content not found"}), 404
        elif "socialwolvez.com" in url:
            extracted_url, extracted_name = bypass_socialwolvez(url)
            return jsonify({"status": "success", "result": {"url": extracted_url, "name": extracted_name}})
        elif "mboost.me" in url:
            target_url = bypass_mboost(url)
            if target_url:
                return jsonify({"status": "success", "result": target_url})
            else:
                return jsonify({"status": "fail", "message": "Target URL not found"}), 404
        elif "mediafire.com" in url:
            download_url = bypass_mediafire(url)
            if download_url:
                return jsonify({"status": "success", "result": download_url})
            else:
                return jsonify({"status": "fail", "message": "Download link not found"}), 404
        else:
            return jsonify({"status": "fail", "message": "Unsupported service"}), 400
    except Exception as e:
        print(f"Exception in bypass function: {e}")  # Added logging
        return jsonify({"status": "fail", "message": str(e)}), 500

@app.route('/supported', methods=['GET'])
def supported():
    services = ["fluxus", "pastedrop", "socialwolvez", "mboost", "mediafire"]
    return jsonify({"supported_services": services})

if __name__ == '__main__':
    app.run(debug=True)
