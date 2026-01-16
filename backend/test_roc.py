import requests

url = 'http://127.0.0.1:8000/api/research/'
print(f"--- Asking Agent to find 'Board of Directors' ---")

payload = {
    'company_name': 'version 1 services private limited',
    'requirements': 'Who are the CEO and email address' 
}

try:
    response = requests.post(url, json=payload)
    print(f"Status: {response.status_code}")
    print(response.json())
except Exception as e:
    print(e)