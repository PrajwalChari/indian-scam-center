import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

try:
    payload = { 'api_key': 'd199dd654e213de081c185f78bbb5f76', 'url': 'https://httpbin.org/' }
    r = requests.get('https://api.scraperapi.com/', params=payload, timeout=30, verify=False)
    print(f"Status Code: {r.status_code}")
    print(f"Response: {r.text[:500]}")
except Exception as e:
    print(f"Error: {e}")
