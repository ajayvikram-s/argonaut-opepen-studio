import json

log_path = r"C:\Users\avsin\.gemini\antigravity-ide\brain\6e2e0c2a-e2ed-43fc-852a-9e642ba2725d\.system_generated\logs\transcript_full.jsonl"

with open(log_path, 'r', encoding='utf-8') as f:
    for line in f:
        obj = json.loads(line)
        content = obj.get('content', '')
        if 'M560 0H0V560H560V0Z' in content:
            # Look for lines in the view_file tool output
            # In view_file output, lines are formatted as "<line_num>: <content>"
            # Let's extract all lines of the file
            lines = content.split('\n')
            svg_lines = []
            for l in lines:
                # Match "123: <path ...>" or "1: <svg ...>"
                parts = l.split(': ', 1)
                if len(parts) == 2 and parts[0].strip().isdigit():
                    svg_lines.append(parts[1])
            
            if svg_lines:
                recovered_svg = '\n'.join(svg_lines)
                print(f"Recovered {len(svg_lines)} lines.")
                with open('demo_svg_recovered.svg', 'w', encoding='utf-8') as out:
                    out.write(recovered_svg)
                break

print("Done scanning logs.")
