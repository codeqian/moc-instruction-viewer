"""应用配置"""

import os
from pathlib import Path

# 项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent

# 数据目录
DATA_DIR = Path(os.getenv("DATA_DIR", BASE_DIR / "data"))

# 源文件目录
SOURCE_DIR = DATA_DIR / "source"

# LDraw 零件库目录
LDRAW_LIB_DIR = DATA_DIR / "ldraw-lib"

# 缓存目录
CACHE_DIR = DATA_DIR / "cache"
PACKED_CACHE_DIR = CACHE_DIR / "packed"
STEPS_CACHE_DIR = CACHE_DIR / "steps"

# 日志目录
LOG_DIR = DATA_DIR / "logs"

# 确保目录存在
for dir_path in [SOURCE_DIR, LDRAW_LIB_DIR, PACKED_CACHE_DIR, STEPS_CACHE_DIR, LOG_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# 缓存有效期（秒），默认 24 小时
CACHE_TTL = int(os.getenv("CACHE_TTL", "86400"))
