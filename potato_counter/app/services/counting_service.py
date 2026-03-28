from dataclasses import dataclass, field
from typing import Dict, List, Optional
from ..domain.potato_track import PotatoTrack, PotatoClass, TrackState
from ..utils.geometry_utils import line_crossing

@dataclass
class CountingStats:
    total: int = 0
    good: int = 0
    defective: int = 0
    breakdown: Dict[str, int] = field(default_factory=lambda: {
        "DAMAGED": 0, "DISEASED": 0, "SPROUTED": 0, "DEFORMED": 0
    })

class CountingService:
    """Service to count potatoes as they cross the line."""
    def __init__(self):
        self.stats = CountingStats()
        self.counted_ids = set() # Track already counted IDs

    def update(self, tracks: List[PotatoTrack], count_line: Optional[List[List[int]]]):
        """Check for line crossing and update stats."""
        if not count_line or len(count_line) < 2:
            return
            
        line_p1 = count_line[0]
        line_p2 = count_line[1]
        
        for track in tracks:
            if track.track_id in self.counted_ids:
                continue
            
            if len(track.history) < 2:
                continue

            prev_pos = track.history[-2]
            curr_pos = track.history[-1]
            
            if line_crossing(prev_pos, curr_pos, line_p1, line_p2):
                # We also need the track to be finalized (classed) before counting? 
                # Prompt says: "COUNTED... after FINALIZED".
                # But let's assume if it crossed and was finalized, we count it.
                if track.quality.is_final:
                    self._increment_stats(track.quality.class_name)
                    self.counted_ids.add(track.track_id)
                    track.state = TrackState.COUNTED

    def _increment_stats(self, p_class: PotatoClass):
        self.stats.total += 1
        if p_class == PotatoClass.GOOD:
            self.stats.good += 1
        else:
            self.stats.defective += 1
            if p_class.name in self.stats.breakdown:
                self.stats.breakdown[p_class.name] += 1

    def reset(self):
        self.stats = CountingStats()
        self.counted_ids.clear()
