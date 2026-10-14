"""Подсказка pytest: искать пакеты в корне проекта."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
