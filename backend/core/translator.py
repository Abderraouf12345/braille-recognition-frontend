"""
backend/core/translator.py
Multi-language translation & Gemini correction logic
"""
import os
import time
from google import genai
from google.genai import types

# Read API key from environment variable only
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# ════════════════════════════════════════════════════════════════════════════════
# CELL 2 — MULTI-LANGUAGE BRAILLE TRANSLATION DICTIONARIES
# ════════════════════════════════════════════════════════════════════════════════

# ── SHARED HELPERS ────────────────────────────────────────────────────────────
CAPITAL_INDICATOR = '⠠'
NUMBER_INDICATOR  = '⠼'

# ─────────────────────────────────────────────────────────────────────────────
# 1. ARABIC
# ─────────────────────────────────────────────────────────────────────────────
def translate_braille_to_arabic(braille_text):
    """Arabic Braille — RNIB / World Braille Usage standard."""
    braille_map = {
        '⠀': ' ',
        # Letters
        '⠁': 'ا',  '⠃': 'ب',  '⠞': 'ت',  '⠹': 'ث',  '⠚': 'ج',
        '⠱': 'ح',  '⠭': 'خ',  '⠙': 'د',  '⠮': 'ذ',  '⠗': 'ر',
        '⠵': 'ز',  '⠎': 'س',  '⠩': 'ش',  '⠯': 'ص',  '⠫': 'ض',
        '⠾': 'ط',  '⠿': 'ظ',  '⠷': 'ع',  '⠣': 'غ',  '⠋': 'ف',
        '⠟': 'ق',  '⠅': 'ك',  '⠇': 'ل',  '⠍': 'م',  '⠝': 'ن',
        '⠓': 'ه',  '⠺': 'و',  '⠊': 'ي',  '⠕': 'ى',  '⠡': 'ة',
        # Ligatures & hamza forms
        '⠧': 'لا', '⠌': 'أ',  '⠨': 'إ',  '⠜': 'آ',  '⠄': 'ء',
        '⠳': 'ؤ',  '⠽': 'ئ',
    }
    num_map = {
        '⠁': '1', '⠃': '2', '⠉': '3', '⠙': '4', '⠑': '5',
        '⠋': '6', '⠛': '7', '⠓': '8', '⠊': '9', '⠚': '0',
    }
    extra_map = {
        # Harakat (diacritics)
        '⠂': 'َ',  '⠑': 'ِ',  '⠥': 'ُ',  '⠆': 'ً',  '⠔': 'ٍ',
        '⠢': 'ٌ',  '⠠': 'ّ',  '⠒': 'ْ',
        # Punctuation
        '⠐': '،', '⠰': ' ',  '⠲': '.', '⠦': '؟', '⠖': '!',
        '⠤': '-',  '⠶': '"', '⠉': '-', '⠏': '(', '⠹': ')',
        '⠴': '.',  '⠸': '',
    }

    translated_lines = []
    for line in braille_text.split('\n'):
        if line.startswith('⠧⠤') or line.startswith('⠏⠉'):
            translated_lines.append('-' * 20)
            continue
        translated_line = ""
        number_mode = False
        i = 0
        while i < len(line):
            char = line[i]
            if i + 1 < len(line) and line[i:i+2] == '⠐⠂':
                translated_line += ":"
                i += 2
                continue
            if char == NUMBER_INDICATOR:
                number_mode = True
                i += 1
                continue
            if number_mode:
                if char in num_map:
                    translated_line += num_map[char]
                    i += 1
                    continue
                else:
                    number_mode = False
            if char == '⠰':
                translated_line += " "
                i += 1
                continue
            if char in braille_map:
                translated_line += braille_map[char]
            elif char in extra_map:
                translated_line += extra_map[char]
            else:
                translated_line += char
            i += 1
        translated_lines.append(translated_line)
    return "\n".join(translated_lines)


# ─────────────────────────────────────────────────────────────────────────────
# 2. FRENCH
# ─────────────────────────────────────────────────────────────────────────────
def translate_braille_to_french(braille_text):
    """French Braille — Braille Français Uniformisé (BFU)."""
    braille_map = {
        '⠀': ' ',
        # Basic letters
        '⠁': 'a', '⠃': 'b', '⠉': 'c', '⠙': 'd', '⠑': 'e',
        '⠋': 'f', '⠛': 'g', '⠓': 'h', '⠊': 'i', '⠚': 'j',
        '⠅': 'k', '⠇': 'l', '⠍': 'm', '⠝': 'n', '⠕': 'o',
        '⠏': 'p', '⠟': 'q', '⠗': 'r', '⠎': 's', '⠞': 't',
        '⠥': 'u', '⠧': 'v', '⠺': 'w', '⠭': 'x', '⠽': 'y',
        '⠵': 'z',
        # Accented characters
        '⠷': 'à', '⠮': 'â', '⠯': 'ç', '⠿': 'è', '⠾': 'é',
        '⠡': 'ê', '⠣': 'ë', '⠩': 'î', '⠹': 'ï', '⠳': 'ô',
        '⠱': 'ù', '⠫': 'û', '⠻': 'ü', '⠜': 'œ', '⠌': 'æ',
    }
    num_map = {
        '⠁': '1', '⠃': '2', '⠉': '3', '⠙': '4', '⠑': '5',
        '⠋': '6', '⠛': '7', '⠓': '8', '⠊': '9', '⠚': '0',
    }
    extra_map = {
        '⠂': ',',  '⠆': ';',  '⠒': ':',  '⠲': '.',  '⠖': '!',
        '⠦': '?',  '⠤': '-',  '⠦⠤': '«', '⠤⠦': '»',
        '⠶': '"',  '⠄': "'",  '⠐': '—',  '⠘': '#',
    }

    translated_lines = []
    for line in braille_text.split('\n'):
        translated_line = ""
        capital_mode = False
        number_mode  = False
        i = 0
        while i < len(line):
            char = line[i]
            if char == CAPITAL_INDICATOR:
                capital_mode = True
                i += 1
                continue
            if char == NUMBER_INDICATOR:
                number_mode = True
                i += 1
                continue
            if number_mode:
                if char in num_map:
                    translated_line += num_map[char]
                    i += 1
                    continue
                else:
                    number_mode = False
            # Two-cell punctuation
            two = line[i:i+2]
            if two in extra_map:
                translated_line += extra_map[two]
                i += 2
                continue
            if char in braille_map:
                letter = braille_map[char]
                if capital_mode:
                    letter = letter.upper()
                    capital_mode = False
                translated_line += letter
            elif char in extra_map:
                translated_line += extra_map[char]
            else:
                translated_line += char
            i += 1
        translated_lines.append(translated_line)
    return "\n".join(translated_lines)


# ─────────────────────────────────────────────────────────────────────────────
# 3. ENGLISH GRADE 1
# ─────────────────────────────────────────────────────────────────────────────
def translate_braille_to_english_g1(braille_text):
    """English Grade 1 — Unified English Braille (UEB), letter-for-letter."""
    braille_map = {
        '⠀': ' ',
        '⠁': 'a', '⠃': 'b', '⠉': 'c', '⠙': 'd', '⠑': 'e',
        '⠋': 'f', '⠛': 'g', '⠓': 'h', '⠊': 'i', '⠚': 'j',
        '⠅': 'k', '⠇': 'l', '⠍': 'm', '⠝': 'n', '⠕': 'o',
        '⠏': 'p', '⠟': 'q', '⠗': 'r', '⠎': 's', '⠞': 't',
        '⠥': 'u', '⠧': 'v', '⠺': 'w', '⠭': 'x', '⠽': 'y',
        '⠵': 'z',
    }
    num_map = {
        '⠁': '1', '⠃': '2', '⠉': '3', '⠙': '4', '⠑': '5',
        '⠋': '6', '⠛': '7', '⠓': '8', '⠊': '9', '⠚': '0',
    }
    extra_map = {
        '⠂':   ',',  '⠆':   ';',  '⠒':   ':',   '⠲':  '.',
        '⠖':   '!',  '⠦':   '?',  '⠤':   '-',   '⠶':  '"',
        '⠄':   "'",  '⠘':   '#',  '⠨':   '$',
        '⠠⠤': '—',  '⠈⠲': '…',
    }
    G1_IND = '⠰'   # Grade-1 passthrough indicator

    translated_lines = []
    for line in braille_text.split('\n'):
        translated_line = ""
        capital_mode = False
        number_mode  = False
        i = 0
        while i < len(line):
            char = line[i]
            if char == G1_IND:
                i += 1
                continue
            if char == CAPITAL_INDICATOR:
                capital_mode = True
                i += 1
                continue
            if char == NUMBER_INDICATOR:
                number_mode = True
                i += 1
                continue
            if number_mode:
                if char in num_map:
                    translated_line += num_map[char]
                    i += 1
                    continue
                else:
                    number_mode = False
            # Two-cell sequences first
            two = line[i:i+2]
            if two in extra_map:
                translated_line += extra_map[two]
                i += 2
                continue
            if char in braille_map:
                letter = braille_map[char]
                if capital_mode:
                    letter = letter.upper()
                    capital_mode = False
                translated_line += letter
            elif char in extra_map:
                translated_line += extra_map[char]
            else:
                translated_line += char
            i += 1
        translated_lines.append(translated_line)
    return "\n".join(translated_lines)


# ─────────────────────────────────────────────────────────────────────────────
# 4. ENGLISH GRADE 2
# ─────────────────────────────────────────────────────────────────────────────
def translate_braille_to_english_g2(braille_text, single_cell_mode=False):
    """English Grade 2 — UEB with whole-word and part-word contractions."""

    # Whole-word contractions (standalone braille cell = full word)
    word_contractions = {
        '⠃':  'but',        '⠉':  'can',        '⠙':  'do',
        '⠑':  'every',      '⠋':  'from',        '⠛':  'go',
        '⠓':  'have',       '⠚':  'just',        '⠅':  'knowledge',
        '⠇':  'like',       '⠍':  'more',        '⠝':  'not',
        '⠏':  'people',      '⠟':  'quite',
        '⠗':  'rather',     '⠎':  'so',          '⠞':  'that',
        '⠥':  'us',         '⠧':  'very',        '⠺':  'will',
        '⠭':  'it',         '⠽':  'you',         '⠵':  'as',
        '⠯':  'and',        '⠿':  'for',         '⠷':  'of',
        '⠮':  'the',        '⠾':  'with',        
        '⠡':  'child',      '⠩':  'shall',      '⠹':  'this',        
        '⠱':  'which',      '⠳':  'out',         '⠌':  'still',
        '⠢':  'enough',     '⠔':  'in',          '⠆':  'be',
    }

    # Part-word contractions (greedy longest-match within a word)
    part_contractions = {
        # Single-cell strong groupsigns
        '⠡': 'ch',
        '⠩': 'sh',
        '⠹': 'th',
        '⠱': 'wh',
        '⠳': 'ou',
        '⠪': 'ow',
        '⠜': 'ar',
        '⠫': 'ed',
        '⠻': 'er',
        '⠬': 'ing',
        '⠌': 'st',
        '⠣': 'gh',
        '⠯': 'and',
        '⠿': 'for',
        '⠷': 'of',
        '⠮': 'the',
        '⠾': 'with',
        '⠔': 'in',
        '⠢': 'en',
    }

    braille_map = {
        '⠀': ' ',
        '⠁': 'a', '⠃': 'b', '⠉': 'c', '⠙': 'd', '⠑': 'e',
        '⠋': 'f', '⠛': 'g', '⠓': 'h', '⠊': 'i', '⠚': 'j',
        '⠅': 'k', '⠇': 'l', '⠍': 'm', '⠝': 'n', '⠕': 'o',
        '⠏': 'p', '⠟': 'q', '⠗': 'r', '⠎': 's', '⠞': 't',
        '⠥': 'u', '⠧': 'v', '⠺': 'w', '⠭': 'x', '⠽': 'y',
        '⠵': 'z',
    }

    num_map = {
        '⠁': '1', '⠃': '2', '⠉': '3', '⠙': '4', '⠑': '5',
        '⠋': '6', '⠛': '7', '⠓': '8', '⠊': '9', '⠚': '0',
    }

    extra_map = {
        '⠂': ',', '⠆': ';', '⠒': ':', '⠲': '.', '⠖': '!',
        '⠦': '?', '⠤': '-', '⠶': '"', '⠄': "'",
    }

    def decode_token(token):
        if not token:
            return ""
        
        # 1. Count leading capitalization indicators
        cap_count = 0
        i = 0
        while i < len(token) and token[i] == CAPITAL_INDICATOR:
            cap_count += 1
            i += 1
            
        remaining_token = token[i:]
        if not remaining_token:
            return CAPITAL_INDICATOR * cap_count
            
        # 2. Check for whole-word contractions (wordsigns) on the remaining part (only if not in single_cell_mode)
        if not single_cell_mode:
            word = word_contractions.get(remaining_token, None)
            if word is not None:
                if cap_count == 1:
                    word = word.capitalize()
                elif cap_count >= 2:
                    word = word.upper()
                return word

        # 3. Decode character-by-character with contraction matching
        result = ""
        chars = list(remaining_token)
        j = 0
        number_mode = False
        capital_mode = False
        
        while j < len(chars):
            c = chars[j]
            
            if c == CAPITAL_INDICATOR:
                capital_mode = True
                j += 1
                continue
                
            if c == NUMBER_INDICATOR:
                number_mode = True
                j += 1
                continue
                
            if number_mode:
                if c in num_map:
                    result += num_map[c]
                    j += 1
                    continue
                else:
                    number_mode = False
                    
            # Check for part-word contractions (checking sizes 3, 2, 1)
            matched = False
            for length in [3, 2, 1]:
                if j + length <= len(chars):
                    key = "".join(chars[j:j+length])
                    if key in part_contractions:
                        val = part_contractions[key]
                        if capital_mode:
                            val = val.capitalize()
                            capital_mode = False
                        result += val
                        j += length
                        matched = True
                        break
            if matched:
                continue
                
            # Fallback to literal maps
            if c in braille_map:
                letter = braille_map[c]
                if capital_mode:
                    letter = letter.upper()
                    capital_mode = False
                result += letter
            elif c in extra_map:
                result += extra_map[c]
            else:
                result += c
            j += 1
            
        # 4. Apply leading capitalization indicators
        if cap_count == 1:
            if result:
                result = result[0].upper() + result[1:]
        elif cap_count >= 2:
            result = result.upper()
            
        return result

    translated_lines = []
    for line in braille_text.split('\n'):
        tokens = line.split('⠀')  # Split by Braille space (U+2800)
        output_tokens = [decode_token(t) for t in tokens]
        translated_lines.append(" ".join(output_tokens))
    return "\n".join(translated_lines)


# ─────────────────────────────────────────────────────────────────────────────
# 5. RUSSIAN
# ─────────────────────────────────────────────────────────────────────────────
def translate_braille_to_russian(braille_text):
    """Russian Braille — GOST R 58511-2019 / classical Russian Braille."""
    braille_map = {
        '⠀': ' ',
        # 33 Cyrillic letters
        '⠁': 'а', '⠃': 'б', '⠺': 'в', '⠛': 'г', '⠙': 'д',
        '⠑': 'е', '⠡': 'ё', '⠚': 'ж', '⠵': 'з', '⠊': 'и',
        '⠯': 'й', '⠅': 'к', '⠇': 'л', '⠍': 'м', '⠝': 'н',
        '⠕': 'о', '⠏': 'п', '⠗': 'р', '⠎': 'с', '⠞': 'т',
        '⠥': 'у', '⠋': 'ф', '⠓': 'х', '⠉': 'ц', '⠟': 'ч',
        '⠱': 'ш', '⠭': 'щ', '⠷': 'ъ', '⠮': 'ы', '⠾': 'ь',
        '⠿': 'э', '⠳': 'ю', '⠫': 'я',
    }
    num_map = {
        '⠁': '1', '⠃': '2', '⠉': '3', '⠙': '4', '⠑': '5',
        '⠋': '6', '⠛': '7', '⠓': '8', '⠊': '9', '⠚': '0',
    }
    extra_map = {
        '⠂':   ',',  '⠆':   ';',  '⠒':   ':',  '⠲':  '.',
        '⠖':   '!',  '⠦':   '?',  '⠤':   '-',  '⠶':  '"',
        '⠄':   "'",  '⠐':   ' ',  '⠰':   ' ',
        '⠜':   'ъ',  '⠌':   'ь',  '⠈':   '«',  '⠘':  '»',
        '⠠⠤': '—',
    }

    translated_lines = []
    for line in braille_text.split('\n'):
        translated_line = ""
        capital_mode = False
        number_mode  = False
        i = 0
        while i < len(line):
            char = line[i]
            two = line[i:i+2]
            if two == '⠠⠤':
                translated_line += '—'; i += 2; continue
            if char == CAPITAL_INDICATOR:
                capital_mode = True; i += 1; continue
            if char == NUMBER_INDICATOR:
                number_mode = True; i += 1; continue
            if number_mode:
                if char in num_map:
                    translated_line += num_map[char]; i += 1; continue
                else:
                    number_mode = False
            if char in braille_map:
                letter = braille_map[char]
                if capital_mode:
                    letter = letter.upper()
                    capital_mode = False
                translated_line += letter
            elif char in extra_map:
                translated_line += extra_map[char]
            else:
                translated_line += char
            i += 1
        translated_lines.append(translated_line)
    return "\n".join(translated_lines)


# ════════════════════════════════════════════════════════════════════════════════
# LANGUAGE SELECTOR — interactive prompt at runtime
# ════════════════════════════════════════════════════════════════════════════════

# ── Registry ─────────────────────────────────────────────────────────────────
translators = {
    "1": ("Arabic     — عربي",              translate_braille_to_arabic),
    "2": ("French     — Français",           translate_braille_to_french),
    "3": ("English G1 — Grade 1 (literal)",  translate_braille_to_english_g1),
    "4": ("English G2 — Grade 2 (contrac.)", translate_braille_to_english_g2),
    "5": ("Russian    — Русский",            translate_braille_to_russian),
}

lang_keys = {
    "1": "arabic",
    "2": "french",
    "3": "english_g1",
    "4": "english_g2",
    "5": "russian",
}



# ── Gemini Correction ─────────────────────────────────────────────────────────
_gemini_client = None

def _get_client():
    """Lazily initialise the Gemini client using the env-var key."""
    global _gemini_client
    if _gemini_client is None:
        key = os.environ.get("GEMINI_API_KEY", GEMINI_API_KEY)
        if not key:
            raise RuntimeError("GEMINI_API_KEY environment variable is not set.")
        _gemini_client = genai.Client(api_key=key)
    return _gemini_client


def correct_text_with_gemini(input_text):
    prompt = """You are correcting text extracted from a Braille recognition system.
The text may contain Arabic, French, English, or Russian.

Fix all errors so the text is fully readable and correct in each language.
Use your full language knowledge to identify and fix mistakes in whichever
language each part is written in.
Preserve diacritics unless one is clearly on the wrong letter.

For blank answer slots: replace with -----
A blank slot is either an explicit filler sequence (ءءءءء, -----, ......, etc.)
or a space that context reveals as an answer area in a fill-in-the-gap exercise.
Only apply this to actual answer spaces — continuous readable text stays as text.

Output the corrected text only, no comments or explanations.

TEXT TO CORRECT:
""" + input_text


    config = types.GenerateContentConfig(
        temperature=0.0,
        max_output_tokens=2048,
    )

    max_retries = 3
    for attempt in range(max_retries):
        try:
            client = _get_client()
            print(f"\U0001f680 Sending to Gemini (attempt {attempt + 1}/{max_retries})...")
            t0 = time.time()

            response = client.models.generate_content(
                model="gemini-2.5-flash-lite",
                contents=prompt,
                config=config,
            )

            elapsed = time.time() - t0
            if response.text:
                print(f"\u2705 Gemini success! ({elapsed:.2f}s)")
                return response.text.strip()

        except Exception as e:
            err = str(e)
            if "429" in err or "RESOURCE_EXHAUSTED" in err:
                wait = 3 * (attempt + 1)
                print(f"\u26a0\ufe0f  Rate limit hit. Retrying in {wait}s... (attempt {attempt + 1}/{max_retries})")
                time.sleep(wait)
            elif "503" in err or "UNAVAILABLE" in err or "experiencing high demand" in err:
                wait = 3 * (attempt + 1)
                print(f"\u26a0\ufe0f  Google servers overloaded (503/UNAVAILABLE). Retrying in {wait}s... (attempt {attempt + 1}/{max_retries})")
                time.sleep(wait)
            else:
                print(f"\u274c Gemini error: {err}")
                break

    print("\u26a0\ufe0f  Gemini unavailable - returning raw translation.")
    return input_text


# ── Dispatcher ───────────────────────────────────────────────────────────────
def translate_results(braille_text: str, language: str = "arabic"):
    """
    Translates braille text to the specified language, then applies Gemini correction.
    Returns (translated_text, gemini_corrected_text)
    """
    lang = language.lower()

    if lang == "arabic":
        translated = translate_braille_to_arabic(braille_text)
        translated = translated.replace("\u064f\u0622", "\u064f\u0647\u0627").replace("\u0627\u0650\u0651\u062a\u0626\u062f", "\u0627\u062a\u062e\u0630")
    elif lang == "french":
        translated = translate_braille_to_french(braille_text)
    elif lang == "english_g1":
        translated = translate_braille_to_english_g1(braille_text)
    elif lang == "english_g2":
        translated = translate_braille_to_english_g2(braille_text)
    elif lang == "russian":
        translated = translate_braille_to_russian(braille_text)
    elif lang == "raw":
        # Raw mode: bypass translation and Gemini correction entirely
        print("🔵 Raw mode selected — skipping translation and Gemini correction.")
        return braille_text, ""
    else:
        translated = translate_braille_to_arabic(braille_text)

    key = os.environ.get("GEMINI_API_KEY", GEMINI_API_KEY)
    if key:
        corrected = correct_text_with_gemini(translated)
    else:
        corrected = "Gemini API key not configured. Unable to perform correction."

    return translated, corrected


def translate_only(braille_text: str, language: str = "arabic", single_cell_mode: bool = None) -> str:
    """
    Translates braille text to the specified language using the dictionary ONLY.
    Does NOT call the Gemini API. Use this for fast, synchronous translation
    when Gemini correction will be done separately as an async step.
    Returns translated_text string.
    """
    lang = language.lower()

    if single_cell_mode is None:
        single_cell_mode = (len(braille_text) == 1)

    if lang == "arabic":
        translated = translate_braille_to_arabic(braille_text)
        translated = translated.replace("\u064f\u0622", "\u064f\u0647\u0627").replace("\u0627\u0650\u0651\u062a\u0626\u062f", "\u0627\u062a\u062e\u0630")
    elif lang == "french":
        translated = translate_braille_to_french(braille_text)
    elif lang == "english_g1":
        translated = translate_braille_to_english_g1(braille_text)
    elif lang == "english_g2":
        translated = translate_braille_to_english_g2(braille_text, single_cell_mode=single_cell_mode)
    elif lang == "russian":
        translated = translate_braille_to_russian(braille_text)
    elif lang == "raw":
        return braille_text  # Raw mode: return braille as-is
    else:
        translated = translate_braille_to_arabic(braille_text)

    return translated


# ── Auto-Detect Language ──────────────────────────────────────────────────────
def auto_detect_and_translate(braille_text: str):
    """
    Transcribes Braille Unicode with all available dictionaries and sends a
    single Gemini disambiguation prompt to identify the best-matching language.

    Returns:
        (detected_lang_key: str, raw_translation: str, gemini_corrected: str)

    Where detected_lang_key is one of:
        "arabic" | "french" | "english_g1" | "english_g2" | "russian" | "raw"

    "raw" means no valid language was identified — caller should display
    only the Braille Unicode.
    """
    # 1. Translate with every dictionary
    candidates = {
        "arabic":     translate_braille_to_arabic(braille_text),
        "french":     translate_braille_to_french(braille_text),
        "english_g1": translate_braille_to_english_g1(braille_text),
        "english_g2": translate_braille_to_english_g2(braille_text),
        "russian":    translate_braille_to_russian(braille_text),
    }

    # 2. Build a single disambiguation prompt
    candidate_block = "\n".join(
        f"[{lang}]: {text[:600]}"   # cap per-candidate to keep prompt short
        for lang, text in candidates.items()
    )

    prompt = f"""You are analyzing candidate transcriptions of a Braille sheet to identify the correct language.

The candidates are:
{candidate_block}

Task:
Evaluate each candidate above. Identify if exactly ONE candidate is a cohesive, readable, and meaningful human text in its target language.

Rules:
1. If ONE candidate is clearly readable and makes perfect sense, return its key: "arabic", "french", "english_g1", "english_g2", or "russian".
2. If ALL candidates are mostly gibberish, random letter noise, scattered punctuation, disjointed words, or contain raw untranslated Braille Unicode symbols (such as ⠛, ⠪, ⠈, ⠬, ⠠, ⠼), you MUST return "none".
3. Default to "none" if there is any doubt, if the text is noisy dot output, or if it consists of meaningless character sequences. Never choose a language key just because a candidate uses that language's alphabet/script; the words themselves MUST form actual, coherent, and readable human sentences.

Format:
Return a single-line JSON object (no markdown, no code fences):
{{"reasoning": "<1-sentence quality assessment>", "language": "<chosen_key_or_none>", "corrected": "<corrected_text_or_empty>"}}
"""

    key = os.environ.get("GEMINI_API_KEY", GEMINI_API_KEY)
    if not key:
        print("⚠️  Auto-detect: GEMINI_API_KEY not set — falling back to raw mode.")
        return "raw", braille_text, ""

    config = types.GenerateContentConfig(
        temperature=0.0,
        max_output_tokens=1024,
    )

    max_retries = 3
    for attempt in range(max_retries):
        try:
            client = _get_client()
            print(f"🔍 Auto-detect: Gemini attempt {attempt + 1}/{max_retries}…")
            t0 = time.time()
            response = client.models.generate_content(
                model="gemini-2.5-flash-lite",
                contents=prompt,
                config=config,
            )
            elapsed = time.time() - t0

            raw_response = (response.text or "").strip()
            print(f"✅ Auto-detect Gemini response ({elapsed:.2f}s): {raw_response[:120]}")

            # Strip markdown code fences if present
            import re as _re
            cleaned = _re.sub(r"^```[a-z]*\n?|```$", "", raw_response, flags=_re.MULTILINE).strip()

            import json as _json
            parsed = _json.loads(cleaned)
            detected_lang = parsed.get("language", "none").strip().lower()
            corrected = parsed.get("corrected", "").strip()

            if detected_lang == "none" or detected_lang not in candidates:
                print("⚠️  Auto-detect: No valid language identified — raw fallback.")
                return "raw", braille_text, ""

            raw_translation = candidates[detected_lang]
            print(f"🌐 Auto-detect: identified language = {detected_lang}")
            return detected_lang, raw_translation, corrected

        except Exception as e:
            err = str(e)
            if "429" in err or "RESOURCE_EXHAUSTED" in err:
                wait = 3 * (attempt + 1)
                print(f"⚠️  Rate limit hit. Retrying in {wait}s... (attempt {attempt + 1}/{max_retries})")
                time.sleep(wait)
            elif "503" in err or "UNAVAILABLE" in err or "experiencing high demand" in err:
                wait = 3 * (attempt + 1)
                print(f"⚠️  Google servers overloaded (503/UNAVAILABLE). Retrying in {wait}s... (attempt {attempt + 1}/{max_retries})")
                time.sleep(wait)
            else:
                print(f"❌ Auto-detect Gemini error: {err}")
                break

    print("⚠️  Auto-detect: Gemini unavailable — raw fallback.")
    return "raw", braille_text, ""
