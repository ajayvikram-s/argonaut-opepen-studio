import os
import glob
import re
from PIL import Image, ImageDraw

# Create output folder for JPGs
jpg_dir = os.path.join(os.getcwd(), 'argonaut_opepens_jpg')
os.makedirs(jpg_dir, exist_ok=True)

svg_dir = os.path.join(os.getcwd(), 'argonaut_opepens')
svg_files = sorted(glob.glob(os.path.join(svg_dir, '*.svg')))

print(f"Found {len(svg_files)} SVG files to convert to JPG.")

def hex_to_rgb(hex_str):
    hex_str = hex_str.lstrip('#')
    if len(hex_str) == 3:
        hex_str = ''.join(c*2 for c in hex_str)
    return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))

def parse_d_box(d):
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
    return int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys))

converted_count = 0
for svg_path in svg_files:
    base_name = os.path.splitext(os.path.basename(svg_path))[0]
    jpg_filename = f"{base_name}.jpg"
    jpg_path = os.path.join(jpg_dir, jpg_filename)
    
    with open(svg_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Create 560x560 image with RGBA for accurate alpha-blending
    img = Image.new('RGBA', (560, 560), (0, 0, 0, 255))
    draw = ImageDraw.Draw(img)
    
    # Parse all path elements in SVG
    paths = re.findall(r'<path d="([^"]+)" fill="([^"]+)"(?: fill-opacity="([^"]+)")?/>', content)
    
    for d, fill, op_str in paths:
        box = parse_d_box(d)
        if not box:
            continue
        min_x, min_y, max_x, max_y = box
        
        # Color parsing
        if fill.lower() == 'black':
            r, g, b = 0, 0, 0
        elif fill.lower() == 'white':
            r, g, b = 255, 255, 255
        elif fill.startswith('#'):
            r, g, b = hex_to_rgb(fill)
        else:
            r, g, b = 0, 0, 0
            
        opacity = float(op_str) if op_str else 1.0
        alpha = int(opacity * 255)
        
        if alpha == 255:
            draw.rectangle([min_x, min_y, max_x, max_y], fill=(r, g, b, 255))
        else:
            # Alpha composite overlay
            overlay = Image.new('RGBA', (max_x - min_x, max_y - min_y), (r, g, b, alpha))
            img.paste(Image.alpha_composite(img.crop([min_x, min_y, max_x, max_y]), overlay), (min_x, min_y))
            
    # Convert RGBA to RGB for JPEG
    rgb_img = img.convert('RGB')
    rgb_img.save(jpg_path, 'JPEG', quality=98)
    converted_count += 1
    print(f"[{converted_count:02d}/20] Converted {os.path.basename(svg_path)} -> {jpg_filename} ({os.path.getsize(jpg_path)} bytes)")

print(f"\nSUCCESS: Converted {converted_count} SVGs into high-quality JPGs in argonaut_opepens_jpg/")
