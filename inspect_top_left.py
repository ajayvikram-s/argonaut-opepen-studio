import re

with open('gold argonaut opepen.svg', 'r') as f:
    content = f.read()

paths = re.findall(r'<path d="([^"]+)" fill="([^"]+)"(?: fill-opacity="([^"]+)")?/>', content)
print(f"Total paths: {len(paths)}")

# Let's inspect paths that have coordinates around x=140..280, y=140..280
left_top_paths = []
for idx, (d, fill, op) in enumerate(paths):
    nums = list(map(int, re.findall(r'\d+', d)))
    if len(nums) >= 2:
        xs = [nums[k] for k in range(0, len(nums), 2)]
        ys = [nums[k] for k in range(1, len(nums), 2)]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        if min_y < 280 and min_x < 280:
            left_top_paths.append((idx+1, d, fill, op, min_x, min_y, max_x, max_y))

print(f"Total paths in top-left (x < 280, y < 280): {len(left_top_paths)}")
for p in left_top_paths[:30]:
    print(f"  Line/Path {p[0]}: d='{p[1]}' fill='{p[2]}' bounds=[x:{p[4]}..{p[6]}, y:{p[5]}..{p[7]}]")
