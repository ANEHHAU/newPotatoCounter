from ..domain.potato_track import PotatoTrack, TrackState, PotatoClass
from ..utils.geometry_utils import is_point_in_polygon
from typing import List, Optional

class PotatoStateMachine:
    """Manages the lifecycle of individual PotatoTrack objects through defined zones."""
    def __init__(self, roi_polygon: List[List[int]], define_zone_polygon: List[List[int]], operating_mode: int):
        self.roi = roi_polygon
        self.define_zone = define_zone_polygon
        self.operating_mode = operating_mode

    def update_track(self, track: PotatoTrack):
        """Transition the track to its next state based on current geometry and history."""
        if track.state == TrackState.EXPIRED or track.state == TrackState.LOST:
            return

        center = track.history[-1]
        
        # 1. NEW -> TRACKING
        if track.state == TrackState.NEW:
            track.state = TrackState.TRACKING

        # 2. Check ROI (Filter if needed, but tracks are usually in ROI if detected there)
        in_roi = is_point_in_polygon(center, self.roi) if self.roi else True
        if in_roi and track.state == TrackState.TRACKING:
            track.state = TrackState.IN_ROI

        # 3. Handle Define Zone (for gathering classification info)
        in_define_zone = is_point_in_polygon(center, self.define_zone) if self.define_zone else False
        
        if in_define_zone:
            # While in define zone, keep accumulating detections
            track.state = TrackState.DEFINING
            if hasattr(track, 'latest_detection'):
                track.collected_predictions.append({
                    'class': track.latest_detection['class'],
                    'conf': track.latest_detection['conf']
                })
        else:
            # If was in define zone and now left it -> finalize classification
            if track.state == TrackState.DEFINING:
                track.finalize_decision(self.operating_mode)
                track.state = TrackState.FINALIZED
            elif track.state == TrackState.IN_ROI:
                # Still in ROI but not in Define Zone
                pass

        # Finalizer for tracks that skipped define zone but crossed line? 
        # Usually they MUST pass through it.
