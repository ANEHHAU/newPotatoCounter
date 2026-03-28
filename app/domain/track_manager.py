from .potato_track import PotatoTrack, PotatoState
from ..utils.logger import ls

class TrackManager:
    """
    Manages all active tracks, ensuring lifecycle transitions and memory cleanup.
    """
    def __init__(self, max_lost_frames=30):
        self.active_tracks = {}  # {track_id: PotatoTrack}
        self.max_lost_frames = max_lost_frames
        self.lost_frames_counter = {} # {track_id: int}
        
    def update_tracks(self, current_ids, detections_by_id):
        """
        Input: 
            current_ids: List[int] of current tracked IDs from ByteTrack
            detections_by_id: Dict mapping id to {bbox, class_id, conf}
        Output:
            List of tracks that were just updated.
        """
        updated_tracks = []
        
        # 1. Update tracks that were found in this frame
        for tid in current_ids:
            if tid not in self.active_tracks:
                self.active_tracks[tid] = PotatoTrack(tid)
                ls.info(f"New track created: {tid}")
                
            track = self.active_tracks[tid]
            self.lost_frames_counter[tid] = 0
            
            # Update data from detections
            det = detections_by_id.get(tid)
            if det:
                track.bbox_history.append(det['bbox'])
                track.add_prediction(det['class_id'], det['conf'])
                
            updated_tracks.append(track)
            
        # 2. Update lost frames for tracks that were NOT found
        dead_tracks = []
        for tid in list(self.active_tracks.keys()):
            if tid not in current_ids:
                self.lost_frames_counter[tid] += 1
                if self.lost_frames_counter[tid] > self.max_lost_frames:
                    self.active_tracks[tid].state = PotatoState.EXPIRED
                    dead_tracks.append(tid)
                    ls.info(f"Track expired: {tid}")
                    
        # 3. Clean up expired tracks
        for tid in dead_tracks:
            del self.active_tracks[tid]
            del self.lost_frames_counter[tid]
            
        return updated_tracks
    
    def get_track(self, track_id):
        return self.active_tracks.get(track_id)
    
    def reset(self):
        """
        Clears all internal state for seeking.
        """
        self.active_tracks.clear()
        self.lost_frames_counter.clear()
        ls.info("Track manager reset (seek occurred)")

    def get_all_active(self):
        return list(self.active_tracks.values())
