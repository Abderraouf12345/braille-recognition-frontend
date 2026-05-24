"""
Quick regression test: verify the in/ing fix and other common syllables.
Run from the project root: python test_in_ing_fix.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
from core.translator import translate_braille_to_chinese

# Each tuple: (description, braille_input, expected_pinyin_substring)
CASES = [
    # ── in / ing (the swapped pair) ─────────────────────────────────────
    # xin (心) = h/x initial ⠓ + ing-final ⠡... wait, let's be explicit:
    # Standard: ⠡ = ing (dots 1-6), ⠣ = in (dots 1-2-6)

    # jin (今) = ⠛⠣   → g/j initial + in final → jin
    ("jin (今)", "⠛⠣", "jin"),
    # jing (京) = ⠛⠡  → g/j initial + ing final → jing
    ("jing (京)", "⠛⠡", "jing"),
    # xin (心) = ⠓⠣   → h/x initial + in final → xin
    ("xin (心)", "⠓⠣", "xin"),
    # xing (行) = ⠓⠡  → h/x initial + ing final → xing
    ("xing (行)", "⠓⠡", "xing"),
    # yin (音) = zero-initial + in → yin
    ("yin (音, zero-init)", "⠣", "yin"),
    # ying (英) = zero-initial + ing → ying
    ("ying (英, zero-init)", "⠡", "ying"),
    # min (民) = ⠍⠣
    ("min (民)", "⠍⠣", "min"),
    # ming (明) = ⠍⠡
    ("ming (明)", "⠍⠡", "ming"),

    # ── Other key syllables (regression) ────────────────────────────────
    # zhong (中) = ⠌⠲   zh + ong
    ("zhong (中)", "⠌⠲", "zhong"),
    # guo (国) = ⠛⠕    g + uo
    ("guo (国)", "⠛⠕", "guo"),
    # bo (波) = ⠃⠕     b + o (labial rule)
    ("bo (波)", "⠃⠕", "bo"),
    # hua (花) = ⠓⠿    h + ua → hua
    ("hua (花)", "⠓⠿", "hua"),
    # xue (学) = ⠓⠾    h/x + üe → xue
    ("xue (学)", "⠓⠾", "xue"),
    # yuan (元) = zero + üan → yuan
    ("yuan (元, zero-init)", "⠯", "yuan"),
]

print("=" * 60)
print("REGRESSION TEST: in/ing fix + common syllables")
print("=" * 60)
pass_count = fail_count = 0
for desc, braille, expected in CASES:
    result = translate_braille_to_chinese(braille).strip()
    ok = expected in result
    status = "✓ PASS" if ok else "✗ FAIL"
    if ok:
        pass_count += 1
    else:
        fail_count += 1
    print(f"  {status}  {desc:20s}  {braille!r:12s}  → '{result}'  (expected '{expected}')")

print()
print(f"  Results: {pass_count} passed, {fail_count} failed out of {len(CASES)} tests")
print("=" * 60)
