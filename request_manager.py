#!/usr/bin/env python3
"""
request_manager.py

Workflow:
  1) Use get_phases_with_coco() to retrieve all phases in the project with null collectionConfigurationId.
  2) Prompt the user to select an eligible phase ID.
  3) Confirm the phase name and the project name from "api/v1/users/me/projects".
  4) If user confirms, transform the server response and PUT it to /api/v1/collection-configurations.
  5) Save the successful PUT response in 'response.json' (do not print it).

Requires:
  - get_phases_with_coco function from get_phases_with_coco.py
  - transform_server_response_to_minimal from transform.py
  - Environment variables for QTM_ENVIRONMENT, AUTH_TOKEN, PROJECT_ID, etc.
"""

import os
import json
import requests
from dotenv import load_dotenv

from getCollectionConfigurations import get_phases_with_coco
from transform import transform_server_response_to_minimal

# Same environment dictionary used elsewhere
ENVIRONMENTS = {
    "qa": "https://qtm-backend-qa.azurewebsites.net",
    "dev": "https://qtm-backend-dev.azurewebsites.net",
    "prod": "https://qtm-backend.azurewebsites.net"
    # Add additional environments as needed
}

def prompt_and_send_put():
    """
    Main function for orchestrating the prompt workflow:
      1) get_phases_with_coco to retrieve all phases for the current project
      2) filter by phases that have collectionConfigurationId == None
      3) prompt user to pick one of those phase IDs
      4) confirm by displaying the name & the project name
      5) if confirmed, transform & PUT the new CoCo
      6) save the response to response.json
    """
    load_dotenv()  # ensure we have fresh .env variables
    auth_token = os.getenv("AUTH_TOKEN")
    if not auth_token:
        print("ERROR: AUTH_TOKEN not found. Make sure you have authenticated first.")
        return

    # Determine environment base URL
    environment_name = os.getenv("QTM_ENVIRONMENT", "qa").lower().strip()
    base_url = ENVIRONMENTS.get(environment_name)
    if not base_url:
        print(f"ERROR: Unknown environment '{environment_name}'. Check QTM_ENVIRONMENT in .env.")
        return

    # Retrieve project info from .env (and possibly from user/projects endpoint to get name)
    project_id_env = os.getenv("PROJECT_ID")
    if not project_id_env:
        print("ERROR: PROJECT_ID not found in .env. Cannot proceed.")
        return
    try:
        project_id = int(project_id_env)
    except ValueError:
        print(f"ERROR: PROJECT_ID in .env is not a valid integer: {project_id_env}")
        return

    # 1) Get phases with CoCo info
    print("Fetching phases with CoCo data (get_phases_with_coco)...")
    all_phases = get_phases_with_coco(project_id=project_id)
    if not all_phases:
        print("No phases returned, or an error occurred. Aborting.")
        return

    # 2) Filter only those with null collectionConfigurationId
    eligible_phases = [p for p in all_phases if p.get("collectionConfigurationId") is None]
    if not eligible_phases:
        print("No phases are eligible (none have null collectionConfigurationId). Aborting.")
        return

    # Show user the eligible phase IDs for selection
    print("\nEligible Workflow Phases (Null collectionConfigurationId):")
    for p in eligible_phases:
        print(f"  ID: {p['id']}, Name: {p['name']}, PhaseType: {p['phaseType']}")

    # 3) Prompt user to pick one
    selected_phase = None
    while not selected_phase:
        choice_str = input("\nEnter the ID of the phase you wish to configure: ").strip()
        try:
            choice_id = int(choice_str)
        except ValueError:
            print("Invalid integer. Please try again.")
            continue

        # Validate
        match = next((ph for ph in eligible_phases if ph['id'] == choice_id), None)
        if not match:
            print(f"No eligible phase with ID = {choice_id}. Please select a valid ID from the list.")
        else:
            selected_phase = match

    # 4) Confirm the selected phase by displaying name & project name
    phase_name = selected_phase["name"]
    project_name = get_project_name(base_url, auth_token, project_id)
    print(f"\nYou have selected phase ID = {selected_phase['id']}, name = '{phase_name}'")
    if project_name:
        print(f"Project: {project_name} (ID = {project_id})")
    else:
        print(f"Project ID = {project_id} (Name lookup failed)")

    confirm = input("Is this correct? (Y/N): ").strip().lower()
    if confirm not in ("y", "yes"):
        print("Operation canceled by user.")
        return

    # 5) Transform the server response to the minimal payload
    minimal_payload = transform_server_response_to_minimal(selected_phase["id"])
    if not minimal_payload:
        print("Failed to create minimal payload. Aborting.")
        return

    # 6) Perform the PUT request
    put_collection_configuration(minimal_payload, base_url, auth_token)


def put_collection_configuration(payload, base_url, auth_token):
    """
    Sends a PUT request to /api/v1/collection-configurations with the given payload.
    On success, saves the JSON response to 'response.json' in the working directory.
    Does not print the response JSON to console.
    """
    url = f"{base_url}/api/v1/collection-configurations"
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0"
    }

    print(f"\nSending PUT to {url}...")
    try:
        resp = requests.put(url, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()

        # Save response to file
        with open("response.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print("SUCCESS: PUT request returned 2xx. Response saved to 'response.json'.")
    except requests.RequestException as e:
        print(f"ERROR during PUT request: {e}")
        if e.response is not None:
            print("Response text:", e.response.text)


# ---------------------------------------------------------
# Additional Helper Function to Retrieve Project Name
# ---------------------------------------------------------

def get_project_name(base_url, auth_token, project_id):
    """
    Calls GET /api/v1/users/me/projects to find the project
    whose 'id' matches 'project_id' and returns its 'name'.
    If not found or an error occurs, returns None.
    """
    url = f"{base_url}/api/v1/users/me/projects"
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Authorization": f"Bearer {auth_token}",
        "User-Agent": "Mozilla/5.0"
    }

    try:
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        project_list = resp.json()  # should be a list of projects
        if not isinstance(project_list, list):
            return None

        for proj in project_list:
            if proj.get("id") == project_id:
                return proj.get("name")
        return None
    except requests.RequestException:
        return None
