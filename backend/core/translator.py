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


# ─────────────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────
# 6. CHINESE  (现行盲文 / Mainland Chinese Braille → Hanyu Pinyin)
# ─────────────────────────────────────────────────────────────────────────────
def translate_braille_to_chinese(braille_text):
    """
    Mainland Chinese Braille (现行盲文) — Phonetic Pinyin decoder.

    Each syllable: [Initial?] + [Final] + [Tone? (skipped)]
    Output: Hanyu Pinyin text. Gemini then converts to Simplified Chinese (Hanzi).

    Bug-fixes vs v1:
      - Core phonetic mapping tables updated to standard Mainland Chinese Braille.
      - Core finals mapped unambiguously. Tone marks (⠂, ⠄, ⠆) skipped correctly.
      - Numeric mode (⠼) supported, decoding digit sequences cleanly.
      - ü → u after j/q/x (standard Pinyin: xue not xüe).
      - Punctuation / indicator cells mapped correctly.
    """
    # ── 18 Initial cells (声母) ────────────────────────────────────────────
    INITIALS = {
        '⠃': 'b',  '⠏': 'p',  '⠍': 'm',  '⠋': 'f',
        '⠙': 'd',  '⠞': 't',  '⠝': 'n',  '⠇': 'l',
        '⠛': 'g',  '⠅': 'k',  '⠓': 'h',   # also j/q/x before i/ü
        '⠌': 'zh', '⠟': 'ch', '⠱': 'sh', '⠚': 'r',
        '⠵': 'z',  '⠉': 'c',  '⠎': 's',
    }
    PALATAL_CELLS = {'⠛', '⠅', '⠓'}
    PALATAL_MAP   = {'g': 'j', 'k': 'q', 'h': 'x'}

    # Finals starting with i/ü to trigger palatalization of g/k/h -> j/q/x
    PALATAL_FINALS = {
        '⠊', '⠫', '⠑', '⠜', '⠩', '⠭', '⠡', '⠣', '⠹', '⠳',
        '⠬', '⠾', '⠯', '⠸'
    }

    # Unambiguous finals (same reading regardless of preceding initial)
    FINALS_UNAMB = {
        '⠁': 'a',
        '⠢': 'e',
        '⠕': 'uo', # o after b/p/m/f, uo elsewhere (handled contextually)
        '⠪': 'ai',
        '⠖': 'ao',
        '⠮': 'ei',
        '⠷': 'ou',
        '⠧': 'an',
        '⠴': 'en',
        '⠦': 'ang',
        '⠼': 'eng',
        '⠗': 'er',

        '⠊': 'i',
        '⠫': 'ia',
        '⠑': 'ie',
        '⠜': 'iao',
        '⠩': 'ian',
        '⠭': 'iang',
        '⠡': 'ing',  # dots 1-6   (was incorrectly 'in')
        '⠣': 'in',   # dots 1-2-6 (was incorrectly 'ing')
        '⠹': 'iong',
        '⠳': 'iu',

        '⠥': 'u',
        '⠿': 'ua',
        '⠽': 'uai',
        '⠺': 'ui',
        '⠻': 'uan',
        '⠒': 'un',
        '⠶': 'uang',
        '⠲': 'ong',

        '⠬': 'ü',
        '⠾': 'üe',
        '⠯': 'üan',
        '⠸': 'ün',
    }

    SILENT_I_INITIALS = {'zh', 'ch', 'sh', 'r', 'z', 'c', 's'}

    ZERO_INIT = {
        'a':'a',    'ai':'ai',   'an':'an',    'ang':'ang',  'ao':'ao',
        'e':'e',    'ei':'ei',   'en':'en',    'eng':'eng',  'er':'er',
        'i':'yi',   'ia':'ya',   'ian':'yan',  'iang':'yang', 'iao':'yao',
        'ie':'ye',  'in':'yin',  'ing':'ying', 'iong':'yong', 'iu':'you',
        'o':'o',    'ong':'weng',
        'ou':'ou',
        'u':'wu',   'ua':'wa',   'uai':'wai',  'uan':'wan',  'uang':'wang',
        'ui':'wei', 'un':'wen',  'uo':'wo',
        'ü':'yu',   'üan':'yuan', 'üe':'yue',  'ün':'yun',
    }

    # ── Abbreviations (现行盲文简写词) ──────────────────────────────
    SINGLE_ABBREV = {
        'b': 'bu',    # 不
        'd': 'de',    # 的
        'g': 'ge',    # 个
        'h': 'he',    # 和
        't': 'ta',    # 他/她/它
        'l': 'le',    # 了
        'p': 'pi',    # 批 / 平
        'f': 'fa',    # 发 / 否 / 佛
        'm': 'men',   # 们
        'n': 'na',    # 那 / 呢
        'zh': 'zhe',  # 这
        's': 'shi',   # 是
        'r': 'ri',    # 日
        'c': 'cong',  # 从
        'z': 'zai',   # 在
    }

    MULTI_ABBREV = {
        ('t', 'b'): 'te bie',      # 特别
        ('b', 'c'): 'bi ci',       # 彼此
        ('g', 'm'): 'ge ming',     # 革命
        ('zh', 'zh'): 'zheng zhi', # 政治
    }


    NUM_MAP = {
        '⠁': '1', '⠃': '2', '⠉': '3', '⠙': '4', '⠑': '5',
        '⠋': '6', '⠛': '7', '⠓': '8', '⠊': '9', '⠚': '0'
    }

    # Two-cell punctuation
    TWO_PUNCT = {
        '⠐⠆': '。', '⠐⠄': '，', '⠐⠂': '、',
        '⠒⠒': '：', '⠰⠦': '？', '⠰⠖': '！',
        '⠰⠤': '——', '⠠⠤': '——', '⠰⠆': '；',
        '⠦⠴': '“”', '⠘⠦': '“',  '⠸⠴': '”',
        '⠐⠤': '…',  '⠠⠠': '《', '⠠⠄': '》',
        '⠐⠦': '（', '⠐⠴': '）',   # parentheses
        '⠠⠦': '"', '⠠⠴': '"',    # alternative quote form
    }

    # Single-cell: map to symbol or '' to discard
    ONE_SP = {
        '⠀': ' ',
        '⠤': '-',
        '⠐': '',   '⠰': '',
        '⠈': '',   '⠘': '',
        '⠠': '',
        # '⠼' is handled contextually in number mode
        '⠂': '',   '⠄': '',   '⠆': '',
    }

    def _syl(init, fin):
        """Build Pinyin syllable; after j/q/x drop diaeresis on ü."""
        if init in ('j', 'q', 'x'):
            fin = fin.replace('ü', 'u')
        return init + fin

    def _decode(chars):
        out = []
        i, n = 0, len(chars)
        number_mode = False

        while i < n:
            c = chars[i]

            # ── number mode processing ─────────────────────────────────────
            if number_mode:
                if c in NUM_MAP:
                    out.append(NUM_MAP[c])
                    i += 1
                    continue
                else:
                    number_mode = False

            # ── number indicator ───────────────────────────────────────────
            if c == '⠼':
                if i + 1 < n and chars[i+1] in NUM_MAP:
                    number_mode = True
                    i += 1
                    continue

            # two-cell punct
            two = c + chars[i+1] if i+1 < n else ''
            if two in TWO_PUNCT:
                out.append(TWO_PUNCT[two]); i += 2; continue
            # single-cell special
            if c in ONE_SP:
                s = ONE_SP[c]
                if s: out.append(s)
                i += 1; continue
            # Initial
            if c in INITIALS:
                init_raw = INITIALS[c]; i += 1
                if i >= n or chars[i] not in FINALS_UNAMB:
                    # Check for multi-cell abbreviations (two consecutive isolated initials)
                    if i < n and chars[i] in INITIALS:
                        next_init = INITIALS[chars[i]]
                        # ensure the next initial is also isolated
                        if i + 1 >= n or chars[i+1] not in FINALS_UNAMB:
                            combo = (init_raw, next_init)
                            if combo in MULTI_ABBREV:
                                out.append(MULTI_ABBREV[combo])
                                i += 1  # consume the second initial
                                continue

                    # Single-cell processing
                    if init_raw in SILENT_I_INITIALS:
                        out.append(init_raw + 'i')
                    elif init_raw in SINGLE_ABBREV:
                        out.append(SINGLE_ABBREV[init_raw])
                    else:
                        out.append(init_raw)
                    continue
                fc = chars[i]
                is_pal = c in PALATAL_CELLS and fc in PALATAL_FINALS
                init_py = PALATAL_MAP.get(init_raw, init_raw) if is_pal else init_raw
                # resolve final
                fin = FINALS_UNAMB[fc]
                if fc == '⠕':
                    fin = 'o' if init_py in ('b','p','m','f') else 'uo'
                i += 1
                if i < n and chars[i] in ('⠂', '⠄', '⠆'): i += 1
                out.append(_syl(init_py, fin) if fin else init_py)
                continue
            # Zero-initial final
            if c in FINALS_UNAMB:
                fin = FINALS_UNAMB[c]; i += 1
                if i < n and chars[i] in ('⠂', '⠄', '⠆'): i += 1
                out.append(ZERO_INIT.get(fin, fin)); continue
            i += 1  # unknown: skip

        # Join tokens with space except for consecutive digits/punctuation
        result = []
        for token in out:

            if not result:
                result.append(token)
            else:
                last = result[-1]
                if (last.isdigit() and token.isdigit()) or last == ' ' or token == ' ' or \
                   last in TWO_PUNCT.values() or token in TWO_PUNCT.values() or \
                   last in ONE_SP.values() or token in ONE_SP.values():
                    result.append(token)
                else:
                    result.append(' ' + token)
        return ''.join(result)

    lines = []
    for line in braille_text.split('\n'):
        lines.append('' if not line.strip() else _decode(list(line)))
    return '\n'.join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# 7. CHINESE  (汉语双拼盲文 / Two-Cell Chinese Braille → Hanyu Pinyin)
# ─────────────────────────────────────────────────────────────────────────────
def translate_braille_to_shuangpin(braille_text):
    """
    Two-Cell Chinese Braille (汉语双拼盲文 Shuangpin) — Phonetic Pinyin decoder.
    Every syllable is strictly two cells: Cell 1 (Onset+Medial) + Cell 2 (Rime+Tone).
    """
    ONSETS = {
        '⠾': '',   '⠊': 'b',  '⠦': 'p',  '⠪': 'm',  '⠖': 'f',
        '⠌': 'd',  '⠎': 't',  '⠏': 'n',  '⠇': 'l',  '⠁': 'g',
        '⠅': 'k',  '⠃': 'h',  '⠉': 'zh', '⠍': 'ch', '⠋': 'sh', '⠔': 'r',
        '⠒': 'y',  '⠚': 'bi', '⠶': 'pi', '⠺': 'mi',
        '⠜': 'di', '⠞': 'ti', '⠟': 'ni', '⠗': 'li',
        '⠑': 'ji',  '⠕': 'qi',  '⠓': 'xi',  '⠙': 'z',  '⠝': 'c',  '⠛': 's',
        '⠢': 'w',  '⠬': 'du', '⠮': 'tu', '⠯': 'nu', '⠧': 'lu',
        '⠡': 'gu', '⠥': 'ku', '⠣': 'hu', '⠩': 'zhu','⠭': 'chu','⠫': 'shu','⠴': 'ru',
        '⠲': 'yu', '⠿': 'nü', '⠷': 'lü', '⠱': 'ju', '⠵': 'qu', '⠳': 'xu',
        '⠹': 'zu', '⠽': 'cu', '⠻': 'su'
    }

    RIMES = {
        '⠃': 'i/u/ü', '⠚': 'a', '⠊': 'e/o', '⠛': 'ai', '⠌': 'ei', '⠓': 'ao', '⠉': 'ou', '⠋': 'an', '⠁': 'en', '⠙': 'ang', '⠑': 'eng',
        '⠇': 'i/u/ü', '⠞': 'a', '⠎': 'e/o', '⠟': 'ai', '⠜': 'ei', '⠗': 'ao', '⠍': 'ou', '⠏': 'an', '⠅': 'en', '⠝': 'ang', '⠕': 'eng',
        '⠣': 'i/u/ü', '⠺': 'a', '⠪': 'e/o', '⠻': 'ai', '⠬': 'ei', '⠳': 'ao', '⠩': 'ou', '⠫': 'an', '⠡': 'en', '⠹': 'ang', '⠱': 'eng',
        '⠧': 'i/u/ü', '⠾': 'a', '⠮': 'e/o', '⠿': 'ai', '⠼': 'ei', '⠷': 'ao', '⠭': 'ou', '⠯': 'an', '⠥': 'en', '⠽': 'ang', '⠵': 'eng',
        '⠆': 'i/u/ü'
    }

    PUNCTUATION = {
        '⠐⠆': '。', '⠐⠄': '？', '⠐⠂': '、', '⠰⠂': '！',
        '⠠⠄': '：', '⠰⠆': '；', '⠐⠐⠐': '……', '⠤': '—',
        '⠰⠄': '「', '⠠⠆': '」', '⠐⠤': '《', '⠤⠂': '》',
        '⠰⠤': '（', '⠤⠆': '）', '⠰': '；',
        '⠐': '，', '⠠': '、'
    }

    CONTRACTIONS = {
        '⠌⠔': 'de',
        '⠉⠔': 'zhe',
        '⠘⠙': 'zai',
        '⠈⠙': 'zai',
        '⠌': 'de',
        '⠜': 'de',
        '⠟': 'ni',
        '⠋': 'shi',
        '⠭': 'you',
        '⠓': 'yao',
        '⠣': 'shi',
        '⠮': 'ye',
        '⠱': 'jiu',
        '⠂': 'men',
        '⠙': 'zai',
        '⠔': 'r',
        '⠇': 'le',
        '⠪': 'me',
        '⠴': 'ne',
        '⠆': 'ba',
        '⠒': 'yi',
        '⠾': 'a',
        '⠁': 'ge',
        '⠊': 'bu',
        '⠦': 'pi',
        '⠖': 'fu',
        '⠎': 'ta',
        '⠏': 'ni',
        '⠅': 'ke',
        '⠃': 'he',
        '⠍': 'chu',
        '⠝': 'ci',
        '⠛': 'suo',
        '⠢': 'wo'
    }

    NUM_MAP = {
        '⠁': '1', '⠃': '2', '⠉': '3', '⠙': '4', '⠑': '5',
        '⠋': '6', '⠛': '7', '⠓': '8', '⠊': '9', '⠚': '0'
    }

    def resolve_syllable(onset, rime):
        # 1. Handle i/u/ü rime
        if rime == 'i/u/ü':
            if onset == 'y': return 'yi'
            if onset == 'w': return 'wu'
            if onset.endswith('i') or onset.endswith('u') or onset.endswith('ü'): 
                return onset
            if onset in ('b', 'p', 'm', 'f'): return onset + 'u'
            if onset in ('zh', 'ch', 'sh', 'r', 'z', 'c', 's'): return onset + 'i'
            return onset + 'i'
            
        # 2. Handle e/o rime
        if rime == 'e/o':
            if onset in ('b', 'p', 'm', 'f', 'w'): return onset + 'o'
            if onset == 'y': return 'ye'
            if onset in ('ju', 'qu', 'xu', 'yu'): return onset[:-1] + 'ue'
            if onset.endswith('i'): return onset + 'e'
            if onset.endswith('ü'): return onset + 'e'
            if onset.endswith('u'): return onset[:-1] + 'uo'
            return onset + 'e'
            
        # 3. Concatenate and apply Pinyin orthography adjustments
        res = onset + rime
        
        # Adjustments for eng group (eng, ing, ong, iong)
        if rime == 'eng':
            if onset == 'y': return 'ying'
            if onset == 'yu': return 'yong'
            if onset in ('ju', 'qu', 'xu'): return onset[:-1] + 'iong'
            if onset.endswith('i'): return onset[:-1] + 'ing'
            if onset.endswith('u'): return onset[:-1] + 'ong'
            
        # Adjustments for en group (en, in, un, ün)
        elif rime == 'en':
            if onset == 'y': return 'yin'
            if onset == 'yu': return 'yun'
            if onset.endswith('i'): return onset[:-1] + 'in'
            if onset.endswith('u'): return onset[:-1] + 'un'
            if onset.endswith('ü'): return onset[:-1] + 'ün'
            
        # Triphthong reductions (iou -> iu, uei -> ui)
        if 'iou' in res:
            res = res.replace('iou', 'iu')
        if 'uei' in res:
            res = res.replace('uei', 'ui')
            
        # Standard duplicate vowel cleaning
        res = res.replace('ii', 'i').replace('uu', 'u').replace('üü', 'ü')
        
        return res

    text = braille_text.replace('⠀', ' ')
    out = []
    i = 0
    number_mode = False
    while i < len(text):
        c1 = text[i]
        
        if number_mode:
            if c1 in NUM_MAP:
                out.append(NUM_MAP[c1])
                i += 1; continue
            else:
                number_mode = False
                
        if c1 == '⠼':
            if i + 1 < len(text) and text[i+1] in NUM_MAP:
                number_mode = True
                i += 1; continue
        
        if c1 == '⠈':
            i += 1; continue
            
        if i + 2 < len(text) and text[i:i+3] in PUNCTUATION:
            out.append(PUNCTUATION[text[i:i+3]])
            i += 3; continue
        if i + 1 < len(text) and text[i:i+2] in PUNCTUATION:
            out.append(PUNCTUATION[text[i:i+2]])
            i += 2; continue
        if c1 in PUNCTUATION:
            out.append(PUNCTUATION[c1])
            i += 1; continue
            
        if c1 in (' ', '\n', '-', '》', '5', '？'):
            out.append(c1)
            i += 1; continue
            
        # 1. Standard Syllable
        if i + 1 < len(text):
            c2 = text[i+1]
            if c1 in ONSETS and c2 in RIMES:
                out.append(resolve_syllable(ONSETS[c1], RIMES[c2]))
                i += 2
                continue
                
        # 2. Contractions & Abbreviations
        if i + 1 < len(text) and text[i:i+2] in CONTRACTIONS:
            out.append(CONTRACTIONS[text[i:i+2]])
            i += 2
            continue
            
        if c1 in CONTRACTIONS:
            val = CONTRACTIONS[c1]
            if val == 'r' and out and out[-1] not in (' ', '\n', '，', '。', '、', '？', '！', '—', '：', '；', '…', '《', '》', '（', '）', '「', '」', '·'):
                out[-1] = out[-1] + 'r'
            else:
                out.append(val)
            i += 1; continue
            
        out.append(c1)
        i += 1
        
    return ' '.join(out).replace('  ', ' ')

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
    "6": ("Chinese    — 中文",               translate_braille_to_chinese),
    "7": ("Shuangpin  — 汉语双拼盲文",         translate_braille_to_shuangpin),
}

lang_keys = {
    "1": "arabic",
    "2": "french",
    "3": "english_g1",
    "4": "english_g2",
    "5": "russian",
    "6": "chinese",
    "7": "shuangpin",
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


def correct_text_with_gemini(input_text, language: str = ""):
    is_chinese = language.lower() in ("chinese", "shuangpin")

    if is_chinese:
        prompt = """You are converting Hanyu Pinyin syllables extracted from a Chinese Braille recognition system into natural Simplified Chinese characters (Hanzi).

The input is space-separated Pinyin syllables decoded from Mainland Chinese Braille (现行盲文).
Tones are absent or unreliable — use context and common vocabulary to select the correct characters.

Rules:
1. Convert every Pinyin syllable (or run of syllables) into the most contextually appropriate Simplified Chinese Hanzi.
2. Add correct punctuation where natural sentence boundaries are evident.
3. Preserve line breaks from the original text.
4. Do NOT output Pinyin — output ONLY Hanzi (plus punctuation and spaces as needed).
5. The input may contain residual abbreviated consonants or phonetic fragments (e.g. 'd' for 的, 'f' for 佛/非, 't b' for 特别) due to Braille shorthand. Expand them logically based on context.
6. If a run of syllables is incomprehensible even as Chinese, output them as-is.
7. Syllables containing ü (e.g. lü, nü) are valid Pinyin; convert them correctly.

Output the Hanzi text only, no comments or explanations.

PINYIN TO CONVERT:
""" + input_text
    else:
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
    elif lang == "chinese":
        translated = translate_braille_to_chinese(braille_text)
    elif lang == "shuangpin":
        translated = translate_braille_to_shuangpin(braille_text)
    elif lang == "raw":
        # Raw mode: bypass translation and Gemini correction entirely
        print("🔵 Raw mode selected — skipping translation and Gemini correction.")
        return braille_text, ""
    else:
        translated = translate_braille_to_arabic(braille_text)

    key = os.environ.get("GEMINI_API_KEY", GEMINI_API_KEY)
    if key:
        corrected = correct_text_with_gemini(translated, language=lang)
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
    elif lang == "chinese":
        translated = translate_braille_to_chinese(braille_text)
    elif lang == "shuangpin":
        translated = translate_braille_to_shuangpin(braille_text)
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
        "chinese":    translate_braille_to_chinese(braille_text),
        "shuangpin":  translate_braille_to_shuangpin(braille_text),
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
1. If ONE candidate is clearly readable and makes perfect sense, return its key: "arabic", "french", "english_g1", "english_g2", "russian", "chinese", or "shuangpin".
   For "chinese" or "shuangpin": the candidate will be Hanyu Pinyin syllables (e.g. "ni hao", "zhong guo"). Select "chinese" or "shuangpin" if the Pinyin syllables form a plausible sequence of Mandarin sounds that, when spoken, would constitute coherent Chinese speech.
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

            # For Chinese and Shuangpin: run a dedicated Pinyin→Hanzi Gemini pass
            if detected_lang in ("chinese", "shuangpin") and not corrected:
                raw_translation = candidates[detected_lang]
                corrected = correct_text_with_gemini(raw_translation, language="chinese")

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
