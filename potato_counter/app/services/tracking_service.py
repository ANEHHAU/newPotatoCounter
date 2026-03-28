from typing import List, Dict, Tuple
from ..domain.potato_track import PotatoTrack, TrackState
from ..utils.geometry_utils import is_point_in_polygon
import numpy as np

class TrackingService:
    """Service to track potato objects between frames."""
    def __init__(self, iou_threshold: float = 0.3):
        self.iou_threshold = iou_threshold
        self.active_tracks: Dict[int, PotatoTrack] = {}
        self.next_track_id = 1
        self.max_lost_frames = 30 # For expiring tracks

    def update(self, detections: List[Dict], roi_polygon: List[List[int]]) -> List[PotatoTrack]:
        """Match detections with existing tracks (simple centroid/IOU matching for now)."""
        # In mock mode, the mock service might provide its own IDs or we assign them here.
        # Here we'll maintain our own PotatoTrack instances.
        
        # 1. Update positions for tracks based on detections (simple matching)
        matched_detect_indices = set()
        track_ids_to_remove = []

        # (Simplified distance matching since mock and real ByteTrack will handle this better)
        # Using centroids for matching.
        for track_id, track in self.active_tracks.items():
            best_match_idx = -1
            best_dist = 100 # Max pixels to match
            
            track_center = [track.bbox[0] + track.bbox[2]/2, track.bbox[1] + track.bbox[3]/2]
            
            for i, det in enumerate(detections):
                if i in matched_detect_indices:
                    continue
                det_center = [det['bbox'][0] + det['bbox'][2]/2, det['bbox'][1] + det['bbox'][3]/2]
                dist = np.linalg.norm(np.array(track_center) - np.array(det_center))
                
                if dist < best_dist:
                    best_match_idx = i
                    best_dist = dist
            
            if best_match_idx != -1:
                det = detections[best_match_idx]
                track.bbox = det['bbox']
                track.add_history((det['bbox'][0] + det['bbox'][2]/2, det['bbox'][1] + det['bbox'][3]/2))
                track.last_update = 0 # reset lost count or timestamp
                # Store prediction for class voting if in appropriate state later
                track.latest_detection = det
                matched_detect_indices.add(best_match_idx)
            else:
                track.last_update += 1 # Frame count since lost
                if track.last_update > self.max_lost_frames:
                    track_ids_to_remove.append(track_id)
        
        # 2. Add new detections as new tracks
        for i, det in enumerate(detections):
            if i not in matched_detect_indices:
                center = (det['bbox'][0] + det['bbox'][2]/2, det['bbox'][1] + det['bbox'][3]/2)
                new_track = PotatoTrack(
                    track_id=self.next_track_id,
                    bbox=det['bbox']
                )
                new_track.add_history(center)
                new_track.latest_detection = det
                self.active_tracks[self.next_track_id] = new_track
                self.next_track_id += 1

        # 3. Handle ROI Filter
        for track in self.active_tracks.values():
            center = (track.bbox[0] + track.bbox[2]/2, track.bbox[1] + track.bbox[3]/2)
            if roi_polygon and not is_point_in_polygon(center, roi_polygon):
                # Optionally mark as OUT_OF_ROI or just tracker continues.
                # Usually we only process if in ROI.
                pass
            
        # 4. Remove lost tracks
        for tid in track_ids_to_remove:
            del self.active_tracks[tid]

        return list(self.active_tracks.values())

    def clear(self):
        """Clears all tracks (e.g. on seek)."""
        self.active_tracks.clear()
        self.next_track_id = 1
