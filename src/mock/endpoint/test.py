import httpx
city_name_en="Loudi City1"
url = f"http://localhost:8000/looking-glass/city?city_name_en={city_name_en}"

response = httpx.get(url)
response.raise_for_status()
res_json = response.json()
print(response)
print(res_json)
if not res_json:
    print(111)