#!/bin/python3

# Imports
import os
import time
from typing import Optional
import httpx
import json

# Constants
IP_CHECKER_ENDPOINT = "https://api.ipify.org"
RENEW_ENDPOINT = "https://sso-f.orange.fr/ecd_wp/configEquipement/v2.0/users/current/contracts/{contract_id}/equipments/devices/{device_id}/actions/renewIp"
BODY = "{}"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0",
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "X-Orange-Origin-Id": "ECQ",
    "X-Orange-Caller-Id": "ECQ",
    "X-App-Device-Type": "desktop",
    "Content-Type": "application/json",
    "Origin": "https://espace-client.orange.fr",
    "Connection": "keep-alive",
    "Referer": "https://espace-client.orange.fr/"
}

class Configurator:
    @staticmethod
    def load_config() -> dict:
        conf = Configurator._read_config()
        if conf:
            return conf
        
        conf = Configurator._ask_for_config()
        Configurator._save_config(conf)

        return conf

    def _read_config() -> Optional[dict]:
        if not os.path.isfile("pacobox_data.json"):
            return None
        with open("pacobox_data.json", "r") as config:
            try: return json.load(config)
            except: return None

    def _save_config(data: dict) -> None:
        with open("pacobox_data.json", "w") as config:
            json.dump(data, config, indent=4)

    def _ask_for_config() -> dict:
        print("Config not yet present.")
        conf = {}
        conf["print_ip"] = "y" in input("Do you want the script to print your IP? (y/n): ")
        conf["save_ip"] = "y" in input("Do you want the script to save your IP into a list of used IPs? (y/n): ")
        
        print("How to get: ")
        print("Go to https://espace-client.orange.fr/equipement and click on your livebox.")
        print("You'll get 2 numbers at the end of the url, first is the contract id and second is the device id.")
        conf["contract_id"] = input("Please enter your contract ID: ").strip()
        conf["device_id"] = input("Please enter your device ID: ").strip()

        print("How to get: ")
        print("Go back to the previous URL for your livebox and open the devtools, then go to the \"Network\" tab")
        print("Search for \"key\" and refresh the page. You'll find 2 requests, a POST and an OPTIONS, click on the POST one.")
        print("On the right, click on the \"Headers\" tab, find the Request Headers and enable \"raw\".")
        print("Inside there, find the Cookie header and copy its value (the part after Cookie: )")
        conf["cookie"] = input("Please enter your cookie: ").replace("Cookie:", "").strip()

        return conf

def get_ip() -> str:
    return httpx.get(IP_CHECKER_ENDPOINT).text

def wait_until_new_ip(initial_ip: str) -> Optional[str]:
    new_ip = initial_ip
    tries = 0

    while new_ip == initial_ip:
        print(f"\rWaiting for new IP... (tries: {tries})", end="")
        try:
            new_ip = get_ip()
        except:
            pass

        tries += 1

        if tries > 20: 
            print()
            return None
        
        time.sleep(5)
    
    print() # Otherwise next print will be on same line
    return new_ip

def main():
    conf = Configurator.load_config()

    initial_ip = get_ip()
    if conf["print_ip"]:
        print(f"Initial IP: {initial_ip}")

    formatted_url = RENEW_ENDPOINT.format(
            contract_id = conf["contract_id"], 
            device_id = conf["device_id"]
        )

    headers_full = {
        "Cookie": conf["cookie"],
        **HEADERS
    }

    res = httpx.post(formatted_url, headers=headers_full, data=BODY)
    if res.status_code != 200:
        print("Error happened while sending the request !")
        return
    
    new_ip = wait_until_new_ip(initial_ip)
    if new_ip:
        print(f"Got a new IP: {new_ip}")
        if conf["save_ip"]:
            with open("pacobox_ips.txt", "a") as pacobox_file:
                pacobox_file.write(new_ip + "\n")
    else:
        print("Couldn't get new IP in 20 pings.")
        print("Check if either:")
        print("- Your router rebooted but with the same IP")
        print("- Your router crashed/isn't starting")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nKeyboard interrupted.")
    except Exception as err:
        print("\n\nAn error occured.")
        print(err)

