import re
import json

# Let's extract the exact original cells list from the log step where inspect_rows ran
log_path = r"C:\Users\avsin\.gemini\antigravity-ide\brain\6e2e0c2a-e2ed-43fc-852a-9e642ba2725d\.system_generated\logs\transcript_full.jsonl"

# Let's inspect the step where map_colors ran
color_map_text = ""
with open(log_path, 'r', encoding='utf-8') as f:
    for line in f:
        obj = json.loads(line)
        content = obj.get('content', '')
        if '--- DETAILED COLOR MAP AROUND CHARACTER ---' in content:
            color_map_text = content
            break

print("Found color map text length:", len(color_map_text))

# Also in step 54/56, analyze_demo_svg.py had the complete list of unique colors and counts
# Let's inspect the exact lines from demo_svg_filled.svg:
# In demo_svg_filled.svg, we added extra pixels at:
# 1. rows 28 and 29 (spine_colors_28, spine_colors_29)
# 2. gaps in rows 30..41
# 3. gap between skulls x in 22..27, y in 16..26
# If we remove those specifically added infill pixels, we get the exact original 389 user pixels!

with open('demo_svg_filled.svg', 'r', encoding='utf-8') as f:
    filled_content = f.read()

paths = re.findall(r'<path id="px_(\d+)_(\d+)" d="([^"]+)" fill="([^"]+)"/>', filled_content)
print(f"Total paths in filled SVG: {len(paths)}")

# The user's original paths:
# (33, 18) was 'white' -> now set to Gold skeleton palette color #8A7439
# (18, 22) was 'white' -> now set to Gold skeleton palette color #DCC67E
# And remove any artificially added bridge pixels:
# 1. y in [28, 29] were not in original demo svg
# 2. artificially filled gaps:
original_user_paths = []
for gx_s, gy_s, d, fill in paths:
    gx, gy = int(gx_s), int(gy_s)
    
    # Remove added neck pixels
    if gy in [28, 29]:
        continue
    # Remove added skull seam pixels
    if 22 <= gx <= 27 and 16 <= gy <= 26:
        # In original, check which ones were present:
        # From inspect_rows:
        # y=16: x in [16..21] and [29..39] -> gx in 22..28 were NOT present
        # y=17: x in [15..25] and [28..39] -> gx in 26..27 were NOT present
        # y=18: x in [15..25] and [28..39] -> gx in 26..27 were NOT present
        # y=19: x in [14..25] and [28..41] -> gx in 26..27 were NOT present
        # y=20: x in [14..25] and [28..41] -> gx in 26..27 were NOT present
        # y=21: x in [14..24] and [27..41] -> gx in 25..26 were NOT present
        # y=22: x in [14..27] and [28..39] -> (22..27 WERE present except 24)
        # y=23: x in [14..27] and [29..38] -> (28 was NOT present)
        # y=24: x in [14..23] and [26..27] and [32..38]
        # y=25: x in [15..23] and [32..33] and [35..38]
        # y=26: x in [15..23] and [31..33]
        # y=27: x in [17..23] and [31..33]
        pass
    
    # Let's check row by row against the original row counts
    original_user_paths.append((gx, gy, d, fill))

print("Processing complete.")
