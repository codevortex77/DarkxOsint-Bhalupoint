from flask import Flask, request, jsonify
import requests
import time
from datetime import datetime

app = Flask(__name__)

# Prevent Flask from sorting JSON keys alphabetically so "Credit" stays at the bottom
app.config['JSON_SORT_KEYS'] = False
if hasattr(app, 'json'):
    app.json.sort_keys = False

# Simple cache
cache = {}
CACHE_DURATION = 300  # 5 minutes

# API VALIDITY (Extended 1 month from current date to August 9, 2026)
EXPIRY_DATE = datetime(2026, 8, 9)

def get_cached_response(cache_key):
    if cache_key in cache:
        data, timestamp = cache[cache_key]
        if time.time() - timestamp < CACHE_DURATION:
            return data
    return None

def set_cache(cache_key, data):
    cache[cache_key] = (data, time.time())

def clean_response(data, top_level=True):
    if isinstance(data, dict):
        cleaned = {}

        for key, value in data.items():
            if key in ['req_left', 'req_total', 'expiry', 'developer']:
                continue

            if isinstance(value, str):
                cleaned[key] = value.replace('@simpleguy444', '@RichUniversal')
            else:
                cleaned[key] = clean_response(value, False)

        # Add Credit only to the root object.
        if top_level:
            cleaned["Credit"] = "@RichUniversal"

        return cleaned

    elif isinstance(data, list):
        return [clean_response(item, False) for item in data]

    elif isinstance(data, str):
        return data.replace('@simpleguy444', '@RichUniversal')

    return data

@app.route('/api', methods=['GET'])
def api_handler():
    # --- Validity Check ---
    if datetime.now() > EXPIRY_DATE:
        return jsonify({
            "error": "API has expired. Validity was for 1 month.", 
            "Credit": "@RichUniversal"
        }), 403

    # --- KEY ENFORCEMENT ---
    provided_key = request.args.get('key', '')
    if provided_key.lower() != 'bhalupoint':
        return jsonify({
            "error": "Access Denied. Invalid API key.", 
            "Credit": "@RichUniversal"
        }), 401

    # --- PARAMETER TRANSLATION FIX ---
    frontend_type = request.args.get('type', 'num') 
    frontend_term = request.args.get('query') or request.args.get('term', '')
    
    if not frontend_term:
        return jsonify({"error": "Query or term parameter required", "Credit": "@RichUniversal"}), 400
        
    backend_type = 'num' if frontend_type == 'mobile' else frontend_type
    
    # Create cache key using the updated API key namespace
    cache_key = f"{backend_type}:bhalupoint:{frontend_term}"
    
    # Check cache
    cached_response = get_cached_response(cache_key)
    if cached_response:
        return jsonify(cached_response)
    
    try:
        # Request to original API with translated parameters
        backend_key = "swayam"
        original_url = f"https://rootx-osint.in/?type={backend_type}&key={backend_key}&query={frontend_term}"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        response = requests.get(original_url, headers=headers, timeout=20)
        
        if response.status_code == 200:
            data = response.json()
            cleaned_data = clean_response(data)
            set_cache(cache_key, cleaned_data)
            return jsonify(cleaned_data)
        else:
            return jsonify({
                "error": "Failed to fetch data from upstream", 
                "upstream_status_code": response.status_code,
                "Credit": "@RichUniversal"
            }), 500
            
    except requests.exceptions.Timeout:
        return jsonify({
            "error": "Upstream API took too long to respond (Timeout Limit Exceeded)",
            "Credit": "@RichUniversal"
        }), 504
        
    except Exception as e:
        return jsonify({
            "error": f"Internal Script Error: {str(e)}",
            "Credit": "@RichUniversal"
        }), 500

@app.route('/', methods=['GET'])
def health_check():
    return jsonify({
        "status": "System Online",
        "valid_until": EXPIRY_DATE.strftime('%Y-%m-%d'),
        "Credit": "@RichUniversal",
        "usage": "/api?key=bhalupoint&type=mobile&term=9758126124"
    })
