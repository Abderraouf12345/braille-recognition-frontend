"""Final surgical fix v2 — remove all remaining stray interactive fragments."""
import re, ast

text  = open('backend/core/processor.py', encoding='utf-8').read()
lines = text.split('\n')

KILL_CONTAINS = [
    "if 'braille_output' in locals",
    "    print(result_text)",
    "        f.write(result_text)",
    "# ── Registry",
    "# ── Interactive prompt",
    "# Arabic Text Corrector",
    "# ════════════════════════════════════════════════",
    "# ── Run ─",
]

result = []
for i, line in enumerate(lines):
    s = line.strip()

    if any(k in line for k in KILL_CONTAINS):
        continue

    # Lone 'else:' at module level (no parent if)
    if s == 'else:' and not line[0].isspace():
        continue

    # Duplicate bare imports appearing deep in the file (past line 50)
    if i > 50 and re.match(r'^import os$|^import google\.generativeai as genai$', s):
        continue

    result.append(line)

open('backend/core/processor.py', 'w', encoding='utf-8').write('\n'.join(result))

# Verify
try:
    ast.parse('\n'.join(result))
    print(f'Syntax OK. Lines: {len(result)}')
except SyntaxError as e:
    print(f'Error at line {e.lineno}: {e.msg}')
    start = max(0, e.lineno - 6)
    for j, l in enumerate(result[start:e.lineno+2], start=start+1):
        print(f'  {j}: {repr(l)}')
