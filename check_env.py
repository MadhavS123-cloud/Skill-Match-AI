import os
from dotenv import load_dotenv

load_dotenv()

def check_env():
    keys = [
        "GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET",
        "LINKEDIN_CLIENT_ID", "LINKEDIN_CLIENT_SECRET",
        "GITHUB_CLIENT_ID", "GITHUB_CLIENT_SECRET",
        "FLASK_SECRET_KEY"
    ]
    
    print("--- Environment Check ---")
    for key in keys:
        val = os.getenv(key)
        if val:
            print(f"{key}: [SET] (Ends with ...{val[-4:] if len(val) > 4 else val})")
        else:
            print(f"{key}: [MISSING]")
    
    print("\n--- OAUTHLIB Config ---")
    print(f"OAUTHLIB_INSECURE_TRANSPORT: {os.getenv('OAUTHLIB_INSECURE_TRANSPORT')}")
    print(f"OAUTHLIB_RELAX_TOKEN_SCOPE: {os.getenv('OAUTHLIB_RELAX_TOKEN_SCOPE')}")

if __name__ == "__main__":
    check_env()
