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
def validate_vectors(v1, v2):
    norm_v1 = np.linalg.norm(v1)
    norm_v2 = np.linalg.norm(v2)
    cond_norm = norm_v2 <= norm_v1 * 1.2
    if norm_v1 < 1e-6 or norm_v2 < 1e-6:
        cond_angle = False
    else:
        cos_angle = np.dot(v1, v2) / (norm_v1 * norm_v2)
        cos_angle = np.clip(cos_angle, -1.0, 1.0)
        angle_deg = np.degrees(np.arccos(cos_angle))
        cond_angle = angle_deg > 150.0

    if not (cond_norm and cond_angle):
        v2 = (-v1[0], -v1[1])

    return v1, v2

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
    v1, v2 = validate_vectors(v1, v2)
    return v1, v2

def process_image_in_tiles_4pass(warped_rgb, tile_size, margin_size=0):
    if len(warped_rgb.shape) == 3:
        gray = cv2.cvtColor(warped_rgb, cv2.COLOR_BGR2GRAY)
    else:
        gray = warped_rgb
    gray_f = gray.astype(np.float32)
    h, w = gray_f.shape
    offsets = [0,
               int(round(tile_size * 0.25)),
               int(round(tile_size * 0.50)),
               int(round(tile_size * 0.75))]

    acc1 = np.zeros((h, w), dtype=np.float32)
    acc2 = np.zeros((h, w), dtype=np.float32)
    for offset in offsets:
        pad_top = (tile_size - offset) % tile_size
        pad_left = (tile_size - offset) % tile_size
        padded = np.pad(gray_f,
                        ((pad_top, tile_size), (pad_left, tile_size)),
                        mode='edge')

        ph, pw = padded.shape
        ny = ph // tile_size
        nx = pw // tile_size
        tiled = padded[:ny*tile_size, :nx*tile_size]\
                    .reshape(ny, tile_size, nx, tile_size)\
                    .transpose(0, 2, 1, 3)

        tile_medians = np.median(
            tiled.reshape(ny, nx, -1), axis=-1
        )
        delta_tiled = (128.0 - tile_medians)\
                        .repeat(tile_size, axis=0)\
                        .repeat(tile_size, axis=1)

        delta_map = delta_tiled[pad_top:pad_top+h, pad_left:pad_left+w]
        nv = np.clip(gray_f + delta_map, 0.0, 255.0)
        acc1 += np.clip(2.0 * nv - 255.0, 0.0, None)
        acc2 += np.clip(255.0 - 2.0 * nv, 0.0, None)

    acc1 = np.clip(acc1 * 0.25, 0, 255).astype(np.uint8)
    acc2 = np.clip(acc2 * 0.25, 0, 255).astype(np.uint8)
    return acc1, acc2

def process_directional_wb(cleaned_total, Dot_Diameter):
    img = cleaned_total.astype(np.float32)
    h, w = img.shape
    k = max(1, int(round(Dot_Diameter / 2)))
    shifted = np.empty_like(img)
    temp    = np.empty_like(img)
    h_wb  = np.zeros_like(img)
    v_wb  = np.zeros_like(img)
    d1_wb = np.zeros_like(img)
    d2_wb = np.zeros_like(img)
    for i in range(1, k + 1):
        shifted[:, i:]  = img[:, :-i];  shifted[:, :i]  = img[:, :1]
        np.subtract(img, shifted, out=temp); np.maximum(0.0, temp, out=temp); h_wb += temp
        shifted[:, :-i] = img[:, i:];  shifted[:, -i:] = img[:, -1:]
        np.subtract(img, shifted, out=temp); np.maximum(0.0, temp, out=temp); h_wb += temp
        shifted[i:, :]  = img[:-i, :];  shifted[:i, :]  = img[:1, :]
        np.subtract(img, shifted, out=temp); np.maximum(0.0, temp, out=temp); v_wb += temp
        shifted[:-i, :] = img[i:, :];  shifted[-i:, :] = img[-1:, :]
        np.subtract(img, shifted, out=temp); np.maximum(0.0, temp, out=temp); v_wb += temp
        shifted[i:, i:] = img[:-i, :-i]; shifted[:i, :] = img[:1, :]; shifted[:, :i] = img[:, :1]
        np.subtract(img, shifted, out=temp); np.maximum(0.0, temp, out=temp); d1_wb += temp
        shifted[:-i, :-i] = img[i:, i:]; shifted[-i:, :] = img[-1:, :]; shifted[:, -i:] = img[:, -1:]
        np.subtract(img, shifted, out=temp); np.maximum(0.0, temp, out=temp); d1_wb += temp
        shifted[i:, :-i] = img[:-i, i:]; shifted[:i, :] = img[:1, :]; shifted[:, -i:] = img[:, -1:]
        np.subtract(img, shifted, out=temp); np.maximum(0.0, temp, out=temp); d2_wb += temp
        shifted[:-i, i:] = img[i:, :-i]; shifted[-i:, :] = img[-1:, :]; shifted[:, :i] = img[:, :1]
        np.subtract(img, shifted, out=temp); np.maximum(0.0, temp, out=temp); d2_wb += temp

    WB_mean = (h_wb + v_wb + d1_wb + d2_wb) * 0.25
    return np.clip(WB_mean, 0, 255).astype(np.uint8)

def translate(img, dy, dx):
    h, w = img.shape[:2]
    M = np.float32([[1, 0, dx], [0, 1, dy]])
    return cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_NEAREST, borderValue=0)

def build_probabilistic_layers(cleaned1, cleaned2, v1, v2):
    h, w = cleaned1.shape
    recto_blanc = np.zeros_like(cleaned1, dtype=np.float32)
    verso_blanc = np.zeros_like(cleaned1, dtype=np.float32)
    shifted_v1 = translate(cleaned2, v1[1], v1[0])
    shifted_v2 = translate(cleaned2, v2[1], v2[0])
    A = shifted_v1.astype(np.float32)
    B = shifted_v2.astype(np.float32)
    C = cleaned1.astype(np.float32)
    p_recto = A / (A + B + + 1e-6)
    p_verso = B / (A + B + + 1e-6)
    recto_blanc = C * p_recto
    verso_blanc = C * p_verso
    return (recto_blanc.astype(np.uint8),
            verso_blanc.astype(np.uint8))


def mean_neighbors_kernel_full(img, k=4):
    return cv2.boxFilter(img.astype(np.float32), -1, (k, k),
                         normalize=True, borderType=cv2.BORDER_CONSTANT)

def merge_with_full_kernel_4layers(rb, rn, vb, vn, k=4, p=3):
    total_recto = rb.astype(np.float32) + rn.astype(np.float32)
    total_verso = vb.astype(np.float32) + vn.astype(np.float32)
    mean_r = mean_neighbors_kernel_full(total_recto, k)
    mean_v = mean_neighbors_kernel_full(total_verso, k)
    cond_recto = mean_r > (mean_v * p)
    cond_verso = mean_v > (mean_r * p)
    rb_new, rn_new = rb.copy(), rn.copy()
    vb_new, vn_new = vb.copy(), vn.copy()
    rb_new = np.where(cond_recto, rb_new + vb_new, rb_new)
    vb_new = np.where(cond_recto, 0, vb_new)
    rn_new = np.where(cond_recto, rn_new + vn_new, rn_new)
    vn_new = np.where(cond_recto, 0, vn_new)
    vb_new = np.where(cond_verso, vb_new + rb_new, vb_new)
    rb_new = np.where(cond_verso, 0, rb_new)
    vn_new = np.where(cond_verso, vn_new + rn_new, vn_new)
    rn_new = np.where(cond_verso, 0, rn_new)
    return (np.clip(rb_new, 0, 255).astype(np.uint8), 
            np.clip(rn_new, 0, 255).astype(np.uint8), 
            np.clip(vb_new, 0, 255).astype(np.uint8), 
            np.clip(vn_new, 0, 255).astype(np.uint8))

def plus_kernel_filter(img, size, v1_first):
    k = size
    img_f = img.astype(np.float32)
    vx, vy = v1_first
    angle = atan2(vy, vx)
    use_horizontal_strip = (abs(cos(angle)) >= abs(sin(angle)))

    weights_5 = np.array([0.25, 0.5, 1.0, 0.5, 0.25], dtype=np.float32)

    if use_horizontal_strip:
        tmp    = cv2.boxFilter(img_f, -1, (k, 1), normalize=False,
                               borderType=cv2.BORDER_CONSTANT)
        conv_h = convolve1d(tmp, weights_5, axis=0, mode='constant', cval=0.0)
        conv_v = np.zeros_like(img_f)
    else:
        tmp    = cv2.boxFilter(img_f, -1, (1, k), normalize=False,
                               borderType=cv2.BORDER_CONSTANT)
        conv_v = convolve1d(tmp, weights_5, axis=1, mode='constant', cval=0.0)
        conv_h = np.zeros_like(img_f)

    sum_h  = float(np.sum(weights_5) * k) if use_horizontal_strip else 1e-6
    sum_v  = float(np.sum(weights_5) * k) if not use_horizontal_strip else 1e-6
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
    v_a = np.array(vec).flatten()
    v_b = np.array(reference_v).flatten()
    norm_a = np.linalg.norm(v_a)
    norm_b = np.linalg.norm(v_b)
    if norm_a == 0 or norm_b == 0:
        return np.pi
        
    cos_theta = np.dot(v_a, v_b) / (norm_a * norm_b)
    cos_theta = np.clip(cos_theta, -1.0, 1.0)
    return np.arccos(cos_theta)

def separate_by_probability(img_recto, img_verso, threshold=0.7):
    R = img_recto.astype(np.float32)
    V = img_verso.astype(np.float32)
    total = R + V + 1e-6
    p_recto = R / total
    mask_sure_R  = p_recto >= threshold
    mask_sure_V  = p_recto <  (1.0 - threshold)
    sure_R   = (R   * mask_sure_R).astype(np.uint8)
    unsure_R = (R   * ~mask_sure_R).astype(np.uint8)
    sure_V   = (V   * mask_sure_V).astype(np.uint8)
    unsure_V = (V   * ~mask_sure_V).astype(np.uint8)
    return sure_R, unsure_R, sure_V, unsure_V

def translate_image(img, shift):
    M = np.float32([[1, 0, shift[0]],
                    [0, 1, shift[1]]])
    return cv2.warpAffine(img, M, (img.shape[1], img.shape[0]),
                          flags=cv2.INTER_LINEAR,
                          borderMode=cv2.BORDER_CONSTANT,
                          borderValue=0)

def get_image_median(img):
    hist = cv2.calcHist([img], [0], None, [256], [0, 256])
    cumulative_sum = hist.cumsum()
    median_val = np.searchsorted(cumulative_sum, cumulative_sum[-1] / 2)
    return median_val

def restore_intensity(noisy_img, clean_mask, expand=1):
    mask = clean_mask > 0
    if expand > 0:
        kernel = np.ones((3, 3), dtype=np.uint8)
        mask = cv2.dilate(mask.astype(np.uint8), kernel, iterations=expand).astype(bool)
    Dot_Diameter = np.zeros_like(noisy_img)
    Dot_Diameter[mask] = noisy_img[mask]
    return Dot_Diameter

@njit(cache=True, fastmath=True, nogil=True)
def phase1_concentrate_centroid(img, win_size):
    rows, cols = img.shape
    k = win_size // 2
    res = np.zeros((rows, cols), dtype=img.dtype)
    for y in range(rows):
        for x in range(cols):
            val = img[y, x]
            if val <= 0:
                continue
                
            y_min = max(0, y - k)
            y_max = min(rows, y + k + 1)
            x_min = max(0, x - k)
            x_max = min(cols, x + k + 1)
            mass_sum = 0.0
            y_weighted_sum = 0.0
            x_weighted_sum = 0.0
            for wy in range(y_min, y_max):
                for wx in range(x_min, x_max):
                    v = img[wy, wx]
                    if v > 0:
                        mass_sum += v
                        y_weighted_sum += wy * v
                        x_weighted_sum += wx * v

            if mass_sum > 0:
                target_y = int(y_weighted_sum / mass_sum + 0.5)
                target_x = int(x_weighted_sum / mass_sum + 0.5)
                if target_y < 0: target_y = 0
                elif target_y >= rows: target_y = rows - 1
                if target_x < 0: target_x = 0
                elif target_x >= cols: target_x = cols - 1
                res[target_y, target_x] += val
            else:
                res[y, x] += val
    return res

@njit(cache=True, nogil=True)
def phase2_redistribute(img, median_1):
    rows, cols = img.shape

    for y in range(rows):
        for x in range(cols):
            val = img[y, x]
            if val <= median_1:
                continue

            k    = int(val / median_1)
            rest = val - median_1 * k
            img[y, x] = median_1
            needed    = k - 1
            has_rest  = rest > 0
            filled    = 0
            rest_done = not has_rest
            max_r = int(k**0.5 * 2) + 5
            r = 1
            while (filled < needed or not rest_done) and r <= max_r:
                for dy in range(-r, r + 1):
                    for dx in range(-r, r + 1):
                        if abs(dy) != r and abs(dx) != r:
                            continue
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

def filter_dots_by_mass(concentrated_img, ratio=0.15):
    img = concentrated_img.copy()
    masses = img[img > 0]
    if masses.size == 0:
        return img
    median_mass = np.mean(masses)
    threshold = ratio * median_mass
    img[img < threshold] = 0
    return img

def filter_dots_by_mass_top_1(concentrated_img, median_1, ratio=0.15):
    img = concentrated_img.copy()
    threshold = ratio * median_1
    img[img < threshold] = 0
    return img

def median_top_1_percent(img, per= 99):
    pixels = img.ravel()
    threshold = np.percentile(pixels, per)
    top_pixels = pixels[pixels >= threshold]
    if top_pixels.size == 0: return 255.0
    return np.median(top_pixels)

def concentrate_single_image(image, window_size):
    if window_size % 2 == 0:
        window_size += 1
        
    Dot_Diameter = phase1_concentrate_centroid(image.astype(np.float32), window_size)
    return Dot_Diameter

def concentrate_contours_second_slow(image, k=2):
    binary_mask = (image > 0).astype(np.uint8)
    num_labels, labels = cv2.connectedComponents(binary_mask)
    h, w = image.shape
    output = np.zeros((h, w), dtype=np.float64)
    threshold_limit = k * 255.0
    if num_labels <= 1:
        return output.astype(image.dtype), []

    flat_labels = labels.ravel()
    flat_image = image.ravel().astype(np.float64)
    masses = np.bincount(flat_labels, weights=flat_image)
    y_coords, x_coords = np.indices((h, w))
    sum_y = np.bincount(flat_labels, weights=(flat_image * y_coords.ravel()))
    sum_x = np.bincount(flat_labels, weights=(flat_image * x_coords.ravel()))
    areas = np.bincount(flat_labels)
    contour_data = []
    for i in range(1, num_labels):
        pixel_sum = masses[i]
        
        if pixel_sum <= threshold_limit:
            continue
            
        cy = int(round(sum_y[i] / pixel_sum))
        cx = int(round(sum_x[i] / pixel_sum))
        cy = max(0, min(h - 1, cy))
        cx = max(0, min(w - 1, cx))
        output[cy, cx] += pixel_sum
        contour_data.append({
            "center": (cx, cy),
            "pixel_sum": pixel_sum,
            "area": areas[i]
        })
    return output.astype(image.dtype), contour_data

def apply_centroid_concentration_2(img_input, v1_norm, median_1, win):
    if win % 2 == 0: win += 1
    concentrated = phase1_concentrate_centroid(img_input.astype(np.float32), win)
    final_float = phase2_redistribute(concentrated, median_1)
    return np.round(np.clip(final_float, 0, 255)).astype(np.uint8), concentrated

def get_shifted(image, dx, dy):
    dx, dy = int(round(dx)), int(round(dy))
    if dx == 0 and dy == 0:
        return image.copy()
    h, w = image.shape[:2]
    Dot_Diameter = np.zeros_like(image)
    src_y0, src_y1 = max(0, -dy), h - max(0, dy)
    src_x0, src_x1 = max(0, -dx), w - max(0, dx)
    dst_y0, dst_y1 = max(0, dy),  h - max(0, -dy)
    dst_x0, dst_x1 = max(0, dx),  w - max(0, -dx)
    if src_y1 > src_y0 and src_x1 > src_x0:
        Dot_Diameter[dst_y0:dst_y1, dst_x0:dst_x1] = image[src_y0:src_y1, src_x0:src_x1]
    return Dot_Diameter

def filter_vertical_anomalies_center_only(img, nv, r_size):
    rows, cols = img.shape
    img_f = img.astype(np.float32)
    density = cv2.boxFilter(img_f, -1, (r_size, r_size), normalize=False)
    d0 = density                         
    d1 = get_shifted(density, 0, -nv)    
    d2 = get_shifted(density, 0, -2*nv)  
    d3 = get_shifted(density, 0, -3*nv)
    active4 = (d0 > 0) & (d1 > 0) & (d2 > 0) & (d3 > 0)
    min_val = np.minimum(np.minimum(d0, d1), np.minimum(d2, d3))
    kill0 = active4 & (d0 == min_val)
    kill1 = get_shifted((active4 & (d1 == min_val) & (d1 < d0)).astype(np.float32), 0, nv)
    kill2 = get_shifted((active4 & (d2 == min_val) & (d2 < d1) & (d2 < d0)).astype(np.float32), 0, 2*nv)
    kill3 = get_shifted((active4 & (d3 == min_val) & (d3 < d2) & (d3 < d1) & (d3 < d0)).astype(np.float32), 0, 3*nv)
    final_kill_points = (kill0.astype(np.uint8) | kill1.astype(np.uint8) | 
                         kill2.astype(np.uint8) | kill3.astype(np.uint8))

    filtered_img = img.copy()
    filtered_img[final_kill_points > 0] = 0
    
    return filtered_img, final_kill_points

def complete_by_grid_density(img, period, N=3, threshold=3):
    rows, cols = img.shape
    _, binary = cv2.threshold(img, 1, 1, cv2.THRESH_BINARY)
    binary = binary.astype(np.float32)
    density_accumulator = np.zeros_like(binary)
    dy = 0
    for kx in range(-N, N+1):
        dx = kx * period
        density_accumulator += get_shifted(binary, dx, dy)

    new_discoveries = (density_accumulator > threshold).astype(np.uint8)
    Dot_Diameter_img = np.maximum(img, (new_discoveries * 255))
    
    return Dot_Diameter_img

def _build_block_matrix(y_idx, x_idx, norm_int,
                        nv, hw_x, hw_y, tol, nvm):
    n = len(y_idx)
    xi = x_idx.astype(np.float32)
    yi = y_idx.astype(np.float32)
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
    dy_raw = yi[jj] - yi[ii]
    dx_abs = np.abs(xi[jj] - xi[ii])
    dy_abs = np.abs(dy_raw)
 
    in_box = (dy_abs < hw_y) & (dx_abs < hw_x)
    if not in_box.any():
        return _empty_block()
 
    ii  = ii[in_box];  jj     = jj[in_box]
    dy_raw = dy_raw[in_box]; dx_abs = dx_abs[in_box]; dy_abs = dy_abs[in_box]
    inv_d = (1.0 / (np.hypot(dx_abs, dy_abs) + 1.0)).astype(np.float32)
    w_ij  = inv_d * norm_int[jj]
    w_ji  = inv_d * norm_int[ii]
    def _masks(dr, da):
        mA  = (da < tol) | (np.abs(da - nvm) < tol)
        mB  = (~mA) & ((np.abs(dr - nv) < tol)  | (np.abs(dr - nv + nvm) < tol))
        mC  = (~mA) & (~mB) & \
              ((np.abs(dr + nv) < tol)  | (np.abs(dr + nv - nvm) < tol))
        mD  = (~mA) & (~mB) & (~mC) & \
              ((np.abs(da - 2*nv) < tol) | (np.abs(da - 2*nv + nvm) < tol))
        return mA, mB, mC, mD & (dr > 0), mD & (dr <= 0)
 
    mA,  mB,  mC,  mDb,  mDa  = _masks( dy_raw, dy_abs)
    mAr, mBr, mCr, mDbr, mDar = _masks(-dy_raw, dy_abs)
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
    M = bmat([[WA,  WC,  WDa],
              [WB,  WA,  WC ],
              [WDb, WB,  WA ]], format='csr')
    return M

def propagate_unsure_beliefs(concentrated_recto, nv, hw_x, hw_y,
                              neighbors_vertical_mid_p,
                              iterations=20, confidence_threshold=0.34):
    t0 = time.perf_counter()
    y_idx, x_idx = np.where(concentrated_recto > 0)
    n = len(y_idx)
    shape = concentrated_recto.shape
    Z = np.zeros(shape, dtype=np.float64)
    if n == 0:
        return Z, Z.copy(), Z.copy(), Z.copy()
 
    intens   = concentrated_recto[y_idx, x_idx].astype(np.float32)
    mx       = float(intens.max()) or 1.0
    norm_int = intens / mx
    tol      = nv * 0.4
    M = _build_block_matrix(y_idx, x_idx, norm_int,
                            nv, hw_x, hw_y, tol, neighbors_vertical_mid_p)
    probs_f = np.full(3 * n, 1.0 / 3.0, dtype=np.float32)
    norm3   = np.tile(norm_int, 3)
    combined_f = np.empty(3 * n, dtype=np.float32)
    total_buf  = np.empty(n,     dtype=np.float32)
    old_f      = np.empty(3 * n, dtype=np.float32)
    actual_iters = 0
    for it in range(iterations):
        if it % 5 == 0:
            old_f[:] = probs_f
 
        votes_f = M @ probs_f
        np.multiply(probs_f, norm3, out=combined_f)
        combined_f += votes_f
        combined_3xn = combined_f.reshape(3, n)
        np.sum(combined_3xn, axis=0, out=total_buf)
        has_signal = total_buf > 0
        if has_signal.any():
            probs_3xn = probs_f.reshape(3, n)
            probs_3xn[:, has_signal] = (
                combined_3xn[:, has_signal] / total_buf[has_signal]
            )
        actual_iters = it + 1
        if it % 5 == 4:
            delta = float(np.abs(probs_f - old_f).max())
            if delta < 1e-4:
                break
 
    probs_mat = probs_f.reshape(3, n).T
    best_idx = np.argmax(probs_mat, axis=1)
    best_val = probs_mat[np.arange(n), best_idx]
    confident   = best_val >= confidence_threshold
    unconfident = ~confident
    intens64 = intens.astype(np.float64)
    out_T        = np.zeros(shape, np.float32)
    out_M        = np.zeros(shape, np.float32)
    out_D        = np.zeros(shape, np.float32)
    still_unsure = np.zeros(shape, np.float32)
    still_unsure[y_idx[unconfident], x_idx[unconfident]] = intens64[unconfident]
    m0 = confident & (best_idx == 0)
    m1 = confident & (best_idx == 1)
    m2 = confident & (best_idx == 2)
    out_T[y_idx[m0], x_idx[m0]] = intens64[m0]
    out_M[y_idx[m1], x_idx[m1]] = intens64[m1]
    out_D[y_idx[m2], x_idx[m2]] = intens64[m2]
    return out_T, out_M, out_D, still_unsure

def apply_centroid_concentration_batch(imgs, v1_norm, median_1, win):
    if win % 2 == 0: win += 1

    def process_one(img):
        final = phase2_redistribute(img, median_1)
        return np.round(np.clip(final, 0, 255)).astype(np.uint8)

    with ThreadPoolExecutor(max_workers=min(len(imgs), 7)) as ex:
        Dot_Diameters = list(ex.map(process_one, imgs))
    return Dot_Diameters

def _build_block_matrix_lr(y_idx, x_idx, norm_int,
                           nh, fnh, period, hw_x, hw_y, tol):
    n  = len(y_idx)
    xi = x_idx.astype(np.float32)
    yi = y_idx.astype(np.float32)
    tree  = cKDTree(np.column_stack([yi, xi]))
    max_r = float(np.hypot(hw_y, hw_x))
    try:
        pairs = tree.query_pairs(max_r, output_type='ndarray', workers=-1)
    except TypeError:                          # scipy < 1.7
        pairs = tree.query_pairs(max_r, output_type='ndarray')
    empty = csr_matrix((n, n), dtype=np.float32)
    def _empty_block():
        return bmat([[empty, empty], [empty, empty]], format='csr')

    if pairs.shape[0] == 0:
        return _empty_block()

    ii, jj = pairs[:, 0], pairs[:, 1]
    dx_raw = xi[jj] - xi[ii]
    dy_abs = np.abs(yi[jj] - yi[ii])
    dx_abs = np.abs(dx_raw)
    in_box = (dy_abs < hw_y) & (dx_abs < hw_x)
    if not in_box.any():
        return _empty_block()

    ii     = ii[in_box];     jj     = jj[in_box]
    dx_raw = dx_raw[in_box]; dx_abs = dx_abs[in_box]; dy_abs = dy_abs[in_box]
    inv_d = (1.0 / (np.hypot(dx_abs, dy_abs) + 1.0)).astype(np.float32)
    w_ij  = inv_d * norm_int[jj] 
    w_ji  = inv_d * norm_int[ii]
    def _masks(dx):
        da = np.abs(dx)
        mSame = (da < tol) | (np.abs(da - period) < tol)
        mRL = (
            (np.abs(dx - nh)          < tol) |
            (np.abs(dx + fnh)         < tol)
        )
        mLR = (
            (np.abs(dx + nh)          < tol) |
            (np.abs(dx - fnh)         < tol)
        )

        return mSame, mRL, mLR

    mSame,  mRL,  mLR  = _masks( dx_raw)
    mSamer, mRLr, mLRr = _masks(-dx_raw)
    def _csr(mi, mj, wi, wj):
        r = np.concatenate([ii[mi], jj[mj]])
        c = np.concatenate([jj[mi], ii[mj]])
        d = np.concatenate([wi[mi], wj[mj]])
        if len(r) == 0:
            return empty
        return csr_matrix((d, (r, c)), shape=(n, n), dtype=np.float32)

    W_same = _csr(mSame, mSamer, w_ij, w_ji)
    W_RL   = _csr(mRL,   mRLr,   w_ij, w_ji)
    W_LR   = _csr(mLR,   mLRr,   w_ij, w_ji)
    M = bmat([[W_same, W_RL ],
              [W_LR,   W_same]], format='csr')
    return M

def propagate_lr_beliefs(concentrated_recto, nh, fnh, period,
                         hw_x, hw_y,
                         iterations=20, confidence_threshold=0.6):
    y_idx, x_idx = np.where(concentrated_recto > 0)
    n     = len(y_idx)
    shape = concentrated_recto.shape
    Z     = np.zeros(shape, dtype=np.float64)
    if n == 0:
        return Z, Z.copy(), Z.copy()

    intens   = concentrated_recto[y_idx, x_idx].astype(np.float32)
    mx       = float(intens.max()) or 1.0
    norm_int = intens / mx
    tol = abs(nh - fnh) * 0.4
    t1 = time.perf_counter()
    M = _build_block_matrix_lr(y_idx, x_idx, norm_int,
                               nh, fnh, period, hw_x, hw_y, tol)
    probs_f = np.full(2 * n, 0.5, dtype=np.float32)
    norm2   = np.tile(norm_int, 2)
    combined_f = np.empty(2 * n, dtype=np.float32)
    total_buf  = np.empty(n,     dtype=np.float32)
    old_f      = np.empty(2 * n, dtype=np.float32)
    actual_iters = 0
    for it in range(iterations):
        if it % 5 == 0:
            old_f[:] = probs_f

        votes_f = M @ probs_f
        np.multiply(probs_f, norm2, out=combined_f)
        combined_f += votes_f
        combined_2xn = combined_f.reshape(2, n)   # view — no copy
        np.sum(combined_2xn, axis=0, out=total_buf)

        has_signal = total_buf > 0
        if has_signal.any():
            probs_2xn = probs_f.reshape(2, n)
            probs_2xn[:, has_signal] = (
                combined_2xn[:, has_signal] / total_buf[has_signal]
            )
        actual_iters = it + 1
        if it % 5 == 4:
            delta = float(np.abs(probs_f - old_f).max())
            if delta < 1e-4:
                break

    probs_mat = probs_f.reshape(2, n).T
    best_idx  = np.argmax(probs_mat, axis=1)
    best_val  = probs_mat[np.arange(n), best_idx]
    confident   = best_val >= confidence_threshold
    unconfident = ~confident
    intens64    = intens.astype(np.float64)
    out_L        = np.zeros(shape, np.float64)
    out_R        = np.zeros(shape, np.float64)
    still_unsure = np.zeros(shape, np.float64)
    still_unsure[y_idx[unconfident], x_idx[unconfident]] = intens64[unconfident]
    mL = confident & (best_idx == 0)
    mR = confident & (best_idx == 1)
    out_L[y_idx[mL], x_idx[mL]] = intens64[mL]
    out_R[y_idx[mR], x_idx[mR]] = intens64[mR]
    return out_L, out_R, still_unsure

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

def refine_horizontal_by_modulo_voting_vec(concentrated_unsure_dots,
                                           conc_L, conc_R,
                                           period, hw_x, hw_y):
    shape = concentrated_unsure_dots.shape
    u_y, u_x = np.where(concentrated_unsure_dots > 0)
    n_u = len(u_y)
    if n_u == 0:
        return (np.zeros(shape, np.float64),
                np.zeros(shape, np.float64))

    u_coords = np.column_stack([u_y, u_x]).astype(np.float32)
    u_vals   = concentrated_unsure_dots[u_y, u_x].astype(np.float64)
    tree_u   = cKDTree(u_coords)
    errors  = np.zeros((n_u, 2), dtype=np.float64)   # [L, R]
    weights = np.zeros((n_u, 2), dtype=np.float64)
    max_r = float(np.hypot(hw_y, hw_x))
    for c_idx, conc in enumerate([conc_L, conc_R]):
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

        dx_raw = np.abs(u_x[u_ids] - a_x[a_ids]).astype(np.float64)
        dy_raw = np.abs(u_y[u_ids] - a_y[a_ids]).astype(np.float64)
        in_box = (dy_raw < hw_y) & (dx_raw < hw_x)
        u_ids, a_ids   = u_ids[in_box],  a_ids[in_box]
        dx_raw, dy_raw = dx_raw[in_box], dy_raw[in_box]
        if len(u_ids) == 0:
            continue

        dist          = np.hypot(dx_raw, dy_raw)
        w             = a_vals[a_ids] / (dist + 1.0)
        mod           = dx_raw % period
        alignment_err = np.minimum(mod, period - mod)
        errors [:, c_idx] += np.bincount(u_ids, weights=alignment_err * w, minlength=n_u)
        weights[:, c_idx] += np.bincount(u_ids, weights=w,                 minlength=n_u)

    has_weight = weights > 0
    avg_err    = np.where(has_weight, errors / np.where(has_weight, weights, 1.0), np.inf)
    best_class = np.argmin(avg_err, axis=1)   # 0=L, 1=R
    has_any    = has_weight.any(axis=1)
    out_L = np.zeros(shape, np.float64)
    out_R = np.zeros(shape, np.float64)
    mL = has_any & (best_class == 0)
    mR = has_any & (best_class == 1)
    out_L[u_y[mL], u_x[mL]] = u_vals[mL]
    out_R[u_y[mR], u_x[mR]] = u_vals[mR]
    return out_L, out_R

def apply_horizontal_refinement(concentrated_unsure_dots,
                                 concentrated_left_f, concentrated_right_f,
                                 period, hw_x, hw_y):
    concentrated_new_l, concentrated_new_r = refine_horizontal_by_modulo_voting_vec(
        concentrated_unsure_dots.astype(np.float64),
        concentrated_left_f.astype(np.float64),
        concentrated_right_f.astype(np.float64),
        period, hw_x, hw_y
    )
    concentrated_left_v  = concentrated_left_f.astype(np.float64)  + concentrated_new_l
    concentrated_right_v = concentrated_right_f.astype(np.float64) + concentrated_new_r
    concentrated_classified_mask = (concentrated_new_l + concentrated_new_r) > 0
    concentrated_still_unsure    = concentrated_unsure_dots.copy().astype(np.float64)
    concentrated_still_unsure[concentrated_classified_mask] = 0
    return concentrated_left_v, concentrated_right_v, concentrated_still_unsure

def redistribute(L, R, top_mask, mid_mask, down_mask):
    t, m, d = [mask.astype(np.uint8) for mask in [top_mask, mid_mask, down_mask]]
    rd1 = cv2.bitwise_and(L, L, mask=t)
    rd2 = cv2.bitwise_and(L, L, mask=m)
    rd3 = cv2.bitwise_and(L, L, mask=d)
    rd4 = cv2.bitwise_and(R, R, mask=t)
    rd5 = cv2.bitwise_and(R, R, mask=m)
    rd6 = cv2.bitwise_and(R, R, mask=d)
    return rd1, rd2, rd3, rd4, rd5, rd6

def enhance_score_map_by_voting(score_map, period, nv, threshold=5):
    rows, cols = score_map.shape
    binary_scores = (score_map > 0).astype(np.float32)
    votes = np.zeros_like(binary_scores)
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

def find_and_score_structural_boxes_fast(fd_list, nh, nv, NP=4):
    rows, cols = fd_list[0].shape
    total_score_map = np.zeros((rows, cols), dtype=np.float32)
    presence_count = np.zeros((rows, cols), dtype=np.uint8)
    dot_size = int(nh/3) | 1
    warp_params = [(0, -2*nv), (0, -nv), (0, 0), (-nh, -2*nv), (-nh, -nv), (-nh, 0)]
    for fd, p in zip(fd_list, warp_params):
        s = cv2.boxFilter(fd.astype(np.float32), -1, (dot_size, dot_size), normalize=True)
        if p == (0, 0):
            shifted_s = s
        else:
            shifted_s = get_shifted(s, p[0], p[1])
            
        total_score_map += shifted_s
        presence_count += (shifted_s > 0).astype(np.uint8)
    total_score_map *= (presence_count >= NP)
    
    return [], total_score_map

def rescue_and_concentrate_boxes_dual(nh, nv, period, neighbors_vertical_mid_p, Dot_Diameter, score_map_strict, score_map_loose, Nx=10, Ny=10):
    rows, cols = score_map_strict.shape
    dot_size = int(nh/2) | 1
    step_x = int(round(period))
    step_y = int(round(min(4 * nv, neighbors_vertical_mid_p)))
    def _get_k1d(N, step, horizontal=True):
        length = 2 * N * step + 1
        k = np.zeros((1, length) if horizontal else (length, 1), dtype=np.float32)
        for i in range(-N, N + 1):
            if i == 0: continue
            center = i * step + N * step
            k.flat[max(0, center-dot_size) : center+dot_size+1] = 1.0
        return k
    
    kh = _get_k1d(Nx, step_x, True)
    kv = _get_k1d(Ny, step_y, False)
    binary_strict = (score_map_strict > 0).astype(np.uint8)
    votes_h = cv2.filter2D(binary_strict, -1, kh, borderType=cv2.BORDER_CONSTANT)
    votes_v = cv2.filter2D(binary_strict, -1, kv, borderType=cv2.BORDER_CONSTANT)
    rescue_mask = ((votes_h >= 1) | (votes_v >= 1)) & (score_map_loose > 0)
    combined_score_map = score_map_strict.copy()
    mask_to_fill = (combined_score_map == 0) & rescue_mask
    combined_score_map[mask_to_fill] = score_map_loose[mask_to_fill]
    win = int(period) | 1
    final_map, _ = concentrate_contours_second_slow(combined_score_map, k=2)
    y_idx, x_idx = np.where(final_map > 0)
    scores = final_map[y_idx, x_idx]
    sort_idx = np.argsort(-scores) # Sort descending by score
    x_s, y_s, scores_s = x_idx[sort_idx], y_idx[sort_idx], scores[sort_idx]
    final_boxes = []
    if len(x_s) > 0:
        pts_arr = np.column_stack((x_s, y_s))
        tree_nms = cKDTree(pts_arr)
        all_pairs = tree_nms.query_pairs(period * 0.8, output_type='ndarray')
        suppressed = np.zeros(len(x_s), dtype=bool)
        if all_pairs.size > 0:
            for i, j in all_pairs:
                if not suppressed[i]:
                    suppressed[j] = True

        is_rescued_arr = (score_map_strict[y_s, x_s] == 0)
        for i in range(len(x_s)):
            if suppressed[i]: continue
            final_boxes.append({
                'x': int(x_s[i] - nh / 2),
                'y': int(y_s[i] - nv / 2),
                'w': int(2 * nh),
                'h': int(3 * nv),
                'score': float(scores_s[i]),
                'is_rescued': bool(is_rescued_arr[i])
            })
    return final_boxes, combined_score_map

def reconstruct_layer(img_a, img_b):
    added_a = cv2.add(128, img_a.astype(np.uint8))
    added_b = cv2.add(128, img_b.astype(np.uint8))
    res = cv2.addWeighted(added_a, 0.5, 255 - added_b, 0.5, 0)
    return np.clip(res, 0, 255).astype(np.uint8)

def remove_small_dots_binary(img, min_area=10):
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(
        img, connectivity=8
    )
    valid = np.where(stats[:, cv2.CC_STAT_AREA] >= min_area)[0]
    valid = valid[valid != 0]
    cleaned = np.isin(labels, valid).astype(np.uint8) * 255
    return cleaned

def _shift_inplace(src, dx, dy, dst):
    dx, dy = int(round(dx)), int(round(dy))
    h, w = src.shape
    dst[:] = 0
    if dx == 0 and dy == 0:
        np.copyto(dst, src); return
    sy0, sy1 = max(0, -dy), h - max(0, dy)
    sx0, sx1 = max(0, -dx), w - max(0, dx)
    dy0, dy1 = max(0,  dy), h - max(0,-dy)
    dx0, dx1 = max(0,  dx), w - max(0,-dx)
    if sy1 > sy0 and sx1 > sx0:
        dst[dy0:dy1, dx0:dx1] = src[sy0:sy1, sx0:sx1]

def complete_braille_grid_logic_merged(img, h_offsets, v_distances):
    _, binary = cv2.threshold(img, 1, 1, cv2.THRESH_BINARY)
    binary = binary.astype(np.float32)
    discovery_map = np.zeros_like(binary)
    unique_h = sorted(set(abs(x) for x in h_offsets if x != 0))
    p2 = np.empty_like(binary); p3 = np.empty_like(binary)
    p4 = np.empty_like(binary); cs = np.empty_like(binary)
    t0 = np.empty_like(binary); t1 = np.empty_like(binary)
    t2 = np.empty_like(binary); t3 = np.empty_like(binary)
    for dx in unique_h:
        _shift_inplace(binary, dx, 0, p2)
        for dy in v_distances:
            _shift_inplace(binary, 0, dy, p3)
            _shift_inplace(binary, dx, dy, p4)
            np.add(binary, p2, out=cs); cs += p3; cs += p4
            np.greater_equal(cs, 3, out=t0); t0 = t0.astype(np.float32)
            _shift_inplace(t0, -dx,   0, t1)
            _shift_inplace(t0,   0, -dy, t2)
            _shift_inplace(t0, -dx, -dy, t3)
            np.maximum(discovery_map, t0, out=discovery_map)
            np.maximum(discovery_map, t1, out=discovery_map)
            np.maximum(discovery_map, t2, out=discovery_map)
            np.maximum(discovery_map, t3, out=discovery_map)
    return np.maximum(img, (discovery_map * 255).astype(np.uint8))

def complete_braille_diagonal_logic_merged(img, h_offsets, v_distances):
    _, binary = cv2.threshold(img, 1, 1, cv2.THRESH_BINARY)
    binary = binary.astype(np.float32)
    discovery_map = np.zeros_like(binary)
    unique_h = sorted(set(abs(x) for x in h_offsets if x != 0))
    p2 = np.empty_like(binary); p3 = np.empty_like(binary)
    p4 = np.empty_like(binary)
    db = np.empty_like(binary); df = np.empty_like(binary)
    t1 = np.empty_like(binary); t2 = np.empty_like(binary)
    for dx in unique_h:
        _shift_inplace(binary, dx, 0, p2)
        for dy in v_distances:
            _shift_inplace(binary, 0, dy, p3)
            _shift_inplace(binary, dx, dy, p4)
            np.greater(binary, 0, out=db); db2 = db.astype(np.float32)
            np.greater(p4, 0, out=db);     db_f = (db2 * db.astype(np.float32))
            _shift_inplace(db_f, -dx,   0, t1)
            _shift_inplace(db_f,   0, -dy, t2)
            np.maximum(discovery_map, t1, out=discovery_map)
            np.maximum(discovery_map, t2, out=discovery_map)
            np.greater(p2, 0, out=db);     df2 = db.astype(np.float32)
            np.greater(p3, 0, out=db);
            diag_fs = df2 * db.astype(np.float32)
            np.maximum(discovery_map, diag_fs, out=discovery_map)
            _shift_inplace(diag_fs, -dx, -dy, t1)
            np.maximum(discovery_map, t1, out=discovery_map)
    return np.maximum(img, (discovery_map * 255).astype(np.uint8))


def find_top_k_self_translations(img, min_h, min_w, max_h, max_w, k=20):
    img_f = img.astype(np.float32)
    padded = cv2.copyMakeBorder(img_f, max_h, max_h, max_w, max_w, cv2.BORDER_CONSTANT, value=0)
    res = cv2.matchTemplate(padded, img_f, cv2.TM_CCORR_NORMED)
    h_res, w_res = res.shape
    center_y, center_x = h_res // 2, w_res // 2
    res[center_y - min_h : center_y + min_h,
        center_x - min_w : center_x + min_w] = 0

    suppression_h = max(3, min_h // 2)
    suppression_w = max(3, min_w // 2)
    vectors = []
    temp_res = res.copy()
    for _ in range(k):
        _, max_val, _, max_loc = cv2.minMaxLoc(temp_res)
        if max_val <= 1e-6:
            break
        dx = max_loc[0] - max_w
        dy = max_loc[1] - max_h
        vectors.append((dx, dy, max_val))
        y, x = max_loc[1], max_loc[0]
        temp_res[max(0, y - suppression_h) : min(h_res, y + suppression_h),
                 max(0, x - suppression_w) : min(w_res, x + suppression_w)] = 0
    return vectors

def extract_braille_metrics_from_vectors(vectors, v1_norm):
    cluster_thr  = v1_norm * 0.25
    additive_tol = v1_norm * 0.5
    min_dx       = v1_norm * 1.5
    clusters: list[list[float]] = []   # [center, total_weight]
    for dx, dy, score in vectors:
        adx = abs(dx)
        if adx < min_dx:
            continue

        horizontal_purity = 1.0 / (1.0 + abs(dy) / v1_norm)
        effective_weight  = score * horizontal_purity
        for entry in clusters:
            if abs(adx - entry[0]) <= cluster_thr:
                new_w    = entry[1] + effective_weight
                entry[0] = (entry[0] * entry[1] + adx * effective_weight) / new_w
                entry[1] = new_w
                break
        else:
            clusters.append([float(adx), float(effective_weight)])

    for entry in clusters:
        entry[0] = round(entry[0])

    clusters.sort(key=lambda x: x[0])
    n = len(clusters)
    if n == 0:
        h_near = v1_norm * 2.5
        return {
            "neighbors_horizontal":     round(h_near, 3),
            "far_neighbors_horizontal": round(h_near * 1.3, 3),
            "period_horizontal":        round(h_near * 2.3, 3),
        }

    best_triplet = None
    best_score   = -1.0
    for i in range(n):
        for j in range(i + 1, n):
            a, wa = clusters[i]
            b, wb = clusters[j]
            if not (a * 1.1 <= b <= a * 1.6):
                continue
            
            expected = a + b
            for k in range(n):
                if k == i or k == j:
                    continue
                c, wc = clusters[k]
                if abs(c - expected) <= additive_tol:
                    total = wa + wb + wc
                    if total > best_score:
                        best_score   = total
                        best_triplet = (a, wa, b, wb, c, wc)

    if best_triplet is not None:
        a, wa, b, wb, c, wc = best_triplet
        h_near, h_far, period = a, b, max(c, a * 2.11)
    elif n >= 3:
        top3 = sorted(clusters, key=lambda x: x[1], reverse=True)[:3]
        top3.sort(key=lambda x: x[0])
        h_near, h_far, period = top3[0][0], top3[1][0], top3[2][0]
    elif n == 2:
        h_near, h_far, period = clusters[0][0], clusters[1][0], clusters[0][0] + clusters[1][0]
    else:
        h_near, h_far, period = clusters[0][0], clusters[0][0] * 1.2 , clusters[0][0] * 2.2

    return {
        "neighbors_horizontal":     round(h_near),
        "far_neighbors_horizontal": round(h_far),
        "period_horizontal":        round(period),
    }

@njit(cache=True)
def get_vertical_distances_2(coords, intensities, v1_norm):
    sort_idx = np.argsort(coords[:, 0])
    sorted_coords = coords[sort_idx]
    sorted_weights = intensities[sort_idx]
    n = len(sorted_coords)
    dy_out = np.zeros(n, dtype=np.float32)
    weights_out = np.zeros(n, dtype=np.float32)
    count = 0
    min_dy = v1_norm * 3.5
    max_dy = v1_norm * 9.0
    max_dx = v1_norm * 3.5

    for i in range(n):
        y1, x1 = sorted_coords[i, 0], sorted_coords[i, 1]
        w1 = sorted_weights[i]
        for j in range(i + 1, n):
            dy = sorted_coords[j, 0] - y1
            if dy > max_dy: 
                break

            if dy >= min_dy:
                if abs(x1 - sorted_coords[j, 1]) <= max_dx:
                    dy_out[count] = dy
                    weights_out[count] = w1
                    count += 1
                    break
            
    return dy_out[:count], weights_out[:count]

def analyze_braille_spacing_2(concentrated_img, v1_norm):
    y_idx, x_idx = np.nonzero(concentrated_img)
    if len(y_idx) < 2: return [], np.zeros(0)
    coords = np.column_stack((y_idx, x_idx)).astype(np.float32)
    intensities = concentrated_img[y_idx, x_idx].astype(np.float32)
    dy_list, weights_list = get_vertical_distances_2(coords, intensities, v1_norm)

    def process_weighted(distances, weights):
        if len(distances) == 0: return [], np.zeros(0)
        dist_idx = np.round(distances).astype(np.int32)
        weighted_counts = np.bincount(dist_idx, weights=weights)
        top_indices = np.argsort(weighted_counts)[::-1]
        common_distances = [d for d in top_indices if d > 0 and weighted_counts[d] > 0]
        return common_distances, weighted_counts

    common_vals, weights_vals = process_weighted(dy_list, weights_list)
    return common_vals, weights_vals

def extract_braille_metrics_2(common_y, weights_y, v1_norm):
    dynamic_threshold = int(round(v1_norm / 4))
    def get_weighted_clusters(sorted_vals, weight_array, threshold, min_val):
        if len(sorted_vals) == 0: return []
        clusters = []
        used = np.zeros(len(weight_array), dtype=np.bool_)
        for val in sorted_vals:
            if used[val]: continue
            low, high = max(0, val - threshold), min(len(weight_array) - 1, val + threshold)
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

    clusters = get_weighted_clusters(common_y[:1], weights_y, threshold=dynamic_threshold, min_val=v1_norm * 3.5)
    if len(clusters) > 0:
        v_gap = clusters[0]
    else:
        print("Warning: Vertical inter-line distance NOT found. Setting to default: Dot_Diameter * 4.")
        v_gap = v1_norm * 4.0

    return { "neighbors_vertical": round(v_gap, 3) }

def extract_vertical_braille_metrics(vectors, v1_norm):
    cluster_thr  = v1_norm * 0.25
    additive_tol = v1_norm * 0.5
    min_dy       = v1_norm * 0.5
    clusters = []
    for dx, dy, score in vectors:
        ady = abs(dy)
        if ady < min_dy:
            continue

        vertical_purity = 1.0 / (1.0 + abs(dx) / v1_norm)
        effective_weight = score * vertical_purity
        for entry in clusters:
            if abs(ady - entry[0]) <= cluster_thr:
                new_w    = entry[1] + effective_weight
                entry[0] = (entry[0] * entry[1] + ady * effective_weight) / new_w
                entry[1] = new_w
                break
        else:
            clusters.append([float(ady), float(effective_weight)])

    for entry in clusters:
        entry[0] = round(entry[0])

    clusters.sort(key=lambda x: x[0])
    n = len(clusters)
    best_pair = None
    best_score = -1.0
    for i in range(n):
        for j in range(n):
            if i == j: continue

            a, wa = clusters[i]
            b, wb = clusters[j]
            if abs(b - 2 * a) <= additive_tol:
                total = wa + wb
                if total > best_score:
                    best_score = total
                    best_pair = (a, wa, b, wb)

    if best_pair is not None:
        v_near, v_double = best_pair[0], best_pair[2]
    elif n >= 2:
        print("\n  → No double-relation found — using top-2 weight fallback")
        top2 = sorted(clusters, key=lambda x: x[1], reverse=True)[:2]
        top2.sort(key=lambda x: x[0])
        v_near, v_double = top2[0][0], top2[1][0]
    elif n == 1:
        v_near = clusters[0][0]
        v_double = v_near * 2
    else:
        v_near = v1_norm * 2.5
        v_double = v_near * 2

    return {
        "v_distance_near": round(v_near),
        "v_distance_double": round(v_double)
    }


# ── Warmup ────────────────────────────────────────────────────────────────────
def warmup_numba():
    _img = np.zeros((20, 20), dtype=np.float32)
    _img[10, 10] = 600.0
    _img[10, 11] = 400.0
    _ = phase1_concentrate_centroid(_img, 5)
    _ = phase2_redistribute(_img.copy(), 200.0)
    _coords = np.array([[1.0, 1.0], [5.0, 5.0], [10.0, 10.0]], dtype=np.float32)
    _ints   = np.array([100.0, 150.0, 200.0], dtype=np.float32)
    _ = get_vertical_distances_2(_coords, _ints, 3)
    
warmup_numba()


# ── Model reference ───────────────────────────────────────────────────────────
from .model import model_3ch as _model_3ch, device as _device
cv2.setUseOptimized(True)


# ── Decode + translation functions ────────────────────────────────────────────

def get_braille_text_content_ultra_fast(img1, img2, img3, boxes, model, device, warped_rgb,
                                       nv_dist=15, h_period=30, line_gap=60):
    """
    Unified function: Pre-processing -> Inference -> Plotting -> Structural Assembly
    """
    if not boxes: return "", {}

    import numpy as _np
    import cv2 as _cv2
    import torch

    start_func = time.time()
    num_boxes = len(boxes)
    expansion_factor = 0.1 
   
    # 1. MODEL OPTIMIZATION
    model.eval()
    if not isinstance(model, torch.jit.ScriptModule) and not isinstance(model, torch.jit.RecursiveScriptModule):
        example_input = torch.randn(1, 3, 32, 32).to(device)
        traced_model = torch.jit.trace(model, example_input)
        fast_model = torch.jit.optimize_for_inference(traced_model)
    else:
        fast_model = model
   
    # 2. PARALLEL PRE-PROCESSING
    def process_box(box_data):
        idx, b = box_data
        x, y, w, h = int(b['x']), int(b['y']), int(b['w']), int(b['h'])
        r1, r2, r3 = img1[max(0,y):y+h, max(0,x):x+w], img2[max(0,y):y+h, max(0,x):x+w], img3[max(0,y):y+h, max(0,x):x+w]
        if r1.size == 0: return None
       
        H, W = r1.shape
        h_pts, w_pts = [0, H//3, (2*H)//3, H], [0, W//2, W]
        box_patches = _np.zeros((6, 3, 32, 32), dtype=_np.float32)
        
        p_idx = 0
        for col in range(2):
            for row in range(3):
                y_s, y_e, x_s, x_e = h_pts[row], h_pts[row+1], w_pts[col], w_pts[col+1]
                pad_h, pad_w = int((y_e-y_s) * expansion_factor), int((x_e-x_s) * expansion_factor)
                y_s_ext, y_e_ext = max(0, y_s - pad_h), min(H, y_e + pad_h)
                x_s_ext, x_e_ext = max(0, x_s - pad_w), min(W, x_e + pad_w)
                
                box_patches[p_idx, 0] = _cv2.resize(r1[y_s_ext:y_e_ext, x_s_ext:x_e_ext], (32, 32))
                box_patches[p_idx, 1] = _cv2.resize(r2[y_s_ext:y_e_ext, x_s_ext:x_e_ext], (32, 32))
                box_patches[p_idx, 2] = _cv2.resize(r3[y_s_ext:y_e_ext, x_s_ext:x_e_ext], (32, 32))
                p_idx += 1
        return idx, box_patches

    with ThreadPoolExecutor() as executor:
        results = list(executor.map(process_box, enumerate(boxes)))

    valid_results = [r for r in results if r is not None]
    if not valid_results: return "", {}
   
    indices, patches_data = zip(*valid_results)
    all_dots = _np.concatenate(patches_data, axis=0)

    # 3. BATCH INFERENCE
    with torch.inference_mode():
        input_tensor = torch.from_numpy(all_dots).to(device) / 255.0
        probs = fast_model(input_tensor).cpu().numpy().flatten()

    # 4. DECODING
    bits = (probs > 0.5).astype(_np.int32).reshape(-1, 6)
    weights = _np.array([1, 2, 4, 8, 16, 32], dtype=_np.int32)
    unicode_offsets = _np.dot(bits, weights)
   
    decoded_items = []
    for i, orig_idx in enumerate(indices):
        char = chr(0x2800 + unicode_offsets[i])
        # Include w and h for plotting
        decoded_items.append({
            'x': boxes[orig_idx]['x'], 
            'y': boxes[orig_idx]['y'], 
            'w': boxes[orig_idx]['w'], 
            'h': boxes[orig_idx]['h'], 
            'char': char
        })

    # # --- STEP E: PLOTTING (Inside the function) ---
    # ax.imshow(warped_rgb)
    # # Create rects from decoded_items which matches the indices of the inferred chars
    # rects = [patches.Rectangle((it['x'], it['y']), it['w'], it['h']) for it in decoded_items]
    # pc = PatchCollection(rects, match_original=False, edgecolor='white', facecolor='none', linewidths=1.0, alpha=0.5)
    # ax.add_collection(pc)
    
    # for it in decoded_items:
    #     if it['char'] == chr(0x2800): continue # Don't draw empty cells
    #     ax.text(it['x'] + it['w'] / 2, it['y'] + 1, it['char'],
    #             color='#FFFF00', fontsize=18, fontweight='bold', ha='center', va='top')
    # ax.set_title(f"3-Channel Inference: {num_boxes} Characters", fontsize=20)
    # ax.axis('off')

    # 5. UNIVERSAL STRUCTURAL ASSEMBLER (Curves, Flat, Tables, & Orphans)
    import numpy as _np
    from scipy.spatial import cKDTree

    # --- A. PREPARE STRUCTURAL METRICS ---
    nv = nv_dist
    h_per = h_period
    # Grid rhythm: The vertical distance between the 'Middle Lanes' of two lines
    # If line_gap isn't perfect, we use a standard 4.0 * nv fallback
    l_gap = line_gap if line_gap > nv * 2 else nv * 4.0

    # Align nodes to the 'Middle Lane' (Center of the cell)
    nodes = _np.array([[it['x'], it['y'] + (nv * 1.5)] for it in decoded_items])
    n_nodes = len(nodes)
    line_assignments = _np.full(n_nodes, -1, dtype=_np.int32)
    next_line_id = 0
    
    x_sorted_indices = _np.argsort(nodes[:, 0])
    tree = cKDTree(nodes)

    # --- B. PASS 1: ITERATIVE WAVE PROPAGATION ---
    for idx in x_sorted_indices:
        if line_assignments[idx] != -1: continue
            
        curr_line_id = next_line_id
        line_assignments[idx] = curr_line_id
        next_line_id += 1
        active_nodes = [idx]
        
        # Trend tracking: [dx, dy]
        local_trend = _np.array([h_per, 0.0]) 

        while active_nodes:
            new_active = []
            for a_idx in active_nodes:
                pos = nodes[a_idx]
                
                # Search Radius: Bridging up to 3 empty cells
                search_radius = h_per * 3.5 
                neighbors = tree.query_ball_point(pos, r=search_radius)
                
                for n_idx in neighbors:
                    if line_assignments[n_idx] != -1: continue
                    
                    delta = nodes[n_idx] - pos
                    dx, dy = delta[0], delta[1]
                    
                    # 1. Forward direction only (with small tolerance for vertical stacks)
                    if dx < h_per * 0.3: continue 
                    
                    # 2. LOCAL BELIEF (Curve Tracking)
                    # Predicted Y based on local slope
                    expected_dy = (dx / h_per) * local_trend[1]
                    # Score: How well does it fit the curve?
                    p_curve = _np.exp(-((dy - expected_dy)**2) / (2 * (nv * 1.0)**2))
                    
                    # 3. STRUCTURAL BELIEF (Lane Guardrail)
                    # Checks if the point is physically in the correct '3-lane track'
                    # even if the page is flat or slightly misaligned
                    mod_val = abs(dy) % l_gap
                    alignment_err = min(mod_val, l_gap - mod_val)
                    p_lane = _np.exp(-(alignment_err**2) / (2 * (nv * 0.6)**2))

                    # 4. FINAL VOTE
                    # High probability if it follows the curve OR fits the global grid rhythm
                    # This dual check makes it 'Universal'
                    if (p_curve * p_lane) > 0.25:
                        line_assignments[n_idx] = curr_line_id
                        new_active.append(n_idx)
                        # Adaptive trend update
                        local_trend[1] = 0.8 * local_trend[1] + 0.2 * delta[1]
            active_nodes = new_active

    # --- C. PASS 2: GLOBAL ANCHOR MERGING (Universal Fixer) ---
    # This pass handles orphans and bridge gaps in tables or headers
    clusters = {}
    for i, l_id in enumerate(line_assignments):
        if l_id not in clusters: clusters[l_id] = []
        clusters[l_id].append(i)

    merged_ids = line_assignments.copy()
    u_ids = sorted(clusters.keys(), key=lambda lid: _np.min(nodes[clusters[lid], 0]))

    for i in range(len(u_ids)):
        id1 = u_ids[i]
        if not clusters[id1]: continue
        
        # Line 1 context (End)
        idx1_sorted = sorted(clusters[id1], key=lambda x: nodes[x, 0])
        pts1 = nodes[idx1_sorted]
        end1 = pts1[-1]
        slope1 = (pts1[-1][1] - pts1[-min(3, len(pts1))][1]) / max(1, pts1[-1][0] - pts1[-min(3, len(pts1))][0]) if len(pts1) >= 2 else 0

        for j in range(len(u_ids)):
            id2 = u_ids[j]
            if id1 == id2 or not clusters[id2]: continue
            
            pts2 = nodes[clusters[id2]]
            start2 = pts2[_np.argmin(pts2[:, 0])]
            
            dx = start2[0] - end1[0]
            if dx <= 0: continue # Must be to the right
            
            # Universal Bridge Rule:
            # Bridging across tables or gaps: Trajectory projection + Lane check
            projected_y = end1[1] + (dx * slope1)
            dy_err = abs(start2[1] - projected_y)
            
            # Use dynamic thresholds: Orphans (len<=2) get much wider adoption rules
            is_orphan = (len(pts1) <= 2 or len(pts2) <= 2)
            v_tol = nv * 1.5 if is_orphan else nv * 0.8
            h_tol = h_per * 25.0 if is_orphan else h_per * 6.0

            if dx < h_tol and dy_err < v_tol:
                # One last grid check to prevent merging Line 1 with Line 2
                grid_mod = abs(start2[1] - end1[1]) % l_gap
                if min(grid_mod, l_gap - grid_mod) < nv * 1.2:
                    for idx_to_move in clusters[id2]:
                        merged_ids[idx_to_move] = id1
                    clusters[id1].extend(clusters[id2])
                    clusters[id2] = []

    # --- D. FINAL CLUSTER ASSEMBLY ---
    final_clusters = {}
    for i, l_id in enumerate(merged_ids):
        if l_id not in final_clusters: final_clusters[l_id] = []
        final_clusters[l_id].append(decoded_items[i])
    
    final_clusters = {k: v for k, v in final_clusters.items() if len(v) > 0}
    
    # Final sort: Standard Top-to-Bottom reading order based on average height
    sorted_ids = sorted(final_clusters.keys(), 
                        key=lambda k: sum(it['y'] for it in final_clusters[k])/len(final_clusters[k]))
    
    final_lines = []
    prev_y = None

    for l_id in sorted_ids:
        # Standard Left-to-Right order for characters within the line
        cluster = sorted(final_clusters[l_id], key=lambda it: it['x'])
        avg_y = sum(it['y'] for it in cluster) / len(cluster)
        
        line_str = "".join([it['char'] for it in cluster])
        if not line_str.strip(' \t\n\r\u2800'):  # Only keep lines with actual dots
            continue
            
        if prev_y is not None:
            y_diff = avg_y - prev_y
            num_newlines = int(round(y_diff / l_gap))
            if num_newlines > 1:
                final_lines.extend([""] * (num_newlines - 1))
                
        final_lines.append(line_str.rstrip('\u2800'))  # Remove trailing empty cells for cleaner output
        prev_y = avg_y

    return "\n".join(final_lines), final_clusters




# CELL 2 — MULTI-LANGUAGE BRAILLE TRANSLATION DICTIONARIES

# ── SHARED HELPERS ────────────────────────────────────────────────────────────
CAPITAL_INDICATOR = '⠠'
NUMBER_INDICATOR  = '⠼'

# ─────────────────────────────────────────────────────────────────────────────
# 1. ARABIC
# ─────────────────────────────────────────────────────────────────────────────


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
        if len(img_input.shape) == 3:
            gray = cv2.cvtColor(img_input, cv2.COLOR_BGR2GRAY)
        else:
            gray = img_input.copy()

        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(12, 16))
        clahe_img = clahe.apply(gray)
        preprocessed = cv2.bilateralFilter(clahe_img, d=9, sigmaColor=15, sigmaSpace=15)
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
        v1_norm = np.linalg.norm(v1)
        Dot_Diameter = int(round(v1_norm * 1.5))
        v1_norm = int(round(v1_norm))
        t_size = Dot_Diameter * 2
        cleaned1_total, cleaned2_total = process_image_in_tiles_4pass(gray, t_size, 0)
        with ThreadPoolExecutor(max_workers=2) as ex:
            f_blanc = ex.submit(process_directional_wb, cleaned1_total, Dot_Diameter)
            f_noir  = ex.submit(process_directional_wb, cleaned2_total, Dot_Diameter)
            WB_disp_BLANC = f_blanc.result()
            WB_disp_NOIR  = f_noir.result()
        BLANC_VARIATIONS = cv2.addWeighted(cleaned1_total, 1/2, WB_disp_BLANC, 1/2, 0)
        NOIR_VARIATIONS = cv2.addWeighted(cleaned2_total, 1/2, WB_disp_NOIR, 1/2, 0)
        noise = np.minimum(BLANC_VARIATIONS , NOIR_VARIATIONS)
        cleaned1_total = cv2.subtract(BLANC_VARIATIONS, noise)
        cleaned2_total = cv2.subtract(NOIR_VARIATIONS, noise)
        reconstruction = np.clip(cv2.addWeighted(cv2.add(128, cleaned1_total), 1/2, 255 - cv2.add(128, cleaned2_total), 1/2, 0), 0, 255).astype(np.uint8)
        cleaned1 = cleaned1_total
        cleaned2 = cleaned2_total
        h, w = cleaned1.shape
        v1_first, v2_first = find_best_translations_optimized(cleaned2, cleaned1, search_range=Dot_Diameter, find_second_peak=True, use_gaussian=False)
        angle1 = get_angle_with_v(v1_first, V)
        angle2 = get_angle_with_v(v2_first, V)
        if angle1 > angle2:
            v1_first, v2_first = v2_first, v1_first

        v1_noir = tuple(-x for x in v1_first)
        v2_noir = tuple(-x for x in v2_first)
        mod_v1 = np.linalg.norm(v1)
        v1_norm_f = mod_v1
        Dot_Diameter = int(round(v1_norm * 1.5))
        v1_norm = int(round(v1_norm_f))
        recto_blanc, verso_blanc = build_probabilistic_layers(cleaned1, cleaned2, v1_first, v2_first)
        recto_noir, verso_noir = build_probabilistic_layers(cleaned2, cleaned1, v1_noir, v2_noir)
        reconstruction_recto = np.clip(cv2.addWeighted(cv2.add(128, recto_blanc), 1/2, 255 - cv2.add(128, recto_noir), 1/2, 0), 0, 255).astype(np.uint8)
        reconstruction_verso = np.clip(cv2.addWeighted(cv2.add(128, verso_blanc), 1/2, 255 - cv2.add(128, verso_noir), 1/2, 0), 0, 255).astype(np.uint8)
        sure_RB, uRB, sure_VB, uVB = separate_by_probability(recto_blanc, verso_blanc, threshold=0.8)
        sure_RN, uRN, sure_VN, uVN = separate_by_probability(recto_noir, verso_noir, threshold=0.8)
        current_rb, current_rn = recto_blanc.copy(), recto_noir.copy()
        current_vb, current_vn = verso_blanc.copy(), verso_noir.copy()
        k_size = Dot_Diameter * 4
        for thresh in [0.5, 0.8]:
            sRB, uRB, sVB, uVB = separate_by_probability(current_rb, current_vb, threshold=thresh)
            sRN, uRN, sVN, uVN = separate_by_probability(current_rn, current_vn, threshold=thresh)
            unsure_combined_blanc = uRB + uVB
            unsure_combined_noir  = uRN + uVN
            with ThreadPoolExecutor(max_workers=2) as ex:
                f_blanc = ex.submit(
                    split_noise_with_plus_kernel,
                    (sure_RB.astype(np.float32) + sure_RN.astype(np.float32)),
                    (sure_VB.astype(np.float32) + sure_VN.astype(np.float32)),
                    unsure_combined_blanc, k_size, v1_first
                )
                f_noir = ex.submit(
                    split_noise_with_plus_kernel,
                    (sure_RN.astype(np.float32) + sure_RB.astype(np.float32)),
                    (sure_VN.astype(np.float32) + sure_VB.astype(np.float32)),
                    unsure_combined_noir, k_size, v1_first
                )
                refined_uRB, refined_uVB = f_blanc.result()
                refined_uRN, refined_uVN = f_noir.result()

            current_rb = np.clip(sRB + refined_uRB, 0, 255).astype(np.uint8)
            current_vb = np.clip(sVB + refined_uVB, 0, 255).astype(np.uint8)
            current_rn = np.clip(sRN + refined_uRN, 0, 255).astype(np.uint8)
            current_vn = np.clip(sVN + refined_uVN, 0, 255).astype(np.uint8)

        recto_blanc, recto_noir, verso_blanc, verso_noir = merge_with_full_kernel_4layers(current_rb, current_rn, current_vb, current_vn, k = v1_norm, p=2)
        dx = v1_first[0] / 3
        dy = v1_first[1] / 3
        recto_noir_shifted  = translate_image(recto_noir, ( dx,  dy))
        recto_blanc_shifted = translate_image(recto_blanc, (-dx, -dy))
        dx = v2_first[0] / 3
        dy = v2_first[1] / 3
        verso_noir_shifted  = translate_image(verso_noir, ( dx,  dy))
        verso_blanc_shifted = translate_image(verso_blanc, (-dx, -dy))
        recto = cv2.add(recto_blanc_shifted, recto_noir_shifted).astype(np.uint8)
        verso = cv2.add(verso_blanc_shifted, verso_noir_shifted).astype(np.uint8)
        recto_4 = cv2.bilateralFilter(recto, d = v1_norm * 2, sigmaColor=15, sigmaSpace=v1_norm)
        recto_4 = cv2.medianBlur(recto_4, v1_norm + v1_norm % 2 + 1)
        kernel  = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (v1_norm//3, v1_norm//3))
        recto_4 = cv2.morphologyEx(recto_4, cv2.MORPH_OPEN, kernel)
        median_value = get_image_median(recto_4)
        recto_4 = cv2.subtract(recto_4, float(median_value + 1))
        recto_4 = restore_intensity(recto, recto_4, expand = v1_norm)
        gamma = 1.2  # try 1.2–2.0
        lut = np.array([((i / 255.0) ** gamma) * 255 for i in range(256)], dtype=np.uint8)
        recto_4 = cv2.LUT(recto_4, lut)
        recto_2 = recto_4
        median_1 = median_top_1_percent(recto_2, per= 99)
        recto_concentrated_before_treshold = filter_dots_by_mass(recto_2, ratio=1)
        recto_concentrated_before_treshold = filter_dots_by_mass_top_1(recto_concentrated_before_treshold, median_1, ratio = 0.2)
        recto_concentrated_before_treshold = restore_intensity(recto_concentrated_before_treshold, recto_2, expand = v1_norm)
        recto_concentrated_before_treshold = concentrate_single_image(recto_concentrated_before_treshold, window_size= v1_norm)
        recto_concentrated_before_treshold, concentrated = apply_centroid_concentration_2(recto_concentrated_before_treshold, Dot_Diameter, median_1, Dot_Diameter)
        recto_concentrated = np.where(recto_concentrated_before_treshold == median_1, 255, 0).astype(np.uint8)
        recto_concentrated = remove_small_dots_binary(recto_concentrated, min_area=v1_norm/4)
        search_min_h = int(Dot_Diameter)
        search_min_w = int(Dot_Diameter)
        search_max_h = int(v1_norm * 7) 
        search_max_w = int(Dot_Diameter)
        top_vectors = find_top_k_self_translations(
            recto_concentrated,
            min_h=search_min_h,
            min_w=search_min_w,
            max_h=search_max_h,
            max_w=search_max_w,
            k=50,
        )
        metrics_v = extract_vertical_braille_metrics(top_vectors, v1_norm)
        v_near = int(metrics_v['v_distance_near'])
        search_max_h = int(v1_norm)
        search_max_w = int(v_near * 3)
        top_vectors = find_top_k_self_translations(
            recto_concentrated,
            min_h=search_min_h,
            min_w=search_min_w,
            max_h=search_max_h,
            max_w=search_max_w,
            k=50,
        )
        metrics = extract_braille_metrics_from_vectors(top_vectors, v1_norm)
        neighbors_horizontal     = int(round(metrics['neighbors_horizontal']))
        far_neighbors_horizontal = int(round(metrics['far_neighbors_horizontal']))
        period                   = int(round(metrics['period_horizontal']))
        neighbors_vertical       = neighbors_horizontal
        all_h_offsets = [
            neighbors_horizontal, -neighbors_horizontal, 
            far_neighbors_horizontal, -far_neighbors_horizontal, 
            period, -period
        ]
        all_h_offsets_close = [
            neighbors_horizontal, -neighbors_horizontal, 
            far_neighbors_horizontal, -far_neighbors_horizontal
        ]
        recto_completed = complete_braille_grid_logic_merged(
            recto_concentrated,
            all_h_offsets,
            v_distances=[neighbors_vertical, 2 * neighbors_vertical]
        )
        recto_completed = complete_braille_diagonal_logic_merged(
            recto_completed, all_h_offsets_close,
            [neighbors_vertical, 2 * neighbors_vertical]
        )
        recto_completed, _ = filter_vertical_anomalies_center_only(
            recto_completed, 
            nv=neighbors_vertical, 
            r_size=Dot_Diameter 
        )
        recto_completed = complete_by_grid_density(
            recto_completed, 
            period=period,
            N= 2,
            threshold=3
        )
        recto_completed = concentrate_single_image(recto_completed, window_size= v1_norm)
        k_value = 2
        concentrated_recto, contour_data = concentrate_contours_second_slow(recto_completed, k=k_value)
        concentrated_recto = concentrated_recto.astype(np.float32)
        t_img, m_img, d_img, still_unsure_img = propagate_unsure_beliefs(
            concentrated_recto.astype(np.float64),
            nv=neighbors_vertical,
            hw_x= period * 2.1,
            hw_y= neighbors_vertical * 2.2,
            neighbors_vertical_mid_p=neighbors_vertical * 4,
            iterations=20,
            confidence_threshold=0.5
        )
        img_up1 = np.zeros_like(m_img)
        img_up1[:-neighbors_vertical] = m_img[neighbors_vertical:]
        img_up2 = np.zeros_like(t_img)
        img_up2[:-2*neighbors_vertical] = t_img[2*neighbors_vertical:]
        concentrated_mid_f = img_up1 + img_up2 + d_img
        common_y, weights_y = analyze_braille_spacing_2(concentrated_mid_f, neighbors_vertical)
        metrics = extract_braille_metrics_2(common_y, weights_y, neighbors_vertical)
        neighbors_vertical_mid_p = int(round(metrics['neighbors_vertical']))
        with ThreadPoolExecutor(max_workers=2) as ex:
            f_vertical = ex.submit(
                propagate_unsure_beliefs,
                concentrated_recto.astype(np.float64),
                neighbors_vertical, period * 2.1, neighbors_vertical_mid_p * 2.1,
                neighbors_vertical_mid_p, 150, 0.6
            )
            f_lr = ex.submit(
                propagate_lr_beliefs,
                concentrated_recto.astype(np.float64),
                neighbors_horizontal, far_neighbors_horizontal, period,
                period * 2.1, neighbors_vertical_mid_p * 2.1, 100, 0.6
            )
            t_img, m_img, d_img, still_unsure_img = f_vertical.result()
            l_img, r_img, still_unsure_lr = f_lr.result()

        with ThreadPoolExecutor(max_workers=2) as ex:
            f_vert1 = ex.submit(
                apply_vertical_refinement,
                still_unsure_img, t_img, m_img, d_img,
                neighbors_vertical, neighbors_vertical_mid_p,
                1.2 * period, 5 * neighbors_vertical_mid_p
            )
            f_horiz1 = ex.submit(
                apply_horizontal_refinement,
                still_unsure_lr, l_img, r_img,
                period, 1.2 * period, 5 * neighbors_vertical_mid_p
            )
            top_final, mid_final, down_final, unsure_final       = f_vert1.result()
            left_final, right_final, unsure_lr_final          = f_horiz1.result()

        all_dec = apply_centroid_concentration_batch(
            [top_final, mid_final, down_final, unsure_final, left_final, right_final, unsure_lr_final],
            v1_norm, 255, Dot_Diameter
        )
        top_final_deconcentrated, mid_final_deconcentrated, \
        down_final_deconcentrated, unsure_final_deconcentrated = all_dec[:4]
        left_final_deconcentrated, right_final_deconcentrated, \
        unsure_lr_final_deconcentrated = all_dec[4:]
        fd1, fd2, fd3, fd4, fd5, fd6 = redistribute(left_final_deconcentrated, right_final_deconcentrated, top_final_deconcentrated, mid_final_deconcentrated, down_final_deconcentrated)
        all_accounted = cv2.add(cv2.add(cv2.add(fd1, fd2), cv2.add(fd3, fd4)), cv2.add(fd5, fd6))
        all_accounted_mask = (all_accounted > 0).astype(np.uint8) * 255
        recto_mask = recto_concentrated == 255
        pos1_new = fd1 * recto_mask
        pos2_new = fd2 * recto_mask
        pos3_new = fd3 * recto_mask
        pos4_new = fd4 * recto_mask
        pos5_new = fd5 * recto_mask
        pos6_new = fd6 * recto_mask
        aligned1 = get_shifted (pos1_new, 0, -2 * neighbors_vertical)
        aligned2 = get_shifted (pos2_new, 0, -neighbors_vertical)
        aligned3 = pos3_new
        aligned4 = get_shifted (pos4_new, -neighbors_horizontal, -2 * neighbors_vertical)
        aligned5 = get_shifted (pos5_new, -neighbors_horizontal, -neighbors_vertical)
        aligned6 = get_shifted (pos6_new, -neighbors_horizontal, 0)
        sum_aligned = aligned1 + aligned2 + aligned3 + aligned4 + aligned5 + aligned6
        sum_aligned = enhance_score_map_by_voting(
            sum_aligned, 
            period=period, 
            nv=neighbors_vertical, 
            threshold=2
        )
        fd_list = [fd1, fd2, fd3, fd4, fd5, fd6]
        fd_list_or = [pos1_new, pos2_new, pos3_new, pos4_new, pos5_new, pos6_new]
        with ThreadPoolExecutor(max_workers=2) as ex:
            f1 = ex.submit(find_and_score_structural_boxes_fast,
                           fd_list, neighbors_horizontal, neighbors_vertical, 4)
            f2 = ex.submit(find_and_score_structural_boxes_fast,
                           fd_list_or, neighbors_horizontal, neighbors_vertical, 2)
            _, score_map_new      = f1.result()
            _, score_map_original = f2.result()
    
        score_map = np.maximum(score_map_new, score_map_original)
        final_boxes, combined_score_map = rescue_and_concentrate_boxes_dual(
            neighbors_horizontal, 
            neighbors_vertical, 
            period,
            neighbors_vertical_mid_p,
            Dot_Diameter, 
            score_map,
            sum_aligned,
            Nx=5,
            Ny=10
        )
        recto = np.maximum(recto_blanc, recto_noir).astype(np.uint8)
        verso = np.maximum(verso_blanc, verso_noir).astype(np.uint8)

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

        # ── Translate (dictionary only — Gemini is handled by the stream endpoint) ──
        from .translator import translate_only
        translated = translate_only(braille_text, language=language)
        return braille_text, translated
