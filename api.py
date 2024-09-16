from flask import Flask, request, jsonify
import re
import requests
import time
import json
from bs4 import BeautifulSoup

app = Flask(__name__)

# Regular expression for matching the content key in the final response
key_regex = r'let content = "([^"]+)";'

def fetch(url, headers):
    """Fetch the content of a given URL with specified headers."""
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch URL: {url}. Error: {e}")
        raise

def bypass_fluxus(url):
    """Bypass the Fluxus URL protection."""
    try:
        # Extract HWID from the provided URL
        hwid = url.split("HWID=")[-1]
        if not hwid:
            raise Exception("Invalid HWID in URL")

        start_time = time.time()

        # Endpoint URLs used during the bypass process
        endpoints = [
            {"url": f"https://flux.li/android/external/start.php?HWID={hwid}", "referer": ""},
            {"url": "https://flux.li/android/external/check1.php?hash=PLACEHOLDER_HASH", "referer": "https://linkvertise.com"},
            {"url": "https://flux.li/android/external/main.php?hash=PLACEHOLDER_HASH", "referer": "https://linkvertise.com"}
        ]

        # Fetch the first response (initial HWID request)
        first_response_text = fetch(endpoints[0]["url"], {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'DNT': '1',
            'Connection': 'close',
            'Referer': endpoints[0]["referer"],
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
        })

        # Attempt to extract the hash dynamically from the first response
        hash_match = re.search(r'"hash":"([^"]+)"', first_response_text)
        if hash_match:
            hash_value = hash_match.group(1)
            print(f"Extracted hash: {hash_value}")
        else:
            raise Exception("Failed to extract hash from the first response")

        # Continue with the remaining requests using the extracted hash
        for endpoint in endpoints[1:]:
            url = endpoint["url"].replace("PLACEHOLDER_HASH", hash_value)
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
                # Search for the content key in the final response
                match = re.search(key_regex, response_text)
                if match:
                    end_time = time.time()
                    time_taken = end_time - start_time
                    return match.group(1), time_taken
                else:
                    raise Exception("Failed to find content key in the final response")

    except Exception as e:
        print(f"Failed to bypass Fluxus link. Error: {e}")
        raise

def bypass_paste_drop(url):
    """Bypass Paste-Drop URL protection."""
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
        print(f"Failed to get Paste Drop content. Error: {e}")
        raise

def bypass_socialwolvez(url):
    """Bypass SocialWolvez URL protection."""
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
        print(f"Failed to make request to the provided URL. Error: {e}")
        raise

def bypass_mboost(url):
    """Bypass MBoost URL protection."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        targeturl_regex = r'"targeturl":\s*"(.*?)"'
        match = re.search(targeturl_regex, response.text, re.MULTILINE)
        return match.group(1) if match else None
    except requests.RequestException as e:
        print(f"Error fetching MBoost URL. Error: {e}")
        raise

def bypass_mediafire(url):
    """Bypass MediaFire URL protection."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        download_button = soup.find('a', {'id': 'downloadButton'})
        return download_button.get('href') if download_button else None
    except Exception as e:
        print(f"Error fetching MediaFire URL. Error: {e}")
        raise

@app.route('/api/bypass', methods=['GET'])
def bypass():
    """API endpoint for bypassing different types of URL protections."""
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
        print(f"Exception in bypass function: {e}")
        return jsonify({"status": "fail", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
