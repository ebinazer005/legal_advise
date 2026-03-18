import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

url = "https://www.courtlistener.com/api/rest/v4/search/"
headers = {"Authorization": "Token 4571f32c57dbb3dc179613ea6d8b064c2baffb33"}
params = {"q": "murder", "type": "o", "format": "json", "page": 1}

response = requests.get(url, headers=headers, params=params, verify=False, timeout=15)
print(f"Status: {response.status_code}")
data = response.json()
print(f"Results: {len(data.get('results', []))}")
for case in data.get("results", [])[:3]:
    print(f"  - {case.get('caseName')} | {case.get('absolute_url')}")