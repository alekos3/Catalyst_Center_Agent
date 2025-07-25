#!/usr/bin/env python3
__author__ = "Alexios Nersessian"
__copyright__ = "Copyright 2025, Alexios Nersessian"
__version__ = "v1"

import requests
import os
from dotenv import load_dotenv
load_dotenv()

# ---- Constants ----
_BASE_URL = os.getenv("_BASE_URL")
_USERNAME = os.getenv("_USERNAME")
_PASSWORD = os.getenv("_PASSWORD")
_TOKEN = ""


def get_auth_token():
    """
    Retrieves an authentication token from the specified base URL using the provided credentials.

    This function sends a POST request to the DNA Center API to obtain an authentication token.
    It utilizes basic authentication with the given _USERNAME and _PASSWORD. The function does not
    verify SSL certificates for the request.

    Returns:
    - str: The authentication token if the request is successful.

    Raises:
    - ValueError: If the response contains an error, indicating a failure to retrieve the access token.

    Note:
    - SSL verification is disabled for this request (`verify=False`), which might pose a security risk.
    """
    global _TOKEN
    url = "{}/dna/system/api/v1/auth/token".format(_BASE_URL)
    response = requests.post(url, auth=(_USERNAME, _PASSWORD), verify=False)

    if "error" in response.text:
        raise ValueError("ERROR: Failed to retrieve Access Token! REASON: {}".format(response.json()["error"]))
    else:
        _TOKEN = response.json()["Token"]
        return response.json()["Token"]


def get_device_inventory(token: str) -> list:
    """
    Retrieves the device inventory from the specified DNA Center base URL using a token.

    Parameters:
    - token (str): The authentication token for accessing the API.

    Returns:
    - list: A list of dictionary objects of network devices retrieved from the API.
    """
    headers = {
        "x-auth-token": token,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    device_list = []
    offset = 1
    limit = 500  # Do NOT exceed 500 as the limit (Per CC documentation)
    try:
        while True:
            url = f"{_BASE_URL}/dna/intent/api/v1/network-device?&offset={offset}&limit={limit}"
            response = requests.get(url, headers=headers, verify=False)

            if response.json().get("response"):
                device_list.extend(response.json()["response"])
                offset += limit
            else:
                break
    except Exception as e:
        print(e)
    return device_list


def get_device_config(token: str, device_id: str) -> str:
    """
    Retrieves running configuration for a device id. Needs token to authenticate.

    Parameters:
    - token (str): The authentication token for accessing the API.
    - device_id (str): The device to get configuration for.

    Returns:
    - str: A string representation of the devices running configuration.
    """
    headers = {
        "x-auth-token": token,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    url = f"{_BASE_URL}/dna/intent/api/v1/network-device/{device_id}/config"
    response = requests.get(url, headers=headers, verify=False)

    return response.json()["response"]
