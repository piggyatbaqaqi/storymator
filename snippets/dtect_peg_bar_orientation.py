# From Google Search AI.
import cv2
import numpy as np
import math

def detect_peg_bar_orientation(image_path):
    # 1. Load image and preprocess
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Threshold to get binary image (adjust if background is dark/light)
    _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    
    # 2. Find contours
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    peg_centers = []
    
    for cnt in contours:
        # Filter out tiny noise and massive backgrounds
        area = cv2.contourArea(cnt)
        if 100 < area < 50000: 
            # Get center of the contour
            M = cv2.moments(cnt)
            if M["m00"] != 0:
                cX = int(M["m10"] / M["m00"])
                cY = int(M["m01"] / M["m00"])
                peg_centers.append((cX, cY))
    
    # We need at least the 2 outer pegs to find the line
    if len(peg_centers) < 2:
        print("Could not find enough peg markers.")
        return None

    # Sort peg centers by X coordinate to easily find the leftmost and rightmost pegs
    peg_centers = sorted(peg_centers, key=lambda p: p[0])
    
    # Use the leftmost and rightmost detected pegs to calculate the baseline
    p1 = peg_centers[0]
    p2 = peg_centers[-1]
    
    # 3. Calculate rotation angle
    delta_x = p2[0] - p1[0]
    delta_y = p2[1] - p1[1]
    
    angle_rad = math.atan2(delta_y, delta_x)
    angle_deg = math.degrees(angle_rad)
    
    # Draw logic for visualization
    cv2.line(img, p1, p2, (0, 0, 255), 3)
    for center in peg_centers:
        cv2.circle(img, center, 7, (0, 255, 0), -1)
        
    print(f"Detected Peg Bar Rotation Angle: {angle_deg:.2f} degrees")
    
    return angle_deg, img

# Example usage:
# angle, processed_img = detect_peg_bar_orientation('peg_bar.jpg')
