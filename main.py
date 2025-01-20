#!/usr/bin/env python3
"""
main.py

Coordinates the entire flow:
  1. Authenticates to the QTM QA environment (saving token to .env).
  2. Prompts for the workflowPhaseId and transforms the JSON.
  3. Sends the PUT request.

Usage:
    python main.py
"""

from authenticate import authenticate_and_save_token
from request_manager import prompt_and_send_put

def main():
    # Comment out the authentication call if you don't have MFA disabled on your account.
    # You will have to manually paste the token into the .env file.
    print("\n--- 1) Authenticating ---")
    try:
        authenticate_and_save_token()
    except Exception as auth_err:
        print(f"Authentication failed: {auth_err}")
        return

    print("\n--- 2 & 3) Prompt and Send PUT Request ---")
    prompt_and_send_put()

if __name__ == "__main__":
    main()
