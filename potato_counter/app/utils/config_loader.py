import yaml
from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Tuple, Any

class VideoConfig(BaseModel):
    source: str = "0"
    input_fps: int = 30
    processing_fps_limit: int = 30
    resolution: List[int] = [1920, 1080]

class PipelineConfig(BaseModel):
    confidence_threshold: float = 0.5
    iou_threshold: float = 0.3
    clahe_clip_limit: float = 2.0
    brightness: int = 0
    contrast: int = 0
    enable_otsu: bool = False

class ZonesConfig(BaseModel):
    roi: List[List[int]] = []
    define_zone: List[List[int]] = []
    count_line: Optional[List[List[int]]] = None

class PotatoCounterConfig(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    video: VideoConfig = VideoConfig()
    pipeline: PipelineConfig = PipelineConfig()
    zones: ZonesConfig = ZonesConfig()
    operating_mode: int = 1

def load_config(file_path: str = "config.yaml") -> PotatoCounterConfig:
    """Loads configuration from a YAML file."""
    try:
        with open(file_path, 'r') as f:
            data = yaml.safe_load(f) or {}
            # Ensure we don't have python-specific tags if someone edited it manually
            return PotatoCounterConfig(**data)
    except Exception as e:
        print(f"[Error] Failed to load config: {e}. Using default configuration.")
        return PotatoCounterConfig()

def save_config(config: PotatoCounterConfig, file_path: str = "config.yaml"):
    """Saves the current configuration back to a YAML file."""
    try:
        # model_dump() returns a dict with basic python types, safe for yaml.dump
        with open(file_path, 'w') as f:
            yaml.dump(config.model_dump(), f, default_flow_style=False, sort_keys=False)
    except Exception as e:
        print(f"[Error] Failed to save config: {e}")
