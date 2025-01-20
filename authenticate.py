#!/usr/bin/env python3
"""
authenticate.py

Authenticates to a QTM backend environment using username/password, then saves
the Bearer token in a local .env file under AUTH_TOKEN.

Environment/Configuration:
1. Looks for QTM_ENVIRONMENT in the .env file, defaulting to "qa" if not found.
2. Looks for AUTH_USERNAME and AUTH_PASSWORD in the .env file, defaulting to
   "dszilagyi" / "Koszonom1!!!" if not found.
3. Map QTM_ENVIRONMENT to the correct base URL from ENVIRONMENTS.

Example .env:
    QTM_ENVIRONMENT=qa
    AUTH_USERNAME=someuser
    AUTH_PASSWORD=somepass
"""

import os
import json
import requests
from dotenv import load_dotenv, set_key

# Dictionary of possible environments
ENVIRONMENTS = {
    "qa": "https://qtm-backend-qa.azurewebsites.net",
    "staging": "https://qtm-backend-staging.azurewebsites.net",
    "prod": "https://qtm-backend.azurewebsites.net"
    # Add additional environments as needed
}

def authenticate_and_save_token():
    """
    Authenticates to the QTM environment selected by QTM_ENVIRONMENT in .env,
    using the provided username/password from .env as well.
    Saves the returned accessToken to .env under 'AUTH_TOKEN'.

    Raises:
        SystemError: If the authentication request fails (network issue, 4xx/5xx response).
        ValueError: If 'accessToken' was not found in the response.
    """

    # Load environment variables from .env
    load_dotenv()

    # Determine which environment to use
    environment_name = os.getenv("QTM_ENVIRONMENT", "qa").lower().strip()
    base_url = ENVIRONMENTS.get(environment_name)
    if not base_url:
        # If the environment is not in our dictionary, raise an error
        raise ValueError(
            f"Unknown environment '{environment_name}'. "
            f"Check QTM_ENVIRONMENT in .env or add to ENVIRONMENTS dict."
        )

    # Retrieve credentials from .env or use defaults
    user_name = os.getenv("AUTH_USERNAME", "dszilagyi")
    password = os.getenv("AUTH_PASSWORD", "Koszonom1!!!")

    # Construct the login endpoint URL
    url = f"{base_url}/api/v1/login"
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    data = {
        "userName": user_name,
        "password": password
    }

    try:
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        response_data = response.json()
        token = response_data.get('accessToken')

        if not token:
            raise ValueError("ERROR: 'accessToken' not found in response JSON.")

        dotenv_path = '.env'
        set_key(dotenv_path, 'AUTH_TOKEN', token)
        print(f"Bearer token saved to .env file under AUTH_TOKEN for environment '{environment_name}'.")

    except requests.RequestException as e:
        raise SystemError(f"Authentication request failed: {e}")
    except ValueError as ve:
        raise ValueError(str(ve))
