import re

with open('demo svg.svg', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print("Analyzing lines 985 to 1108 (the user's original lower paths from Group 12607.svg):")
lower_user_paths = lines[984:1107]
print(f"Count: {len(lower_user_paths)}")

for i, l in enumerate(lower_user_paths):
    d_m = re.search(r'd="([^"]+)"', l)
    f_m = re.search(r'fill="([^"]+)"', l)
    op_m = re.search(r'fill-opacity="([^"]+)"', l)
    d = d_m.group(1) if d_m else ""
    f = f_m.group(1) if f_m else ""
    op = op_m.group(1) if op_m else ""
    nums = list(map(int, re.findall(r'\d+', d)))
    print(f"{i+985}: d='{d}' fill='{f}' op='{op}' nums={nums}")
