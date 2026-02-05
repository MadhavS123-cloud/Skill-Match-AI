import json
import re

def extract_json(text):
    obj_match = re.search(r'(\{.*\}|\[.*\])', text, re.DOTALL)
    if obj_match:
        try: return json.loads(obj_match.group(1))
        except: pass
    try: return json.loads(text)
    except: return None
