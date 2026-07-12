import requests
import sys

URL = "https://roshini-backend.onrender.com/health"

try:
    response = requests.get(URL, timeout=20)

    if response.status_code == 200:
        print("Backend is healthy.")
        sys.exit(0)

    print(f"Backend returned {response.status_code}")
    sys.exit(1)

except Exception as e:
    print(f"Backend unavailable: {e}")
    sys.exit(1)