#!/usr/bin/env python3
"""
request_manager.py

Adds verbose logging to diagnose potential mismatches between the
provided "existingCoCoServerResponse.json" and the final payload.
"""

import os
import json
import datetime
import requests
from dotenv import load_dotenv

from getCollectionConfigurations import get_phases_with_coco
from transform import transform_server_response_to_minimal

ENVIRONMENTS = {
    "qa": "https://qtm-backend-qa.azurewebsites.net",
    "staging": "https://qtm-backend-staging.azurewebsites.net",
    "prod": "https://qtm-backend.azurewebsites.net"
}

def prompt_and_send_put():
    load_dotenv()
    auth_token = os.getenv("AUTH_TOKEN")
    environment_name = os.getenv("QTM_ENVIRONMENT", "qa").lower().strip()
    base_url = ENVIRONMENTS.get(environment_name)
    project_id_str = os.getenv("PROJECT_ID")

    log(f"Starting prompt_and_send_put with environment='{environment_name}' and project_id='{project_id_str}'")

    if not auth_token:
        log("ERROR: AUTH_TOKEN not found. Authentication may have failed.")
        return
    if not base_url:
        log(f"ERROR: Unrecognized environment '{environment_name}'. Aborting.")
        return
    if not project_id_str:
        log("ERROR: PROJECT_ID not set in .env. Aborting.")
        return

    try:
        project_id = int(project_id_str)
    except ValueError:
        log(f"ERROR: PROJECT_ID in .env is not a valid integer: {project_id_str}")
        return

    # Step 1: Fetch phases
    log("Fetching phases via get_phases_with_coco...")
    all_phases = get_phases_with_coco(project_id=project_id)
    if not all_phases:
        log("ERROR: No phases returned, or an error occurred. Aborting.")
        return

    # Filter only those with null CoCo
    eligible_phases = [p for p in all_phases if p.get("collectionConfigurationId") is None]
    log(f"Found {len(eligible_phases)} eligible phases (collectionConfigurationId == null).")

    if not eligible_phases:
        log("No eligible phases found. Aborting.")
        return

    # List them out
    log("Listing eligible phases:")
    for p in eligible_phases:
        log(f" -> ID={p['id']} Name='{p['name']}' PhaseType='{p['phaseType']}'")

    # Prompt
    selected_phase = None
    while not selected_phase:
        choice_str = input("Enter the ID of the phase to configure: ").strip()
        try:
            choice_id = int(choice_str)
        except ValueError:
            log("Invalid integer. Try again.")
            continue

        found = next((ph for ph in eligible_phases if ph['id'] == choice_id), None)
        if not found:
            log(f"No eligible phase with ID={choice_id}. Please pick from the listed IDs.")
        else:
            selected_phase = found

    phase_id = selected_phase["id"]
    phase_name = selected_phase["name"]
    log(f"User selected phase_id={phase_id}, name='{phase_name}'")

    # Confirm
    from request_manager import get_project_name  # or define inline
    project_name = get_project_name(base_url, auth_token, project_id)
    log(f"Project name from /users/me/projects: '{project_name}'")

    print(f"You have selected phase ID = {phase_id}, Name = '{phase_name}' for project '{project_name}' (ID={project_id}).")
    confirm = input("Is this correct? (Y/N): ").strip().lower()
    if confirm not in ("y", "yes"):
        log("User canceled operation.")
        return

    # Step 2: Transform
    # (Here is the crucial part where you specify the file to read)
    existing_coco_file = "existingCoCoServerResponse.json"
    log(f"Starting transformation from file='{existing_coco_file}' with workflowPhaseId={phase_id}")
    minimal_payload = transform_server_response_to_minimal(
        workflow_phase_id=phase_id,
        existing_coco_path=existing_coco_file,
        debug_log=False  # set to True to see logs from transform.py
    )

    if not minimal_payload:
        log("ERROR: transform_server_response_to_minimal() returned None. Aborting.")
        return

    # Optionally preview
    log("Transformation completed. Minimal payload top-level keys:")
    for key in minimal_payload.keys():
        log(f"   -> {key}")

    # Step 3: PUT
    put_collection_configuration(minimal_payload, base_url, auth_token)

def put_collection_configuration(payload, base_url, auth_token):
    url = f"{base_url}/api/v1/collection-configurations"
    headers = {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json",
        "Accept": "application/json, text/plain, */*",
        "User-Agent": "Mozilla/5.0"
    }

    log(f"Sending PUT to: {url}")
    try:
        resp = requests.put(url, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()
        # Save to response.json
        with open("response.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        log("SUCCESS: PUT returned 2xx. Saved to 'response.json'.")
    except requests.RequestException as e:
        log(f"PUT request failed: {e}")
        if e.response is not None:
            log(f"Response status code: {e.response.status_code}")
            log(f"Response text: {e.response.text}")

def get_project_name(base_url, auth_token, project_id):
    """ Same function from your script. """
    url = f"{base_url}/api/v1/users/me/projects"
    headers = {
        "Authorization": f"Bearer {auth_token}",
        "Accept": "application/json, text/plain, */*",
        "User-Agent": "Mozilla/5.0"
    }
    try:
        r = requests.get(url, headers=headers)
        r.raise_for_status()
        projects = r.json()
        if not isinstance(projects, list):
            return None
        for pr in projects:
            if pr.get("id") == project_id:
                return pr.get("name")
        return None
    except requests.RequestException:
        return None

def log(message):
    """ Utility for timestamped logs. """
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now_str}] [request_manager] {message}")
