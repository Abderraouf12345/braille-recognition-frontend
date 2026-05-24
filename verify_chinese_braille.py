"""
Verify Chinese Braille mappings in translator.py against the standard.
Computes dot patterns from Unicode codepoints for analysis.
"""

def braille_to_dots(char):
    """Convert a Braille Unicode character to its dot pattern string."""
    code = ord(char) - 0x2800
    dots = []
    for i in range(6):
        if code & (1 << i):
            dots.append(str(i + 1))
    return '-'.join(dots) if dots else 'blank'

# === INITIALS from the code (lines 488-494) ===
INITIALS = {
    '⠃': 'b',  '⠏': 'p',  '⠍': 'm',  '⠋': 'f',
    '⠙': 'd',  '⠞': 't',  '⠝': 'n',  '⠇': 'l',
    '⠛': 'g',  '⠅': 'k',  '⠓': 'h',
    '⠌': 'zh', '⠟': 'ch', '⠱': 'sh', '⠚': 'r',
    '⠵': 'z',  '⠉': 'c',  '⠎': 's',
}

# === FINALS from the code (lines 505-543) ===
FINALS_CODE = {
    '⠁': 'a',
    '⠢': 'e',
    '⠕': 'uo',
    '⠪': 'ai',
    '⠖': 'ao',
    '⠮': 'ei',
    '⠷': 'ou',
    '⠧': 'an',
    '⠴': 'en',
    '⠦': 'ang',
    '⠼': 'eng',  # NOTE: also used as number indicator!
    '⠗': 'er',

    '⠊': 'i',
    '⠫': 'ia',
    '⠑': 'ie',
    '⠜': 'iao',
    '⠩': 'ian',
    '⠭': 'iang',
    '⠡': 'in',
    '⠣': 'ing',
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

# === EXPECTED standard from multiple authoritative sources ===
# Based on Wikipedia, brailleaustralia.org, and Chinese national standard
EXPECTED_INITIALS = {
    'dots 1-2':    ('⠃', 'b'),
    'dots 1-2-3-4': ('⠏', 'p'),
    'dots 1-3-4':  ('⠍', 'm'),
    'dots 1-2-4':  ('⠋', 'f'),
    'dots 1-4-5':  ('⠙', 'd'),
    'dots 2-3-4-5': ('⠞', 't'),
    'dots 1-3-4-5': ('⠝', 'n'),
    'dots 1-2-3':  ('⠇', 'l'),
    'dots 1-2-4-5': ('⠛', 'g/j'),
    'dots 1-3':    ('⠅', 'k/q'),
    'dots 1-2-5':  ('⠓', 'h/x'),
    'dots 3-4':    ('⠌', 'zh'),
    'dots 1-2-3-4-5': ('⠟', 'ch'),
    'dots 1-5-6':  ('⠱', 'sh'),
    'dots 2-4':    ('⠚', 'r'),
    'dots 1-3-5-6': ('⠵', 'z'),
    'dots 1-4':    ('⠉', 'c'),
    'dots 2-3-4':  ('⠎', 's'),
}

print("=" * 70)
print("INITIALS VERIFICATION")
print("=" * 70)
for char, pinyin in sorted(INITIALS.items(), key=lambda x: x[1]):
    dots = braille_to_dots(char)
    unicode_hex = f"U+{ord(char):04X}"
    print(f"  {char} ({unicode_hex}) dots {dots:15s} → {pinyin}")

print()
print("=" * 70)
print("FINALS VERIFICATION")
print("=" * 70)
for char, pinyin in FINALS_CODE.items():
    dots = braille_to_dots(char)
    unicode_hex = f"U+{ord(char):04X}"
    print(f"  {char} ({unicode_hex}) dots {dots:15s} → {pinyin}")

# Cross-reference check with known search result data
print()
print("=" * 70)
print("CROSS-REFERENCE CHECKS (from multiple authoritative sources)")
print("=" * 70)

# These are confirmed from multiple search results
expected_finals = {
    # From search: ai=dots 2,4,6; ei=dots 2,3,4,6; ui=dots 2,4,5,6
    # ao=dots 2,3,5; ou=dots 1,2,3,5,6; iu=dots 1,2,5,6
    'ai':   '2-4-6',
    'ei':   '2-3-4-6',
    'ui':   '2-4-5-6',
    'ao':   '2-3-5',
    'ou':   '1-2-3-5-6',
    'iu':   '1-2-5-6',
    
    # From search: ua=dots 1-2-3-4-5-6; uai=dots 1-3-4-5-6
    # uan=dots 1-2-4-5-6; uang=dots 2-3-5-6; un=dots 2-5; ong=dots 2-5-6
    'ua':   '1-2-3-4-5-6',
    'uai':  '1-3-4-5-6',
    'uan':  '1-2-4-5-6',
    'uang': '2-3-5-6',
    'un':   '2-5',
    'ong':  '2-5-6',
    
    # Basic ones confirmed by multiple sources
    'a':    '1',
    'i':    '2-4',
    'u':    '1-3-6',
    'e':    '2-6',
}

print()
for pinyin, expected_dots in expected_finals.items():
    # Find the char in code that maps to this pinyin
    found_char = None
    for char, py in FINALS_CODE.items():
        if py == pinyin:
            found_char = char
            break
    if found_char:
        actual_dots = braille_to_dots(found_char)
        status = "✓" if actual_dots == expected_dots else "✗ MISMATCH"
        print(f"  {pinyin:6s}: expected dots {expected_dots:15s}, code has {found_char} (dots {actual_dots:15s}) {status}")
    else:
        print(f"  {pinyin:6s}: NOT FOUND in code finals!")

# Check for the specific in/ing potential swap
print()
print("=" * 70)
print("SPECIFIC CHECK: in/ing (potential swap)")
print("=" * 70)
# ⠡ = U+2821 = dots 1,6
# ⠣ = U+2823 = dots 1,2,6
print(f"  Code: ⠡ (U+2821, dots {braille_to_dots('⠡')}) → 'in'")
print(f"  Code: ⠣ (U+2823, dots {braille_to_dots('⠣')}) → 'ing'")
print()
print("  From search results (brailleaustralia.org, Wikipedia, thelanguagecloset.com):")
print("    in  = dots 1-2-6")
print("    ing = dots 1-6")
print()
print("  Analysis: dots 1-6 = ⠡ (U+2821), dots 1-2-6 = ⠣ (U+2823)")
print("  If search is correct: ⠡ should be 'ing', ⠣ should be 'in'")
print("  Code has: ⠡ → 'in', ⠣ → 'ing'  → POTENTIALLY SWAPPED")

# Check for ⠼ dual use (eng final AND number indicator)
print()
print("=" * 70)
print("DUAL-USE CHECK: ⠼ (eng / number indicator)")
print("=" * 70)
print(f"  ⠼ (U+{ord('⠼'):04X}, dots {braille_to_dots('⠼')}) is mapped as final 'eng'")
print(f"  ⠼ is also used as NUMBER_INDICATOR in other languages")
print(f"  The code handles this contextually at line 647:")
print(f"    if c == '⠼': if i + 1 < n and chars[i+1] in NUM_MAP: number_mode = True")
print(f"  But if no digit follows, it falls through to be treated as 'eng' final")
print(f"  ISSUE: ⠼ appears in FINALS_UNAMB but is also number indicator.")
print(f"  The code at line 647-651 checks for number mode BEFORE checking finals.")
print(f"  If followed by a digit, it acts as number indicator; otherwise falls to final 'eng'.")
print(f"  This is CORRECT contextual handling.")

# Count total finals
print()
print("=" * 70)
print("COVERAGE SUMMARY")
print("=" * 70)
print(f"  Initials in code: {len(INITIALS)} (standard has 18 → {'✓ MATCH' if len(INITIALS) == 18 else '✗'})")
print(f"  Finals in code:   {len(FINALS_CODE)} (standard has ~34-35)")

# Check for missing finals
all_pinyin_finals = [
    'a', 'o', 'e', 'ai', 'ei', 'ao', 'ou', 'an', 'en', 'ang', 'eng', 'er',
    'i', 'ia', 'ie', 'iao', 'iu', 'ian', 'in', 'iang', 'ing', 'iong',
    'u', 'ua', 'uo', 'uai', 'ui', 'uan', 'un', 'uang', 'ong',
    'ü', 'üe', 'üan', 'ün'
]
code_finals = set(FINALS_CODE.values())
missing = [f for f in all_pinyin_finals if f not in code_finals]
extra = code_finals - set(all_pinyin_finals)
print(f"  Missing finals: {missing if missing else 'None'}")
print(f"  Extra finals:   {extra if extra else 'None'}")

# Note about 'o' — it's handled contextually via ⠕
print()
if 'o' in missing:
    print("  NOTE: 'o' is missing as a separate entry but is handled contextually:")
    print("    ⠕ maps to 'o' after b/p/m/f and 'uo' otherwise (line 690-691)")
    print("    This is CORRECT behavior per Chinese phonology.")
