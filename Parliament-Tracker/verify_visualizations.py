import requests, sys
base = 'http://localhost:8000'
endpoints = ['/','/bills/','/analytics/','/map/','/calendar/','/api/v1/bills/']
for e in endpoints:
    try:
        r = requests.get(base+e)
        print(f"{e}: {r.status_code}")
    except: print(f"{e}: FAIL")
    