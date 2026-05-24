import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
from core.translator import (
    translate_braille_to_english_g1,
    translate_braille_to_english_g2,
    translate_braille_to_french,
    translate_braille_to_chinese
)

# A rough mapping from the Pinyin output back to the likely Mainland Chinese Braille cells
# This is a heuristic reverse-lookup based on the Chinese dictionary.
reverse_map = {
    '-': '⠤',
    'yi': '⠊',  # Could also be zero-initial versions, but ⠊ is the cell for 'i'
    'bi': '⠃⠊',
    'er': '⠗',
    'yue': '⠾',
    'te': '⠞⠢',
    'bie': '⠃⠑',
    'sian': '⠎⠩',
    'zhi': '⠌',
    'ye': '⠑',
    'ta': '⠞⠁',
    'fin': '⠋⠣', # f + in (after our fix, in = ⠣)
    'e': '⠢',
    'wai': '⠽', # zero initial uai = wai = ⠽
    'an': '⠧',
    'wen': '⠒', # zero initial un = wen = ⠒
    'le': '⠇⠢',
    'ying': '⠡', # zero initial ing = ying = ⠡
    'ei': '⠮',
    'a': '⠁',
    'si': '⠎',
    'ci': '⠉',
    'fa': '⠋⠁',
    'de': '⠙⠢',
    'zhüe': '⠌⠾',
    'pi': '⠏⠊',
    'ri': '⠚',
    'wo': '⠕',
    'huai': '⠓⠽',
    'yin': '⠣',
    'ai': '⠪',
    'yuan': '⠯',
    'cou': '⠉⠷',
    'ao': '⠖',
    'cai': '⠉⠪',
    '。': '⠐⠆',
    'men': '⠍⠴',
    'yan': '⠩',
    'dou': '⠙⠷',
    'ma': '⠍⠁',
    'yong': '⠹', # iong / yong
    'yu': '⠬', # ü / yu
    'cuai': '⠉⠽',
    'luo': '⠇⠕',
    'ya': '⠫',
    'lüan': '⠇⠯',
    'ge': '⠛⠢',
    'ter': '⠞⠗',
    'bu': '⠃⠥',
    'shi': '⠱',
    'fiang': '⠋⠭',
    'sing': '⠎⠡',
    'you': '⠳',
    'k': '⠅',
    'wei': '⠺',
    'fang': '⠋⠦',
    'dui': '⠙⠺',
    'bai': '⠃⠪',
    'din': '⠙⠣',
    'yang': '⠭',
    'luan': '⠇⠻',
    'he': '⠓⠢',
    'süan': '⠎⠯',
    'dai': '⠙⠪',
    'han': '⠓⠧',
    'zi': '⠵',
    'shao': '⠱⠖',
    'mui': '⠍⠺',
    'lian': '⠇⠩',
    'yao': '⠜',
    'qi': '⠅⠊', # q = k cell (⠅) + i (⠊)
    'xia': '⠓⠫', # x = h cell (⠓) + ia (⠫)
    'rü': '⠚⠬',
    'cie': '⠉⠑',
    'ang': '⠦',
    'wan': '⠻',
    'muai': '⠍⠽',
    'ker': '⠅⠗',
    'cer': '⠉⠗',
    'rou': '⠚⠷',
    'shai': '⠱⠪',
    'en': '⠴',
    'chan': '⠟⠧',
    'rai': '⠚⠪',
    'zheng': '⠌⠼',
    'fian': '⠋⠩',
    'eng': '⠼',
    'wu': '⠥',
    'piong': '⠏⠹',
    'nin': '⠝⠣',
    'bun': '⠃⠒',
    'run': '⠚⠒',
    'tuo': '⠞⠕',
    'weng': '⠲',
    'can': '⠉⠧',
    'rie': '⠚⠑',
    'sui': '⠎⠺',
    '》': '⠠⠄',
    '5': '⠼⠑',
    ' ': ' ',
    '\n': '\n'
}

raw_pinyin = """-yi bi er yi yue te bie sian zhi ye ta fin e wai yi er
-er an wen le ying ei a si ci le si fa de ye ta ci
zhüe ci pi ri yue e wo e wo huai zhi yin fa sian ai yuan ye si
fa de cou ao fa cai。
 te bie sian zhi ye wai ye men yan ta dou ma pi ri er yong
-fin ai yu cuai ye ri ci luo ya lüan fa de ge ter yue yan an
-ying bu wai shi ying ye ta fiang er an ye sing yi ye an ai you
wo ya yan yuan fa k yi a wei fang bu wen er fa de ye an ye k dui
-bai wei fa ao din yu ye ter an de ge yang le luan he k
-er an ye ci süan ya le。wen yong ao ye ta shi dai yi bu
-ya si ta dou fa de wo an luan han ya bu e ya ri bu
wai shi ye ter an yang le luan he pi zi bu an shao yin ge bu ri pi
-fa de zhi ying wai si ge mui lian bu si mui men le dou yao yuan
yao ya bi ci ri fa bai de bie an ya yin fin zhi mui qi er you
xia ta pi。dou wo an yong yi mui lian zhi zhi rü si zhi men
yi bu fa e zhi bu de cie wei ye zhi yan an wen yong ao ye ta shi
wen ei wen he ye wai ci a yi ang wan muai wen yang ye yin he ker an
cer rou wei fa fa de shai yi bu pi shi de ying k fa
-yang le luan。en yin ying ei wen yang pi ri ci luo shi yu zhie a
zhi ying e a si ta》ao ye ta shi chan yi bu men rai en
zhi wen ei zheng zhi he ye si fa de yan fian fa ya bu
e ei yong eng wan wu chan ci ai a piong yi ci pi ri
yang nin bun yuan er an pi shi ao yao ye a he fa zhi run yong luan
ai en， ai eng ao shi tuo zhi he ci le zhi yin ri wen yong
-ao ye ta shi ri fa weng ye fiang wen le can zhi rie sui fa》
5"""

# Reconstruct braille string
braille_chars = []
tokens = []
# split keeping spaces and newlines
import re
for token in re.split(r'(\s+|-|。|》|，|5)', raw_pinyin):
    if not token: continue
    if token in reverse_map:
        braille_chars.append(reverse_map[token])
    else:
        # try to handle missing
        braille_chars.append("?")

reconstructed_braille = "".join(braille_chars)

print("--- RECONSTRUCTED BRAILLE ---")
print(reconstructed_braille)

print("\n--- DECODED AS ENGLISH GRADE 2 ---")
print(translate_braille_to_english_g2(reconstructed_braille))

print("\n--- DECODED AS FRENCH ---")
print(translate_braille_to_french(reconstructed_braille))

print("\n--- DECODED AS ENGLISH GRADE 1 ---")
print(translate_braille_to_english_g1(reconstructed_braille))

