#!/usr/bin/env python3
"""
transform.py

Detailed logging version.

Reads the server-style CoCo JSON from `existingCoCoServerResponse.json`
(or a provided path) and transforms it into a minimal payload structure.
Also updates parentModuleId references and rules, if applicable.
"""

import json
import random
import os
import datetime

def transform_server_response_to_minimal(
    workflow_phase_id,
    existing_coco_path="existingCoCoServerResponse.json",
    # set to true if you want really detailed logs on why your shit is broken
    debug_log=True
):
    """
    Reads a server-style CoCo JSON from 'existing_coco_path' and constructs a minimal payload.
    
    Args:
        workflow_phase_id (int): The workflow phase ID provided by the user.
        existing_coco_path (str): The path to the JSON file with the server response.
        debug_log (bool): If True, prints verbose debug statements.

    Returns:
        dict: A Python dictionary containing the minimal payload with ephemeral IDs.
    """
    if debug_log:
        print(f"[{timestamp()}] [transform.py] -> Starting transform_server_response_to_minimal()")
        print(f"[{timestamp()}] [transform.py] -> Attempting to read: '{existing_coco_path}'")
        print(f"[{timestamp()}] [transform.py] -> Using workflowPhaseId: {workflow_phase_id}")

    # 1) Read the original server JSON
    server_json = None
    try:
        with open(existing_coco_path, "r", encoding="utf-8") as f:
            server_json = json.load(f)
    except (IOError, json.JSONDecodeError) as e:
        if debug_log:
            print(f"[{timestamp()}] [transform.py] ERROR reading file '{existing_coco_path}': {e}")
        return None

    if debug_log:
        print(f"[{timestamp()}] [transform.py] -> Successfully read '{existing_coco_path}'.")
        # Optionally dump the entire file for debugging:
        # print(f"[{timestamp()}] [transform.py] -> server_json content:\n{json.dumps(server_json, indent=2)}\n")

    # 2) Extract modules. This depends on your file’s structure. For example:
    #    Possibly inside: server_json["modules"] or server_json["phaseCollectionConfigurations"][0]["modules"]
    #    We'll demonstrate your sample structure:
    phase_collection_configs = server_json.get("phaseCollectionConfigurations", [])
    if not phase_collection_configs or not isinstance(phase_collection_configs, list):
        if debug_log:
            print(f"[{timestamp()}] [transform.py] -> 'phaseCollectionConfigurations' missing or empty. Cannot proceed.")
        return None

    # For demonstration, we assume you want the first item in the array (or merge multiple?)
    # We'll take the first item for this example:
    first_config = phase_collection_configs[0]
    server_modules = first_config.get("modules", [])
    if debug_log:
        config_id = first_config.get("id", "Unknown ID")
        project_id_from_file = first_config.get("projectId", "N/A")
        print(f"[{timestamp()}] [transform.py] -> Found config ID: {config_id}, projectId in JSON: {project_id_from_file}")
        print(f"[{timestamp()}] [transform.py] -> Number of modules: {len(server_modules)}")

    # 3) Build a dictionary of old module IDs -> ephemeral IDs
    old_to_new_id_map = {}
    for mod in server_modules:
        old_id = mod.get("moduleId")
        if old_id is not None:
            ephemeral_id = random.randint(100000, 999999)
            old_to_new_id_map[old_id] = ephemeral_id
            if debug_log:
                print(f"[{timestamp()}] [transform.py] -> Mapping old moduleId {old_id} -> ephemeral {ephemeral_id}")

    # 4) Construct final minimal payload
    final_payload = {
        "workflowPhaseId": workflow_phase_id,
        "isLocationCollectionConfiguration": False,
        "modules": []
    }

    # 5) Populate new modules
    for mod in server_modules:
        old_module_id = mod.get("moduleId")
        if old_module_id not in old_to_new_id_map:
            # Possibly this module has no valid ID -> skip or handle specially
            if debug_log:
                print(f"[{timestamp()}] [transform.py] -> Skipping module with old_module_id={old_module_id} not in map.")
            continue

        ephemeral_id = old_to_new_id_map[old_module_id]

        # basic fields
        mod_type = mod.get("type", "Text")
        ordinal = mod.get("ordinal", 0)
        meta = mod.get("meta", {})
        
        # Remap meta.parentModuleId if needed
        old_parent_id = meta.get("parentModuleId")
        new_parent_id = None
        if old_parent_id and old_parent_id in old_to_new_id_map:
            new_parent_id = old_to_new_id_map[old_parent_id]

        new_meta = dict(meta)
        new_meta["parentModuleId"] = new_parent_id

        # If you have rules to transform, do that here similarly

        minimal_module = {
            "id": ephemeral_id,
            "moduleId": ephemeral_id,
            "projectId": 23,  # or derive from file if needed
            "type": mod_type,
            "ordinal": ordinal,
            "meta": new_meta,
            "rules": []  # or transform from mod["rules"] if needed
        }

        if debug_log:
            print(f"[{timestamp()}] [transform.py] -> Created minimal module ephemeral_id={ephemeral_id} from old_id={old_module_id}")

        final_payload["modules"].append(minimal_module)

    if debug_log:
        print(f"[{timestamp()}] [transform.py] -> Finished constructing final payload with {len(final_payload['modules'])} modules.")

    return final_payload

def timestamp():
    """ Helper for consistent time-based logging. """
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
