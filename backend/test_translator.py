# -*- coding: utf-8 -*-
from core.translator import translate_braille_to_chinese

test_cases = [
    ('⠓⠳⠀⠙⠡⠀⠈⠀⠻⠀⠱⠧⠀⠐⠢', 'xiu din  wan shan e'), # "修订和完善的"
    ('⠐⠤⠧⠀⠍⠢⠀⠓⠾⠀⠛⠊⠀⠟⠥⠤⠂⠀⠃⠩⠀⠺⠀⠓⠺', '…an me xue ji chu- bian wei hui'),
    ('⠼⠃⠚⠁⠙⠝⠩⠀⠼⠉⠤⠾', '2014 nian 3-yue')
]

all_pass = True
for case, expected in test_cases:
    res = translate_braille_to_chinese(case)
    if res == expected:
        print(f"PASS: {repr(case)} -> {repr(res)}")
    else:
        print(f"FAIL: {repr(case)}")
        print(f"  Expected: {repr(expected)}")
        print(f"  Got:      {repr(res)}")
        all_pass = False

if all_pass:
    print("ALL TESTS PASSED SUCCESSFULLY ON MAIN TRANSLATOR.PY!")
else:
    print("SOME TESTS FAILED!")
