"""
Robust extractor: reads the notebook, strips ALL GUI/interactive code,
and produces a clean processor.py with BrailleProcessor class.
"""
import json, os, re

ROOT = os.path.dirname(os.path.abspath(__file__))
NB   = os.path.join(ROOT, "final_code_for_interface (1)-version_1.ipynb")
OUT  = os.path.join(ROOT, "backend", "core", "processor.py")

with open(NB, encoding="utf-8") as f:
    nb = json.load(f)

code_cells = [c for c in nb["cells"] if c["cell_type"] == "code"]
sources    = ["".join(c["source"]) for c in code_cells]

# ── Line-level bad patterns ────────────────────────────────────────────────────
BAD_STARTS = [
    "import tkinter", "from tkinter", "import matplotlib", "from matplotlib",
    "import ipywidgets", "import nest_asyncio", "from IPython",
    "import edge_tts", "import subprocess",
]
BAD_CONTAINS = [
    "filedialog.", "root = tk.", "root.withdraw", "if not file_path",
    "img = cv2.imread", "scale = 0.15", "img_small =", "points = []",
    "light_pts = []", "img_small_light", "cv2.imshow", "cv2.setMouseCallback",
    "cv2.waitKey", "cv2.destroyAllWindows", "cv2.imwrite",
    "V = -(np",   "V vector defined",
    "save_path =", "Warped image saved",
    "choice = \"\"", "while choice not in", "LANGUAGE     =",
    "label, translate_fn =", "Selected:", "full_braille_text =",
    "result_text = translate_fn", "result_text = result_text.replace",
    "RÉSULTAT FINAL", "resultat_", "💾  Saved to: resultat",
    "braille_output' not found", "[!] 'braille_output'",
    "Enter your choice", "SELECT TRANSLATION",
    "for key, (label, _) in translators",
    "if choice not in translators", "[!] Invalid choice",
    "print(\"═\" *", "print(\"\\n\" + \"═\"",
    "global_start =", "global_end =", "Whole code without", "Horodaté le",
    "plt.", "# Added missing import",
    "lang_drop", "voice_drop", "btn = widgets", "out = widgets", "display(",
    "nest_asyncio.apply", "loop = asyncio",
    "os.environ['GEMINI_API_KEY'] = 'AI",
    "print(braille_output)",
    "# ── Run ─",
    "# --- EXECUTION ---",
    "# --- Run ---",
    "corrected_arabic",
    "corrected = correct_arabic_text",
    "print(\"\\n\" + \"=\"*50)",
    "print(\"✨ CORRECTED TEXT",
    "print(\"=\"*50)",
    "print(corrected)",
    "with open(\"corrected_",
    "print(\"\\n💾 Saved to corrected",
    "❌ 'arabic_text' variable",
    "img_rgb = cv2.cvtColor",
    "preview = cv2.resize",
]

def is_bad(line):
    s = line.strip()
    for b in BAD_STARTS:
        if s.startswith(b):
            return True
    for b in BAD_CONTAINS:
        if b in line:
            return True
    return False

def strip_src(src):
    """
    Remove bad lines AND skip entire indented blocks that follow a bad line
    (handles multi-line GUI callbacks and continuation args).
    """
    lines  = src.splitlines()
    result = []
    # State: are we inside a skipped def?
    skip_def = False
    # State: are we inside a multi-line call that was started by a bad line?
    skip_until_balanced = 0   # paren depth to consume

    for line in lines:
        stripped = line.strip()

        # ── Track skipped defs (select_point / select_light) ──────────────────
        if re.match(r"def select_point\(|def select_light\(", stripped):
            skip_def = True
        if skip_def:
            if line and not line[0].isspace() and not re.match(r"def select", stripped):
                skip_def = False
            else:
                continue

        # ── If we are consuming a multi-line bad call ─────────────────────────
        if skip_until_balanced > 0:
            skip_until_balanced += line.count('(') - line.count(')')
            if skip_until_balanced <= 0:
                skip_until_balanced = 0
            continue

        # ── Check if this line is bad ─────────────────────────────────────────
        if is_bad(line):
            # Count unmatched open parens to skip continuation lines
            unmatched = line.count('(') - line.count(')')
            if unmatched > 0:
                skip_until_balanced = unmatched
            continue

        result.append(line)

    return "\n".join(result)

# ─── Extract cell content ──────────────────────────────────────────────────────
helpers  = strip_src(sources[2])   # all helper functions
warmup   = strip_src(sources[3])   # warmup_numba

pipeline_raw = strip_src(sources[5])
# Remove lines we re-add inside the class method
PIPELINE_SKIP = [
    r"^\s*img_input\s*=\s*warped_rgb",
    r"^\s*img1_src\s*=",
    r"^\s*img2_src\s*=",
    r"^\s*img3_src\s*=",
]
pipeline = "\n".join(
    l for l in pipeline_raw.splitlines()
    if not any(re.match(p, l) for p in PIPELINE_SKIP)
)

# Model definition: keep DotPredictor class, cv2.setUseOptimized
model_raw = strip_src(sources[8])
MODEL_KEEP = []
skip_model = False
for line in model_raw.splitlines():
    s = line.strip()
    if re.match(r"(device\s*=\s*torch|model_3ch\s*=\s*Dot|model_path\s*=|if os\.path\.exists\(model_path\)|model_3ch\.load|model_3ch\.eval|print.*Model loaded|print.*Model file|else:)", s):
        skip_model = True
    if skip_model and (not s or (s and not line[0].isspace() and not re.match(r"(device|model_3ch|model_path|if os|else)", s))):
        skip_model = False
    if skip_model:
        continue
    if re.match(r"(import os$|import torch$|import torch\.nn|from PIL|from matplotlib|#.*MODEL DEF|#.*LOAD WEIGHT)", s):
        continue
    MODEL_KEEP.append(line)
model_def = "\n".join(MODEL_KEEP)

decode_src = strip_src(sources[9])

# Gemini cell: keep only the function def, strip runner block
gemini_raw   = strip_src(sources[10])
gemini_lines = []
in_runner    = False
for line in gemini_raw.splitlines():
    if "# --- Run ---" in line or "if 'result_text' in locals" in line:
        in_runner = True
    if in_runner:
        continue
    gemini_lines.append(line)
gemini_src = "\n".join(gemini_lines)
gemini_src = gemini_src.replace(
    "def correct_arabic_text(",
    "def _correct_text_with_gemini("
)

# ─── indent helper ────────────────────────────────────────────────────────────
def indent(src, n=8):
    pad = " " * n
    return "\n".join((pad + l) if l.strip() else l for l in src.splitlines())

# ─── Assemble ─────────────────────────────────────────────────────────────────
TEMPLATE = '''\
"""
backend/core/processor.py
Derived from: final_code_for_interface (1)-version_1.ipynb
"""
import cv2
import numpy as np
import time
import os
import torch
import torch.nn as nn
from math import atan2, cos, sin
from scipy.sparse import csr_matrix, bmat
from scipy.spatial import cKDTree
from scipy.ndimage import uniform_filter, convolve1d
from datetime import datetime
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from PIL import Image
from numba import njit
import google.generativeai as genai

_GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "")
if _GEMINI_KEY:
    genai.configure(api_key=_GEMINI_KEY)


# ── Perspective warp ──────────────────────────────────────────────────────────
def _do_warp(orig_img, pts_src_in):
    """Perspective-correct the image to remove page curvature."""
    orig    = orig_img.copy()
    pts_src = np.float32(pts_src_in)
    w_top   = np.linalg.norm(pts_src[0] - pts_src[1])
    w_bot   = np.linalg.norm(pts_src[2] - pts_src[3])
    mw      = int(max(w_top, w_bot))
    h_left  = np.linalg.norm(pts_src[0] - pts_src[3])
    h_right = np.linalg.norm(pts_src[1] - pts_src[2])
    mh      = int(max(h_left, h_right))
    dst     = np.float32([[0,0],[mw-1,0],[mw-1,mh-1],[0,mh-1]])
    M       = cv2.getPerspectiveTransform(pts_src, dst)
    warped  = cv2.warpPerspective(orig, M, (mw, mh))
    rgb     = cv2.cvtColor(warped, cv2.COLOR_BGR2RGB)
    MAX_H, MAX_W = 1024, 1448
    h, w = rgb.shape[:2]
    if h > MAX_H and w > MAX_W:
        s   = max(MAX_H / h, MAX_W / w)
        rgb = cv2.resize(rgb, (int(w*s), int(h*s)), interpolation=cv2.INTER_AREA)
    return rgb


# ── Helper functions ──────────────────────────────────────────────────────────
{helpers}


# ── Warmup ────────────────────────────────────────────────────────────────────
{warmup}


# ── Model definition ──────────────────────────────────────────────────────────
{model_def}

_device    = torch.device("cuda" if torch.cuda.is_available() else "cpu")
_model_3ch = DotPredictor().to(_device)

def load_model():
    path = os.path.join(os.path.dirname(__file__),
                        "..", "..", "best_braille_model_3_channel_augmented.pth")
    if os.path.exists(path):
        _model_3ch.load_state_dict(torch.load(path, map_location=_device))
        _model_3ch.eval()
        print("\\u2705 Model loaded.")
    else:
        print(f"\\u274c Model not found: {{path}}")
    return _model_3ch, _device


# ── Decode + translation functions ────────────────────────────────────────────
{decode_src}


# ── Gemini correction ─────────────────────────────────────────────────────────
{gemini_src}


# ── BrailleProcessor ─────────────────────────────────────────────────────────
class BrailleProcessor:
    def __init__(self):
        warmup_numba()

    def process(self, orig_img, pts_src_in, V_input, language="arabic"):
        """
        orig_img   : BGR numpy array
        pts_src_in : 4x2 float32 corner points (full-resolution)
        V_input    : [vx, vy] light direction
        language   : arabic | french | english_g1 | english_g2 | russian
        Returns (braille_text, translated_text, gemini_corrected)
        """
        from .translator import translate_results
        V          = np.array(V_input, dtype=np.float32)
        warped_rgb = _do_warp(orig_img, pts_src_in)

        # ── Pipeline ──────────────────────────────────────────────────────────
        img_input = warped_rgb
{pipeline_indented}

        # ── Image sources for the decoder ─────────────────────────────────────
        img1_src   = gray
        img2_src   = reconstruct_layer(recto_blanc, recto_noir)
        recto_full = np.maximum(recto_blanc, recto_noir).astype(np.uint8)
        verso_full = np.maximum(verso_blanc, verso_noir).astype(np.uint8)
        img3_src   = reconstruct_layer(recto_full, verso_full)

        # ── Decode ────────────────────────────────────────────────────────────
        braille_text, _ = get_braille_text_content_ultra_fast(
            img1_src, img2_src, img3_src, final_boxes,
            _model_3ch, _device, warped_rgb,
            nv_dist=neighbors_vertical,
            h_period=period,
            line_gap=neighbors_vertical_mid_p,
        )

        # ── Translate ─────────────────────────────────────────────────────────
        translated, gemini_corrected = translate_results(braille_text,
                                                         language=language)
        return braille_text, translated, gemini_corrected
'''

output = TEMPLATE.format(
    helpers=helpers,
    warmup=warmup,
    model_def=model_def,
    decode_src=decode_src,
    gemini_src=gemini_src,
    pipeline_indented=indent(pipeline, 8),
)

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    f.write(output)
print(f"Written {len(output):,} chars -> {OUT}")
