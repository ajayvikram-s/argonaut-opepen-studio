import re

with open('Group 12607.svg', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f"Total lines in Group 12607.svg: {len(lines)}")

white_matches = []
all_fills = set()

for idx, line in enumerate(lines):
    fills = re.findall(r'fill="([^"]+)"', line)
    for fill in fills:
        all_fills.add(fill)
        if fill.lower() in ['white', '#ffffff', '#fff', '#ffffffff']:
            white_matches.append((idx + 1, line.strip()))

print(f"\nWhite elements found: {len(white_matches)}")
for line_num, text in white_matches:
    print(f"  Line {line_num}: {text}")

# Let's decode the coordinates of each white pixel
for line_num, text in white_matches:
    d_m = re.search(r'd="([^"]+)"', text)
    if d_m:
        d = d_m.group(1)
        nums = [int(n) for n in re.findall(r'\d+', d)]
        # M(x) (y)V(y+10)... or M(x) (y)H...
        xs = nums[0::2]
        ys = nums[1::2]
        gx = min(nums) // 10
        print(f"  -> Path at line {line_num}: raw numbers={nums}, d={d}")

print("\nAll Unique Fills in Group 12607.svg:")
for fill in sorted(list(all_fills)):
    print(f"  {fill}")
