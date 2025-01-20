#!/usr/bin/env python3
"""
get_phases_with_coco.py

Combines retrieving specific workflow phases and their corresponding
collection configurations into a single step. It looks for phases of type:
  - 2D iOS Collection
  - QC Web Collection
  - 2D Web Collection
  - 2D iOS Field QC

Environment-based Approach:
1. Looks up QTM_ENVIRONMENT from .env (default: "qa") to pick base URL from ENVIRONMENTS.
2. Reads AUTH_TOKEN from .env, needed for authorization headers.
3. Optionally reads PROJECT_ID from .env if none is specified as an argument.
"""

import os
import json
import requests
from dotenv import load_dotenv

# Define the set of phase type names we want to match
TARGET_PHASE_TYPES = {
    "2D iOS Collection",
    "QC Web Collection",
    "2D Web Collection",
    "2D iOS Field QC"
}

# Environment dictionary
ENVIRONMENTS = {
    "qa": "https://qtm-backend-qa.azurewebsites.net",
    "dev": "https://qtm-backend-dev.azurewebsites.net",
    "prod": "https://qtm-backend.azurewebsites.net"
    # Add additional environments as necessary
}


def get_phases_with_coco(project_id=None, output_file=None):
    """
    1. Loads environment variables for AUTH_TOKEN and optional PROJECT_ID, as well
       as QTM_ENVIRONMENT to determine the base URL.
    2. Fetches workflow data for the specified (or default) project.
    3. Extracts only phases whose 'type.name' is in the set TARGET_PHASE_TYPES.
    4. Fetches collection configurations for that project.
    5. Creates a single list of dicts that includes:
       {
         "id": <phaseId>,
         "name": <phaseName>,
         "phaseType": <typeName>,
         "collectionConfigurationId": <cocoId or None>
       }
    6. Optionally writes the result to a JSON file if output_file is provided.

    Args:
        project_id (int | str): The project ID. If None, uses environment PROJECT_ID.
        output_file (str): If provided, writes the final data to this JSON file.

    Returns:
        list[dict]: A list of dicts, each containing phase info with CoCo ID attached.
    """
    # Step 1: Load environment variables
    load_dotenv()
    auth_token = os.getenv("AUTH_TOKEN")
    env_project_id = os.getenv("PROJECT_ID")
    environment_name = os.getenv("QTM_ENVIRONMENT", "qa").lower().strip()

    if project_id is None:
        project_id = env_project_id

    if not project_id:
        print("ERROR: No project_id provided and none found in .env (PROJECT_ID).")
        return []

    if not auth_token:
        print("ERROR: AUTH_TOKEN not found in environment. Please run authentication or set AUTH_TOKEN in .env.")
        return []

    # Determine the correct base URL
    base_url = ENVIRONMENTS.get(environment_name)
    if not base_url:
        print(f"ERROR: Unknown environment '{environment_name}'. Check QTM_ENVIRONMENT in .env.")
        return []

    # Step 2: Fetch workflow data
    workflows_url = f"{base_url}/api/v1/project/{project_id}/workflows"
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Authorization": f"Bearer {auth_token}",
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0"
        ),
    }

    try:
        wf_resp = requests.get(workflows_url, headers=headers)
        wf_resp.raise_for_status()
        workflow_data = wf_resp.json()
    except requests.RequestException as e:
        print(f"Failed to retrieve workflow phases: {e}")
        return []

    # Ensure we have a list of workflows
    if isinstance(workflow_data, dict):
        workflow_data = [workflow_data]

    # Step 3: Extract only phases whose type.name is in our target list
    matched_phases = []
    for workflow in workflow_data:
        for phase in workflow.get("phases", []):
            phase_type = phase.get("type", {})
            type_name = phase_type.get("name")
            if type_name in TARGET_PHASE_TYPES:
                matched_phases.append({
                    "id": phase["id"],
                    "name": phase["name"],
                    "phaseType": type_name,
                })

    # Step 4: Fetch collection configurations
    coco_url = f"{base_url}/api/v1/project/{project_id}/collection-configurations"
    try:
        coco_resp = requests.get(coco_url, headers=headers)
        coco_resp.raise_for_status()
        coco_map = coco_resp.json()  # e.g., {"1864": {...}, "1866": {...}, ...}
    except requests.RequestException as e:
        print(f"Failed to retrieve collection configurations: {e}")
        return matched_phases  # Return at least the phases we found

    # Step 5: Merge them into a single structure
    for phase_info in matched_phases:
        phase_key = str(phase_info["id"])  # Convert to string for dictionary lookup
        if phase_key in coco_map:
            phase_info["collectionConfigurationId"] = coco_map[phase_key].get("id")
        else:
            phase_info["collectionConfigurationId"] = None

    # Step 6: Optionally write to JSON
    if output_file:
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(matched_phases, f, indent=2)
            print(f"Saved merged data to {output_file}")
        except IOError as ioe:
            print(f"Error writing to {output_file}: {ioe}")

    return matched_phases


# Optional main routine for testing
if __name__ == "__main__":
    # Optionally specify a project ID here or rely on .env for PROJECT_ID
    result = get_phases_with_coco(project_id=267, output_file="EligiblePhases.json")
    print("Final Merged Result:")
    print(json.dumps(result, indent=2))
