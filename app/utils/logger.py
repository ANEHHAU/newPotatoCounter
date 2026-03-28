import logging
import os
import sys

def setup_logger(name='potato_qc', log_level=logging.INFO):
    """
    Sets up a structured application-level logger.
    """
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    
    # Create console handler and set level to info
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(log_level)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Add formatter to ch
    ch.setFormatter(formatter)
    
    # Add ch to logger
    if not logger.handlers:
        logger.addHandler(ch)
        
    return logger

logger = setup_logger()
ls = logger  # shorthand for quick logging
