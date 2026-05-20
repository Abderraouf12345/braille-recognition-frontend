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
def translate_braille_to_english_g2(braille_text):
    """English Grade 2 — UEB with whole-word and part-word contractions."""

    # Whole-word contractions (standalone braille cell = full word)
    word_contractions = {
        '⠃':  'but',        '⠉':  'can',        '⠙':  'do',
        '⠑':  'every',      '⠋':  'from',        '⠛':  'go',
        '⠓':  'have',       '⠚':  'just',        '⠅':  'knowledge',
        '⠇':  'like',       '⠍':  'more',        '⠝':  'not',
        '⠕':  'o',          '⠏':  'people',      '⠟':  'quite',
        '⠗':  'rather',     '⠎':  'so',          '⠞':  'that',
        '⠥':  'us',         '⠧':  'very',        '⠺':  'will',
        '⠭':  'it',         '⠽':  'you',         '⠵':  'as',
        '⠯':  'and',        '⠿':  'for',         '⠷':  'of',
        '⠮':  'the',        '⠾':  'with',        '⠡':  'child',
        '⠩':  'shall',      '⠹':  'this',        '⠱':  'which',
        '⠫':  'out',        '⠻':  'still',       '⠳':  'ou',
        '⠣':  'gh',         '⠜':  'ar',          '⠌':  'st',
        '⠬':  'ing',
    }
    # Part-word contractions (greedy longest-match within a word)
    part_contractions = {
        '⠁⠃': 'ab',    '⠁⠉': 'ac',    '⠁⠋': 'af',    '⠁⠇': 'al',
        '⠁⠍': 'am',    '⠁⠝': 'an',    '⠃⠇': 'ble',   '⠉⠊': 'ci',
        '⠉⠕': 'com',   '⠙⠊': 'dis',   '⠑⠝': 'en',    '⠑⠗': 'er',
        '⠋⠥': 'ful',   '⠛⠝': 'gn',    '⠊⠝': 'in',    '⠇⠑⠎': 'less',
        '⠇⠽': 'ly',    '⠍⠑⠝': 'ment', '⠝⠑⠎': 'ness', '⠕⠥': 'ous',
        '⠎⠓': 'sh',    '⠞⠓': 'th',    '⠺⠓': 'wh',
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

    def decode_token(chars):
        token_str = "".join(chars)
        if token_str in word_contractions:
            return word_contractions[token_str]
        result = ""
        i = 0
        while i < len(chars):
            matched = False
            for length in [3, 2]:
                key = "".join(chars[i:i+length])
                if key in part_contractions:
                    result += part_contractions[key]
                    i += length
                    matched = True
                    break
            if not matched:
                result += braille_map.get(chars[i], chars[i])
                i += 1
        return result

    translated_lines = []
    for line in braille_text.split('\n'):
        tokens = line.split('⠀')
        output_tokens = []
        for token in tokens:
            chars = list(token)
            capital = False
            number  = False
            out_chars = []
            i = 0
            while i < len(chars):
                c = chars[i]
                if c == CAPITAL_INDICATOR:
                    capital = True;  i += 1; continue
                if c == NUMBER_INDICATOR:
                    number  = True;  i += 1; continue
                if number and c in num_map:
                    out_chars.append(num_map[c]); i += 1; continue
                else:
                    number = False
                if c in braille_map:
                    ch = braille_map[c]
                    if capital:
                        ch = ch.upper(); capital = False
                    out_chars.append(ch)
                elif c in extra_map:
                    out_chars.append(extra_map[c])
                else:
                    out_chars.append(c)
                i += 1
            # Try contraction resolution on the raw token
            resolved = word_contractions.get(token, decode_token(list(token)))
            # Apply capitalisation flag if first char was capital
            output_tokens.append(resolved)
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
                wait = 65 * (attempt + 1)
                print(f"\u26a0\ufe0f  Rate limit hit. Waiting {wait}s... (attempt {attempt + 1}/{max_retries})")
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


def translate_only(braille_text: str, language: str = "arabic") -> str:
    """
    Translates braille text to the specified language using the dictionary ONLY.
    Does NOT call the Gemini API. Use this for fast, synchronous translation
    when Gemini correction will be done separately as an async step.
    Returns translated_text string.
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

    prompt = f"""You are a language expert analysing candidate transcriptions of a Braille document.
Each candidate was produced by a different Braille dictionary (Arabic, French, English Grade 1,
English Grade 2, Russian). Exactly one candidate (or none) represents a valid, semantically
coherent text in that language.

Your task:
1. Identify which single candidate is the most semantically valid/readable text in its language.
2. Return a JSON object on a single line — NO markdown, NO code fences, NO extra text.

Format:
{{"language": "<key>", "corrected": "<corrected text>"}}

Where:
- "language" is ONE of: arabic, french, english_g1, english_g2, russian
- OR "none" if NO candidate is semantically valid
- "corrected" is the lightly corrected version of the winning candidate
  (fix obvious OCR/Braille errors; preserve the original language and meaning)
- If language is "none", set "corrected" to ""

Candidates:
{candidate_block}
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
                wait = 65 * (attempt + 1)
                print(f"⚠️  Rate limit hit. Waiting {wait}s… (attempt {attempt + 1}/{max_retries})")
                time.sleep(wait)
            else:
                print(f"❌ Auto-detect Gemini error: {err}")
                break

    print("⚠️  Auto-detect: Gemini unavailable — raw fallback.")
    return "raw", braille_text, ""
