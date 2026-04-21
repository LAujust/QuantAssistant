"""
通用工具函数
"""
import uuid
from datetime import datetime


def generate_run_id() -> str:
    """生成唯一的运行ID"""
    return datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + uuid.uuid4().hex[:6]
