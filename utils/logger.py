# utils/logger.py
import logging
from datetime import datetime

def setup_logger():
    logging.basicConfig(
        filename='remote_control.log',
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def log_action(action, target, status):
    logging.info(f"Action: {action}, Target: {target}, Status: {status}")
