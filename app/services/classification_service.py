from ..domain.quality_decision import finalize_track
from ..domain.potato_track import PotatoState
from ..utils.logger import ls

class ClassificationService:
    """
    Temporal voting stabilizer for classification.
    """
    def __init__(self, mode="good_defect", min_frames=3, unknown_gap=0.08):
        self.mode = mode
        self.min_frames = min_frames
        self.unknown_gap = unknown_gap
        
    def set_config(self, mode=None, min_frames=None, unknown_gap=None):
        if mode: self.mode = mode
        if min_frames: self.min_frames = min_frames
        if unknown_gap: self.unknown_gap = unknown_gap

    def process_tracks(self, tracks):
        """
        Processes list of PotatoTracks for classification finalization.
        """
        finalized_this_frame = []
        for track in tracks:
            # Only finalize if it JUST transitioned from IN_DEFINE_ZONE to FINALIZING
            if track.state == PotatoState.FINALIZING:
                finalize_track(track, self.mode, self.min_frames, self.unknown_gap)
                finalized_this_frame.append(track)
                
        return finalized_this_frame
