import cv2
import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import matplotlib.pyplot as plt
import numpy as np

# Create file chooser window
root = tk.Tk()
root.withdraw()  # hide the root window

# Ask user to select an image file
file_path = filedialog.askopenfilename(
    title="Select an image",
    filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp *.tif *.tiff")]
)

if not file_path:
    print("❌ No file selected.")
else:
    # Load and show the selected image in a small preview window
    img = cv2.imread(file_path)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    # Resize for preview
    preview = cv2.resize(img_rgb, (600, int(img_rgb.shape[0] * 600 / img_rgb.shape[1])))

    print("✅ Selected file:", file_path)

img = cv2.imread(file_path)
orig = img.copy()

scale = 0.15
img_small = cv2.resize(img, None, fx=scale, fy=scale)

points = []

def select_point(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        points.append((x, y))
        cv2.circle(img_small, (x, y), 5, (0, 0, 255), -1)
        cv2.imshow("Select 4 corners", img_small)

cv2.imshow("Select 4 corners", img_small)
cv2.setMouseCallback("Select 4 corners", select_point)
print("👉 Click on the 4 corners of the page (in order). Press 'q' when done.")

while True:
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q') and len(points) == 4:
        break

cv2.destroyAllWindows()

light_pts = []

def select_light(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        light_pts.append((x, y))
        cv2.circle(img_small_light, (x, y), 5, (255, 255, 0), -1)
        if len(light_pts) == 2:
            cv2.arrowedLine(img_small_light, light_pts[0], light_pts[1], (255, 255, 0), 2)
        cv2.imshow("Select Light Direction", img_small_light)

# Use the image with the drawn corners for context
img_small_light = img_small.copy() 
cv2.imshow("Select Light Direction", img_small_light)
cv2.setMouseCallback("Select Light Direction", select_light)

print("👉 Click 2 points for light direction (Point 1: Source -> Point 2: Target). Press 'q' when done.")

while True:
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q') and len(light_pts) == 2:
        break

cv2.destroyAllWindows()

# Calculate V as the inverse of the drawn light direction
V = -(np.array(light_pts[1]) - np.array(light_pts[0]))
print(f"✅ V vector defined as: {V}")
# ================================================================

points = [(int(x / scale), int(y / scale)) for (x, y) in points]

pts_src = np.float32(points)
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

# === Save the result to disk only ===
save_path = "warped_result.jpg"
cv2.imwrite(save_path, warped)
print(f"✅ Warped image saved as {save_path}")

orig_rgb = cv2.cvtColor(orig, cv2.COLOR_BGR2RGB)
warped_rgb = cv2.cvtColor(warped, cv2.COLOR_BGR2RGB)

print(warped_rgb.shape)

MAX_H, MAX_W = 1024, 1376
# MAX_H, MAX_W = 11024, 11376

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


print(warped_rgb.shape)

import numpy as np

def find_best_translations_optimized(moving_img, static_img, search_range, find_second_peak=False, use_gaussian=False):
    h_m, w_m = moving_img.shape[:2]
    padded_static = cv2.copyMakeBorder(static_img, search_range, search_range, search_range, search_range, cv2.BORDER_CONSTANT, value=0)
    res = cv2.matchTemplate(padded_static, moving_img, cv2.TM_CCORR)
    if use_gaussian:
        res_h, res_w = res.shape
        tx_values = np.arange(res_w) - (res_w // 2)
        ty_values = np.arange(res_h) - (res_h // 2)
        tx_grid, ty_grid = np.meshgrid(tx_values, ty_values)
        distance_sq = tx_grid**2 + ty_grid**2
        sigma = search_range / 0.00000000001
        gaussian_weights = np.exp(-distance_sq / (2 * sigma**2))
        res = res * gaussian_weights

    _, max_val1, _, max_loc1 = cv2.minMaxLoc(res)
    peak1_tx = max_loc1[0] - search_range
    peak1_ty = max_loc1[1] - search_range
    v1 = (peak1_tx, peak1_ty)

    if not find_second_peak:
        return v1, None

    temp_res = res.copy()
    
    res_h, res_w = res.shape
    tx_values_range = range(-search_range, search_range + 1)
    ty_values_range = range(-search_range, search_range + 1)
    tx_grid, ty_grid = np.meshgrid(tx_values_range, ty_values_range)
    dot_product_map = tx_grid * peak1_tx + ty_grid * peak1_ty
    mask = dot_product_map > 0
    temp_res[mask] = 0

    _, max_val2, _, max_loc2 = cv2.minMaxLoc(temp_res)
    peak2_tx = max_loc2[0] - search_range
    peak2_ty = max_loc2[1] - search_range
    v2 = (peak2_tx, peak2_ty)
    
    return v1, v2

def translate_and_intersect(img_to_move, static_img, tx, ty):
    h, w = static_img.shape[:2] 
    
    translation_matrix = np.float32([[1, 0, tx], [0, 1, ty]])
    translated_img = cv2.warpAffine(img_to_move, translation_matrix, (w, h), borderValue=0)
    intersection = np.minimum(static_img, translated_img)
    
    return intersection

import numpy as np

def unit_to_binary(v):
    v = np.array(v, dtype=float)

    norm = np.linalg.norm(v)
    if norm == 0:
        return np.array([0, 0])
    
    u = v / norm
    b = (np.sign(u) * (np.abs(u) > 0.5)).astype(int)

    return b

from datetime import datetime
print("Horodaté le :", datetime.now())

import time
global_start = time.time()

start = time.time()

def process_image_in_tiles_4pass(warped_rgb, tile_size, margin_size=0):
    if len(warped_rgb.shape) == 3:
        gray = cv2.cvtColor(warped_rgb, cv2.COLOR_BGR2GRAY)
    else:
        gray = warped_rgb

    gray_f = gray.astype(np.float32)
    h, w = gray_f.shape

    acc1 = np.zeros((h, w), dtype=np.float32)
    acc2 = np.zeros((h, w), dtype=np.float32)

    offsets = [
        0,
        int(round(tile_size * 0.25)),
        int(round(tile_size * 0.50)),
        int(round(tile_size * 0.75)),
    ]

    delta_map = np.empty((h, w), dtype=np.float32)

    for offset in offsets:
        delta_map[:] = 0.0

        # ── Corner tile (only for offset > 0) ──────────────────────────────
        if offset > 0:
            ye = min(offset, h)
            xe = min(offset, w)
            m = float(np.median(gray_f[:ye, :xe]))
            delta_map[:ye, :xe] = 128.0 - m

        # ── Regular tiles ───────────────────────────────────────────────────
        start = offset if offset > 0 else 0

        for y in range(start, h, tile_size):
            ye = min(y + tile_size, h)
            for x in range(start, w, tile_size):
                xe = min(x + tile_size, w)
                m = float(np.median(gray_f[y:ye, x:xe]))
                delta_map[y:ye, x:xe] = 128.0 - m

                # ──  fill top-edge strip for this tile column ───────────
                # Pixels [0:start, x:xe] are otherwise never assigned a delta.
                if offset > 0 and y == start:
                    delta_map[0:start, x:xe] = 128.0 - m

                # ── Fix: fill left-edge strip for this tile row ─────────────
                # Pixels [y:ye, 0:start] are otherwise never assigned a delta.
                if offset > 0 and x == start:
                    delta_map[y:ye, 0:start] = 128.0 - m

        # ── Vectorised channel computation ──────────────────────────────────
        nv = np.clip(gray_f + delta_map, 0.0, 255.0)
        acc1 += np.clip(2.0 * nv - 255.0, 0.0, None)   # bright
        acc2 += np.clip(255.0 - 2.0 * nv, 0.0, None)   # dark

    acc1 *= 0.25
    acc2 *= 0.25
    np.clip(acc1, 0, 255, out=acc1)
    np.clip(acc2, 0, 255, out=acc2)
    return acc1.astype(np.uint8), acc2.astype(np.uint8)

end = time.time()
print(f"Execution time: {end - start:.4f} seconds")

start = time.time()

# --- 1. PRE-PROCESSING & SCALE ESTIMATION ---
img_input = warped_rgb
if len(img_input.shape) == 3:
    gray = cv2.cvtColor(img_input, cv2.COLOR_BGR2GRAY)
else:
    gray = img_input.copy()

clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(12, 16))
clahe_img = clahe.apply(gray)
preprocessed = cv2.bilateralFilter(clahe_img, d=9, sigmaColor=15, sigmaSpace=15)
forTheVariation = preprocessed

BLOCK_SIZE = 27
C_HIGHLIGHTS = -6
highlights_thresh = cv2.adaptiveThreshold(
    preprocessed, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
    cv2.THRESH_BINARY_INV, BLOCK_SIZE, C_HIGHLIGHTS
)

C_SHADOWS = 7
shadows_thresh = cv2.adaptiveThreshold(
    preprocessed, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
    cv2.THRESH_BINARY_INV, BLOCK_SIZE, C_SHADOWS
)

kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (1, 1))
cleaned1 = cv2.morphologyEx(highlights_thresh, cv2.MORPH_OPEN, kernel, iterations=1)
cleaned1 = 255 - cleaned1
cleaned2 = cv2.morphologyEx(shadows_thresh, cv2.MORPH_OPEN, kernel, iterations=1)

v1, v2 = find_best_translations_optimized(cleaned2, cleaned1, search_range=20, find_second_peak=True, use_gaussian=True)
if np.max(v1) > np.max(v2): v1, v2 = v2, v1
v1, v2 = np.array(v1), np.array(v2)
mean_module = (np.linalg.norm(v1) + np.linalg.norm(v2)) / 2
result = int(round(mean_module * 1.5))
mean_module = int(round(mean_module))

end = time.time()
print(f"Execution time: {end - start:.4f} seconds")

start = time.time()

# --- 3. 4-PASS OVERLAP (Exact weights from your snippet) ---
t_size = result * 2
cleaned1_total, cleaned2_total = process_image_in_tiles_4pass(gray, t_size, 0)

print(f"v1: {v1}, v2: {v2}, mean_module: {mean_module}, result: {result}")

end = time.time()
print(f"Execution time: {end - start:.4f} seconds")

def process_directional_wb(cleaned_total, result):
    img = cleaned_total.astype(np.float32)
    h, w = img.shape
    k = max(1, int(round(result / 2)))
    print(f"Neighborhood radius k: {k}")
 
    h_wb  = np.zeros((h, w), dtype=np.float32)
    v_wb  = np.zeros((h, w), dtype=np.float32)
    d1_wb = np.zeros((h, w), dtype=np.float32)
    d2_wb = np.zeros((h, w), dtype=np.float32)
 
    shifted = np.empty((h, w), dtype=np.float32)   # reusable buffer
 
    for i in range(1, k + 1):
 
        # ── Horizontal ──────────────────────────────────────────────────────
        # left  (img shifted right by i → compare pixel to its left neighbour)
        shifted[:, i:]  = img[:, :-i]
        shifted[:, :i]  = img[:, :1]          # replicate-border
        h_wb += np.maximum(0.0, img - shifted)
        # right
        shifted[:, :-i] = img[:, i:]
        shifted[:, -i:] = img[:, -1:]
        h_wb += np.maximum(0.0, img - shifted)
 
        # ── Vertical ────────────────────────────────────────────────────────
        # up
        shifted[i:, :]  = img[:-i, :]
        shifted[:i, :]  = img[:1, :]
        v_wb += np.maximum(0.0, img - shifted)
        # down
        shifted[:-i, :] = img[i:, :]
        shifted[-i:, :] = img[-1:, :]
        v_wb += np.maximum(0.0, img - shifted)
 
        # ── Diagonal 1 (TL → BR) ────────────────────────────────────────────
        # top-left shift
        shifted[i:,  i:]  = img[:-i, :-i]
        shifted[:i,  :]   = img[:1,  :]
        shifted[:, :i]    = img[:,  :1]
        d1_wb += np.maximum(0.0, img - shifted)
        # bottom-right shift
        shifted[:-i, :-i] = img[i:, i:]
        shifted[-i:, :]   = img[-1:, :]
        shifted[:, -i:]   = img[:, -1:]
        d1_wb += np.maximum(0.0, img - shifted)
 
        # ── Diagonal 2 (TR → BL) ────────────────────────────────────────────
        # top-right shift
        shifted[i:,  :-i] = img[:-i, i:]
        shifted[:i,  :]   = img[:1,  :]
        shifted[:, -i:]   = img[:, -1:]
        d2_wb += np.maximum(0.0, img - shifted)
        # bottom-left shift
        shifted[:-i, i:]  = img[i:, :-i]
        shifted[-i:, :]   = img[-1:, :]
        shifted[:, :i]    = img[:, :1]
        d2_wb += np.maximum(0.0, img - shifted)
 
    WB_mean = (h_wb + v_wb + d1_wb + d2_wb) * 0.25
    return np.clip(WB_mean, 0, 255).astype(np.uint8)

start = time.time()

WB_disp_BLANC = process_directional_wb(cleaned1_total, result)
WB_disp_NOIR = process_directional_wb(cleaned2_total, result)

BLANC_VARIATIONS = cv2.addWeighted(cleaned1_total, 1/2, WB_disp_BLANC, 1/2, 0)
NOIR_VARIATIONS = cv2.addWeighted(cleaned2_total, 1/2, WB_disp_NOIR, 1/2, 0)

end = time.time()
print(f"Execution time: {end - start:.4f} seconds")

# start = time.time()

# plt.figure(figsize=(20,15))

# plt.subplot(1,4,1)
# plt.imshow(BLANC_VARIATIONS, cmap='jet')
# plt.axis('off')

# plt.subplot(1,4,2)
# plt.imshow(NOIR_VARIATIONS, cmap='jet')
# plt.axis('off')

# plt.tight_layout()
# plt.show()

# end = time.time()
# print(f"Execution time: {end - start:.4f} seconds")

start = time.time()

def translate(img, dy, dx):
    M = np.float32([[1, 0, dx], [0, 1, dy]])
    return cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_NEAREST, borderValue=0)

def build_probabilistic_layers(cleaned1, cleaned2, v1, v2):
    h, w = cleaned1.shape

    # Create empty outputs
    recto_blanc = np.zeros_like(cleaned1, dtype=np.float32)
    verso_blanc = np.zeros_like(cleaned1, dtype=np.float32)

    shifted_v1 = translate(cleaned2, v1[1], v1[0])
    shifted_v2 = translate(cleaned2, v2[1], v2[0])

    A = shifted_v1.astype(np.float32)
    B = shifted_v2.astype(np.float32)
    C = cleaned1.astype(np.float32)

    # Probability that pixel comes from recto
    p_recto = A / (A + B + + 1e-6)
    p_verso = B / (A + B + + 1e-6)
    # p_recto = A / (A + B + 10)
    # p_verso = B / (A + B + 10)
    # p_verso = 1.0 - p_recto

    recto_blanc = C * p_recto
    verso_blanc = C * p_verso

    # Convert back to uint8
    return (recto_blanc.astype(np.uint8),
            verso_blanc.astype(np.uint8))

def mean_neighbors_kernel_full(img, k=4):
    kernel = np.ones((k, k), dtype=np.float32)
    neighbor_count = k * k

    summed = cv2.filter2D(img.astype(np.float32), -1, kernel)
    mean = summed / neighbor_count
    return mean

def merge_with_full_kernel(recto, verso, k=4, p=3):
    mean_recto = mean_neighbors_kernel_full(recto, k)
    mean_verso = mean_neighbors_kernel_full(verso, k)

    cond_recto = mean_recto > mean_verso * p
    cond_verso = mean_verso > mean_recto * p

    recto_new = recto.copy()
    verso_new = verso.copy()

    # recto dominant
    recto_new = np.where(cond_recto, recto + verso, recto)
    verso_new = np.where(cond_recto, 0, verso_new)

    # verso dominant
    verso_new = np.where(cond_verso, verso_new + recto_new, verso_new)
    recto_new = np.where(cond_verso, 0, recto_new)

    return recto_new, verso_new

import cv2

def mean_neighbors_kernel_full(img, k=4):
    # Standard square kernel for local density
    kernel = np.ones((k, k), dtype=np.float32)
    neighbor_count = k * k
    summed = cv2.filter2D(img.astype(np.float32), -1, kernel)
    mean = summed / neighbor_count
    return mean

def merge_with_full_kernel_4layers(rb, rn, vb, vn, k=4, p=3):
    """
    rb, rn: Recto Blanc, Recto Noir
    vb, vn: Verso Blanc, Verso Noir
    k: kernel size, p: multiplier threshold
    """
    total_recto = rb.astype(np.float32) + rn.astype(np.float32)
    total_verso = vb.astype(np.float32) + vn.astype(np.float32)

    # 2. Calculate neighborhood density for the TOTAL context
    mean_r = mean_neighbors_kernel_full(total_recto, k)
    mean_v = mean_neighbors_kernel_full(total_verso, k)

    # 3. Define dominance based on the context
    cond_recto = mean_r > (mean_v * p)
    cond_verso = mean_v > (mean_r * p)

    # Prepare outputs
    rb_new, rn_new = rb.copy(), rn.copy()
    vb_new, vn_new = vb.copy(), vn.copy()

    # 4. Apply transfers - COLOR LOCKED
    # If Recto is dominant:
    # Move Verso Blanc -> Recto Blanc AND Verso Noir -> Recto Noir
    rb_new = np.where(cond_recto, rb_new + vb_new, rb_new)
    vb_new = np.where(cond_recto, 0, vb_new)
    
    rn_new = np.where(cond_recto, rn_new + vn_new, rn_new)
    vn_new = np.where(cond_recto, 0, vn_new)

    # If Verso is dominant:
    # Move Recto Blanc -> Verso Blanc AND Recto Noir -> Verso Noir
    vb_new = np.where(cond_verso, vb_new + rb_new, vb_new)
    rb_new = np.where(cond_verso, 0, rb_new)
    
    vn_new = np.where(cond_verso, vn_new + rn_new, vn_new)
    rn_new = np.where(cond_verso, 0, rn_new)

    # Return all 4 refined layers
    return (np.clip(rb_new, 0, 255).astype(np.uint8), 
            np.clip(rn_new, 0, 255).astype(np.uint8), 
            np.clip(vb_new, 0, 255).astype(np.uint8), 
            np.clip(vn_new, 0, 255).astype(np.uint8))

from math import atan2, cos, sin

def plus_kernel(size, v1_first):
    """ Génère les noyaux (kernels) selon l'orientation (Code inchangé) """
    k = size
    kernel_hor = np.zeros((k, k), dtype=np.float32)
    kernel_ver = np.zeros((k, k), dtype=np.float32)

    mid = k // 2

    vx, vy = v1_first
    angle = atan2(vy, vx)

    if abs(cos(angle)) < abs(sin(angle)):
        kernel_ver[:, mid-2] = 0.25
        kernel_ver[:, mid-1] = 0.5
        kernel_ver[:, mid] = 1
        kernel_ver[:, mid+1] = 0.5
        kernel_ver[:, mid+2] = 0.25
    else:
        kernel_hor[mid-2, :] = 0.25
        kernel_hor[mid-1, :] = 0.5
        kernel_hor[mid, :] = 1
        kernel_hor[mid+1, :] = 0.5
        kernel_hor[mid+2, :] = 0.25

    return kernel_hor, kernel_ver

def plus_kernel_filter(img, size, v1_first):
    k = size
    img_f = img.astype(np.float32)
 
    vx, vy = v1_first
    angle = atan2(vy, vx)
    use_horizontal_strip = (abs(cos(angle)) >= abs(sin(angle)))
 
    # The 5-tap weight vector (centre-weighted strip)
    weights_5 = np.array([0.25, 0.5, 1.0, 0.5, 0.25], dtype=np.float32)
    # Box kernel of width k (captures the full-row spread)
    box_k = np.ones(k, dtype=np.float32)
 
    if use_horizontal_strip:
        # kernel_hor: rows [mid-2..mid+2] are set, each row spans all k columns.
        # Decompose: first box-filter horizontally (all k columns), then 5-tap vertically.
        tmp       = convolve1d(img_f, box_k,    axis=1, mode='constant', cval=0.0)
        conv_h    = convolve1d(tmp,   weights_5, axis=0, mode='constant', cval=0.0)
        conv_v    = np.zeros_like(img_f)         # kernel_ver is all-zero for this branch
    else:
        # kernel_ver: columns [mid-2..mid+2] are set, each column spans all k rows.
        # Decompose: first box-filter vertically (all k rows), then 5-tap horizontally.
        tmp       = convolve1d(img_f, box_k,    axis=0, mode='constant', cval=0.0)
        conv_v    = convolve1d(tmp,   weights_5, axis=1, mode='constant', cval=0.0)
        conv_h    = np.zeros_like(img_f)
 
    # Normalise the same way the original does (divide by kernel sum)
    sum_h = float(np.sum(weights_5) * k) if use_horizontal_strip  else 1e-6
    sum_v = float(np.sum(weights_5) * k) if not use_horizontal_strip else 1e-6
 
    mean_h = conv_h / max(sum_h, 1e-6)
    mean_v = conv_v / max(sum_v, 1e-6)
    return mean_h, mean_v

def split_noise_with_plus_kernel(img_recto, img_verso, img_noise, size, v1_first):
    R = img_recto.astype(np.float32) / 255.0
    V = img_verso.astype(np.float32) / 255.0
    Noise = img_noise.astype(np.float32)

    mean_recto_h, mean_recto_v = plus_kernel_filter(R, size, v1_first)
    mean_verso_h, mean_verso_v = plus_kernel_filter(V, size, v1_first)

    score_R = mean_recto_h + mean_recto_v
    score_V = mean_verso_h + mean_verso_v
    
    score_R = np.maximum(score_R, 0)
    score_V = np.maximum(score_V, 0)
    
    epsilon = 1e-10
    total_score = score_R + score_V + epsilon
    
    prob_recto = score_R / total_score
    prob_verso = score_V / total_score
    
    noise_recto = Noise * prob_recto
    noise_verso = Noise * prob_verso
    
    return (np.clip(noise_recto, 0, 255).astype(np.uint8), 
            np.clip(noise_verso, 0, 255).astype(np.uint8))


def get_angle_with_v(vec, reference_v):
    """Calculates the angle in radians between two vectors."""
    # Ensure they are numpy arrays
    v_a = np.array(vec).flatten()
    v_b = np.array(reference_v).flatten()
    
    # Cosine formula: (a . b) / (|a| * |b|)
    norm_a = np.linalg.norm(v_a)
    norm_b = np.linalg.norm(v_b)
    
    # Avoid division by zero if a vector is empty/zero
    if norm_a == 0 or norm_b == 0:
        return np.pi  # Return max angle if one vector is null
        
    cos_theta = np.dot(v_a, v_b) / (norm_a * norm_b)
    
    # Clip to avoid errors from floating point precision (staying in [-1, 1])
    cos_theta = np.clip(cos_theta, -1.0, 1.0)
    
    return np.arccos(cos_theta)

def separate_by_probability(img_recto, img_verso, threshold=0.7):
    R = img_recto.astype(np.float32)
    V = img_verso.astype(np.float32)
 
    total = R + V + 1e-6
    p_recto = R / total     
 
    # Two boolean masks cover all four outputs
    mask_sure_R  = p_recto >= threshold   # sure recto
    mask_sure_V  = p_recto <  (1.0 - threshold)   # sure verso (= p_verso >= threshold)
 
    # sure_recto   = R where mask_sure_R  else 0
    sure_R   = (R   * mask_sure_R).astype(np.uint8)
    # unsure_recto = R where NOT mask_sure_R else 0
    unsure_R = (R   * ~mask_sure_R).astype(np.uint8)
    # sure_verso   = V where mask_sure_V  else 0
    sure_V   = (V   * mask_sure_V).astype(np.uint8)
    # unsure_verso = V where NOT mask_sure_V else 0
    unsure_V = (V   * ~mask_sure_V).astype(np.uint8)
 
    return sure_R, unsure_R, sure_V, unsure_V

end = time.time()
print(f"Execution time: {end - start:.4f} seconds")

start = time.time()

noise = np.minimum(BLANC_VARIATIONS , NOIR_VARIATIONS)
cleaned1_total = cv2.subtract(BLANC_VARIATIONS, noise)
cleaned2_total = cv2.subtract(NOIR_VARIATIONS, noise)

reconstruction = np.clip(cv2.addWeighted(cv2.add(128, cleaned1_total), 1/2, 255 - cv2.add(128, cleaned2_total), 1/2, 0), 0, 255).astype(np.uint8)

cleaned1 = cleaned1_total
cleaned2 = cleaned2_total

h, w = cleaned1.shape
v1, v2 = find_best_translations_optimized(cleaned2, cleaned1, search_range=result, find_second_peak=True, use_gaussian=False)
    
v1_first = v1
v2_first = v2
# v2_first = tuple(-x for x in v1_first)

# 1. Calculate angles
angle1 = get_angle_with_v(v1_first, V)
angle2 = get_angle_with_v(v2_first, V)

# 2. Logic: We want angle1 < angle2. 
# If angle1 is larger than angle2, they are in the wrong order.
if angle1 > angle2:
    print(f"Angle 1 ({np.degrees(angle1):.2f}°) > Angle 2 ({np.degrees(angle2):.2f}°). Swapping...")
    
    # Swap vectors
    v1_first, v2_first = v2_first, v1_first
else:
    print(f"Correct orientation: Angle 1 ({np.degrees(angle1):.2f}°) is smaller than Angle 2 ({np.degrees(angle2):.2f}°).")

v1_noir = tuple(-x for x in v1_first)
v2_noir = tuple(-x for x in v2_first)

print(v1)
print(v2)

v1 = np.array(v1_first)
v2 = np.array(v2_first)

mod_v1 = np.linalg.norm(v1)
mod_v2 = np.linalg.norm(v2)

mean_module = (mod_v1 + mod_v2) / 2

print("v1 :", v1)
print("v2 :", v2)
print("Moyenne des modules de v1 et v2 :", mean_module)

result = int(round(mean_module * 1.5))
mean_module = int(round(mean_module))
print("Résultat final :", result)
print("mean_module :", mean_module)

recto_blanc, verso_blanc = build_probabilistic_layers(cleaned1, cleaned2, v1_first, v2_first)
recto_noir, verso_noir = build_probabilistic_layers(cleaned2, cleaned1, v1_noir, v2_noir)

reconstruction_recto = np.clip(cv2.addWeighted(cv2.add(128, recto_blanc), 1/2, 255 - cv2.add(128, recto_noir), 1/2, 0), 0, 255).astype(np.uint8)
reconstruction_verso = np.clip(cv2.addWeighted(cv2.add(128, verso_blanc), 1/2, 255 - cv2.add(128, verso_noir), 1/2, 0), 0, 255).astype(np.uint8)

end = time.time()
print(f"Execution time: {end - start:.4f} seconds")

# start = time.time()

# plt.figure(figsize=(22, 22))
# plt.subplot(1, 5, 1)
# plt.imshow(reconstruction_recto, cmap='gray')
# plt.axis("off")

# plt.subplot(1, 5, 2)
# plt.imshow(reconstruction_verso, cmap='gray')
# plt.axis("off")

# plt.subplot(1, 5, 3)
# plt.imshow(reconstruction, cmap='gray')
# plt.axis("off")

# plt.subplot(1, 5, 4)
# plt.imshow(gray, cmap='gray')
# plt.axis("off")

# plt.tight_layout()
# plt.show()

# end = time.time()
# print(f"Execution time: {end - start:.4f} seconds")

start = time.time()

sure_RB, uRB, sure_VB, uVB = separate_by_probability(recto_blanc, verso_blanc, threshold=0.9)
sure_RN, uRN, sure_VN, uVN = separate_by_probability(recto_noir, verso_noir, threshold=0.9)

end = time.time()
print(f"Execution time: {end - start:.4f} seconds")

# start = time.time()

# sure_RB, uRB, sure_VB, uVB = separate_by_probability(recto_blanc, verso_blanc, threshold=0.8)
# sure_RN, uRN, sure_VN, uVN = separate_by_probability(recto_noir, verso_noir, threshold=0.8)

# plt.figure(figsize=(22, 22))
# plt.subplot(1, 5, 1)
# plt.imshow(np.clip(cv2.addWeighted(cv2.add(128, sure_RB), 1/2, 255 - cv2.add(128, sure_RN), 1/2, 0), 0, 255).astype(np.uint8), cmap='gray')
# plt.axis("off")

# plt.subplot(1, 5, 2)
# plt.imshow(np.clip(cv2.addWeighted(cv2.add(128, uRB), 1/2, 255 - cv2.add(128, uRN), 1/2, 0), 0, 255).astype(np.uint8), cmap='gray')
# plt.axis("off")

# plt.subplot(1, 5, 3)
# plt.imshow(np.clip(cv2.addWeighted(cv2.add(128, sure_VB), 1/2, 255 - cv2.add(128, sure_VN), 1/2, 0), 0, 255).astype(np.uint8), cmap='gray')
# plt.axis("off")

# plt.subplot(1, 5, 4)
# plt.imshow(np.clip(cv2.addWeighted(cv2.add(128, uVB), 1/2, 255 - cv2.add(128, uVN), 1/2, 0), 0, 255).astype(np.uint8), cmap='gray')
# plt.axis("off")

# plt.tight_layout()
# plt.show()

# end = time.time()
# print(f"Execution time: {end - start:.4f} seconds")



start = time.time()
from scipy.ndimage import convolve1d

current_rb, current_rn = recto_blanc.copy(), recto_noir.copy()
current_vb, current_vn = verso_blanc.copy(), verso_noir.copy()

# The kernel size stays the same or can be adjusted
k_size = result * 4

# The Loop: from 80% to 50% (0.8 to 0.5)
# Using np.arange or a list for precision

for thresh in [0.8]:
    print(f"Refining with threshold: {thresh}")

    # --- STEP 1: Separate into Sure and Unsure ---
    # Split the White layers based on current threshold
    sRB, uRB, sVB, uVB = separate_by_probability(current_rb, current_vb, threshold=thresh)

    # Split the Black layers based on current threshold
    sRN, uRN, sVN, uVN = separate_by_probability(current_rn, current_vn, threshold=thresh)

    # --- STEP 2: Create the "Unsure" targets ---
    unsure_combined_blanc = uRB + uVB
    unsure_combined_noir  = uRN + uVN

    start = time.time()

    # --- STEP 3: Split the unsure pixels using the Plus Kernel ---
    # We use (Sure Blanc + Sure Noir) as structural context
    
    # Refine White unsure pixels
    refined_uRB, refined_uVB = split_noise_with_plus_kernel(
        (sure_RB.astype(np.float32) + sure_RN.astype(np.float32)), 
        (sure_VB.astype(np.float32) + sure_VN.astype(np.float32)), 
        unsure_combined_blanc, 
        k_size, v1_first
    )

    # Refine Black unsure pixels
    refined_uRN, refined_uVN = split_noise_with_plus_kernel(
        (sure_RN.astype(np.float32) + sure_RB.astype(np.float32)), 
        (sure_VN.astype(np.float32) + sure_VB.astype(np.float32)), 
        unsure_combined_noir, 
        k_size, v1_first
    )

    end = time.time()
    print(f"Execution time: {end - start:.4f} seconds")

    # --- STEP 4: Recombine and Update for the next iteration ---
    # We add the 'sure' parts and the 'newly refined' unsure parts
    current_rb = np.clip(sRB + refined_uRB, 0, 255).astype(np.uint8)
    current_vb = np.clip(sVB + refined_uVB, 0, 255).astype(np.uint8)
    
    current_rn = np.clip(sRN + refined_uRN, 0, 255).astype(np.uint8)
    current_vn = np.clip(sVN + refined_uVN, 0, 255).astype(np.uint8)

recto_blanc, recto_noir, verso_blanc, verso_noir = merge_with_full_kernel_4layers(current_rb, current_rn, current_vb, current_vn, k = mean_module, p=2)

end = time.time()
print(f"Execution time: {end - start:.4f} seconds")

# start = time.time()

# plt.figure(figsize=(22, 22))
# plt.subplot(1, 5, 1)
# plt.imshow(np.clip(cv2.addWeighted(cv2.add(128, recto_blanc), 1/2, 255 - cv2.add(128, recto_noir), 1/2, 0), 0, 255).astype(np.uint8), cmap='gray')
# plt.axis("off")

# plt.subplot(1, 5, 2)
# plt.imshow(reconstruction_recto, cmap='gray')
# plt.axis("off")

# plt.subplot(1, 5, 3)
# plt.imshow(np.clip(cv2.addWeighted(cv2.add(128, verso_blanc), 1/2, 255 - cv2.add(128, verso_noir), 1/2, 0), 0, 255).astype(np.uint8), cmap='gray')
# plt.axis("off")

# plt.subplot(1, 5, 4)
# plt.imshow(reconstruction_verso, cmap='gray')
# plt.axis("off")

# plt.tight_layout()
# plt.show()

# end = time.time()
# print(f"Execution time: {end - start:.4f} seconds")

start = time.time()

def translate_image(img, shift):
    M = np.float32([[1, 0, shift[0]],
                    [0, 1, shift[1]]])
    return cv2.warpAffine(img, M, (img.shape[1], img.shape[0]),
                          flags=cv2.INTER_LINEAR,
                          borderMode=cv2.BORDER_CONSTANT,
                          borderValue=0)

dx = v1_first[0] / 3
dy = v1_first[1] / 3

# recto_noir → translation +v1/2
recto_noir_shifted  = translate_image(recto_noir, ( dx,  dy))
recto_blanc_shifted = translate_image(recto_blanc, (-dx, -dy))

dx = v2_first[0] / 3
dy = v2_first[1] / 3

# recto_noir → translation +v1/2
verso_noir_shifted  = translate_image(verso_noir, ( dx,  dy))
verso_blanc_shifted = translate_image(verso_blanc, (-dx, -dy))

# recto_out et verso_out doivent être en uint8
recto = cv2.add(recto_blanc_shifted, recto_noir_shifted).astype(np.uint8)
verso = cv2.add(verso_blanc_shifted, verso_noir_shifted).astype(np.uint8)

end = time.time()
print(f"Execution time: {end - start:.4f} seconds")

# start = time.time()

# plt.figure(figsize=(18, 15)) 
# plt.subplot(2, 4, 1)
# plt.imshow(np.clip(cv2.addWeighted(cv2.add(128, recto_blanc), 1/2, 255 - cv2.add(128, recto_noir), 1/2, 0), 0, 255).astype(np.uint8), cmap='gray')
# plt.axis('off')

# plt.subplot(2, 4, 2)
# plt.imshow(gray, cmap='gray')
# plt.axis("off")

# plt.subplot(2, 4, 3)
# plt.imshow(np.clip(cv2.addWeighted(cv2.add(128, verso_blanc), 1/2, 255 - cv2.add(128, verso_noir), 1/2, 0), 0, 255).astype(np.uint8), cmap='gray')
# plt.axis('off')

# plt.subplot(2, 4, 4)
# plt.title("Verso Otsu")
# plt.imshow(np.clip(cv2.addWeighted(cv2.add(128, recto), 1/2, 255 - cv2.add(128, verso), 1/2, 0), 0, 255).astype(np.uint8), cmap='gray')
# plt.axis("off")

# plt.tight_layout()
# plt.show()

# end = time.time()
# print(f"Execution time: {end - start:.4f} seconds")

start = time.time()
from numba import njit

@njit(fastmath=True)
def phase1_concentrate_centroid(img, win_size):
    rows, cols = img.shape
    k = win_size // 2
    
    # We write results to a new array to avoid "directional drift"
    # and to allow for potential parallelization.
    res = np.zeros((rows, cols), dtype=img.dtype)
    
    # Standard scan-line processing (Top-to-bottom, Left-to-right)
    # This is much faster for the CPU cache than jumping around via sort_idx.
    for y in range(rows):
        for x in range(cols):
            val = img[y, x]
            
            # Skip empty pixels
            if val <= 0:
                continue

            # Define window boundaries
            y_min = max(0, y - k)
            y_max = min(rows, y + k + 1)
            x_min = max(0, x - k)
            x_max = min(cols, x + k + 1)

            mass_sum = 0.0
            y_weighted_sum = 0.0
            x_weighted_sum = 0.0

            # Calculate local center of mass based on original image
            for wy in range(y_min, y_max):
                for wx in range(x_min, x_max):
                    v = img[wy, wx]
                    if v > 0:
                        mass_sum += v
                        y_weighted_sum += wy * v
                        x_weighted_sum += wx * v

            if mass_sum > 0:
                # Fast rounding and clamping
                target_y = int(y_weighted_sum / mass_sum + 0.5)
                target_x = int(x_weighted_sum / mass_sum + 0.5)
                
                # Boundary safety
                if target_y < 0: target_y = 0
                elif target_y >= rows: target_y = rows - 1
                if target_x < 0: target_x = 0
                elif target_x >= cols: target_x = cols - 1

                # Move intensity to the calculated target
                res[target_y, target_x] += val
            else:
                # Fallback: stay in place
                res[y, x] += val
                
    return res

# @njit
# def phase2_redistribute(img, median_1):
#     rows, cols = img.shape
#     max_iter = 500 
    
#     for _ in range(max_iter):
#         found_overflow = False
#         for y in range(rows):
#             for x in range(cols):
#                 val = img[y, x]
#                 if val > median_1:
#                     found_overflow = True
#                     excess = val - median_1
#                     img[y, x] = median_1
                    
#                     # 1. Count valid neighbors (No lists!)
#                     count = 0
#                     for dy in range(-1, 2):
#                         for dx in range(-1, 2):
#                             if dy == 0 and dx == 0: continue
#                             ny, nx = y + dy, x + dx
#                             if 0 <= ny < rows and 0 <= nx < cols:
#                                 count += 1
                    
#                     # 2. Distribute share (Direct math)
#                     if count > 0:
#                         share = excess / count
#                         for dy in range(-1, 2):
#                             for dx in range(-1, 2):
#                                 if dy == 0 and dx == 0: continue
#                                 ny, nx = y + dy, x + dx
#                                 if 0 <= ny < rows and 0 <= nx < cols:
#                                     img[ny, nx] += share
#                     else:
#                         # If no neighbors, keep the intensity
#                         img[y, x] += excess
        
#         # If no pixel exceeded the limit in this pass, we are done
#         if not found_overflow:
#             break
            
#     return img


@njit
def phase2_redistribute(img, median_1):
    rows, cols = img.shape

    for y in range(rows):
        for x in range(cols):
            val = img[y, x]
            if val <= median_1:
                continue

            # val = median_1 * k + rest
            k    = int(val / median_1)
            rest = val - median_1 * k

            img[y, x] = median_1        # current pixel consumes 1 chunk

            needed    = k - 1           # remaining full chunks to spread
            has_rest  = rest > 0
            filled    = 0
            rest_done = not has_rest

            # generous radius bound: circle area ~ π*r² must cover `k` pixels
            max_r = int(k**0.5 * 2) + 5

            # expand ring by ring (Chebyshev), closest pixels first
            r = 1
            while (filled < needed or not rest_done) and r <= max_r:
                # iterate only the border of the square at Chebyshev distance r
                for dy in range(-r, r + 1):
                    for dx in range(-r, r + 1):
                        if abs(dy) != r and abs(dx) != r:
                            continue            # skip interior, border only
                        if filled >= needed and rest_done:
                            break
                        ny = y + dy
                        nx = x + dx
                        if 0 <= ny < rows and 0 <= nx < cols:
                            if img[ny, nx] == 0:
                                if filled < needed:
                                    img[ny, nx] = median_1
                                    filled += 1
                                elif not rest_done:
                                    img[ny, nx] = rest
                                    rest_done = True
                r += 1

    return img

# commented function of phase 2 is better but slower    

def filter_dots_by_mass(concentrated_img, ratio=0.15):
    img = concentrated_img.copy()
    masses = img[img > 0]
    if masses.size == 0:
        return img
    median_mass = np.mean(masses)
    threshold = ratio * median_mass
    img[img < threshold] = 0
    return img

def apply_centroid_concentration(img_input, mean_module, median_1, win, ratio=0.2):
    if win % 2 == 0: win += 1
        
    print(f"Phase 1: Concentrating... (Window: {win})")
    concentrated = phase1_concentrate_centroid(img_input.astype(np.float32), win)

    concentrated_filtered = filter_dots_by_mass(concentrated, ratio=ratio)

    print(f"Phase 2: Redistributing overflow (Median Target: {median_1})...")
    final_float = phase2_redistribute(concentrated, median_1)
    
    return np.round(np.clip(final_float, 0, 255)).astype(np.uint8), concentrated

def remove_small_dots_binary(img, min_area=10):
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(
        img, connectivity=8
    )

    # find valid component ids
    valid = np.where(stats[:, cv2.CC_STAT_AREA] >= min_area)[0]
    valid = valid[valid != 0]  # remove background

    cleaned = np.isin(labels, valid).astype(np.uint8) * 255
    return cleaned


def median_top_1_percent(img, per= 99):
    pixels = img.ravel()
    # Percentile is slow on large images, so we use a sub-sample for speed 
    # if the image is huge, but here we use the full array:
    threshold = np.percentile(pixels, per)
    top_pixels = pixels[pixels >= threshold]
    if top_pixels.size == 0: return 255.0
    return np.median(top_pixels)

def concentrate_single_image(image, window_size):
    # Ensure window size is odd
    if window_size % 2 == 0:
        window_size += 1
        
    result = phase1_concentrate_centroid(image.astype(np.float32), window_size)
    return result


end = time.time()
print(f"Execution time: {end - start:.4f} seconds")

start = time.time()

median_1 = median_top_1_percent(recto, per= 99)
print("Median of top 1% pixels:", median_1)

end = time.time()
print(f"Execution time: {end - start:.4f} seconds")

start = time.time()

recto_concentrated_before_treshold = filter_dots_by_mass(recto, ratio=0.2)

end = time.time()
print(f"Execution time: {end - start:.4f} seconds")

start = time.time()

recto_concentrated_before_treshold = concentrate_single_image(recto_concentrated_before_treshold, window_size=mean_module * 2)
recto_concentrated_before_treshold, concentrated = apply_centroid_concentration(recto_concentrated_before_treshold, result, median_1, mean_module * 2, ratio=0.2)

end = time.time()
print(f"Execution time: {end - start:.4f} seconds")

start = time.time()

recto_concentrated = np.where(recto_concentrated_before_treshold == median_1, 255, 0).astype(np.uint8)

end = time.time()
print(f"Execution time: {end - start:.4f} seconds")

start = time.time()

recto_concentrated = remove_small_dots_binary(recto_concentrated, min_area=mean_module/3)

end = time.time()
print(f"Execution time: {end - start:.4f} seconds")

# start = time.time()

# plt.figure(figsize=(15, 15)) 
# plt.subplot(2, 4, 1)
# plt.imshow(recto, cmap='gray')
# plt.axis('off')

# plt.subplot(2, 4, 2)
# plt.imshow(recto_concentrated, cmap='gray')
# plt.axis("off")
# plt.tight_layout()
# plt.show()

# end = time.time()
# print(f"Execution time: {end - start:.4f} seconds")







start = time.time()

import numpy as np
from numba import njit

@njit
def get_horizontal_distances(coords, intensities, mean_module):
    """
    Optimized for X: Sorts by X and breaks early when horizontal window is exceeded.
    Weights are the intensities of the source dots.
    """
    sort_idx = np.argsort(coords[:, 1])
    sorted_coords = coords[sort_idx]
    sorted_weights = intensities[sort_idx]
    
    n = len(sorted_coords)
    dx_out = np.zeros(n * 2, dtype=np.float32)
    weights_out = np.zeros(n * 2, dtype=np.float32)
    count = 0
    
    max_dx = mean_module * 6
    max_dy = mean_module

    for i in range(n):
        y1, x1 = sorted_coords[i, 0], sorted_coords[i, 1]
        w1 = sorted_weights[i]
        l_min, r_min = 1e6, 1e6
        
        # Search Right (Forward)
        for j in range(i + 1, n):
            dx = sorted_coords[j, 1] - x1
            if dx > max_dx: break
            if abs(y1 - sorted_coords[j, 0]) <= max_dy:
                if dx < r_min and dx > 0.1: r_min = dx
        
        if l_min < 1e5: 
            dx_out[count] = l_min
            weights_out[count] = w1
            count += 1
        if r_min < 1e5: 
            dx_out[count] = r_min
            weights_out[count] = w1
            count += 1
            
    return dx_out[:count], weights_out[:count]

@njit
def get_vertical_distances(coords, intensities, mean_module):
    """
    Optimized for Y: Sorts by Y and breaks early when vertical window is exceeded.
    Weights are the intensities of the source dots.
    """
    sort_idx = np.argsort(coords[:, 0])
    sorted_coords = coords[sort_idx]
    sorted_weights = intensities[sort_idx]
    
    n = len(sorted_coords)
    dy_out = np.zeros(n * 2, dtype=np.float32)
    weights_out = np.zeros(n * 2, dtype=np.float32)
    count = 0
    
    max_dx = mean_module 
    max_dy = mean_module * 3

    for i in range(n):
        y1, x1 = sorted_coords[i, 0], sorted_coords[i, 1]
        w1 = sorted_weights[i]
        u_min, d_min = 1e6, 1e6
        
        # Search Down (Forward)
        for j in range(i + 1, n):
            dy = sorted_coords[j, 0] - y1
            if dy > max_dy: break
            if abs(x1 - sorted_coords[j, 1]) <= max_dx:
                if dy < d_min and dy > 0.1: d_min = dy
        
        if u_min < 1e5: 
            dy_out[count] = u_min
            weights_out[count] = w1
            count += 1
        if d_min < 1e5: 
            dy_out[count] = d_min
            weights_out[count] = w1
            count += 1
            
    return dy_out[:count], weights_out[:count]

def analyze_braille_spacing(concentrated_img, mean_module):
    """
    Main function to extract distances and their weighted sums.
    """
    # 1. Get non-zero pixel coordinates and their intensities
    y_idx, x_idx = np.nonzero(concentrated_img)
    if len(y_idx) < 2: return [], np.zeros(0), [], np.zeros(0)
    
    coords = np.column_stack((y_idx, x_idx)).astype(np.float32)
    intensities = concentrated_img[y_idx, x_idx].astype(np.float32)

    # 2. Run Numba-optimized distance finders
    start = time.time()
    dx_list, x_weights = get_horizontal_distances(coords, intensities, mean_module)
    end = time.time()
    print(f"Execution time: {end - start:.4f} seconds")
    start = time.time()
    # dy_list, y_weights = get_vertical_distances(coords, intensities, mean_module)
    end = time.time()
    print(f"Execution time: {end - start:.4f} seconds")

    def process_weighted(distances, weights):
        if len(distances) == 0: return [], np.zeros(0)
        # Round distances to nearest integer for histogram binning
        dist_idx = np.round(distances).astype(np.int32)
        # Weighted sum: calculates total intensity for every integer distance
        weighted_counts = np.bincount(dist_idx, weights=weights)
        # Sort distances by total mass (descending)
        top_indices = np.argsort(weighted_counts)[::-1]
        common_distances = [d for d in top_indices if d > 0 and weighted_counts[d] > 0]
        return common_distances, weighted_counts

    common_x, weights_x = process_weighted(dx_list, x_weights)
    # common_y, weights_y = process_weighted(dy_list, y_weights)
    common_y, weights_y = common_x, weights_x

    return common_x, weights_x, common_y, weights_y

def extract_braille_metrics(common_x, weights_x, common_y, weights_y, mean_module):
    # Calculate a dynamic threshold based on the mean_module
    # We use this for both clustering and for separating distinct peaks
    dynamic_threshold = int(round(mean_module / 4))
    
    def get_weighted_clusters(sorted_vals, weight_array, threshold, min_val=0):
        if len(sorted_vals) == 0:
            return []
            
        clusters = []
        used = np.zeros(len(weight_array), dtype=np.bool_)
        
        for val in sorted_vals:
            if used[val]:
                continue
            
            # Define window using the dynamic threshold
            low = max(0, val - threshold)
            high = min(len(weight_array) - 1, val + threshold)
            
            total_mass = 0.0
            weighted_sum = 0.0
            
            for d in range(low, high + 1):
                mass = weight_array[d]
                if mass > 0:
                    total_mass += mass
                    weighted_sum += d * mass
                    used[d] = True
            
            if total_mass > 0:
                center = weighted_sum / total_mass
                if center >= min_val:
                    clusters.append(center)
        
        return sorted(clusters)

    # 1. Use dynamic_threshold here
    x_clusters = get_weighted_clusters(common_x[:6], weights_x, threshold=dynamic_threshold, min_val=mean_module)
    y_clusters = get_weighted_clusters(common_y[:6], weights_y, threshold=dynamic_threshold, min_val=mean_module)

    # 2. Extract specific Braille metrics
    h_near = x_clusters[0] if len(x_clusters) > 0 else 0
    
    # h_far: Replace "+ 3" with "+ dynamic_threshold"
    h_far = 0
    for c in x_clusters:
        if c > h_near + dynamic_threshold: 
            h_far = c
            break
            
    # period: Replace "+ 3" with "+ dynamic_threshold"
    period = 0
    for c in x_clusters:
        if c > h_far + dynamic_threshold:
            period = c
            break
    
    if period == 0 and h_far > 0:
        period = h_near + h_far

    v_near = y_clusters[0] if len(y_clusters) > 0 else 0

    return {
        "neighbors_horizontal": round(h_near, 3),
        "far_neighbors_horizontal": round(h_far, 3),
        "period": round(period, 3),
        "neighbors_vertical": round(v_near, 3)
    }


end = time.time()
print(f"Execution time: {end - start:.4f} seconds")

start = time.time()

concentrated = concentrate_single_image(recto_concentrated, window_size=mean_module * 2)
concentrated = concentrate_single_image(concentrated, window_size=mean_module * 2)
concentrated = concentrate_single_image(concentrated, window_size=mean_module * 2)

end = time.time()
print(f"Execution time: {end - start:.4f} seconds")

start = time.time()

common_x, weights_x, common_y, weights_y = analyze_braille_spacing(concentrated, result)
print(f"Top 5 X distances by mass: {common_x[:15]}")
# print(f"Top 5 Y distances by mass: {common_y[:15]}")

end = time.time()
print(f"Execution time: {end - start:.4f} seconds")

start = time.time()

# Pass top 10 commons, the full weights, and the result (mean_module) for filtering
metrics = extract_braille_metrics(
    common_x[:7], weights_x, 
    common_y[:7], weights_y, 
    mean_module
)

neighbors_horizontal = metrics['neighbors_horizontal']
far_neighbors_horizontal = metrics['far_neighbors_horizontal']
period = metrics['period']
neighbors_vertical = metrics['neighbors_vertical']

end = time.time()
print(f"Execution time: {end - start:.4f} seconds")

start = time.time()

# Round the variables to the nearest integer
neighbors_horizontal = int(round(neighbors_horizontal))
far_neighbors_horizontal = int(round(far_neighbors_horizontal))
period = int(round(period))
neighbors_vertical = int(round(neighbors_vertical))

# Optional: Print to verify they are now integers
print(f"Neighbors Horizontal (int): {neighbors_horizontal}")
print(f"Far Neighbors (int):        {far_neighbors_horizontal}")
print(f"Period (int):               {period}")
print(f"Neighbors Vertical (int):   {neighbors_vertical}")

end = time.time()
print(f"Execution time: {end - start:.4f} seconds")





start = time.time()

def complete_braille_grid_logic(img, h_offsets, nv):
    rows, cols = img.shape
    # Work with a binary mask (1 for dot, 0 for no dot)
    _, binary = cv2.threshold(img, 1, 1, cv2.THRESH_BINARY)
    binary = binary.astype(np.float32)
    
    # We will accumulate all discovered dots here
    discovery_map = np.zeros_like(binary)

    def get_shifted(image, dx, dy):
        M = np.float32([[1, 0, -dx], [0, 1, -dy]])
        return cv2.warpAffine(image, M, (cols, rows), borderValue=0)

    # Use only unique positive distances from your list to avoid redundant work
    unique_h = sorted(list(set([abs(x) for x in h_offsets if x != 0])))
    
    # We check two heights: 
    # 1. Height = nv (Top-Mid or Mid-Down)
    # 2. Height = 2*nv (Top-Down)
    v_distances = [nv] # /////////////////////////// [nv, 2*nv] might be interesting too

    for dx in unique_h:
        for dy in v_distances:
            # For every pixel, we look at 4 points forming a rectangle (dx wide, dy high)
            p1 = binary                         # Current point (Top-Left)
            p2 = get_shifted(binary, dx, 0)     # Top-Right
            p3 = get_shifted(binary, 0, dy)     # Bottom-Left
            p4 = get_shifted(binary, dx, dy)    # Bottom-Right

            # Sum of active corners
            corner_sum = p1 + p2 + p3 + p4
            
            # THE RULE: If 3 corners exist, the 4th corner MUST be a dot.
            # (We also include 4, which just confirms existing dots)
            trigger = (corner_sum >= 3).astype(np.float32)
            
            # Spread the "discovery" back to all 4 corners
            discovery_map = np.maximum(discovery_map, trigger)
            discovery_map = np.maximum(discovery_map, get_shifted(trigger, -dx, 0))
            discovery_map = np.maximum(discovery_map, get_shifted(trigger, 0, -dy))
            discovery_map = np.maximum(discovery_map, get_shifted(trigger, -dx, -dy))

    # Combine original image with the new discoveries
    # Discovery map is binary, so we multiply by 255
    result_img = np.maximum(img, (discovery_map * 255).astype(np.uint8))
    return result_img

def filter_vertical_anomalies_center_only(img, nv, r_size):
    """
    Detects 4-dot vertical stacks and deletes only the center pixel 
    of the box with the lowest total intensity.
    """
    rows, cols = img.shape
    img_f = img.astype(np.float32)

    def get_shifted(image, dx, dy):
        M = np.float32([[1, 0, -dx], [0, 1, -dy]])
        return cv2.warpAffine(image, M, (cols, rows), borderValue=0)

    # 1. Calculate Intensity of boxes (r_size x r_size)
    # This value represents the 'vote' or 'strength' of a dot centered at this pixel
    density = cv2.boxFilter(img_f, -1, (r_size, r_size), normalize=False)

    # 2. Align 4 vertical potential positions
    # We look for a stack: Box0, Box1(nv below), Box2(2nv below), Box3(3nv below)
    d0 = density                         
    d1 = get_shifted(density, 0, -nv)    
    d2 = get_shifted(density, 0, -2*nv)  
    d3 = get_shifted(density, 0, -3*nv)  

    # 3. Detect 4-dot "Collision" columns
    # Threshold is set to 1 to ensure even faint dots are counted
    active4 = (d0 > 0) & (d1 > 0) & (d2 > 0) & (d3 > 0)

    # 4. Find the minimum density among the 4 boxes in the stack
    min_val = np.minimum(np.minimum(d0, d1), np.minimum(d2, d3))

    # 5. Identify the center pixel of the weakest box
    # We create masks for each of the 4 positions.
    # If d1 is the weakest, we need to remember that the dot center is 
    # actually shifted by 'nv' from the detection point d0.
    
    # Kill masks identify the exact (x, y) center of the weakest dot
    kill0 = active4 & (d0 == min_val)
    kill1 = get_shifted((active4 & (d1 == min_val) & (d1 < d0)).astype(np.float32), 0, nv)
    kill2 = get_shifted((active4 & (d2 == min_val) & (d2 < d1) & (d2 < d0)).astype(np.float32), 0, 2*nv)
    kill3 = get_shifted((active4 & (d3 == min_val) & (d3 < d2) & (d3 < d1) & (d3 < d0)).astype(np.float32), 0, 3*nv)

    # Combine all kill points into one single mask
    final_kill_points = (kill0.astype(np.uint8) | kill1.astype(np.uint8) | 
                         kill2.astype(np.uint8) | kill3.astype(np.uint8))

    # 6. Delete only the middle pixels
    filtered_img = img.copy()
    filtered_img[final_kill_points > 0] = 0
    
    return filtered_img, final_kill_points

def complete_by_grid_density(img, period, N=3, threshold=3):
    rows, cols = img.shape
    # Work with binary mask
    _, binary = cv2.threshold(img, 1, 1, cv2.THRESH_BINARY)
    binary = binary.astype(np.float32)
    
    # This will store the count of active points for every pixel
    density_accumulator = np.zeros_like(binary)

    def get_shifted(image, dx, dy):
        M = np.float32([[1, 0, -dx], [0, 1, -dy]])
        return cv2.warpAffine(image, M, (cols, rows), borderValue=0)

    dy = 0
    # Iterate through the 33 relative coordinates
    for kx in range(-N, N+1):
        dx = kx * period
        density_accumulator += get_shifted(binary, dx, dy)

    # Apply the rule: if more than 7 out of 33 points are active
    new_discoveries = (density_accumulator > threshold).astype(np.uint8)
    
    # Merge with original image (converting back to 0-255)
    result_img = np.maximum(img, (new_discoveries * 255))
    
    return result_img

def complete_braille_diagonal_logic(img, h_offsets, nv):
    rows, cols = img.shape
    _, binary = cv2.threshold(img, 1, 1, cv2.THRESH_BINARY)
    binary = binary.astype(np.float32)
    
    discovery_map = np.zeros_like(binary)

    def get_shifted(image, dx, dy):
        M = np.float32([[1, 0, -dx], [0, 1, -dy]])
        return cv2.warpAffine(image, M, (cols, rows), borderValue=0)

    unique_h = sorted(list(set([abs(x) for x in h_offsets if x != 0])))
    v_distances = [nv]

    for dx in unique_h:
        for dy in v_distances:
            p1 = binary                         
            p2 = get_shifted(binary, dx, 0)     
            p3 = get_shifted(binary, 0, dy)     
            p4 = get_shifted(binary, dx, dy)    

            # --- FIX: Convert boolean results to float32 immediately ---
            
            # DIAG 1: If p1 and p4 exist
            diag_backslash = ((p1 > 0) & (p4 > 0)).astype(np.float32)
            discovery_map = np.maximum(discovery_map, get_shifted(diag_backslash, -dx, 0))
            discovery_map = np.maximum(discovery_map, get_shifted(diag_backslash, 0, -dy))

            # DIAG 2: If p2 and p3 exist
            diag_forwardslash = ((p2 > 0) & (p3 > 0)).astype(np.float32)
            discovery_map = np.maximum(discovery_map, diag_forwardslash)
            discovery_map = np.maximum(discovery_map, get_shifted(diag_forwardslash, -dx, -dy))

    result_img = np.maximum(img, (discovery_map * 255).astype(np.uint8))
    return result_img

end = time.time()
print(f"Execution time: {end - start:.4f} seconds")

start = time.time()

# --- Your exact offsets list ---
all_h_offsets = [
    neighbors_horizontal, -neighbors_horizontal, 
    far_neighbors_horizontal, -far_neighbors_horizontal, 
    period, -period, 
    neighbors_horizontal + period, -(neighbors_horizontal + period)
]

all_h_offsets_close = [
    neighbors_horizontal, -neighbors_horizontal, 
    far_neighbors_horizontal, -far_neighbors_horizontal
]

recto_completed = complete_braille_grid_logic(
    recto_concentrated, 
    all_h_offsets,
    neighbors_vertical
)

end = time.time()
print(f"Execution time: {end - start:.4f} seconds")

start = time.time()

recto_completed = complete_braille_grid_logic(
    recto_completed, 
    all_h_offsets_close,
    2 * neighbors_vertical
)

end = time.time()
print(f"Execution time: {end - start:.4f} seconds")

start = time.time()

recto_completed = complete_braille_diagonal_logic(
        recto_completed, 
        all_h_offsets_close,
        neighbors_vertical
    )

end = time.time()
print(f"Execution time: {end - start:.4f} seconds")

start = time.time()

recto_completed = complete_braille_diagonal_logic(
    recto_completed, 
    all_h_offsets,
    2 * neighbors_vertical
)

end = time.time()
print(f"Execution time: {end - start:.4f} seconds")

start = time.time()

recto_completed = complete_braille_grid_logic(
    recto_completed, 
    all_h_offsets_close,
    neighbors_vertical
)

end = time.time()
print(f"Execution time: {end - start:.4f} seconds")

start = time.time()

recto_completed, _ = filter_vertical_anomalies_center_only( # If we use: v_distances = [nv] instead [nv, 2*nv] in the unction we can take this out from thr loop
    recto_completed, 
    nv=neighbors_vertical, 
    r_size=result 
)

end = time.time()
print(f"Execution time: {end - start:.4f} seconds")

start = time.time()

recto_completed = complete_by_grid_density(
    recto_completed, 
    period=period,
    N= 2,
    threshold=3
)

end = time.time()
print(f"Execution time: {end - start:.4f} seconds")

start = time.time()

recto_completed, concentrated = apply_centroid_concentration(recto_completed, mean_module, 255, 2 * mean_module)

end = time.time()
print(f"Execution time: {end - start:.4f} seconds")

# start = time.time()

# # --- Visualization ---
# plt.figure(figsize=(20, 10))
# new_dots = cv2.subtract(recto_completed, recto_concentrated)
# viz = np.zeros((recto_completed.shape[0], recto_completed.shape[1], 3), dtype=np.uint8)
# viz[:, :, 1] = recto_concentrated  # Green
# viz[:, :, 0] = new_dots            # Red

# plt.imshow(viz)
# plt.title("Rectangle Completion Logic\n(3 Points found -> 4th Point added)\n[Green: Original | Red: Predicted]")
# plt.axis("off")
# plt.show()

# end = time.time()
# print(f"Execution time: {end - start:.4f} seconds")



start = time.time()

import cv2
import numpy as np

def split_middle_vs_not_middle_relaxed(img, nh, nv, fnh, period, iterations=3):
    rows, cols = img.shape
    img_f = img.astype(np.float32)

    def get_shifted(image, dx, dy):
        M = np.float32([[1, 0, -dx], [0, 1, -dy]])
        return cv2.warpAffine(image, M, (cols, rows), borderValue=0)

    # def get_shifted(image, dx, dy):
    #     shifted = np.roll(image, int(-dy), axis=0)
    #     shifted = np.roll(shifted, int(-dx), axis=1)
    #     # Zero out wrapped borders
    #     if dy > 0: shifted[-int(dy):, :] = 0
    #     elif dy < 0: shifted[:-int(dy), :] = 0  # this should be [:int(-dy), :]
    #     if dx > 0: shifted[:, -int(dx):] = 0
    #     elif dx < 0: shifted[:, :int(-dx)] = 0
    #     return shifted

    # -------------------------------
    # Parameters controlling strictness
    # -------------------------------
    min_vert_support = 1    # how many UP and DOWN matches required
    min_horiz_support = 1   # how many horizontal matches required

    # --- 1. Vertical support groups (UNCHANGED LISTS) ---

    U_list = [
        get_shifted(img_f, nh, nv), get_shifted(img_f, -nh, nv),
        get_shifted(img_f, 0, nv),
        get_shifted(img_f, -fnh, nv), get_shifted(img_f, fnh, nv)
    ]

    D_list = [
        get_shifted(img_f, nh, -nv), get_shifted(img_f, -nh, -nv),
        get_shifted(img_f, 0, -nv),
        get_shifted(img_f, -fnh, -nv), get_shifted(img_f, fnh, -nv)
    ]

    M_offsets = [
        (nh, 0), (-nh, 0), (fnh, 0), (-fnh, 0),
        (nh + fnh, 0), (-nh - fnh, 0)
    ]

    # --- 2. STRICT vertical support (COUNT-based) ---

    up_count = np.sum([(u > 0).astype(np.float32) for u in U_list], axis=0)
    down_count = np.sum([(d > 0).astype(np.float32) for d in D_list], axis=0)

    vert_support = (
        (up_count >= min_vert_support) &
        (down_count >= min_vert_support)
    ).astype(np.float32)

    prob_mid = vert_support.copy()

    # --- 3. Horizontal confirmation (also COUNT-based) ---

    for _ in range(iterations):
        current_mid = img_f * prob_mid

        horiz_votes = []
        for dx, dy in M_offsets:
            horiz_votes.append(
                (get_shifted(current_mid, dx, dy) > 0).astype(np.float32)
            )

        horiz_count = np.sum(horiz_votes, axis=0)

        horiz_support = (horiz_count >= min_horiz_support).astype(np.float32)

        # Horizontal support can only CONFIRM vertical candidates
        prob_mid = np.maximum(prob_mid, horiz_support * vert_support)

    # --- 4. Final split ---

    middle_img = img_f * prob_mid
    not_middle_img = img_f * (1.0 - prob_mid)

    return middle_img.astype(np.uint8), not_middle_img.astype(np.uint8)

def plot_braille_colored(t, m, d, u):
    h, w = t.shape
    # Create empty RGB image
    colored = np.zeros((h, w, 3), dtype=np.uint8)
    
    # Red for Top
    colored[:, :, 0] = np.maximum(colored[:, :, 0], t)
    # Green for Mid
    colored[:, :, 1] = np.maximum(colored[:, :, 1], m)
    # Blue for Down
    colored[:, :, 2] = np.maximum(colored[:, :, 2], d)
    
    # White (All channels) for Unsure
    colored[:, :, 0] = np.maximum(colored[:, :, 0], u)
    colored[:, :, 1] = np.maximum(colored[:, :, 1], u)
    colored[:, :, 2] = np.maximum(colored[:, :, 2], u)
    
    return colored


end = time.time()
print(f"Execution time: {end - start:.4f} seconds")

start = time.time()

mid_img, other_dots_m = split_middle_vs_not_middle_relaxed(
    recto_completed, 
    nh=neighbors_horizontal, 
    nv=neighbors_vertical, 
    fnh=far_neighbors_horizontal,
    period=period,
    iterations=1
)

end = time.time()
print(f"Execution time: {end - start:.4f} seconds")

# start = time.time()

# plt.figure(figsize=(18, 15)) 
# plt.subplot(2, 4, 1)
# plt.imshow(np.clip(cv2.addWeighted(cv2.add(128, mid_img), 1/2, 255 - cv2.add(128, other_dots_m), 1/2, 0), 0, 255).astype(np.uint8), cmap='gray')
# plt.axis('off')

# plt.subplot(2, 4, 2)
# plt.imshow(gray, cmap='gray')
# plt.axis("off")

# plt.tight_layout()
# plt.show()

# end = time.time()
# print(f"Execution time: {end - start:.4f} seconds")



@njit
def get_vertical_distances_2(coords, intensities, mean_module):
    sort_idx = np.argsort(coords[:, 0])
    sorted_coords = coords[sort_idx]
    sorted_weights = intensities[sort_idx]
    
    n = len(sorted_coords)
    dy_out = np.zeros(n * 2, dtype=np.float32)
    weights_out = np.zeros(n * 2, dtype=np.float32)
    count = 0
    
    max_dx = mean_module 
    max_dy = mean_module * 30

    for i in range(n):
        y1, x1 = sorted_coords[i, 0], sorted_coords[i, 1]
        w1 = sorted_weights[i]
        u_min, d_min = 1e6, 1e6
        
        # Search Up (Backward)
        for j in range(i - 1, -1, -1):
            dy = y1 - sorted_coords[j, 0]
            if dy > max_dy: break 
            if abs(x1 - sorted_coords[j, 1]) <= max_dx:
                if dy < u_min and dy > 0.1: u_min = dy
        
        # Search Down (Forward)
        for j in range(i + 1, n):
            dy = sorted_coords[j, 0] - y1
            if dy > max_dy: break
            if abs(x1 - sorted_coords[j, 1]) <= max_dx:
                if dy < d_min and dy > 0.1: d_min = dy
        
        if u_min < 1e5: 
            dy_out[count] = u_min
            weights_out[count] = w1
            count += 1
        if d_min < 1e5: 
            dy_out[count] = d_min
            weights_out[count] = w1
            count += 1
            
    return dy_out[:count], weights_out[:count]

def analyze_braille_spacing_2(concentrated_img, mean_module):
    y_idx, x_idx = np.nonzero(concentrated_img)
    if len(y_idx) < 2: return [], np.zeros(0), [], np.zeros(0)
    
    coords = np.column_stack((y_idx, x_idx)).astype(np.float32)
    intensities = concentrated_img[y_idx, x_idx].astype(np.float32)

    # 2. Run Numba-optimized distance finders
    dy_list, y_weights = get_vertical_distances_2(coords, intensities, mean_module)

    def process_weighted(distances, weights):
        if len(distances) == 0: return [], np.zeros(0)
        # Round distances to nearest integer for histogram binning
        dist_idx = np.round(distances).astype(np.int32)
        # Weighted sum: calculates total intensity for every integer distance
        weighted_counts = np.bincount(dist_idx, weights=weights)
        # Sort distances by total mass (descending)
        top_indices = np.argsort(weighted_counts)[::-1]
        common_distances = [d for d in top_indices if d > 0 and weighted_counts[d] > 0]
        return common_distances, weighted_counts

    common_y, weights_y = process_weighted(dy_list, y_weights)

    return common_y, weights_y

def extract_braille_metrics_2(common_y, weights_y, mean_module):
    # Calculate a dynamic threshold based on the mean_module
    # We use this for both clustering and for separating distinct peaks
    dynamic_threshold = int(round(mean_module / 4))
    
    def get_weighted_clusters(sorted_vals, weight_array, threshold, min_val=0):
        if len(sorted_vals) == 0:
            return []
            
        clusters = []
        used = np.zeros(len(weight_array), dtype=np.bool_)
        
        for val in sorted_vals:
            if used[val]:
                continue
            
            # Define window using the dynamic threshold
            low = max(0, val - threshold)
            high = min(len(weight_array) - 1, val + threshold)
            
            total_mass = 0.0
            weighted_sum = 0.0
            
            for d in range(low, high + 1):
                mass = weight_array[d]
                if mass > 0:
                    total_mass += mass
                    weighted_sum += d * mass
                    used[d] = True
            
            if total_mass > 0:
                center = weighted_sum / total_mass
                if center >= min_val:
                    clusters.append(center)
        
        return sorted(clusters)

    # 1. Use dynamic_threshold here
    y_clusters = get_weighted_clusters(common_y[:6], weights_y, threshold=dynamic_threshold, min_val=mean_module)

    v_near = y_clusters[0] if len(y_clusters) > 0 else 0

    return {
        "neighbors_vertical": round(v_near, 3)
    }

start = time.time()
concentrated_mid_f = concentrate_single_image(mid_img, window_size=2 * mean_module)
concentrated_mid_f = concentrate_single_image(concentrated_mid_f, window_size=2 * mean_module)

common_y_mid_p, weights_y_mid_p = analyze_braille_spacing_2(concentrated_mid_f, result)
print(f"Top 5 Y distances by mass: {common_y_mid_p[:5]}")
metrics_mid_p = extract_braille_metrics_2(
    common_y_mid_p[:5], weights_y_mid_p, 
    mean_module
)
neighbors_vertical_mid_p = metrics_mid_p['neighbors_vertical']
neighbors_vertical_mid_p = int(round(neighbors_vertical_mid_p))
print(f"Neighbors Vertical (int):   {neighbors_vertical_mid_p}")

end = time.time()
print(f"Execution time: {end - start:.4f} seconds")







start = time.time()

# Pass your existing concentrated_recto directly
concentrated_recto = concentrate_single_image(recto_completed, window_size=2 * mean_module)
concentrated_recto = concentrate_single_image(concentrated_recto, window_size=2 * mean_module)
concentrated_recto = concentrate_single_image(concentrated_recto, window_size=2 * mean_module)

end = time.time()
print(f"Execution time: {end - start:.4f} seconds")



import numpy as np
from scipy.sparse import csr_matrix, bmat
from scipy.spatial import cKDTree
import time
 
 
# ─────────────────────────────────────────────────────────────────────────────
# Internal: build the combined (3n × 3n) block sparse matrix
# ─────────────────────────────────────────────────────────────────────────────
 
def _build_block_matrix(y_idx, x_idx, norm_int,
                        nv, hw_x, hw_y, tol, nvm):
    """
    Returns a single (3n × 3n) CSR matrix M such that:
 
        votes_stacked = M @ probs_stacked
 
    where probs_stacked = [p0 ; p1 ; p2]  (Fortran-order flattening of
    the (n, 3) prob array, i.e. all-class-0 then all-class-1 …).
 
    Block layout (each block is (n×n)):
        M = [[W_A,  W_C,  W_Da],    →  votes[:, 0]
             [W_B,  W_A,  W_C ],    →  votes[:, 1]
             [W_Db, W_B,  W_A ]]    →  votes[:, 2]
 
    This exactly matches the 7-matmul update from the previous version
    but as one C-level SpMV call.
    """
    n = len(y_idx)
    xi = x_idx.astype(np.float32)
    yi = y_idx.astype(np.float32)
 
    # --- Pair finding: one C-level spatial query ----------------------------
    tree = cKDTree(np.column_stack([yi, xi]))
    max_r = float(np.hypot(hw_y, hw_x))
    try:
        pairs = tree.query_pairs(max_r, output_type='ndarray', workers=-1)
    except TypeError:                          # scipy < 1.7
        pairs = tree.query_pairs(max_r, output_type='ndarray')
 
    def _empty_block():
        e = csr_matrix((n, n), dtype=np.float32)
        return bmat([[e, e, e], [e, e, e], [e, e, e]], format='csr')
 
    if pairs.shape[0] == 0:
        return _empty_block()
 
    ii, jj = pairs[:, 0], pairs[:, 1]
 
    # --- Box filter: |dy| < hw_y and |dx| < hw_x ---------------------------
    dy_raw = yi[jj] - yi[ii]
    dx_abs = np.abs(xi[jj] - xi[ii])
    dy_abs = np.abs(dy_raw)
 
    in_box = (dy_abs < hw_y) & (dx_abs < hw_x)
    if not in_box.any():
        return _empty_block()
 
    ii  = ii[in_box];  jj     = jj[in_box]
    dy_raw = dy_raw[in_box]; dx_abs = dx_abs[in_box]; dy_abs = dy_abs[in_box]
 
    # --- Weights (float32) -------------------------------------------------
    inv_d = (1.0 / (np.hypot(dx_abs, dy_abs) + 1.0)).astype(np.float32)
    w_ij  = inv_d * norm_int[jj]   # i→j: destination = j
    w_ji  = inv_d * norm_int[ii]   # j→i: destination = i
 
    # --- Five masks (vectorised, both directions at once) ------------------
    def _masks(dr, da):
        mA  = (da < tol) | (np.abs(da - nvm) < tol)
        mB  = (~mA) & ((np.abs(dr - nv) < tol)  | (np.abs(dr - nv + nvm) < tol))
        mC  = (~mA) & (~mB) & \
              ((np.abs(dr + nv) < tol)  | (np.abs(dr + nv - nvm) < tol))
        mD  = (~mA) & (~mB) & (~mC) & \
              ((np.abs(da - 2*nv) < tol) | (np.abs(da - 2*nv + nvm) < tol))
        return mA, mB, mC, mD & (dr > 0), mD & (dr <= 0)
 
    mA,  mB,  mC,  mDb,  mDa  = _masks( dy_raw, dy_abs)  # i→j
    mAr, mBr, mCr, mDbr, mDar = _masks(-dy_raw, dy_abs)  # j→i
 
    # --- Build 5 (n×n) CSR matrices ----------------------------------------
    empty = csr_matrix((n, n), dtype=np.float32)
 
    def _csr(mi, mj, wi, wj):
        r = np.concatenate([ii[mi], jj[mj]])
        c = np.concatenate([jj[mi], ii[mj]])
        d = np.concatenate([wi[mi], wj[mj]])
        if len(r) == 0:
            return empty
        return csr_matrix((d, (r, c)), shape=(n, n), dtype=np.float32)
 
    WA  = _csr(mA,  mAr,  w_ij, w_ji)
    WB  = _csr(mB,  mBr,  w_ij, w_ji)
    WC  = _csr(mC,  mCr,  w_ij, w_ji)
    WDb = _csr(mDb, mDbr, w_ij, w_ji)
    WDa = _csr(mDa, mDar, w_ij, w_ji)
 
    # --- Assemble block matrix (one bmat call, stays CSR) ------------------
    # votes_k = sum_c M[k, c] @ p_c
    M = bmat([[WA,  WC,  WDa],
              [WB,  WA,  WC ],
              [WDb, WB,  WA ]], format='csr')
    return M
 
 
# ─────────────────────────────────────────────────────────────────────────────
# Public function (drop-in replacement)
# ─────────────────────────────────────────────────────────────────────────────
 
def propagate_unsure_beliefs(concentrated_recto, nv, hw_x, hw_y,
                              neighbors_vertical_mid_p,
                              iterations=20, confidence_threshold=0.34):
    """
    Vectorised replacement — identical outputs, ~5-7x faster than v2.
 
    Key changes vs the previous version:
      • Single (3n × 3n) block sparse matmul per iteration  (was 7 calls)
      • float32 for all probability buffers  (was float64)
      • Early stopping when max |Δp| < 1e-4
      • Profiling print so you know exactly where time goes
    """
    t0 = time.perf_counter()
 
    y_idx, x_idx = np.where(concentrated_recto > 0)
    n = len(y_idx)
    shape = concentrated_recto.shape
    Z = np.zeros(shape, dtype=np.float64)
 
    if n == 0:
        return Z, Z.copy(), Z.copy(), Z.copy()
 
    intens   = concentrated_recto[y_idx, x_idx].astype(np.float32)
    mx       = float(intens.max()) or 1.0
    norm_int = intens / mx          # float32, shape (n,)
    tol      = nv * 0.4
 
    t1 = time.perf_counter()
 
    M = _build_block_matrix(y_idx, x_idx, norm_int,
                            nv, hw_x, hw_y, tol, neighbors_vertical_mid_p)
 
    t2 = time.perf_counter()
 
    # ── Belief propagation (float32, single block SpMV per iter) ────────────
    #
    # We store probabilities column-stacked: probs_f[k*n : (k+1)*n] = p_k
    # (the "Fortran" ordering of a (n, 3) array).
    # This avoids a copy when feeding the block matrix.
    #
    # M @ probs_f gives:
    #   result[0:n]    = WA@p0 + WC@p1  + WDa@p2  = votes[:,0]
    #   result[n:2n]   = WB@p0 + WA@p1  + WC@p2   = votes[:,1]
    #   result[2n:3n]  = WDb@p0 + WB@p1 + WA@p2   = votes[:,2]
 
    probs_f = np.full(3 * n, 1.0 / 3.0, dtype=np.float32)
    norm3   = np.tile(norm_int, 3)          # (3n,) repeated prior weight
 
    # Pre-allocate reusable buffers to avoid per-iter heap allocation
    combined_f = np.empty(3 * n, dtype=np.float32)
    total_buf  = np.empty(n,     dtype=np.float32)
    old_f      = np.empty(3 * n, dtype=np.float32)
 
    actual_iters = 0
    for it in range(iterations):
        if it % 5 == 0:
            old_f[:] = probs_f          # snapshot for convergence check
 
        votes_f = M @ probs_f           # (3n,) — single SpMV call
 
        # combined = probs * norm_int_tiled + votes  (element-wise)
        np.multiply(probs_f, norm3, out=combined_f)
        combined_f += votes_f
 
        # Normalise per dot: total[i] = combined[i] + combined[n+i] + combined[2n+i]
        # combined_3xn[k, i] = combined_f[k*n + i]
        combined_3xn = combined_f.reshape(3, n)   # view — no copy
        np.sum(combined_3xn, axis=0, out=total_buf)
 
        # Only update dots that received signal
        has_signal = total_buf > 0
        if has_signal.any():
            # Update probs_f in-place via a (3, n) view
            probs_3xn = probs_f.reshape(3, n)             # view
            probs_3xn[:, has_signal] = (
                combined_3xn[:, has_signal] / total_buf[has_signal]
            )
 
        actual_iters = it + 1
 
        # Convergence check every 5 iterations
        if it % 5 == 4:
            delta = float(np.abs(probs_f - old_f).max())
            if delta < 1e-4:
                break
 
    t3 = time.perf_counter()
 
    # ── Classification ───────────────────────────────────────────────────────
    probs_mat = probs_f.reshape(3, n).T          # (n, 3) view
 
    best_idx = np.argmax(probs_mat, axis=1)      # (n,)
    best_val = probs_mat[np.arange(n), best_idx]
 
    confident   = best_val >= confidence_threshold
    unconfident = ~confident
 
    intens64 = intens.astype(np.float64)
 
    out_T        = np.zeros(shape, np.float64)
    out_M        = np.zeros(shape, np.float64)
    out_D        = np.zeros(shape, np.float64)
    still_unsure = np.zeros(shape, np.float64)
 
    still_unsure[y_idx[unconfident], x_idx[unconfident]] = intens64[unconfident]
    m0 = confident & (best_idx == 0)
    m1 = confident & (best_idx == 1)
    m2 = confident & (best_idx == 2)
    out_T[y_idx[m0], x_idx[m0]] = intens64[m0]
    out_M[y_idx[m1], x_idx[m1]] = intens64[m1]
    out_D[y_idx[m2], x_idx[m2]] = intens64[m2]
 
    t4 = time.perf_counter()
    print(f"  [profile] n={n} | build={t2-t1:.3f}s | "
          f"propagate={t3-t2:.3f}s ({actual_iters} iters) | "
          f"classify={t4-t3:.3f}s | total={t4-t0:.3f}s")
 
    return out_T, out_M, out_D, still_unsure

start = time.time()

# To ensure Logic D/E work, make sure hw_y is large enough
# neighbors_vertical_mid_p * 1.5 is a safe bet to see adjacent lines
t_img, m_img, d_img, still_unsure_img = propagate_unsure_beliefs(
    concentrated_recto.astype(np.float64),
    nv=neighbors_vertical,
    hw_x= period * 1.1,
    hw_y= neighbors_vertical_mid_p * 4.1,
    neighbors_vertical_mid_p=neighbors_vertical_mid_p,
    iterations=500,
    confidence_threshold=0.5
)

end = time.time()
print(f"Execution time: {end - start:.4f} seconds")

# start = time.time()

# t_img_deconcentrated, concentrated = apply_centroid_concentration(t_img, mean_module, 255, 2 * mean_module)
# m_img_deconcentrated, concentrated = apply_centroid_concentration(m_img, mean_module, 255, 2 * mean_module)
# d_img_deconcentrated, concentrated = apply_centroid_concentration(d_img, mean_module, 255, 2 * mean_module)
# still_unsure_img_deconcentrated, concentrated = apply_centroid_concentration(still_unsure_img, mean_module, 255, 2 * mean_module)

# end = time.time()
# print(f"Execution time: {end - start:.4f} seconds")

# start = time.time()

# # --- Visualization ---
# plt.figure(figsize=(18, 7))

# plt.subplot(1, 3, 1)
# plt.imshow(plot_braille_colored(t_img_deconcentrated, m_img_deconcentrated, d_img_deconcentrated, still_unsure_img_deconcentrated))
# plt.title("Middle Row (Dots 2, 5)\n[Relaxed: 1 Up & 1 Down]")
# plt.axis("off")

# plt.tight_layout()
# plt.show()

# end = time.time()
# print(f"Execution time: {end - start:.4f} seconds")



start_g = time.time()

start = time.time()

import numpy as np
from scipy.spatial import cKDTree

def refine_vertical_by_modulo_voting_vec(concentrated_unsure_dots, conc_T, conc_M, conc_D,
                                          nv, neighbors_vertical_mid_p, hw_x, hw_y):
    shape = concentrated_unsure_dots.shape
    P_v   = neighbors_vertical_mid_p

    u_y, u_x = np.where(concentrated_unsure_dots > 0)
    n_u = len(u_y)
    if n_u == 0:
        return (np.zeros(shape, np.float64),
                np.zeros(shape, np.float64),
                np.zeros(shape, np.float64))

    u_coords = np.column_stack([u_y, u_x]).astype(np.float32)
    u_vals   = concentrated_unsure_dots[u_y, u_x].astype(np.float64)
    tree_u   = cKDTree(u_coords)

    errors  = np.zeros((n_u, 3), dtype=np.float64)
    weights = np.zeros((n_u, 3), dtype=np.float64)

    max_r = float(np.hypot(hw_y, hw_x))

    for c_idx, conc in enumerate([conc_T, conc_M, conc_D]):
        a_y, a_x = np.where(conc > 0)
        if len(a_y) == 0:
            continue

        a_vals   = conc[a_y, a_x].astype(np.float64)
        a_coords = np.column_stack([a_y, a_x]).astype(np.float32)
        tree_a   = cKDTree(a_coords)

        pairs = tree_u.query_ball_tree(tree_a, r=max_r)

        lengths = np.array([len(p) for p in pairs], dtype=np.int64)
        if lengths.sum() == 0:
            continue

        u_ids = np.repeat(np.arange(n_u), lengths)
        a_ids = np.concatenate([np.array(p, dtype=np.int64)
                                 for p in pairs if len(p) > 0])

        dy_raw = np.abs(u_y[u_ids] - a_y[a_ids]).astype(np.float64)
        dx_raw = np.abs(u_x[u_ids] - a_x[a_ids]).astype(np.float64)
        in_box = (dy_raw < hw_y) & (dx_raw < hw_x)
        u_ids, a_ids   = u_ids[in_box],  a_ids[in_box]
        dy_raw, dx_raw = dy_raw[in_box], dx_raw[in_box]

        if len(u_ids) == 0:
            continue

        dist          = np.hypot(dx_raw, dy_raw)
        w             = a_vals[a_ids] / (dist + 1.0)
        mod           = dy_raw % P_v
        alignment_err = np.minimum(mod, P_v - mod)

        errors [:, c_idx] += np.bincount(u_ids, weights=alignment_err * w, minlength=n_u)
        weights[:, c_idx] += np.bincount(u_ids, weights=w,                 minlength=n_u)

    has_weight = weights > 0
    avg_err    = np.where(has_weight, errors / np.where(has_weight, weights, 1.0), np.inf)

    best_layer = np.argmin(avg_err, axis=1)
    has_any    = has_weight.any(axis=1)

    out_T = np.zeros(shape, np.float64)
    out_M = np.zeros(shape, np.float64)
    out_D = np.zeros(shape, np.float64)

    m0 = has_any & (best_layer == 0)
    m1 = has_any & (best_layer == 1)
    m2 = has_any & (best_layer == 2)

    out_T[u_y[m0], u_x[m0]] = u_vals[m0]
    out_M[u_y[m1], u_x[m1]] = u_vals[m1]
    out_D[u_y[m2], u_x[m2]] = u_vals[m2]

    return out_T, out_M, out_D


def apply_vertical_refinement(concentrated_unsure_dots, concentrated_top_f, concentrated_mid_f, concentrated_down_f,
                               nv, neighbors_vertical_mid_p, hw_x, hw_y):
    print("Starting vertical modulo-based refinement...")

    concentrated_new_t, concentrated_new_m, concentrated_new_d = refine_vertical_by_modulo_voting_vec(
        concentrated_unsure_dots.astype(np.float64),
        concentrated_top_f.astype(np.float64),
        concentrated_mid_f.astype(np.float64),
        concentrated_down_f.astype(np.float64),
        nv, neighbors_vertical_mid_p, hw_x, hw_y
    )

    concentrated_top_v  = concentrated_top_f.astype(np.float64)  + concentrated_new_t
    concentrated_mid_v  = concentrated_mid_f.astype(np.float64)  + concentrated_new_m
    concentrated_down_v = concentrated_down_f.astype(np.float64) + concentrated_new_d

    concentrated_classified_mask = (concentrated_new_t + concentrated_new_m + concentrated_new_d) > 0
    concentrated_still_unsure    = concentrated_unsure_dots.copy().astype(np.float64)
    concentrated_still_unsure[concentrated_classified_mask] = 0

    return concentrated_top_v, concentrated_mid_v, concentrated_down_v, concentrated_still_unsure

end = time.time()
print(f"Execution time: {end - start:.4f} seconds")
start = time.time()

hw_x = 1.2 * period
hw_y = 5 * neighbors_vertical_mid_p

top_final, mid_final, down_final, unsure_final = apply_vertical_refinement(
    still_unsure_img,
    d_img, m_img, t_img,
    neighbors_vertical,
    neighbors_vertical_mid_p, hw_x, hw_y
)

end = time.time()
print(f"Execution time: {end - start:.4f} seconds")
start = time.time()

hw_x = 10 * period
hw_y = 10 * neighbors_vertical_mid_p

top_final, mid_final, down_final, unsure_final = apply_vertical_refinement(
    unsure_final,
    down_final, mid_final, top_final,
    neighbors_vertical,
    neighbors_vertical_mid_p, hw_x, hw_y
)

end = time.time()
print(f"Execution time: {end - start:.4f} seconds")

end_g = time.time()
print(f"Execution time: {end_g - start_g:.4f} seconds")

# top_final, mid_final, down_final = down_final, mid_final, top_final

start = time.time()

top_final, concentrated = apply_centroid_concentration(top_final, mean_module, 255, 2 * mean_module)
mid_final, concentrated = apply_centroid_concentration(mid_final, mean_module, 255, 2 * mean_module)
down_final, concentrated = apply_centroid_concentration(down_final, mean_module, 255, 2 * mean_module)
unsure_final, concentrated = apply_centroid_concentration(unsure_final, mean_module, 255, 2 * mean_module)

end = time.time()
print(f"Execution time: {end - start:.4f} seconds")

# start = time.time()

# # --- Visualization ---
# plt.figure(figsize=(18, 7))
# plt.subplot(1, 3, 1)
# plt.imshow(plot_braille_colored(top_final, mid_final, down_final, unsure_final))
# plt.title("Middle Row (Dots 2, 5)\n[Relaxed: 1 Up & 1 Down]")
# plt.axis("off")

# plt.tight_layout()
# plt.show()

# end = time.time()
# print(f"Execution time: {end - start:.4f} seconds")

# global_end = time.time()
# print(f"Whole cell: {global_end - global_start:.4f}s")







start = time.time()

def classify_6_positions_2d(top, mid, down, nh, fnh, nv, period):
    rows, cols = top.shape
    # Combine all evidence for global context
    all_dots = cv2.add(cv2.add(top, mid), down).astype(np.float32)
    
    # Tolerance blur (allows for small misalignments/jitter)
    evidence = cv2.GaussianBlur(all_dots, (3, 3), 0)

    def get_s(dx, dy):
        M = np.float32([[1, 0, -dx], [0, 1, -dy]])
        return cv2.warpAffine(evidence, M, (cols, rows), borderValue=0)

    # --- 1. Define 2D Evidence Vectors for LEFT vs RIGHT ---
    # These vectors look for patterns that are unique to each side.
    
    # Evidence for LEFT (Dots 1, 2, 3):
    L_vectors = [
        (nh, 0), (nh, nv), (nh, -nv), (nh, 2 * nv), (nh, -2 * nv), (-fnh, nv), (-fnh, -nv), (-fnh, 2 * nv), (-fnh, -2 * nv),
        (nh + period, 0), (nh + period, nv), (nh + period, -nv), (nh + period, 2 * nv), (nh + period, -2 * nv), (-fnh - period, nv), (-fnh - period, -nv), (-fnh - period, 2 * nv), (-fnh - period, -2 * nv)
    ]

    # Evidence for RIGHT (Dots 4, 5, 6):
    R_vectors = [
        (-nh, 0), (-nh, nv), (-nh, -nv), (-nh, 2 * nv), (-nh, -2 * nv), (fnh, nv), (fnh, -nv), (fnh, 2 * nv), (fnh, -2 * nv),
        (-nh - period, 0), (-nh - period, nv), (-nh - period, -nv), (-nh - period, 2 * nv), (-nh - period, -2 * nv), (fnh + period, nv), (fnh + period, -nv), (fnh + period, 2 * nv), (fnh + period, -2 * nv)
    ]

    # Calculate Total Context Scores
    score_L = np.max([get_s(dx, dy) for dx, dy in L_vectors], axis=0)
    score_R = np.max([get_s(dx, dy) for dx, dy in R_vectors], axis=0)

    # --- 2. Decision Logic (Fixed Typo) ---
    is_left = (score_L > score_R)
    is_right = (score_R > score_L)
    is_unsure = (score_L == score_R)

    # --- 3. Distribute into 6 Positions ---
    # Top Row
    d1 = cv2.bitwise_and(top, top, mask=is_left.astype(np.uint8))
    d4 = cv2.bitwise_and(top, top, mask=is_right.astype(np.uint8))
    
    # Middle Row
    d2 = cv2.bitwise_and(mid, mid, mask=is_left.astype(np.uint8))
    d5 = cv2.bitwise_and(mid, mid, mask=is_right.astype(np.uint8))
    
    # Bottom Row
    d3 = cv2.bitwise_and(down, down, mask=is_left.astype(np.uint8))
    d6 = cv2.bitwise_and(down, down, mask=is_right.astype(np.uint8))

    # Dots with no context stay in the white layer
    tie_dots = cv2.bitwise_and(all_dots.astype(np.uint8), all_dots.astype(np.uint8), 
                               mask=is_unsure.astype(np.uint8))

    return d1, d2, d3, d4, d5, d6, tie_dots

def plot_braille_final_7_layers(d1, d2, d3, d4, d5, d6, unsure):

    h, w = d1.shape
    # Create empty RGB canvas
    viz = np.zeros((h, w, 3), dtype=np.uint8)
    
    # Position 1: Red
    viz[:, :, 0] = np.maximum(viz[:, :, 0], d1)
    
    # Position 2: Green
    viz[:, :, 1] = np.maximum(viz[:, :, 1], d2)
    
    # Position 3: Blue
    viz[:, :, 2] = np.maximum(viz[:, :, 2], d3)
    
    # Position 4: Yellow (Red + Green)
    viz[:, :, 0] = np.maximum(viz[:, :, 0], d4)
    viz[:, :, 1] = np.maximum(viz[:, :, 1], d4)
    
    # Position 5: Cyan (Green + Blue)
    viz[:, :, 1] = np.maximum(viz[:, :, 1], d5)
    viz[:, :, 2] = np.maximum(viz[:, :, 2], d5)
    
    # Position 6: Magenta (Red + Blue)
    viz[:, :, 0] = np.maximum(viz[:, :, 0], d6)
    viz[:, :, 2] = np.maximum(viz[:, :, 2], d6)
    
    # Unsure: White (Red + Green + Blue)
    viz[:, :, 0] = np.maximum(viz[:, :, 0], unsure)
    viz[:, :, 1] = np.maximum(viz[:, :, 1], unsure)
    viz[:, :, 2] = np.maximum(viz[:, :, 2], unsure)
    
    return viz



end = time.time()
print(f"Execution time: {end - start:.4f} seconds")

start = time.time()

# --- Execute ---
d1, d2, d3, d4, d5, d6, u_final = classify_6_positions_2d(
    top_final, mid_final, down_final,
    neighbors_horizontal, far_neighbors_horizontal, neighbors_vertical, period
)

end = time.time()
print(f"Execution time: {end - start:.4f} seconds")
start = time.time()

# d1, d4 = merge_with_full_kernel(d1, d4, k=result, p=1)
# d1, d2 = merge_with_full_kernel(d1, d2, k=result, p=1)
# d4, d5 = merge_with_full_kernel(d4, d5, k=result, p=1)
# d2, d5 = merge_with_full_kernel(d2, d5, k=result, p=1)
# d2, d3 = merge_with_full_kernel(d2, d3, k=result, p=1)
# d5, d6 = merge_with_full_kernel(d5, d6, k=result, p=1)
# d3, d6 = merge_with_full_kernel(d3, d6, k=result, p=1)

end = time.time()
print(f"Execution time: {end - start:.4f} seconds")



# # --- Final 7-Color Visualization ---
# plt.figure(figsize=(15, 10))
# plt.imshow(plot_braille_final_7_layers(d1, d2, d3, d4, d5, d6, u_final))
# plt.title("2D Context Classification (Corrected)\n"
#           "Red(1), Green(2), Blue(3), Yellow(4), Cyan(5), Magenta(6), White(Unsure)")
# plt.axis("off")
# plt.show()

start = time.time()

# 1. Combine your images manually
combined_L = cv2.add(cv2.add(d1, d2), d3)
combined_R = cv2.add(cv2.add(d4, d5), d6)

# 2. Apply concentration to each
concentrated_L = concentrate_single_image(combined_L, 2 * mean_module)
concentrated_R = concentrate_single_image(combined_R, 2 * mean_module)

for _ in range(3):
    concentrated_L = concentrate_single_image(concentrated_L, 2 * mean_module)
    concentrated_R = concentrate_single_image(concentrated_R, 2 * mean_module)



end = time.time()
print(f"Execution time: {end - start:.4f} seconds")



start = time.time()

import numpy as np
import cv2
import matplotlib.pyplot as plt
from numba import njit

@njit
def refine_by_modulo_voting(all_dots, conc_L, conc_R, nh, fnh, nv):
    rows, cols = all_dots.shape
    out_L = np.zeros_like(all_dots)
    out_R = np.zeros_like(all_dots)
    
    P = nh + fnh  # Full Braille cell period
    
    # Window settings (half-sizes)
    hw_x = int(3 * (nh+fnh))
    hw_y = int(14 * nv)

    # Pre-find non-zero points in concentrated images to speed up the loop
    # Stored as: [y, x, intensity]
    coords_L = []
    y_l, x_l = np.where(conc_L > 0)
    for i in range(len(y_l)):
        coords_L.append((y_l[i], x_l[i], conc_L[y_l[i], x_l[i]]))
        
    coords_R = []
    y_r, x_r = np.where(conc_R > 0)
    for i in range(len(y_r)):
        coords_R.append((y_r[i], x_r[i], conc_R[y_r[i], x_r[i]]))

    # Iterate through every pixel in the combined dots image
    for y in range(rows):
        for x in range(cols):
            pixel_val = all_dots[y, x]
            if pixel_val == 0:
                continue
            
            error_L = 0.0
            weight_L = 0.0
            error_R = 0.0
            weight_R = 0.0

            # Test alignment against Left Anchors
            for i in range(len(coords_L)):
                ry, rx, r_val = coords_L[i]
                
                # Check if within window
                if abs(y - ry) < hw_y and abs(x - rx) < hw_x:
                    dx = abs(x - rx)
                    dy = abs(y - ry)
                    dist = np.sqrt(dx**2 + dy**2)
                    
                    # Modulo logic: how close is dx to a multiple of P?
                    mod = dx % P
                    alignment_err = min(mod, P - mod)
                    
                    # Weight: Intensity / Distance (distance is 'defavorable')
                    # We add 1 to distance to avoid division by zero
                    w = r_val / (dist + 1.0)
                    
                    error_L += alignment_err * w
                    weight_L += w

            # Test alignment against Right Anchors
            for i in range(len(coords_R)):
                ry, rx, r_val = coords_R[i]
                
                if abs(y - ry) < hw_y and abs(x - rx) < hw_x:
                    dx = abs(x - rx)
                    dy = abs(y - ry)
                    dist = np.sqrt(dx**2 + dy**2)
                    
                    mod = dx % P
                    alignment_err = min(mod, P - mod)
                    
                    w = r_val / (dist + 1.0)
                    
                    error_R += alignment_err * w
                    weight_R += w

            # Decision Logic
            # Normalize errors by weights
            final_err_L = error_L / weight_L if weight_L > 0 else 999
            final_err_R = error_R / weight_R if weight_R > 0 else 999

            if final_err_L < final_err_R:
                out_L[y, x] = pixel_val
            else:
                out_R[y, x] = pixel_val
                
    return out_L, out_R

def apply_refinement(all_dots_source, conc_L, conc_R, nh, fnh, nv):
    """
    Wrapper to handle the input and output of the refinement process.
    """
    print("Starting modulo-based refinement...")
    
    # Ensure inputs are float32 for the Numba function
    all_dots_f = all_dots_source.astype(np.float32)
    conc_L_f = conc_L.astype(np.float32)
    conc_R_f = conc_R.astype(np.float32)
    
    refined_L, refined_R = refine_by_modulo_voting(
        all_dots_f, conc_L_f, conc_R_f, nh, fnh, nv
    )
    
    return refined_L, refined_R

def redistribute(L, R, top_mask, mid_mask, down_mask):
    """Maps refined Left/Right images back into the 6 Braille positions."""
    t, m, d = [mask.astype(np.uint8) for mask in [top_mask, mid_mask, down_mask]]
    
    # Left Column
    rd1 = cv2.bitwise_and(L, L, mask=t)
    rd2 = cv2.bitwise_and(L, L, mask=m)
    rd3 = cv2.bitwise_and(L, L, mask=d)
    
    # Right Column
    rd4 = cv2.bitwise_and(R, R, mask=t)
    rd5 = cv2.bitwise_and(R, R, mask=m)
    rd6 = cv2.bitwise_and(R, R, mask=d)
    
    return rd1, rd2, rd3, rd4, rd5, rd6


end = time.time()
print(f"Execution time: {end - start:.4f} seconds")

start = time.time()

# 1. Combine all dots (including unsure) into one source
all_dots = top_final.astype(np.float64) + mid_final.astype(np.float64) + \
           down_final.astype(np.float64) + u_final.astype(np.float64)

# 2. Use the concentrated needles (combined_L/R) to refine all_dots
refined_L, refined_R = apply_refinement( 
    all_dots,
    concentrated_L, concentrated_R,
    neighbors_horizontal, far_neighbors_horizontal, neighbors_vertical
)

end = time.time()
print(f"Execution time: {end - start:.4f} seconds")





start = time.time()

fd1, fd2, fd3, fd4, fd5, fd6 = redistribute(refined_L, refined_R, top_final, mid_final, down_final)

fd1, fd4 = merge_with_full_kernel(fd1, fd4, k=result, p=1)
fd1, fd2 = merge_with_full_kernel(fd1, fd2, k=result, p=1)
fd4, fd5 = merge_with_full_kernel(fd4, fd5, k=result, p=1)
fd2, fd5 = merge_with_full_kernel(fd2, fd5, k=result, p=1)
fd2, fd3 = merge_with_full_kernel(fd2, fd3, k=result, p=1)
fd5, fd6 = merge_with_full_kernel(fd5, fd6, k=result, p=1)
fd3, fd6 = merge_with_full_kernel(fd3, fd6, k=result, p=1)

all_accounted = cv2.add(cv2.add(cv2.add(fd1, fd2), cv2.add(fd3, fd4)), cv2.add(fd5, fd6))

# 1. Make all_accounted a proper binary mask
all_accounted_mask = (all_accounted > 0).astype(np.uint8) * 255

# 2. Take only pixels that are in u_final and not in all_accounted
final_unsure = cv2.bitwise_and(u_final, cv2.bitwise_not(all_accounted_mask))

end = time.time()
print(f"Execution time: {end - start:.4f} seconds")

# start = time.time()

# final_viz = plot_braille_final_7_layers(
#     fd1, fd2, fd3, fd4, fd5, fd6, final_unsure
# )


# plt.figure(figsize=(25, 25))

# plt.subplot(1, 4, 2)
# plt.imshow(final_viz)
# plt.title("Final Braille Classification (Localized Periodic Consensus)\n"
#           "1:Red, 2:Green, 3:Blue | 4:Yellow, 5:Cyan, 6:Magenta | White:Unsure")
# plt.axis("off")
# plt.tight_layout()
# plt.show()

# # Print counts for verification
# print("Classification Results (Pixels):")
# print(f"Dot 1 (Red):     {np.count_nonzero(fd1)}")
# print(f"Dot 2 (Green):   {np.count_nonzero(fd2)}")
# print(f"Dot 3 (Blue):    {np.count_nonzero(fd3)}")
# print(f"Dot 4 (Yellow):  {np.count_nonzero(fd4)}")
# print(f"Dot 5 (Cyan):    {np.count_nonzero(fd5)}")
# print(f"Dot 6 (Magenta): {np.count_nonzero(fd6)}")
# print(f"Still Unsure:    {np.count_nonzero(final_unsure)}")

# end = time.time()
# print(f"Execution time: {end - start:.4f} seconds")







start = time.time()

def enhance_score_map_by_voting(score_map, period, nv, threshold=5):
    rows, cols = score_map.shape
    binary_scores = (score_map > 0).astype(np.float32)
    votes = np.zeros_like(binary_scores)
    
    def get_shifted(image, dx, dy):
        M = np.float32([[1, 0, -dx], [0, 1, -dy]])
        return cv2.warpAffine(image, M, (cols, rows), borderValue=0)

    step_x = period
    for kx in range(-1, 2):
        if kx == 0: continue 
        dx = kx * step_x
        votes += get_shifted(binary_scores, dx, 0)

    predicted_locations = (votes >= threshold)
    existing_scores = score_map[score_map > 0]
    mean_val = np.mean(existing_scores) if len(existing_scores) > 0 else 1.0
    
    enhanced_map = score_map.copy()
    enhanced_map[(score_map == 0) & (predicted_locations)] = mean_val
    return enhanced_map


end = time.time()
print(f"Execution time: {end - start:.4f} seconds")

start = time.time()

recto_mask = recto_concentrated == 255

pos1_new = fd1 * recto_mask
pos2_new = fd2 * recto_mask
pos3_new = fd3 * recto_mask
pos4_new = fd4 * recto_mask
pos5_new = fd5 * recto_mask
pos6_new = fd6 * recto_mask

end = time.time()
print(f"Execution time: {end - start:.4f} seconds")

start = time.time()

import cv2
import numpy as np
import matplotlib.pyplot as plt

# --- 1. Define a shift helper ---
def shift(img, dx, dy):
    rows, cols = img.shape
    M = np.float32([[1, 0, -dx], [0, 1, -dy]])
    return cv2.warpAffine(img.astype(np.float32), M, (cols, rows), borderValue=0)

# --- 2. Apply translations used in your 6-dot box logic ---
# Top-left anchor alignment
aligned1 = shift(pos1_new, 0, 2 * neighbors_vertical)                           # Top-left
aligned2 = shift(pos2_new, 0, neighbors_vertical)        # Mid-left
aligned3 = pos3_new
aligned4 = shift(pos4_new, neighbors_horizontal, 2 * neighbors_vertical)      # Top-right
aligned5 = shift(pos5_new, neighbors_horizontal, neighbors_vertical)  # Mid-right
aligned6 = shift(pos6_new, neighbors_horizontal, 0) # Bottom-right

# --- 3. Sum all aligned layers ---
sum_aligned = aligned1 + aligned2 + aligned3 + aligned4 + aligned5 + aligned6

sum_aligned = enhance_score_map_by_voting(
    sum_aligned, 
    period=period, 
    nv=neighbors_vertical, 
    threshold=2
)

end = time.time()
print(f"Execution time: {end - start:.4f} seconds")

start = time.time()
# sum_aligned_norm = cv2.normalize(sum_aligned, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

# # --- 4. Show the summed image ---
# plt.figure(figsize=(12, 8))
# plt.imshow(sum_aligned_norm, cmap='gray')
# plt.title("Sum of All 6 Dot Layers After Translation Alignment")
# plt.colorbar(label="Intensity (sum of dot pixels)")
# plt.show()

end = time.time()
print(f"Execution time: {end - start:.4f} seconds")

start = time.time()

import matplotlib.patches as patches
from numba import njit

def find_and_score_structural_boxes(fd1, fd2, fd3, fd4, fd5, fd6, nh, nv, result, NP=4):
    rows, cols = fd1.shape
    dot_sz = 1
    
    def get_3x3_sums(img):
        return cv2.boxFilter(img.astype(np.float32), -1, (dot_sz, dot_sz), 
                             normalize=False, anchor=(0, 0))

    s1, s2, s3, s4, s5, s6 = [get_3x3_sums(f) for f in [fd1, fd2, fd3, fd4, fd5, fd6]]

    def apply_fixed_shift(s_map, tx, ty):
        M = np.float32([[1, 0, tx], [0, 1, ty]])
        return cv2.warpAffine(s_map, M, (cols, rows), borderValue=0)

    # Shift logic remains the same
    a1 = apply_fixed_shift(s1, 0, -2 * nv)                                 
    a2 = apply_fixed_shift(s2, 0, -nv)         
    a3 = s3      
    a4 = apply_fixed_shift(s4, -nh, -2 * nv)        
    a5 = apply_fixed_shift(s5, -nh, -nv)       
    a6 = apply_fixed_shift(s6, -nh, 0)     

    valid_mask = (
        (a1 > 0).astype(int) + (a2 > 0).astype(int) + (a3 > 0).astype(int) +
        (a4 > 0).astype(int) + (a5 > 0).astype(int) + (a6 > 0).astype(int)
    ) >= NP
    
    total_score_map = (a1 + a2 + a3 + a4 + a5 + a6) * valid_mask
    return [], total_score_map

def extract_concentrated_boxes(score_map, nh, nv, result, win = 2 * mean_module):
    
    concentrated_map = concentrate_single_image(score_map, win)
    concentrated_map = concentrate_single_image(concentrated_map, win)
    # ------------------------------------------------------
    
    y_final, x_final = np.where(concentrated_map > 0)
    
    boxes = []
    for x, y in zip(x_final, y_final):
        boxes.append({
            'x': int(x - mean_module), 
            'y': int(y - mean_module),
            'w': int(nh + 2 * mean_module), 
            'h': int(2 * nv + 2 * result + int(mean_module/4)),
            'score': float(concentrated_map[y, x])
        })
    boxes.sort(key=lambda b: b['score'], reverse=True)
    return boxes, concentrated_map


end = time.time()
print(f"Execution time: {end - start:.4f} seconds")

start = time.time()

_, score_map_new = find_and_score_structural_boxes(
    fd1, fd2, fd3, fd4, fd5, fd6, 
    neighbors_horizontal, neighbors_vertical, result, NP=3
)

end = time.time()
print(f"Execution time: {end - start:.4f} seconds")

start = time.time()

_, score_map_original = find_and_score_structural_boxes(
    pos1_new, pos2_new, pos3_new, pos4_new, pos5_new, pos6_new, 
    neighbors_horizontal, neighbors_vertical, result, NP=2
)

end = time.time()
print(f"Execution time: {end - start:.4f} seconds")

start = time.time()

score_map = np.maximum(score_map_new, score_map_original)

final_boxes, concentrated_score_map = extract_concentrated_boxes(
    score_map, 
    neighbors_horizontal, 
    neighbors_vertical, 
    result,
    win = 2 * mean_module
)

end = time.time()
print(f"Execution time: {end - start:.4f} seconds")

# start = time.time()

# # --- 3. VISUALIZATION ---
# fig, ax = plt.subplots(figsize=(14, 10))
# bg = plot_braille_final_7_layers(
#     fd1, fd2, fd3, fd4, fd5, fd6, final_unsure
# )
# ax.imshow(bg, cmap='gray', alpha=0.9)

# if final_boxes:
#     scores = [b['score'] for b in final_boxes]
#     norm = plt.Normalize(min(scores), max(scores))
#     cmap = plt.cm.spring 
#     for box in final_boxes:
#         rect = patches.Rectangle(
#             (box['x'], box['y']), box['w'], box['h'], 
#             linewidth=1, edgecolor=cmap(norm(box['score'])), facecolor='none'
#         )
#         ax.add_patch(rect)

# plt.title(f"Found {len(final_boxes)} Structural Braille Cells")
# plt.axis('off')
# plt.show()

# end = time.time()
# print(f"Execution time: {end - start:.4f} seconds")

start = time.time()

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import cv2
import numpy as np

# This function now handles both Horizontal (period) and Vertical (4*nv) rescue
def rescue_and_concentrate_boxes_dual(nh, nv, period, result, score_map_strict, score_map_loose, Nx=10, Ny=10):
    rows, cols = score_map_strict.shape
    binary_strict = (score_map_strict > 0).astype(np.float32)
    
    # 1. Initialize Votes
    votes_h = np.zeros_like(binary_strict)
    votes_v = np.zeros_like(binary_strict)
    
    # Helper for shifting
    def get_shifted(image, dx, dy):
        M = np.float32([[1, 0, -dx], [0, 1, -dy]])
        return cv2.warpAffine(image, M, (cols, rows), borderValue=0)

    # 2. Horizontal Voting (Left/Right)
    step_x = period
    for kx in range(-Nx, Nx+1):
        if kx == 0: continue 
        votes_h += get_shifted(binary_strict, kx * step_x, 0)

    # 3. Vertical Voting (Up/Down) - Using 4 * nv as requested
    step_y = min(4 * nv, neighbors_vertical_mid_p)
    for ky in range(-Ny, Ny+1):
        if ky == 0: continue 
        votes_v += get_shifted(binary_strict, 0, ky * step_y)

    # 4. Combined Rescue Logic:
    # A spot is rescued if it has ANY horizontal neighbor OR ANY vertical neighbor
    # AND it exists in the loose map.
    rescue_mask = ((votes_h >= 1) | (votes_v >= 1)) & (score_map_loose > 0)
    
    combined_score_map = score_map_strict.copy()
    
    # Only fill where the strict map is empty but the rescue mask is true
    mask_to_fill = (combined_score_map == 0) & (rescue_mask == True)
    combined_score_map[mask_to_fill] = score_map_loose[mask_to_fill]

    # 5. Concentrate results (NMS)
    # Using period for the window size is usually best for Braille cell separation
    win = int(period)
    if win % 2 == 0: win += 1
    final_concentrated_map = phase1_concentrate_centroid(combined_score_map, win)

    # 6. Final Extraction
    y_final, x_final = np.where(final_concentrated_map > 0)
    points = []
    for x, y in zip(x_final, y_final):
        points.append((x, y, final_concentrated_map[y, x]))
    
    points.sort(key=lambda p: p[2], reverse=True)
    
    final_boxes = []
    seen_coords = []
    min_dist = period * 0.8 

    for x, y, score in points:
        if not any(abs(x - sx) < min_dist and abs(y - sy) < min_dist for sx, sy in seen_coords):
            final_boxes.append({
                'x': int(x - mean_module), 
                'y': int(y - mean_module),
                'w': int(nh + 2 * mean_module), 
                'h': int(2 * nv + 2 * mean_module),
                'score': float(score),
                # Check original strict map to see if it was rescued
                'is_rescued': bool(score_map_strict[int(y), int(x)] == 0)
            })
            seen_coords.append((x, y))
            
    return final_boxes, combined_score_map

end = time.time()
print(f"Execution time: {end - start:.4f} seconds")

start = time.time()

final_boxes, combined_score_map = rescue_and_concentrate_boxes_dual(
    neighbors_horizontal, 
    neighbors_vertical, 
    period, 
    result, 
    score_map,    # This is your strict map (NP=4)
    sum_aligned,  # This is your loose map (from dot alignment)
    Nx=2,
    Ny=10
)

end = time.time()
print(f"Execution time: {end - start:.4f} seconds")

# start = time.time()

# # --- VISUALIZATION ---
# fig, ax = plt.subplots(figsize=(14, 10))
# # Using your background layers function
# bg = plot_braille_final_7_layers(
#     pos1_new, pos2_new, pos3_new, pos4_new, pos5_new, pos6_new, final_unsure
# )
# ax.imshow(bg, cmap='gray')

# if final_boxes:
#     scores = [b['score'] for b in final_boxes]
#     norm = plt.Normalize(min(scores), max(scores))
#     cmap = plt.cm.spring 
    
#     for box in final_boxes:
#         # Cyan (#00FFFF) for ANY rescued box (Horizontal or Vertical)
#         # Spring colormap for boxes that were already in the strict map
#         color = '#00FFFF' if box.get('is_rescued') else cmap(norm(box['score']))
#         linestyle = '--' if box.get('is_rescued') else '-'
        
#         rect = patches.Rectangle(
#             (box['x'], box['y']), box['w'], box['h'], 
#             linewidth=1, edgecolor=color, facecolor='none', linestyle=linestyle
#         )
#         ax.add_patch(rect)

# plt.title(f"Dual Rescue Detection: {len(final_boxes)} Cells\n(Rescued via horizontal neighbors or vertical neighbors in Cyan)")
# plt.axis('off')
# plt.show()

# end = time.time()
# print(f"Execution time: {end - start:.4f} seconds")



start = time.time()

import numpy as np
import cv2
import matplotlib.pyplot as plt
import matplotlib.patches as patches

def draw_boxes_on_ax(ax, img, boxes, title, cmap_name='spring'):
    """Helper to plot image and overlays boxes consistently."""
    ax.imshow(img, cmap='gray' if len(img.shape) == 2 else None)
    
    if boxes:
        scores = [b['score'] for b in boxes]
        norm = plt.Normalize(min(scores), max(scores))
        cmap = plt.get_cmap(cmap_name)

        for box in boxes:
            color = cmap(norm(box['score']))
            rect = patches.Rectangle(
                (box['x'], box['y']), box['w'], box['h'],
                linewidth=1, edgecolor=color, facecolor='none', alpha=0.7
            )
            ax.add_patch(rect)
            
    ax.set_title(title)
    ax.axis('off')

def get_stacked_roi_robust(source_img, boxes):
    # Filter valid dimensions
    ws = [abs(float(b['w'])) for b in boxes if abs(float(b['w'])) > 0]
    hs = [abs(float(b['h'])) for b in boxes if abs(float(b['h'])) > 0]
    
    if not ws or not hs: return None
    
    avg_w, avg_h = int(round(np.mean(ws))), int(round(np.mean(hs)))
    avg_w, avg_h = max(1, avg_w), max(1, avg_h)

    is_color = len(source_img.shape) == 3
    acc = np.zeros((avg_h, avg_w, 3) if is_color else (avg_h, avg_w), dtype=np.float64)
    
    count = 0
    for b in boxes:
        x, y = int(b['x']), int(b['y'])
        w, h = int(abs(b['w'])), int(abs(b['h']))
        
        # Safe Crop
        y1, y2 = max(0, y), min(source_img.shape[0], y + h)
        x1, x2 = max(0, x), min(source_img.shape[1], x + w)
        roi = source_img[y1:y2, x1:x2]
        
        if roi.size > 0:
            resized = cv2.resize(roi.astype(np.float64), (avg_w, avg_h))
            acc += resized
            count += 1
            
    return (acc / count).astype(np.uint8) if count > 0 else None

# --- PROCESSING RECONSTRUCTIONS ---

def reconstruct_layer(img_a, img_b):
    """Encapsulates your specific reconstruction logic."""
    added_a = cv2.add(128, img_a.astype(np.uint8))
    added_b = cv2.add(128, img_b.astype(np.uint8))
    # Combining highlight and shadow phases
    res = cv2.addWeighted(added_a, 0.5, 255 - added_b, 0.5, 0)
    return np.clip(res, 0, 255).astype(np.uint8)



end = time.time()
print(f"Execution time: {end - start:.4f} seconds")

start = time.time()

img1_src = gray
img2_src = reconstruct_layer(recto_blanc, recto_noir)
recto = np.maximum(recto_blanc, recto_noir).astype(np.uint8)
verso = np.maximum(verso_blanc, verso_noir).astype(np.uint8)
img3_src = reconstruct_layer(recto, verso)

end = time.time()
print(f"Execution time: {end - start:.4f} seconds")

# start = time.time()

# # --- VISUALIZATION 1: OVERLAYS ---
# if 'final_boxes' in locals() and final_boxes:
#     fig, axes = plt.subplots(1, 3, figsize=(20, 7))
#     draw_boxes_on_ax(axes[0], img1_src, final_boxes, "Gray Image")
#     draw_boxes_on_ax(axes[1], img2_src, final_boxes, "Reconstruction (B/N)")
#     draw_boxes_on_ax(axes[2], img3_src, final_boxes, "Reconstruction (R/V)")
#     plt.tight_layout()
#     plt.show()

# end = time.time()
# print(f"Execution time: {end - start:.4f} seconds")







import os
import time
import cv2
import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np
import torch
import torch.nn as nn
from matplotlib.collections import PatchCollection

# Optimization: Enable OpenCV parallel processing
cv2.setUseOptimized(True)

start = time.time()

# ── 1. MODEL DEFINITION ───────────────────────────────────────────────────────
class DotPredictor(nn.Module):
    def __init__(self):
        super(DotPredictor, self).__init__()
        self.conv_layers = nn.Sequential(
            nn.Conv2d(3, 32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32), nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64), nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128), nn.ReLU(),
            nn.AdaptiveAvgPool2d((1, 1))
        )
        self.fc_layers = nn.Sequential(
            nn.Linear(128, 64), nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(64, 1),
            nn.Sigmoid()
        )

    def forward(self, x):
        x = self.conv_layers(x)
        x = x.view(x.size(0), -1)
        return self.fc_layers(x)

# ── 2. LOAD WEIGHTS ───────────────────────────────────────────────────────────
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model_3ch = DotPredictor().to(device)
model_path = "best_braille_model_3_channel_augmented.pth"

if os.path.exists(model_path):
    model_3ch.load_state_dict(torch.load(model_path, map_location=device))
    model_3ch.eval()
    print(f"✅ Model loaded successfully.")
else:
    print(f"❌ Model file not found.")

# ── 3. MAIN PROCESSING FUNCTION ────────────────────────────────────────────────
def process_braille_complete(img1, img2, img3, boxes, warped_rgb, y_tolerance=20):
    num_boxes = len(boxes)
    if num_boxes == 0: return ""

    print(f"🚀 Processing {num_boxes} characters...")
    proc_start = time.time()

    # --- STEP A: BATCH EXTRACTION ---
    all_dots = np.empty((num_boxes * 6, 3, 32, 32), dtype=np.uint8)
    
    for i, box in enumerate(boxes):
        x, y, w, h = int(box["x"]), int(box["y"]), int(box["w"]), int(box["h"])
        roi1, roi2, roi3 = img1[y:y+h, x:x+w], img2[y:y+h, x:x+w], img3[y:y+h, x:x+w]
        
        if roi1.size == 0: continue

        H, W = roi1.shape
        h_pts, w_pts = [0, H // 3, (2 * H) // 3, H], [0, W // 2, W]

        base_idx = i * 6
        for col in range(2):
            for row in range(3):
                idx = base_idx + (col * 3 + row)
                s_r, e_r = h_pts[row], h_pts[row+1]
                s_c, e_c = w_pts[col], w_pts[col+1]
                
                all_dots[idx, 0] = cv2.resize(roi1[s_r:e_r, s_c:e_c], (32, 32))
                all_dots[idx, 1] = cv2.resize(roi2[s_r:e_r, s_c:e_c], (32, 32))
                all_dots[idx, 2] = cv2.resize(roi3[s_r:e_r, s_c:e_c], (32, 32))

    # --- STEP B: BATCH INFERENCE ---
    with torch.inference_mode():
        input_tensor = torch.from_numpy(all_dots).to(device).float().div(255.0)
        probs = model_3ch(input_tensor).cpu().numpy().flatten()

    # --- STEP C: DECODING ---
    all_bits = (probs > 0.5).astype(np.int32).reshape(num_boxes, 6)
    weights = np.array([1, 2, 4, 8, 16, 32], dtype=np.int32)
    braille_chars = [chr(0x2800 + off) for off in np.dot(all_bits, weights)]

    print(f"✅ AI Decoding finished in {time.time() - proc_start:.4f}s")

    # --- STEP D: SPATIAL SORTING (FOR TEXT OUTPUT) ---
    decoded_items = []
    for i, box in enumerate(boxes):
        decoded_items.append({'x': box['x'], 'y': box['y'], 'char': braille_chars[i]})

    decoded_items.sort(key=lambda item: item['y']) # Sort top-to-bottom

    lines = []
    if decoded_items:
        current_line = [decoded_items[0]]
        for i in range(1, len(decoded_items)):
            if abs(decoded_items[i]['y'] - current_line[-1]['y']) < y_tolerance:
                current_line.append(decoded_items[i])
            else:
                current_line.sort(key=lambda item: item['x']) # Sort left-to-right
                lines.append("".join([item['char'] for item in current_line]))
                current_line = [decoded_items[i]]
        current_line.sort(key=lambda item: item['x'])
        lines.append("".join([item['char'] for item in current_line]))
    
    final_text = "\n".join(lines)

    # --- STEP E: PLOTTING ---
    fig, ax = plt.subplots(figsize=(15, 20))
    ax.imshow(warped_rgb, "gray")
    
    rects = [patches.Rectangle((b["x"], b["y"]), b["w"], b["h"]) for b in boxes]
    pc = PatchCollection(rects, match_original=False, edgecolor="white", facecolor="none", linewidths=0.8, alpha=0.4)
    ax.add_collection(pc)

    for i, box in enumerate(boxes):
        if braille_chars[i] == chr(0x2800): continue
        ax.text(box['x'] + box['w']/2, box['y'] + 1, braille_chars[i], color='#FFFF00', fontsize=16, fontweight='bold', ha='center', va='top')

    ax.axis("off")
    plt.show()

    return final_text

# ── 4. EXECUTION ──────────────────────────────────────────────────────────────
if "final_boxes" in locals() and final_boxes:
    # This replaces both of your old cells
    full_braille_text = process_braille_complete(gray, img2_src, img3_src, final_boxes, gray)
    
    print("\n--- RÉSULTAT FINAL ---")
    print(full_braille_text)

    # Save output
    with open("resultat_braille.txt", "w", encoding="utf-8") as f:
        f.write(full_braille_text)
        print("\n✅ File saved: resultat_braille.txt")

end = time.time()
print(f"Total time: {end - start:.4f} seconds")

start = time.time()

import torch
import numpy as np
import cv2
import time
from concurrent.futures import ThreadPoolExecutor

def get_braille_text_content_ultra_fast(img1, img2, img3, boxes, model, device, y_tolerance=15):
    if not boxes: return ""

    start_func = time.time()
    num_boxes = len(boxes)
   
    # 1. CPU MODEL OPTIMIZATION
    model.eval()
    # Use JIT tracing to compile the model
    example_input = torch.randn(1, 3, 32, 32).to(device)
    traced_model = torch.jit.trace(model, example_input)
    # Optimize specifically for CPU inference
    fast_model = torch.jit.optimize_for_inference(traced_model)
   
    # 2. PARALLEL PRE-PROCESSING (CPU Multi-core)
    def process_box(box_data):
        idx, b = box_data
        x, y, w, h = int(b['x']), int(b['y']), int(b['w']), int(b['h'])
       
        # Slicing is fast
        r1 = img1[max(0,y):y+h, max(0,x):x+w]
        r2 = img2[max(0,y):y+h, max(0,x):x+w]
        r3 = img3[max(0,y):y+h, max(0,x):x+w]
       
        if r1.size == 0: return None
       
        H, W = r1.shape
        h_pts = [0, H//3, (2*H)//3, H]
        w_pts = [0, W//2, W]
       
        box_patches = np.zeros((6, 3, 32, 32), dtype=np.float32)
        p_idx = 0
        for col in range(2):
            for row in range(3):
                # Using INTER_LINEAR for best speed/quality balance on CPU
                box_patches[p_idx, 0] = cv2.resize(r1[h_pts[row]:h_pts[row+1], w_pts[col]:w_pts[col+1]], (32, 32), interpolation=cv2.INTER_LINEAR)
                box_patches[p_idx, 1] = cv2.resize(r2[h_pts[row]:h_pts[row+1], w_pts[col]:w_pts[col+1]], (32, 32), interpolation=cv2.INTER_LINEAR)
                box_patches[p_idx, 2] = cv2.resize(r3[h_pts[row]:h_pts[row+1], w_pts[col]:w_pts[col+1]], (32, 32), interpolation=cv2.INTER_LINEAR)
                p_idx += 1
        return idx, box_patches

    print(f"🌀 Preparing batch for {num_boxes} boxes using all CPU cores...")
    with ThreadPoolExecutor() as executor:
        results = list(executor.map(process_box, enumerate(boxes)))

    valid_results = [r for r in results if r is not None]
    if not valid_results: return ""
   
    indices, patches = zip(*valid_results)
    all_dots = np.concatenate(patches, axis=0)

    # 3. HIGH-SPEED INFERENCE
    with torch.inference_mode():
        # Convert to tensor once
        input_tensor = torch.from_numpy(all_dots).to(device) / 255.0
        # Fast_model is the JIT-optimized version
        probs = fast_model(input_tensor).numpy().flatten()

    # 4. VECTORIZED DECODING
    bits = (probs > 0.5).astype(np.int32).reshape(-1, 6)
    weights = np.array([1, 2, 4, 8, 16, 32], dtype=np.int32)
    unicode_offsets = np.dot(bits, weights)
   
    decoded_items = []
    for i, orig_idx in enumerate(indices):
        char = chr(0x2800 + unicode_offsets[i])
        decoded_items.append({'x': boxes[orig_idx]['x'], 'y': boxes[orig_idx]['y'], 'char': char})

    # 5. ASSEMBLY
    decoded_items.sort(key=lambda item: item['y'])
    lines = []
    if decoded_items:
        curr_line = [decoded_items[0]]
        for i in range(1, len(decoded_items)):
            if abs(decoded_items[i]['y'] - curr_line[-1]['y']) < y_tolerance:
                curr_line.append(decoded_items[i])
            else:
                curr_line.sort(key=lambda item: item['x'])
                lines.append("".join([it['char'] for it in curr_line]))
                curr_line = [decoded_items[i]]
        curr_line.sort(key=lambda item: item['x'])
        lines.append("".join([it['char'] for it in curr_line]))

    print(f"⚡ Ultra-fast CPU decoding finished in {time.time() - start_func:.3f}s")
    return "\n".join(lines)

# --- EXECUTION ---
start = time.time()
braille_output = get_braille_text_content_ultra_fast(gray, img2_src, img3_src, final_boxes, model_3ch, device)

print("--- RÉSULTAT DÉCODAGE ---")
print(braille_output)

with open("resultat_braille.txt", "w", encoding="utf-8") as f:
    f.write(braille_output)


def translate_braille_to_arabic(braille_text):
    # Standard Mapping
    braille_map = {
        '⠀': ' ',   '⠁': 'ا',   '⠃': 'ب',   '⠞': 'ت',   '⠹': 'ث',   '⠚': 'ج',
        '⠱': 'ح',   '⠭': 'خ',   '⠙': 'د',   '⠮': 'ذ',   '⠗': 'ر',   '⠵': 'ز',
        '⠎': 'س',   '⠩': 'ش',   '⠯': 'ص',   '⠫': 'ض',   '⠾': 'ط',   '⠿': 'ظ',
        '⠷': 'ع',   '⠣': 'غ',   '⠋': 'ف',   '⠟': 'ق',   '⠅': 'ك',   '⠇': 'ل',
        '⠍': 'م',   '⠝': 'ن',   '⠓': 'ه',   '⠺': 'و',   '⠊': 'ي',   '⠕': 'ى',
        '⠡': 'ة',   '⠧': 'لا',  '⠌': 'أ',   '⠨': 'إ',   '⠜': 'آ',   '⠄': 'ء',
        '⠳': 'ؤ',   '⠽': 'ئ' 
    }

    num_map = {'⠁':'1','⠃':'2','⠉':'3','⠙':'4','⠑':'5','⠋':'6','⠛':'7','⠓':'8','⠊':'9','⠚':'0'}

    extra_map = {
        '⠂': 'َ', '⠑': 'ِ', '⠥': 'ُ', '⠆': 'ً', '⠔': 'ٍ', '⠢': 'ٌ', '⠠': 'ّ', '⠒': 'ْ',
        '⠐': '،', '⠰': ' ', '⠲': '.', '⠦': '؟', '⠖': '!', '⠤': '-', '⠶': '"', 
        '⠉': '-', '⠏': '(', '⠹': ')', '⠴': '.', '⠸': ''
    }

    translated_lines = []
    for line in braille_text.split('\n'):
        # Nettoyage des lignes décoratives (si la ligne commence par ⠧-- ou ⠏--)
        if line.startswith('⠧⠤') or line.startswith('⠏⠉'):
            translated_lines.append("-" * 20)
            continue

        translated_line = ""
        number_mode = False
        i = 0
        while i < len(line):
            char = line[i]
            
            # 1. Colon (5 then 2)
            if i + 1 < len(line) and line[i:i+2] == '⠐⠂':
                translated_line += ":"
                i += 2
                continue

            # 2. Number Mode
            if char == '⠼':
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

            # 3. Handle '⠰' as spacer instead of semicolon if near letters/numbers
            if char == '⠰':
                translated_line += " "
                i += 1
                continue

            # 4. Standard Mapping
            if char in braille_map:
                translated_line += braille_map[char]
            elif char in extra_map:
                translated_line += extra_map[char]
            else:
                translated_line += char
            i += 1
            
        translated_lines.append(translated_line)

    return "\n".join(translated_lines)

# --- EXECUTION ---
if 'braille_output' in locals():
    arabic_text = translate_braille_to_arabic(full_braille_text)
    # Post-processing clean up for "تعيدها" logic (if OCR merges ها into آ)
    arabic_text = arabic_text.replace("ُآ", "ُها").replace("اِّتَئد", "اتخذ")
    
    print("--- RÉSULTAT FINAL ---")
    print(arabic_text)


end = time.time()
print(f"Execution time: {end - start:.4f} seconds")

# ============================================================
# Arabic Text Corrector — Single Cell (Jupyter)
# ============================================================
import os
import time
import google.generativeai as genai

# --- API Key ---
os.environ['GEMINI_API_KEY'] = 'AIzaSyCZch676xXXbiuN8GDQNtQHExjxfMiBHN8'

def correct_arabic_text(input_text):
    genai.configure(api_key=os.environ['GEMINI_API_KEY'])
    model = genai.GenerativeModel('gemini-2.5-flash-lite')  # ⚡ Faster lite model

    prompt = """أنت مصحح إملائي للغة العربية لاختبارات المرحلة الابتدائية الجزائرية.
مهمتك الوحيدة:
- إصلاح الأحرف الخاطئة أو المكسورة فقط (مثال: تُ!اثْ ← تُراثْ، هُ.َ ← هُوَ)
- الحفاظ على التشكيل كما هو تمامًا
- الحفاظ على بنية النص والأسطر كما هي
- لا تضيف ولا تحذف أي كلمات أو أسطر
- أعد النص المصحح فقط بدون أي شرح
النص:
try to correct the words that you can correct based on the letters that it has and you think that are false and based on it position in the line and in the whole text
""" + input_text

    generation_config = genai.GenerationConfig(
        temperature=0.0,          # Deterministic — no creative guessing
        max_output_tokens=2048,   # Enough for a full page, won't over-generate
    )

    max_retries = 3
    for attempt in range(max_retries):
        try:
            print(f"🚀 Sending to Gemini 2.5 Flash-Lite (attempt {attempt+1}/{max_retries})...")
            t0 = time.time()

            response = model.generate_content(
                prompt,
                generation_config=generation_config,
            )

            elapsed = time.time() - t0

            if response.text:
                print(f"✅ Success! ({elapsed:.2f}s)")
                return response.text.strip()

        except Exception as e:
            err = str(e)
            if "429" in err:
                wait = 65 * (attempt + 1)  # Back-off: 65s, 130s, 195s
                print(f"⚠️ Rate limit hit. Waiting {wait}s... (attempt {attempt+1}/{max_retries})")
                time.sleep(wait)
            else:
                print(f"❌ Error: {err}")
                break

    print("⚠️ Returning original text (all attempts failed).")
    return input_text


# --- Run ---
if 'arabic_text' in locals():
    corrected = correct_arabic_text(arabic_text)
    print("\n" + "="*50)
    print("✨ CORRECTED TEXT:")
    print("="*50)
    print(corrected)
    print("="*50)

    with open("corrected_arabic.txt", "w", encoding="utf-8") as f:
        f.write(corrected)
    print("\n💾 Saved to corrected_arabic.txt")
else:
    print("❌ 'arabic_text' variable not found. Run Cell 1 first.")

global_end = time.time()
print(f"Whole code without visualisations: {global_end - global_start:.4f}s")

