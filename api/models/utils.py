import json
import re

def extract_json(text):
    """
    Extracts and parses JSON from a potentially messy AI response string.
    """
    # Try to find content between ```json and ```
    json_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    # Try to find content between ``` and ```
    code_match = re.search(r'```\s*(.*?)\s*```', text, re.DOTALL)
    if code_match:
        try:
            return json.loads(code_match.group(1))
        except json.JSONDecodeError:
            pass

    # Try to find anything that looks like a JSON object {...}
    obj_match = re.search(r'(\{.*\}|\[.*\])', text, re.DOTALL)
    if obj_match:
        try:
            return json.loads(obj_match.group(1))
        except json.JSONDecodeError:
            pass

    # Last resort: try to parse the whole text
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        print(f"DEBUG: Failed to parse JSON from AI response.\nRaw Text: {text[:500]}...")
        return None
