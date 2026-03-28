from collections import Counter
import numpy as np
from ..utils.logger import ls

def resolve_label(prediction_history, mode, min_frames=3, unknown_gap=0.08):
    """
    Final label resolution logic (weighted average confidence vote).
    
    Args:
        prediction_history: list[(class_id, conf)]
        mode: "good_defect" | "full_class"
        min_frames: Minimum frames in zone required for a valid classification
        unknown_gap: If top-2 classes are within this confidence delta, it's UNKNOWN
        
    Returns:
        (label, confidence, reason)
    """
    if not prediction_history:
        return ("N/A", 0.0, "No data collected")
    
    if len(prediction_history) < min_frames:
        return ("unknown", 0.0, f"Insufficient frames ({len(prediction_history)} < {min_frames})")
    
    # Mode mapping
    # Assuming class IDs correspond to: 0: good, 1: damaged, 2: diseased, 3: sprouted, 4: deformed
    class_map = {
        0: "good",
        1: "damaged",
        2: "diseased",
        3: "sprouted",
        4: "deformed"
    }
    
    # 1. Tally weighted confidence for each class
    weighted_scores = Counter()
    for class_id, conf in prediction_history:
        weighted_scores[class_id] += conf
        
    # 2. Get top 1 and top 2 classes
    top_two = weighted_scores.most_common(2)
    best_id, best_score_total = top_two[0]
    
    # 3. Calculate mean confidence for the best class
    total_count = sum(1 for cid, conf in prediction_history if cid == best_id)
    mean_conf = best_score_total / total_count if total_count > 0 else 0.0
    
    # 4. Check for ambiguity (gap between top-2)
    if len(top_two) > 1:
        second_id, second_score_total = top_two[1]
        second_count = sum(1 for cid, conf in prediction_history if cid == second_id)
        second_mean_conf = second_score_total / second_count if second_count > 0 else 0.0
        
        if abs(mean_conf - second_mean_conf) < unknown_gap:
            return ("unknown", mean_conf, f"Ambiguous ({mean_conf:.2f} vs {second_mean_conf:.2f})")
            
    # 5. Map result based on mode
    label = class_map.get(best_id, "unknown")
    
    if mode == "good_defect":
        if label == "good":
            return ("GOOD", mean_conf, "Majority vote")
        else:
            return ("DEFECT", mean_conf, f"Detected as {label}")
    else:
        # Full class mode
        return (label, mean_conf, f"Weighted majority over {len(prediction_history)} frames")

# Finalized event trigger function
def finalize_track(track, mode, min_frames=3, unknown_gap=0.08):
    """
    Updates PotatoTrack status and label when it exits the define zone.
    """
    label, confidence, reason = resolve_label(track.prediction_history, mode, min_frames, unknown_gap)
    track.final_label = label
    track.final_confidence = confidence
    track.decision_reason = reason
    
    from .potato_track import PotatoState
    track.state = PotatoState.FINALIZED
    ls.info(f"Potato {track.track_id} finalized as: {label} (conf:{confidence:.2f})")
    return track
