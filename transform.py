#!/usr/bin/env python3
"""
transform.py

Contains logic to load the server-style CoCo JSON from a file (e.g., existingCoCoServerResponse.json)
and transform it into a minimal payload structure. Also correctly remaps any 'parentModuleId' and
module references inside the 'rules' section to new ephemeral 6-digit module IDs.

Key Features:
1. Generate ephemeral IDs for each original moduleId.
2. Update each module's 'id' and 'moduleId' to the ephemeral ID.
3. If meta.parentModuleId is present, update it to the ephemeral ID of the parent.
4. In the rules array, look for conditions where parameters might be "module|OLD_WF_ID.OLD_MOD_ID"
   and convert them into "module|NEW_WF_ID.EPHEMERAL_MOD_ID" using the user-provided workflowPhaseId
   and ephemeral mapping.
"""

import json
import random

def transform_server_response_to_minimal(workflow_phase_id, existing_coco_path="existingCoCoServerResponse.json"):
    """
    Reads a server-style CoCo JSON from 'existing_coco_path' and constructs a minimal payload.

    Steps:
      1) Parse the original JSON and collect all modules.
      2) Build a dictionary: oldModuleId -> new ephemeral 6-digit ID.
      3) Reconstruct each module as a minimal object:
         - "id" and "moduleId" replaced by ephemeral ID
         - "meta.parentModuleId" updated if non-null
         - "rules" updated, particularly "conditions[].parameters[]" with "module|oldWfId.oldModuleId"
           replaced by "module|<workflow_phase_id>.<ephemeral_id>"
      4) Return a final payload object:
         {
           "workflowPhaseId": <user_input>,
           "isLocationCollectionConfiguration": false,
           "modules": [ ... transformed modules ... ]
         }

    Args:
      workflow_phase_id (int): The workflow phase ID to embed in the final payload and use in rule transformations.
      existing_coco_path (str): Path to the JSON file containing the server response.

    Returns:
      dict or None: The transformed payload as a dictionary, or None on file/JSON errors.
    """

    # ------------------ (1) Read original server JSON ------------------
    try:
        with open(existing_coco_path, "r", encoding="utf-8") as f:
            server_json = json.load(f)
    except (IOError, json.JSONDecodeError) as e:
        print(f"ERROR reading {existing_coco_path}: {e}")
        return None

    server_modules = server_json.get("modules", [])
    if not isinstance(server_modules, list):
        print("ERROR: 'modules' is missing or not a list in the server JSON.")
        return None

    # ------------------ (2) Build old -> new ephemeral ID map ------------------
    old_to_new_id_map = {}
    for m in server_modules:
        old_id = m.get("moduleId")
        if old_id is None:
            # If there's no moduleId, skip or handle specially
            continue
        ephemeral_id = random.randint(100000, 999999)  # 6-digit ephemeral
        old_to_new_id_map[old_id] = ephemeral_id

    # ------------------ (3) Construct the minimal payload ------------------
    final_payload = {
        "workflowPhaseId": workflow_phase_id,
        "isLocationCollectionConfiguration": False,
        "modules": []
    }

    for module in server_modules:
        old_module_id = module.get("moduleId")
        if old_module_id is None:
            # Skip modules that do not have a moduleId
            continue

        # Look up ephemeral ID
        ephemeral_id = old_to_new_id_map[old_module_id]

        # Copy fundamental attributes
        mod_type = module.get("type", "Text")
        ordinal = module.get("ordinal", 0)
        meta = module.get("meta", {})

        # ------------------ (3a) Update parentModuleId in meta ------------------
        old_parent_id = meta.get("parentModuleId", None)
        if old_parent_id is not None:
            new_parent_id = old_to_new_id_map.get(old_parent_id, old_parent_id)
        else:
            new_parent_id = None

        new_meta = dict(meta)
        new_meta["parentModuleId"] = new_parent_id

        # ------------------ (3b) Handle the rules array ------------------
        rules = module.get("rules", [])
        # We'll reconstruct each rule, especially conditions.parameters
        new_rules = []
        for rule in rules:
            new_rule = dict(rule)  # copy the rule object

            # Each rule typically has a 'conditions' list
            conditions = new_rule.get("conditions", [])
            new_conditions = []
            for condition in conditions:
                new_condition = dict(condition)  # copy condition
                parameters = new_condition.get("parameters", [])

                # We'll build a new parameter list with updated "module|X.Y" references
                new_params = []
                for param in parameters:
                    # Only transform if param starts with "module|"
                    if isinstance(param, str) and param.startswith("module|"):
                        # param is something like "module|1982.18306"
                        # We want "module|<workflow_phase_id>.<ephemeral_id>"
                        new_param = _transform_rule_parameter(param, workflow_phase_id, old_to_new_id_map)
                        new_params.append(new_param)
                    else:
                        # Keep as-is for non-module references
                        new_params.append(param)

                new_condition["parameters"] = new_params
                new_conditions.append(new_condition)

            new_rule["conditions"] = new_conditions
            new_rules.append(new_rule)

        # ------------------ (3c) Build the minimal module object ------------------
        minimal_module = {
            "id": ephemeral_id,
            "moduleId": ephemeral_id,
            "projectId": 23,  # hard-coded as per specification
            "type": mod_type,
            "ordinal": ordinal,
            "meta": new_meta,
            "rules": new_rules
        }

        final_payload["modules"].append(minimal_module)

    return final_payload

# ------------------ HELPER FUNCTION FOR RULE PARAMS ------------------

def _transform_rule_parameter(param_str, new_workflow_phase_id, old_to_new_id_map):
    """
    Helper function to transform a rule parameter that begins with "module|oldWfId.oldModuleId".
    For example: "module|1982.18306" -> "module|<new_workflow_phase_id>.<ephemeral_id>"

    Steps:
      1) Strip off the "module|" prefix.
      2) Split the remainder by '.' -> oldWfId, oldModId
      3) Convert oldModId to int, look up ephemeral in old_to_new_id_map
      4) Rebuild "module|<new_workflow_phase_id>.<ephemeral_id>"
    """
    # param_str might look like "module|1982.18306"
    # Split at '|', ignoring the first part
    try:
        prefix, remainder = param_str.split("|", 1)
    except ValueError:
        # If it doesn't split properly, return original
        return param_str

    # remainder might be "1982.18306"
    if "." not in remainder:
        # No '.' => can't parse old WF ID and old module ID
        return param_str

    # Extract oldWF and oldModule
    parts = remainder.split(".", 1)
    if len(parts) != 2:
        return param_str  # malformed
    old_wf_str, old_mod_str = parts

    # Convert old_mod_str to int, if possible
    try:
        old_mod_id = int(old_mod_str)
    except ValueError:
        return param_str  # not an integer, skip transform

    # Look up ephemeral
    ephemeral_id = old_to_new_id_map.get(old_mod_id, old_mod_id)

    # Build new string
    new_str = f"module|{new_workflow_phase_id}.{ephemeral_id}"
    return new_str
