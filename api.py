from flask import Flask, request, jsonify
import re
import requests
import time
import json
from bs4 import BeautifulSoup

app = Flask(__name__)

# Regular expression for key extraction
key_regex = r'let content = "([^"]+)";'

def fetch(url, headers):
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
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
                    end_time = time.time()
                    time_taken = end_time - start_time
                    return match.group(1), time_taken
                else:
                    raise Exception("Failed to find content key")
    except Exception as e:
        raise Exception(f"Failed to bypass link. Error: {e}")

def get_paste_drop_content(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Referer': 'https://paste-drop.com/'
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.text
    else:
        raise Exception(f"Failed to get Paste Drop content. Status Code: {response.status_code}")

def parse_html(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    content = soup.find('span', id='content')
    if content:
        return content.get_text().replace('\\', '')
    else:
        return None

@app.route("/")
def home():
    return jsonify({"message": "Invalid Endpoint"})

@app.route("/api/fluxus")
def fluxus():
    url = request.args.get("url")
    if url and url.startswith("https://flux.li/android/external/start.php?HWID="):
        try:
            content, time_taken = bypass_link(url)
            return jsonify({"key": content, "time_taken": time_taken, "credit": "FeliciaXxx"})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify({"message": "Please Enter Fluxus Link!"})

@app.route('/api/paste', methods=['GET'])
def paste_drop():
    url = request.args.get('url')
    if not url:
        return jsonify({"status": "fail", "message": "URL parameter is missing"}), 400

    try:
        html_content = get_paste_drop_content(url)
        parsed_content = parse_html(html_content)
        if parsed_content:
            return jsonify({"status": "success", "result": parsed_content}), 200
        else:
            return jsonify({"status": "fail", "message": "An Error Occurred"}), 500
    except Exception as e:
        return jsonify({"status": "fail", "message": str(e)}), 500

@app.route('/api/socialwolvez', methods=['GET'])
def socialwolvez():
    url = request.args.get('url')
    
    if not url:
        return jsonify({'error': 'Missing parameter: url'}), 400

    try:
        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        script_tag = soup.find('script', {'id': '__NUXT_DATA__'})
        if script_tag and script_tag.string:
            try:
                data = json.loads(script_tag.string)
                
                extracted_url = data.get(5)
                extracted_name = data.get(6)

                if extracted_url and extracted_name:
                    return jsonify({'bypassed_url': extracted_url, 'name': extracted_name})
                else:
                    return jsonify({'error': 'Required data not found in the JSON structure.'}), 500

            except (json.JSONDecodeError, KeyError, IndexError) as e:
                return jsonify({'error': 'Failed to parse JSON data.', 'details': str(e)}), 500
        else:
            return jsonify({'error': 'Script tag with JSON data not found.'}), 404

    except requests.RequestException as e:
        return jsonify({'error': 'Failed to make request to the provided URL.', 'details': str(e)}), 500

@app.route('/api/mboost', methods=['GET'])
def mboost():
    url = request.args.get('url')
    
    if not url:
        return jsonify({"result": "No URL provided."})
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        html_content = response.text
    except requests.RequestException as e:
        return jsonify({"result": f"Error fetching URL: {str(e)}"})

    targeturl_regex = r'"targeturl":\s*"(.*?)"'
    
    match = re.search(targeturl_regex, html_content, re.MULTILINE)
    
    if match and len(match.groups()) > 0:
        result = match.group(1)
        return jsonify({"result": result})
    else:
        return jsonify({"result": "Please try again later"})

# New /supported route
@app.route('/supported', methods=['GET'])
def supported():
    services = ["fluxus", "pastedrop", "socialwolvez", "mboost"]
    return jsonify({"supported_services": services})

if __name__ == '__main__':
    app.run(debug=True)
