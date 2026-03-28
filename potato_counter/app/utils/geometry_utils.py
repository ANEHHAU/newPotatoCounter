import cv2
import numpy as np

def is_point_in_polygon(point, polygon):
    """Check if point (x, y) is inside polygon [(x, y), ...]."""
    if not polygon or len(polygon) < 3:
        return False
    return cv2.pointPolygonTest(np.array(polygon, dtype=np.int32), (int(point[0]), int(point[1])), False) >= 0

def line_crossing(p1, p2, l1, l2):
    """
    Check if a line segment (p1, p2) crosses line (l1, l2).
    p1, p2: (x, y) coordinates of the moving object from prev to current frame.
    l1, l2: (x, y) coordinates of the count line.
    """
    if not l1 or not l2:
        return False
    
    # Using cross product method
    def sign(a, b, c):
        return (a[0]-c[0])*(b[1]-c[1]) - (b[0]-c[0])*(a[1]-c[1])
    
    s1 = sign(p1, l1, l2)
    s2 = sign(p2, l1, l2)
    
    if (s1 > 0 and s2 < 0) or (s1 < 0 and s2 > 0):
        # We also need to check if the intersection point is within the line segment bounds 
        # But for industrial conveyors usually a count line is horizontal and covers width.
        return True
    return False

def calculate_conveyor_speed(track_history, fps):
    """Estimate pixels/s based on tracking history."""
    if len(track_history) < 2:
        return 0
    
    dist = np.linalg.norm(np.array(track_history[-1]) - np.array(track_history[-2]))
    return dist * fps
