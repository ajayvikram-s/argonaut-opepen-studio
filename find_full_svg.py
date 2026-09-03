import json

log_path = r"C:\Users\avsin\.gemini\antigravity-ide\brain\6e2e0c2a-e2ed-43fc-852a-9e642ba2725d\.system_generated\logs\transcript_full.jsonl"

with open(log_path, 'r', encoding='utf-8') as f:
    for line in f:
        obj = json.loads(line)
        content = obj.get('content', '')
        if 'demo svg.svg' in content:
            print(f"Step {obj.get('step_index')}, type={obj.get('type')}, length={len(content)}")
            # If this contains the full SVG
            if '<path' in content and '560' in content:
                # find start and end of svg
                idx = 0
                while True:
                    start = content.find('<svg', idx)
                    if start == -1:
                        break
                    end = content.find('</svg>', start)
                    if end != -1:
                        svg_candidate = content[start:end+6]
                        line_count = svg_candidate.count('\n') + 1
                        print(f"  Found SVG with {line_count} lines, len={len(svg_candidate)}")
                        if line_count > 400: # Original was ~533 lines
                            with open('demo_svg_original_full.svg', 'w', encoding='utf-8') as out:
                                out.write(svg_candidate)
                            print("  -> SAVED demo_svg_original_full.svg!")
                    idx = start + 1
