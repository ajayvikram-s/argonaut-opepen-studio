import re

with open('Group 12607.svg', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f"Read {len(lines)} lines from Group 12607.svg")

# Argonauts official Gold Skeleton palette
GOLD_PALETTE = [
    "#F7EEC2", # Bright Gold
    "#F3E7B4", # Soft Gold highlight
    "#DCC67E", # Primary Gold bone
    "#C6AE6E", # Warm Gold
    "#C3AC6B", # Golden bone
    "#C3A759", # Deep Gold
    "#AC924C", # Amber Gold
    "#9C844F", # Mid Gold
    "#8E7539", # Classic Gold
    "#8A7439", # Shaded Gold
    "#6F5829", # Contour Gold
    "#574217", # Shadow Gold
    "#3A2A0B", # Deep cavity Gold
]

# 1. First, collect all existing non-white path elements and their exact bounding boxes
# In lines 409-532, user has paths like: <path d="M280 300H270V310H280V300Z" fill="#36260E"/>
# Also lines 1-396 have character and background paths.

# Let's see: for any line that is a white rect:
# <rect x="X" y="Y" width="70" height="70" fill="white"/>
# It covers gx from X//10 to (X+70)//10 (7 cells), gy from Y//10 to (Y+70)//10 (7 cells).
# If we expand each 70x70 rect into 49 individual 10x10 <path> elements with gold palette colors,
# and placed right where the <rect> was (below the overlay paths in DOM order),
# then the existing paths in lines 409-532 will naturally sit on top, preserving every single existing pixel exactly!
# And for the 2 white paths (line 195 and line 392), we replace fill="white" with matching gold colors (#8A7439 and #DCC67E).

new_lines = []
expanded_white_rects_count = 0
replaced_white_paths_count = 0

for idx, line in enumerate(lines):
    # Check if white path
    if '<path' in line and ('fill="white"' in line or 'fill="#ffffff"' in line or 'fill="#FFFFFF"' in line):
        # Line 195: (330, 180) -> #8A7439
        # Line 392: (180, 220) -> #DCC67E
        if 'M340 180' in line or '180' in line:
            new_line = line.replace('fill="white"', 'fill="#8A7439"').replace('fill="#ffffff"', 'fill="#8A7439"').replace('fill="#FFFFFF"', 'fill="#8A7439"')
        else:
            new_line = line.replace('fill="white"', 'fill="#DCC67E"').replace('fill="#ffffff"', 'fill="#DCC67E"').replace('fill="#FFFFFF"', 'fill="#DCC67E"')
        new_lines.append(new_line)
        replaced_white_paths_count += 1
        continue
        
    # Check if white rect
    rect_m = re.search(r'<rect\s+x="(\d+)"\s+y="(\d+)"\s+width="(\d+)"\s+height="(\d+)"\s+fill="white"/>', line)
    if rect_m:
        rx = int(rect_m.group(1))
        ry = int(rect_m.group(2))
        rw = int(rect_m.group(3))
        rh = int(rect_m.group(4))
        
        # Expand this 70x70 (or rw x rh) rect into individual 10x10 gold pixel paths
        for py in range(ry, ry + rh, 10):
            for px in range(rx, rx + rw, 10):
                # Pick harmonious gold skeleton palette color based on coordinates
                # Marrow, shading, and bone structure
                gx = px // 10
                gy = py // 10
                gold_color = GOLD_PALETTE[(gx * 3 + gy * 7) % len(GOLD_PALETTE)]
                path_d = f"M{px+10} {py}H{px}V{py+10}H{px+10}V{py}Z"
                new_lines.append(f'<path d="{path_d}" fill="{gold_color}"/>\n')
                
        expanded_white_rects_count += 1
        continue
        
    # All other lines remain 100% UNCHANGED
    new_lines.append(line)

print(f"Replaced {replaced_white_paths_count} individual white paths.")
print(f"Expanded {expanded_white_rects_count} large white rectangles into individual gold pixel paths.")
print(f"Total new lines: {len(new_lines)}")

# Save to Group 12607.svg and demo svg.svg
with open('Group 12607.svg', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

with open('demo svg.svg', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("SUCCESS: Successfully updated Group 12607.svg and demo svg.svg!")
