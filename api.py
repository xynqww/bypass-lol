from flask import Flask, request, jsonify, send_from_directory
import re
import requests
import time
import json
from bs4 import BeautifulSoup
import os

app = Flask(__name__, static_folder='public')

# Serve index.html from /public for the root route
@app.route('/')
def serve_ui():
    return send_from_directory(app.static_folder, 'index.html')

# Other route definitions remain the same...
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

# Other functions (bypass_fluxus, bypass_paste_drop, etc.) are unchanged

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
            return jsonify({"status": "success", "result": content}) if content else jsonify({"status": "fail", "message": "Content not found"}), 500
        elif "socialwolvez.com" in url:
            extracted_url, extracted_name = bypass_socialwolvez(url)
            return jsonify({"status": "success", "result": {"url": extracted_url, "name": extracted_name}})
        elif "mboost.me" in url:
            target_url = bypass_mboost(url)
            return jsonify({"status": "success", "result": target_url}) if target_url else jsonify({"status": "fail", "message": "Target URL not found"}), 500
        elif "mediafire.com" in url:
            download_url = bypass_mediafire(url)
            return jsonify({"status": "success", "result": download_url}) if download_url else jsonify({"status": "fail", "message": "Download link not found"}), 500
        else:
            return jsonify({"status": "fail", "message": "Unsupported service"}), 400
    except Exception as e:
        return jsonify({"status": "fail", "message": str(e)}), 500

@app.route('/supported', methods=['GET'])
def supported():
    services = ["fluxus", "pastedrop", "socialwolvez", "mboost", "mediafire"]
    return jsonify({"supported_services": services})

if __name__ == '__main__':
    app.run(debug=True)
