"""BACKEND menu "Segmentation": Otsu, Adaptive Thresholding, K-Means Clustering.
Menggunakan OpenCV (threshold, adaptiveThreshold, kmeans)."""

import numpy as np
import cv2
from app.backend import register


@register("segmentation.otsu_thresholding")
def otsu_thresholding(img):
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return thresh > 0


@register("segmentation.adaptive_thresholding")
def adaptive_thresholding(img, block=11, c=2, method="Gaussian"):
    block = int(block)
    if block % 2 == 0:
        block += 1
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    method_cv = (cv2.ADAPTIVE_THRESH_GAUSSIAN_C if method == "Gaussian"
                 else cv2.ADAPTIVE_THRESH_MEAN_C)
    # cv2.adaptiveThreshold: dst = maxValue jika src > (mean - C), else 0
    thresh = cv2.adaptiveThreshold(
        gray, 255, method_cv, cv2.THRESH_BINARY, block, float(c)
    )
    return thresh > 0


@register("segmentation.k_means_clustering")
def k_means_clustering(img, k=4):
    """K-Means pada warna piksel (R,G,B) via cv2.kmeans dengan inisialisasi k-means++."""
    k = int(k)
    h, w = img.shape[:2]
    pixels = img.reshape(-1, 3).astype(np.float32)
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.5)
    _, labels, centers = cv2.kmeans(
        pixels, k, None, criteria, attempts=1, flags=cv2.KMEANS_PP_CENTERS
    )
    centers = centers.astype(np.uint8)
    return centers[labels.flatten()].reshape(h, w, 3)