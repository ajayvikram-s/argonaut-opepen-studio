import json
import re

log_path = r"C:\Users\avsin\.gemini\antigravity-ide\brain\6e2e0c2a-e2ed-43fc-852a-9e642ba2725d\.system_generated\logs\transcript_full.jsonl"

found = False
with open(log_path, 'r', encoding='utf-8') as f:
    for line in f:
        if '"type":"USER_INPUT"' in line and 'demo svg.svg' in line:
            obj = json.loads(line)
            content = obj.get('content', '')
            print("User input step found, length:", len(content))
        elif 'fill="white"' in line and '<path' in line and not found:
            obj = json.loads(line)
            content = obj.get('content', '')
            # check if this is an early step before step 64
            step = obj.get('step_index', 0)
            if step < 64:
                raw_paths = re.findall(r'<path\s+([^>]+)/>', content)
                if len(raw_paths) > 300:
                    print(f"Found step {step} with {len(raw_paths)} paths!")
                    with open('original_raw_paths.json', 'w', encoding='utf-8') as out:
                        json.dump(raw_paths, out, indent=2)
                    found = True
                    break

print("Done.")
