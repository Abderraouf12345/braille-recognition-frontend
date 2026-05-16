import cv2
import numpy as np
from core.processor import BrailleProcessor

processor = BrailleProcessor()

# create a dummy image (1000x1000)
img = np.zeros((1000, 1000, 3), dtype=np.uint8)

# fake corners
pts_src = np.float32([
    [0, 0],
    [1000, 0],
    [1000, 1000],
    [0, 1000]
])

# fake light
V = np.array([1.0, 0.0], dtype=np.float32)

try:
    processor.process(img, pts_src, V)
except Exception as e:
    import traceback
    traceback.print_exc()
