import os
from ..utils.logger import ls

# Lazy import to handle DLL load failures on some systems
YOLO_MODEL = None
TORCH_MOD = None

def _ensure_yolo():
    global YOLO_MODEL, TORCH_MOD
    if YOLO_MODEL is None:
        try:
            from ultralytics import YOLO as Y
            import torch as T
            YOLO_MODEL = Y
            TORCH_MOD = T
            ls.info("Ultralytics/PyTorch successfully initialized.")
        except (ImportError, OSError) as e:
            ls.error(f"DLL/Dependency initialization failure for YOLO: {e}")
            YOLO_MODEL = False
    return YOLO_MODEL

class DetectionService:
    """
    YOLOv8 wrapper for object detection.
    """
    def __init__(self, model_path, confidence=0.45, iou=0.5, device='auto'):
        self.model_path = model_path
        self.confidence = confidence
        self.iou = iou
        self.device = device
        self.model = None
        self.torch_device = 'cpu'
        self._load_model()
        
    def _load_model(self):
        """
        Loads the weight file into memory. Handles file-not-found case.
        """
        yolo_cls = _ensure_yolo()
        if not yolo_cls:
            ls.warning("YOLO detection engine disabled due to initialization error.")
            return

        if not os.path.exists(self.model_path):
            ls.error(f"YOLOv8 weights not found at: {self.model_path}")
            return
            
        try:
            # Set torch device
            if self.device == 'auto':
                self.torch_device = 'cuda' if TORCH_MOD.cuda.is_available() else 'cpu'
            else:
                self.torch_device = self.device
                
            self.model = yolo_cls(self.model_path)
            # Move to device
            self.model.to(self.torch_device)
            ls.info(f"YOLOv8 loaded on {self.torch_device} from {self.model_path}")
        except Exception as e:
            ls.error(f"Failed to load YOLOv8 model: {e}")

    def detect(self, frame):
        """
        Sends frame to inference and returns list of detections.
        Each detection: {'bbox': [x1,y1,x2,y2], 'class_id': int, 'conf': float}
        """
        if self.model is None:
            return []
            
        try:
            results = self.model.predict(
                source=frame,
                conf=self.confidence,
                iou=self.iou,
                device=self.torch_device,
                verbose=False,
                imgsz=640
            )
            
            detections = []
            for r in results:
                boxes = r.boxes.xyxy.cpu().numpy()
                confs = r.boxes.conf.cpu().numpy()
                classes = r.boxes.cls.cpu().numpy().astype(int)
                
                for box, conf, cls_id in zip(boxes, confs, classes):
                    detections.append({
                        'bbox': box.tolist(),
                        'conf': float(conf),
                        'class_id': int(cls_id)
                    })
            return detections
        except Exception as e:
            ls.error(f"Inference failed: {e}")
            return []

    def set_config(self, conf=None, iou=None):
        if conf is not None: self.confidence = conf
        if iou is not None: self.iou = iou
