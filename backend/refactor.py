import ast
import os
import re

source_path = "extracted_logic.py"
dest_path = os.path.join("backend", "core", "processor.py")

with open(source_path, 'r', encoding='utf-8') as f:
    source_code = f.read()

# 1. We will wrap the entire source code inside a function `def run_pipeline(img_input, pts_src, V_input):`
# But we need to keep Numba imports and @njit functions OUTSIDE because Numba doesn't compile local functions well.

# Let's extract all imports and @njit functions.
# A simple regex to find @njit functions:
njit_pattern = re.compile(r'(@njit.*?def\s+[a-zA-Z0-9_]+\(.*?\):(?:\n(?:(?:[ \t]+.*?\n)|(?:^\s*\n))+)*)', re.MULTILINE | re.DOTALL)

njit_functions = []
for match in njit_pattern.finditer(source_code):
    njit_functions.append(match.group(1))

# Remove njit functions from the source
source_code_no_njit = njit_pattern.sub('\n# [NJIT FUNCTION REMOVED]\n', source_code)

# 2. Let's create the final processor.py structure
header = """
import cv2
import numpy as np
import time
import math
from math import atan2, cos, sin
import torch
from numba import njit
from scipy.ndimage import convolve1d

# Try to import from the model (assuming it's in the same directory or core module)
try:
    from .model import model_3ch, device
except ImportError:
    pass

# ==========================================
# NUMBA OPTIMIZED FUNCTIONS
# ==========================================
"""

for njit_func in njit_functions:
    header += njit_func + "\n\n"

# 3. Now we put the rest inside a class BrailleProcessor
class_start = """
class BrailleProcessor:
    def __init__(self):
        pass

    def process(self, orig_img, pts_src_in, V_in):
        \"\"\"
        orig_img: BGR image from user
        pts_src_in: list of 4 dicts [{'x':0,'y':0}, ...] or numpy array
        V_in: numpy array [vx, vy] representing light direction
        \"\"\"
        img = orig_img.copy()
        orig = img.copy()
        
        # Format inputs
        pts_src = np.float32(pts_src_in)
        V = np.array(V_in, dtype=np.float32)
        
        # Replicate the initial warp setup
        width_top = np.linalg.norm(pts_src[0] - pts_src[1])
        width_bottom = np.linalg.norm(pts_src[2] - pts_src[3])
        max_width = int(max(width_top, width_bottom))
        
        height_left = np.linalg.norm(pts_src[0] - pts_src[3])
        height_right = np.linalg.norm(pts_src[1] - pts_src[2])
        max_height = int(max(height_left, height_right))
        
        pts_dst = np.float32([
            [0, 0],
            [max_width - 1, 0],
            [max_width - 1, max_height - 1],
            [0, max_height - 1]
        ])
        
        matrix = cv2.getPerspectiveTransform(pts_src, pts_dst)
        warped = cv2.warpPerspective(orig, matrix, (max_width, max_height))
        
        orig_rgb = cv2.cvtColor(orig, cv2.COLOR_BGR2RGB)
        warped_rgb = cv2.cvtColor(warped, cv2.COLOR_BGR2RGB)
        
        MAX_H, MAX_W = 1024, 1376
        h, w = warped_rgb.shape[:2]
        
        if h > MAX_H and w > MAX_W:
            scale_h = MAX_H / h
            scale_w = MAX_W / w
            scale = max(scale_h, scale_w)
            new_h = int(h * scale)
            new_w = int(w * scale)
            warped_rgb = cv2.resize(
                warped_rgb,
                (new_w, new_h),
                interpolation=cv2.INTER_AREA
            )

        print("✅ Warp completed. Size:", warped_rgb.shape)
        
        # --- BEGIN INJECTED PROCEDURAL CODE ---
"""

class_end = """
        # --- END INJECTED PROCEDURAL CODE ---
        
        # Attempt to return the final translated string.
        # Based on extracted_logic.py, it should have a 'lines' list or similar at the end.
        try:
            # We join the final list of decoded braille lines
            return "\\n".join(lines)
        except Exception as e:
            print("Error retrieving final string:", e)
            return "Error during Braille processing."
"""

# Let's clean the procedural code.
# Remove GUI, imshow, plt, and tkinter
lines = source_code_no_njit.split('\n')
filtered_lines = []
skip = False
for line in lines:
    if "import tkinter" in line or "from tkinter" in line:
        continue
    if "filedialog." in line or "tk.Tk(" in line or "root.withdraw()" in line:
        continue
    if "cv2.imshow" in line or "cv2.waitKey" in line or "cv2.destroyAllWindows" in line or "cv2.setMouseCallback" in line:
        continue
    if "plt." in line or "matplotlib" in line:
        continue
    if "import cv2" in line or "import numpy" in line or "import time" in line or "import os" in line:
        continue
    if "cv2.imwrite" in line:
        continue # Don't save to disk on the server
    if "print(\"👉 Click" in line:
        continue
    if "def select_point(" in line:
        skip = True
        continue
    if "def select_light(" in line:
        skip = True
        continue
    if "def complete_braille_grid_logic" in line and skip:
        # Wait, if we are skipping, we shouldn't skip everything!
        pass
        
    if skip and len(line.strip()) > 0 and not line.startswith(" ") and not line.startswith("\t"):
        # We assume end of function if unindented
        if not line.startswith("def "):
            skip = False

    if not skip:
        # We also need to remove the exact block that defines warp because we rewrote it in the header
        # The warp block in extracted_logic starts around line 30 and ends around 140
        # Instead of parsing, we can just comment out the specific top-level assignments
        if line.startswith("orig = ") or line.startswith("scale = ") or line.startswith("img_small = "):
            continue
        if line.startswith("pts_src =") or line.startswith("pts_dst ="):
            continue
        if line.startswith("width_top =") or line.startswith("width_bottom =") or line.startswith("max_width ="):
            continue
        if line.startswith("height_left =") or line.startswith("height_right =") or line.startswith("max_height ="):
            continue
        if line.startswith("matrix = ") or line.startswith("warped = ") or line.startswith("warped_rgb = ") or line.startswith("h, w = warped_rgb.shape"):
            continue
        if line.startswith("MAX_H") or line.startswith("scale_h = ") or line.startswith("scale_w = ") or line.startswith("new_h = ") or line.startswith("new_w = "):
            continue
        if "img = cv2.imread" in line or "points =" in line or "light_pts =" in line or "V =" in line:
            continue
        # Also remove the DotPredictor model load, we assume it's imported
        if "model_3ch =" in line or "model_3ch.load_state_dict" in line or "device =" in line:
            continue
        if "class DotPredictor" in line:
            skip = True
            continue
        
        filtered_lines.append("        " + line)

indented_code = "\n".join(filtered_lines)

with open(dest_path, 'w', encoding='utf-8') as f:
    f.write(header + class_start + indented_code + class_end)

print("✅ processor.py successfully generated!")
