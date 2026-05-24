import re

# Onsets mapping (First cell)
# Keys are unicode braille characters, values are the initial+medial pinyin
ONSETS = {
    # No medial
    '⠾': '',   '⠊': 'b',  '⠦': 'p',  '⠪': 'm',  '⠖': 'f',
    '⠌': 'd',  '⠎': 't',  '⠏': 'n',  '⠇': 'l',  '⠁': 'g',
    '⠅': 'k',  '⠃': 'h',  '⠉': 'zh', '⠍': 'ch', '⠋': 'sh', '⠔': 'r',
    # i-medial
    '⠒': 'y',  '⠚': 'bi', '⠶': 'pi', '⠺': 'mi',
    '⠜': 'di', '⠞': 'ti', '⠟': 'ni', '⠗': 'li',
    '⠑': 'j',  '⠕': 'q',  '⠓': 'x',  '⠙': 'z',  '⠝': 'c',  '⠛': 's',
    # Note: j, q, x inherently have 'i' medial, and z, c, s are used here in the i-medial row for some reason?
    # Actually, in Shuangpin, z/c/s are encoded using the i-medial row but they don't have 'i' medial.
    # Wait, the table says:
    # Row 1: -, b, p, m, f, d, t, n, l, g, k, h, zh, ch, sh, r
    # Row 2: y, bi, pi, mi, di, ti, ni, li, ji, qi, xi, z, c, s
    # Row 3: w, du, tu, nu, lu, gu, ku, hu, zhu, chu, shu, ru
    # Row 4: yu, nü, lü, ju, qu, xu, zu, cu, su
    
    # u-medial
    '⠢': 'w',  '⠬': 'du', '⠮': 'tu', '⠯': 'nu', '⠧': 'lu',
    '⠡': 'gu', '⠥': 'ku', '⠣': 'hu', '⠩': 'zhu','⠭': 'chu','⠫': 'shu','⠴': 'ru',
    # ü-medial
    '⠲': 'yu', '⠿': 'nü', '⠷': 'lü', '⠱': 'ju', '⠵': 'qu', '⠳': 'xu',
    '⠹': 'zu', '⠽': 'cu', '⠻': 'su'
}

# Fix for the ji/qi/xi vs ju/qu/xu:
# In Chinese pinyin, ji/qi/xi have the 'i' built-in to the onset.
# We will just map them as 'j', 'q', 'x' and let the rime add the vowel if needed, OR we map as 'ji' and drop the 'i' if the rime starts with one.
# Let's map them literally for now and fix up in the syllable builder.

# Rimes mapping (Second cell)
RIMES = {
    # Base (Tone 4/0)
    '⠃': 'i/u/ü', '⠚': 'a', '⠊': 'e/o', '⠛': 'ai', '⠌': 'ei', '⠓': 'ao', '⠉': 'ou', '⠋': 'an', '⠁': 'en', '⠙': 'ang', '⠑': 'eng',
    # Tone 1
    '⠇': 'i/u/ü', '⠞': 'a', '⠎': 'e/o', '⠟': 'ai', '⠜': 'ei', '⠗': 'ao', '⠍': 'ou', '⠏': 'an', '⠅': 'en', '⠝': 'ang', '⠕': 'eng',
    # Tone 2
    '⠣': 'i/u/ü', '⠺': 'a', '⠪': 'e/o', '⠻': 'ai', '⠬': 'ei', '⠳': 'ao', '⠩': 'ou', '⠫': 'an', '⠡': 'en', '⠹': 'ang', '⠱': 'eng',
    # Tone 3
    '⠧': 'i/u/ü', '⠾': 'a', '⠮': 'e/o', '⠿': 'ai', '⠼': 'ei', '⠷': 'ao', '⠭': 'ou', '⠯': 'an', '⠥': 'en', '⠽': 'ang', '⠵': 'eng'
}

def resolve_syllable(onset, rime):
    # Onset is something like 'b', 'bi', 'j', 'zh', 'w', ''
    # Rime is something like 'a', 'i/u/ü', 'e/o', 'ang'
    
    # Handle i/u/ü rime
    if rime == 'i/u/ü':
        # If onset already has a vowel (bi, yu, w, etc), the rime is just empty or 'i'
        if onset.endswith('i') or onset.endswith('u') or onset in ('y', 'w'):
            return onset
        # For j/q/x, they take 'i' or 'u' (which is written u but pronounced ü).
        # Actually, in Shuangpin, the medial is in the onset.
        # So 'j' (from ji row) is 'ji'. If rime is i/u/ü, it's just 'ji'.
        # 'ju' (from ju row) is 'ju'. If rime is i/u/ü, it's just 'ju'.
        # For b, p, m, f, d, t, n, l, g, k, h, zh, ch, sh, r, z, c, s
        # The base form takes 'i' usually?
        # Wait, if onset has no medial, and rime is i/u/ü...
        # In Pinyin, 'i', 'u', 'ü' are medials. If the rime is JUST i/u/ü, then the onset already contains the information.
        # e.g., 'bi' onset + 'i/u/ü' rime = 'bi'.
        # 'b' onset + 'i/u/ü' rime -> 'bu'? Wait. 'b' is in row 1 (no medial). 'bu' is missing from row 3!
        # Ah! 'bu', 'pu', 'mu', 'fu' are not in row 3! They use row 1 (b, p, m, f) + 'i/u/ü' rime = bu, pu, mu, fu!
        # Let's check: 'b' + 'i/u/ü' = 'bu'? Yes!
        # 'zh' + 'i/u/ü' = 'zhi'.
        # 'z' + 'i/u/ü' = 'zi'.
        # So if onset is in row 1, 'i/u/ü' means 'i' (for zh,ch,sh,r,z,c,s)? Wait, z,c,s are in row 2.
        if onset in ('b','p','m','f'): return onset + 'u'
        if onset in ('zh','ch','sh','r'): return onset + 'i'
        if onset in ('z','c','s'): return onset + 'i'
        return onset + 'i' # fallback
        
    if rime == 'e/o':
        # e/o depends on onset. b/p/m/f/w usually take 'o'. Others take 'e'.
        if onset in ('b','p','m','f','w'): return onset + 'o'
        if onset.endswith('i'): return onset + 'e'
        if onset.endswith('u'): return onset[:-1] + 'uo' # e.g. du+o = duo? No, tu+e = tuo.
        return onset + 'e'
        
    # Standard appending
    res = onset + rime
    # fix up 'ie' 'ue' 'ye'
    res = res.replace('ii', 'i').replace('uu', 'u').replace('üü', 'ü')
    if res == 'yian': return 'yan'
    if res == 'yiang': return 'yang'
    if res == 'yiao': return 'yao'
    if res == 'yiei': return 'ye'
    if res == 'yie': return 'ye'
    if res == 'yiou': return 'you'
    if res == 'yin': return 'yin'
    if res == 'yia': return 'ya'
    
    if res == 'wi': return 'wei'
    if res == 'weng': return 'weng'
    if res == 'wan': return 'wan'
    if res == 'wang': return 'wang'
    
    # j,q,x with 'i' built in:
    if res.startswith('j') and not res.startswith('ju'):
        res = 'j' + res[2:] if res.startswith('ji') else res
        if not res.startswith('ji'): res = res.replace('j', 'ji', 1)
        res = res.replace('jii', 'ji')
    # simple cleanup
    if 'iuü' in res: res = res.replace('iuü', 'i')
    
    return res

PUNCTUATION = {
    '⠐⠆': '。', '⠐⠄': '，', '⠐⠂': '、', '⠰⠂': '！',
    '⠠⠄': '：', '⠰': '；', '⠐⠐⠐': '……', '⠤': '—'
}

def decode_shuangpin(text):
    text = text.replace('⠀', ' ')
    out = []
    i = 0
    while i < len(text):
        c1 = text[i]
        
        # Punctuation check
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
            
        # Needs pairs
        if i + 1 < len(text):
            c2 = text[i+1]
            if c1 in ONSETS and c2 in RIMES:
                onset = ONSETS[c1]
                rime = RIMES[c2]
                syl = resolve_syllable(onset, rime)
                out.append(syl)
                i += 2
                continue
                
        out.append(c1)
        i += 1
        
    return ' '.join(out).replace('  ', ' ')

raw_braille = "⠤⠊⠃⠊⠗⠐⠀⠊⠾⠀⠞⠃⠎⠩⠀⠌⠀⠑⠞⠋⠣⠀⠢⠽⠀⠊⠗\n⠤⠗⠧⠀⠒⠇⠀⠡⠮⠐⠀⠁⠎⠉⠇⠢⠎⠀⠋⠙⠀⠑⠞⠉⠔⠐\n⠌⠾⠉⠔⠀⠏⠚⠊⠾⠀⠢⠕⠢⠕⠓⠽⠀⠌⠀⠣⠋⠎⠩⠐⠀⠪⠯⠑⠎\n⠋⠙⠀⠉⠷⠀⠖⠋⠉⠪⠐⠆\n⠞⠃⠎⠩⠀⠌⠀⠑⠽⠑⠍⠀⠩⠞⠙⠷⠔⠐⠀⠍⠁⠀⠏⠚⠀⠗⠹\n⠤⠋⠣⠀⠪⠬⠀⠉⠽⠑⠚⠀⠉⠇⠕⠫⠐⠀⠇⠯⠋⠙⠀⠛⠞⠗⠾⠀⠩⠧\n⠤⠡⠃⠐⠀⠽⠱⠀⠔⠡⠑⠞⠀⠋⠭⠗⠧⠀⠑⠎⠡⠊⠀⠑⠧⠪⠳\n⠕⠫⠐⠀⠩⠯⠋⠅⠀⠊⠁⠀⠺⠋⠦⠃⠐⠀⠒⠗⠋⠙⠀⠑⠧⠑⠅⠀⠙⠺\n⠤⠃⠪⠺⠋⠀⠖⠙⠣⠬⠀⠑⠞⠗⠧⠐⠀⠈⠙⠛⠀⠭⠇⠇⠻⠀⠓⠅\n⠤⠗⠧⠀⠑⠉⠀⠎⠯⠔⠫⠀⠇⠔⠐⠆⠒⠹⠖⠑⠞⠱⠀⠙⠪⠀⠊⠃\n⠤⠔⠫⠐⠀⠎⠞⠀⠙⠷⠋⠙⠀⠕⠧⠇⠻⠀⠓⠧⠫⠃⠀⠢⠫⠚⠃\n⠽⠱⠀⠑⠞⠗⠧⠀⠭⠇⠇⠻⠐⠀⠓⠏⠀⠵⠃⠀⠧⠱⠖⠣⠛⠃⠀⠚⠏\n⠤⠋⠙⠀⠌⠀⠡⠽⠎⠛⠀⠍⠺⠇⠩⠀⠃⠎⠍⠺⠠⠀⠍⠇⠀⠙⠷⠜⠯⠐\n⠜⠫⠃⠉⠀⠚⠋⠀⠃⠪⠀⠙⠃⠑⠧⠀⠫⠣⠋⠣⠀⠌⠀⠍⠺⠅⠊⠀⠗⠳\n⠓⠫⠞⠏⠔⠐⠆⠙⠷⠕⠧⠀⠹⠊⠀⠍⠺⠇⠩⠀⠌⠀⠌⠚⠬⠎⠀⠌⠍\n⠊⠃⠋⠀⠢⠌⠀⠔⠃⠙⠆⠀⠉⠑⠺⠑⠀⠌⠀⠩⠧⠔⠐⠀⠒⠹⠖⠑⠞⠱\n⠒⠮⠀⠒⠓⠀⠑⠽⠀⠉⠊⠁⠊⠀⠦⠻⠍⠽⠐⠀⠒⠭⠀⠑⠣⠀⠓⠅⠗⠧\n⠉⠗⠐⠀⠚⠷⠺⠋⠀⠋⠙⠀⠱⠪⠊⠃⠏⠱⠀⠔⠙⠀⠔⠡⠀⠅⠋\n⠤⠭⠇⠇⠻⠐⠆⠴⠣⠡⠮⠀⠒⠭⠀⠏⠚⠀⠉⠇⠕⠱⠀⠬⠌⠑⠁\n⠌⠀⠔⠡⠀⠢⠁⠀⠎⠞⠠⠄⠰⠄⠖⠑⠞⠱⠐⠀⠟⠧⠀⠊⠃⠍⠚⠪⠴⠔\n⠌⠀⠒⠮⠀⠌⠼⠀⠌⠓⠀⠑⠎⠋⠙⠀⠩⠋⠩⠋⠐⠀⠫⠃\n⠢⠮⠀⠹⠼⠀⠻⠥⠐⠀⠟⠧⠀⠉⠊⠪⠔⠀⠁⠏⠹⠊⠉⠔⠐⠀⠏⠚\n⠭⠝⠣⠃⠒⠯⠔⠀⠗⠧⠀⠏⠱⠀⠖⠜⠑⠁⠀⠓⠋⠌⠚⠒⠹⠀⠇⠻\n⠪⠴⠐⠄⠠⠆⠀⠪⠼⠖⠱⠀⠞⠕⠌⠓⠀⠉⠊⠇⠌⠀⠣⠚⠐⠀⠒⠹\n⠤⠖⠑⠞⠱⠀⠚⠋⠀⠲⠑⠀⠋⠭⠀⠒⠇⠉⠧⠀⠌⠚⠑⠎⠺⠋⠔⠠⠄\n⠼⠑"

print(decode_shuangpin(raw_braille))

