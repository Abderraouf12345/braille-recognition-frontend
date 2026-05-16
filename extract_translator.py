"""Script to extract translation logic to translator.py and remove it from processor.py."""
import json, os, re

ROOT = os.path.dirname(os.path.abspath(__file__))
NB   = os.path.join(ROOT, "final_code_for_interface (1)-version_1.ipynb")
PROCESSOR_PY = os.path.join(ROOT, "backend", "core", "processor.py")
TRANSLATOR_PY = os.path.join(ROOT, "backend", "core", "translator.py")

with open(NB, encoding="utf-8") as f:
    nb = json.load(f)

cells = [c for c in nb["cells"] if c["cell_type"] == "code"]
decode_src = "".join(cells[9]["source"])
gemini_src = "".join(cells[10]["source"])

# Extract translation part from cell 9
# It starts at "# ════════════════════════════════════════════════════════════════════════════════"
# followed by "# CELL 2 — MULTI-LANGUAGE BRAILLE TRANSLATION DICTIONARIES"
start_trans = decode_src.find("# ════════════════════════════════════════════════════════════════════════════════\n# CELL 2")
if start_trans == -1:
    start_trans = decode_src.find("def translate_braille_to_arabic")

trans_part = decode_src[start_trans:]
# Remove the execution part at the end
trans_lines = []
for line in trans_part.splitlines():
    if re.match(r"^braille_output, line_clusters\s*=", line):
        break
    # also stop if we hit interactive prompt
    if "# ── Interactive prompt" in line or "print(\"\\n\" + \"═\"" in line:
        break
    trans_lines.append(line)
trans_code = "\n".join(trans_lines)

# Extract Gemini part
gemini_lines = []
for line in gemini_src.splitlines():
    if "# --- Run ---" in line or "if 'result_text' in locals():" in line:
        break
    gemini_lines.append(line)
gemini_code = "\n".join(gemini_lines)
gemini_code = gemini_code.replace("def correct_arabic_text(input_text):", "def correct_text_with_gemini(input_text):")

# Construct translator.py
translator_content = f'''"""
backend/core/translator.py
Multi-language translation & Gemini correction logic
"""
import os
import time
import google.generativeai as genai

# Setup Gemini API using environment variable
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

{trans_code}

{gemini_code}

# ── Dispatcher ───────────────────────────────────────────────────────────────
def translate_results(braille_text: str, language: str = "arabic"):
    """
    Translates braille text to the specified language, then applies Gemini correction.
    Returns (translated_text, gemini_corrected_text)
    """
    lang = language.lower()
    
    if lang == "arabic":
        translated = translate_braille_to_arabic(braille_text)
        # Arabic-specific post-processing as seen in the notebook
        translated = translated.replace("ُآ", "ُها").replace("اِّتَئد", "اتخذ")
    elif lang == "french":
        translated = translate_braille_to_french(braille_text)
    elif lang == "english_g1":
        translated = translate_braille_to_english_g1(braille_text)
    elif lang == "english_g2":
        translated = translate_braille_to_english_g2(braille_text)
    elif lang == "russian":
        translated = translate_braille_to_russian(braille_text)
    else:
        # Default to Arabic if unknown
        translated = translate_braille_to_arabic(braille_text)
        
    if GEMINI_API_KEY:
        corrected = correct_text_with_gemini(translated)
    else:
        corrected = "Gemini API key not configured. Unable to perform correction."
        
    return translated, corrected
'''

with open(TRANSLATOR_PY, "w", encoding="utf-8") as f:
    f.write(translator_content)

print(f"✅ translator.py created ({len(translator_content)} chars)")

# Now, strip the translation logic from processor.py to clean it up
with open(PROCESSOR_PY, encoding="utf-8") as f:
    proc = f.read()

# We can just remove everything between "# ════════════════════════════════════════════════════════════════════════════════\n# CELL 2"
# and "class BrailleProcessor:"
start_remove = proc.find("# ════════════════════════════════════════════════════════════════════════════════\n# CELL 2")
end_remove = proc.find("class BrailleProcessor:")

if start_remove != -1 and end_remove != -1:
    new_proc = proc[:start_remove] + "\n\n# ── BrailleProcessor ─────────────────────────────────────────────────────────\n" + proc[end_remove:]
    with open(PROCESSOR_PY, "w", encoding="utf-8") as f:
        f.write(new_proc)
    print("✅ processor.py cleaned up.")
else:
    # Try another pattern
    start_remove = proc.find("def translate_braille_to_arabic(")
    if start_remove != -1 and end_remove != -1:
        new_proc = proc[:start_remove] + "\n\n# ── BrailleProcessor ─────────────────────────────────────────────────────────\n" + proc[end_remove:]
        with open(PROCESSOR_PY, "w", encoding="utf-8") as f:
            f.write(new_proc)
        print("✅ processor.py cleaned up (alt pattern).")
    else:
        print("⚠️ Could not find translation block in processor.py to clean up.")
