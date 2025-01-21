# README

## Overview

This tool automates the creation of a new **Collection Configuration** (CoCo) on the Quantum application backend. The overall workflow is:

1. **Authenticate** to the target environment (QA, DEV, PROD, etc.) and save a bearer token to `.env`.  
2. **Fetch** available workflow phases for a given project.  
3. **Identify** a specific workflow phase **without** an existing collection configuration.  
4. **Transform** an “existingCoCoServerResponse.json” (i.e., a server response from another environment or phase) into a minimal CoCo payload.  
5. **PUT** that payload to create the new CoCo in the selected workflow phase.


## Setup & Installation

> **Important for First-Time Users**  
> These instructions guide you through installing Python (Windows or macOS), setting up a virtual environment, and cloning this repository. If you already have Python and Git installed, you may skip to [Step 3](#3-clone-the-github-repository).

### 1. Install Python

#### Windows

1. **Download the installer**  
   - Navigate to [https://www.python.org/downloads/](https://www.python.org/downloads/).  
   - Choose the Windows installer (e.g., “Windows x86-64 executable installer” if you have a 64-bit system).

2. **Run the installer**  
   - Double-click the downloaded `.exe`.  
   - **Check** the box “Add Python 3.x to PATH” to enable running Python from the command prompt.  
   - Click “Install Now” and wait for completion.

3. **Verify installation**  
   - Open **Command Prompt** (press `Win + R`, type `cmd`, press Enter).  
   - Type:
     ```bash
     python --version
     ```
   - You should see something like `Python 3.x.x`.

#### macOS

1. **Check existing Python**  
   - Open **Terminal** (Applications → Utilities → Terminal).  
   - Type:
     ```bash
     python3 --version
     ```
   - If you see `Python 3.x.x`, you already have Python 3 installed.

2. **Install or update if needed**  
   - Download the macOS installer (`.pkg` file) from [https://www.python.org/downloads/](https://www.python.org/downloads/).  
   - Double-click to install.  
   - Verify by typing:
     ```bash
     python3 --version
     ```
     in Terminal.

---

### 2. Install Git (Optional but Recommended)

Having Git makes it easier to clone and update this repository. If you prefer, you can download a ZIP file, but Git is strongly recommended.

- **Windows**  
  - Download Git from [https://git-scm.com/download/win](https://git-scm.com/download/win).  
  - Run the installer, accept defaults unless you have specific requirements.  
  - Verify:
    ```bash
    git --version
    ```

- **macOS**  
  - Many macOS versions include Git. Try:
    ```bash
    git --version
    ```
  - If it’s not installed, you may be prompted to install **Xcode Command Line Tools**, or you can install from [https://git-scm.com/download/mac](https://git-scm.com/download/mac).

---

### 3. Clone the GitHub Repository

1. **Using Git (recommended)**  
   ```bash
   git clone https://github.com/dszilagyiques/CloneCoCo.git
   ```
2. **Download a ZIP (if Git is unavailable)**  
   - Go to [https://github.com/dszilagyiques/CloneCoCo](https://github.com/dszilagyiques/CloneCoCo).  
   - Click the green **Code** button, then select **Download ZIP**.  
   - Extract/unzip the downloaded file to a convenient location on your computer (e.g., your Desktop or Documents folder).  
   - Proceed to the next steps in this guide using the extracted folder as your project directory.

---

### 4. Create and Activate a Virtual Environment

Isolating dependencies in a virtual environment ensures that the required packages for this project do not conflict with other Python projects on your system.

#### Windows

1. **Open Command Prompt** and navigate to the project folder:
   ```bash
   cd path\to\CloneCoCo
   ```
2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   ```
3. **Activate the virtual environment**:
   ```bash
   venv\Scripts\activate
   ```

#### macOS

1. **Open Terminal** and navigate to the project folder:
   ```bash
   cd path/to/CloneCoCo
   ```
2. **Create a virtual environment**:
   ```bash
   python3 -m venv venv
   ```
3. **Activate the virtual environment**:
   ```bash
   source venv/bin/activate
   ```

---

### 5. Install Required Packages

With the virtual environment activated, install the necessary packages using `pip`:

```bash
pip install -r requirements.txt
```

---

### 6. Run the Scripts

Follow the instructions in the **File Descriptions** section to run the appropriate scripts for your workflow.

---

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

# CloneCoCo

A collection of Python scripts that handle authentication, transformation of “CoCo” (collection configuration) JSON, and sending or retrieving data from the Quantum (QTM) backend.

---



