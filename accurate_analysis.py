import re
import json

def parse_d(d):
    # Parse tokens
    tokens = re.findall(r'([A-Za-z]|-?\d+(?:\.\d+)?)', d)
    curr_x, curr_y = 0, 0
    xs, ys = [], []
    i = 0
    while i < len(tokens):
        cmd = tokens[i]
        if cmd == 'M':
            curr_x = float(tokens[i+1])
            curr_y = float(tokens[i+2])
            xs.append(curr_x)
            ys.append(curr_y)
            i += 3
        elif cmd == 'H':
            curr_x = float(tokens[i+1])
            xs.append(curr_x)
            i += 2
        elif cmd == 'V':
            curr_y = float(tokens[i+1])
            ys.append(curr_y)
            i += 2
        elif cmd in ['Z', 'z']:
            i += 1
        else:
            i += 1
    if not xs or not ys:
        return None
    min_x, max_x = int(min(xs)), int(max(xs))
    min_y, max_y = int(min(ys)), int(max(ys))
    return min_x, min_y, max_x, max_y

with open('gold argonaut opepen.svg', 'r') as f:
    content = f.read()

paths = re.findall(r'<path d="([^"]+)" fill="([^"]+)"(?: fill-opacity="([^"]+)")?/>', content)

# Load original head pixels
with open('gold_argonaut_head_pixels.json', 'r') as f:
    orig_head_pixels = json.load(f)

head_left = {}
head_right = {}
body = {}
base = {}

for d, fill, op in paths:
    if d == "M560 0H0V560H560V0Z":
        continue
    box = parse_d(d)
    if not box:
        continue
    min_x, min_y, max_x, max_y = box
    gx = min_x // 10
    gy = min_y // 10
    
    if 14 <= gy <= 27:
        if 14 <= gx <= 27:
            head_left[(gx, gy)] = (fill, op, d)
        elif 28 <= gx <= 41:
            head_right[(gx, gy)] = (fill, op, d)
    elif 28 <= gy <= 41:
        body[(gx, gy)] = (fill, op, d)
    elif 49 <= gy <= 55:
        base[(gx, gy)] = (fill, op, d)

print(f"Properly parsed cell counts:")
print(f"  Head Left  (gx: 14..27, gy: 14..27): {len(head_left)} pixels")
print(f"  Head Right (gx: 28..41, gy: 14..27): {len(head_right)} pixels")
print(f"  Body       (gx: 14..41, gy: 28..41): {len(body)} pixels")
print(f"  Base       (gx: 14..41, gy: 49..55): {len(base)} pixels")

# Now let's test transformations between Head Right (original) and Head Left (transformed):
transforms = {
    "Identity (gx_l = gx_r - 14, gy_l = gy_r)": lambda u, v: (u, v),
    "Rotate 90 CW": lambda u, v: (13 - v, u),
    "Rotate 180": lambda u, v: (13 - u, 13 - v),
    "Rotate 270 CW (90 CCW)": lambda u, v: (v, 13 - u),
    "Flip Horizontal (Mirror X)": lambda u, v: (13 - u, v),
    "Flip Vertical (Mirror Y)": lambda u, v: (u, 13 - v),
    "Transpose (Rot 90 + Flip H)": lambda u, v: (v, u),
    "Anti-transpose (Rot 90 + Flip V)": lambda u, v: (13 - v, 13 - u),
}

print("\n--- ISOMETRY MATCHING BETWEEN HEAD RIGHT AND HEAD LEFT ---")
for name, func in transforms.items():
    matches = 0
    total = 0
    for (gx_r, gy_r), (fill_r, op_r, _) in head_right.items():
        u_r = gx_r - 28 # 0..13
        v_r = gy_r - 14 # 0..13
        u_l, v_l = func(u_r, v_r)
        gx_l = u_l + 14
        gy_l = v_l + 14
        total += 1
        if (gx_l, gy_l) in head_left:
            fill_l, op_l, _ = head_left[(gx_l, gy_l)]
            if fill_l.lower() == fill_r.lower():
                matches += 1
    print(f"  {name:55s}: {matches}/{total} matching pixels")

