# README

## Overview

This tool automates the creation of a new **Collection Configuration** (CoCo) on the Quantum application backend. The overall workflow is:

1. **Authenticate** to the target environment (QA, DEV, PROD, etc.) and save a bearer token to `.env`.  
2. **Fetch** available workflow phases for a given project.  
3. **Identify** a specific workflow phase **without** an existing collection configuration.  
4. **Transform** an “existingCoCoServerResponse.json” (i.e., a server response from another environment or phase) into a minimal CoCo payload.  
5. **PUT** that payload to create the new CoCo in the selected workflow phase.

### Key Capabilities / Features

1. **Prompts the user for a `workflowPhaseId`**. The script ensures that this phase does **not** already have a `collectionConfigurationId`.  
2. **Requires an empty collection configuration**. It will only work if the chosen workflow phase currently has no CoCo.  
3. **Does not copy column definitions**. There is no need to replicate the underlying dataset.  
4. **Copies module rules**. If modules in the original have rules, they are preserved in the transformed payload.  
5. **Ensure the phase export type is the same**. You can copy module roles so long as the phase export type matches. 
6. **Cross-compatible with other 2D phases**. For instance, a 2D iOS Collection can be cloned into a 2D Web Collection.  
7. **Preloaded modules are not copied**. Preloaded modules are tied to specialized data in certain phases, so they are excluded to avoid broken references.

---

## File Descriptions

1. **`authenticate.py`**  
   - Authenticates against the QTM environment (e.g., `qa`, `dev`, `prod`) using credentials from `.env`.  
   - Stores the resulting bearer token into `.env` under `AUTH_TOKEN`.

2. **`transform.py`**  
   - Reads **`existingCoCoServerResponse.json`** (provided by you) and transforms it into a minimal JSON payload.  
   - Randomizes module IDs so that they do not conflict with any existing configuration.  
   - Preserves references like `parentModuleId` and fixes up any “module|OldWorkflowPhaseId.OldModuleId” rules.

3. **`request_manager.py`**  
   - Orchestrates the main user prompts (post-authentication) for selecting which workflow phase to configure.  
   - Validates that the chosen phase has a `null` `collectionConfigurationId`.  
   - Confirms your choice, transforms the JSON, and **PUT**s the new CoCo.  
   - Saves the **response** from the PUT request to **`response.json`** (rather than printing it to console).

4. **`get_phases_with_coco.py`**  
   - Utility script that queries the project’s workflows (using your `PROJECT_ID` from `.env`) to find all phases.  
   - Returns a list of phases, including whether they already have a CoCo (`collectionConfigurationId`).  
   - Used by `request_manager.py` to determine which phases are eligible (i.e., `collectionConfigurationId == null`).

5. **`main.py`**  
   - Coordinates the entire flow. Typically:
     1. Calls `authenticate_and_save_token()` (unless you comment this out due to MFA).  
     2. Calls `prompt_and_send_put()` from `request_manager.py` to execute the rest of the logic.

6. **`existingCoCoServerResponse.json`**  
   - **You** must manually provide this file containing an **already existing** server-style CoCo.  
   - The script will transform this JSON into a minimal payload suitable for creating a new CoCo in your chosen phase.

---

## Setup & Installation

1. **Clone / Download** these Python scripts into a single directory.
2. **Install dependencies**:
   ```bash
   pip install requests python-dotenv
