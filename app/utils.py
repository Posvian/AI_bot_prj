import os
from dotenv import load_dotenv
import requests

load_dotenv()
authorization = os.getenv("AUTHORIZATION_STRING")


url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"

payload = {"scope": "GIGACHAT_API_PERS"}
headers = {
    "Content-Type": "application/x-www-form-urlencoded",
    "Accept": "application/json",
    "RqUID": "e2c634ff-67f3-47c5-aac4-4c1eff1512ea",
    "Authorization": authorization,
}


def get_access_token():

    response = requests.request("POST", url, headers=headers, data=payload)

    response_data = response.json()

    access_token = response_data["access_token"]
    return access_token
