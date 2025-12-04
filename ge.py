# ge.py
import os
import sys
import requests
from dotenv import load_dotenv

# Load .env if present (looks for .env in current working dir)
load_dotenv()

API_KEY = os.getenv("GOOGLE_API_KEY")

if not API_KEY:
    print("\nERROR: GOOGLE_API_KEY not found in environment.")
    print("Options to fix:")
    print("  1) create a .env file in this folder with:\n     GOOGLE_API_KEY=\"YOUR_KEY_HERE\"")
    print("  2) set the environment variable in your shell before running python")
    print("     (see README below for Windows examples).")
    print("\nExiting.\n")
    sys.exit(2)

# List models endpoint
URL = f"https://generativelanguage.googleapis.com/v1beta/models?key={API_KEY}"

try:
    r = requests.get(URL, timeout=15)
    # raise_for_status will raise an HTTPError on 4xx/5xx
    r.raise_for_status()
except requests.exceptions.HTTPError as he:
    print("HTTP error while calling ListModels:", he)
    # print response body if available for debugging
    try:
        print("Response body:", r.text)
    except Exception:
        pass
    raise
except Exception as e:
    print("Network / other error:", e)
    raise

data = r.json()
models = data.get("models", [])
if not models:
    print("No models found in response. Full response:")
    print(data)
else:
    print(f"Found {len(models)} models. Sample list:")
    for m in models[:50]:  # print up to first 50
        # print the keys that help you choose a model
        name = m.get("name", "<no-name>")
        display = m.get("displayName", "")
        desc = m.get("description", "")
        print(f"- name: {name}, displayName: {display}")
        if desc:
            short = desc if len(desc) < 200 else desc[:197] + "..."
            print(f"   desc: {short}")
