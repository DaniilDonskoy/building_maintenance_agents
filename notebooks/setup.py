import sys
import os
from pathlib import Path


def setup_modules():
	PROJECT_ROOT = Path.cwd()
	if PROJECT_ROOT.name == "notebooks":
		PROJECT_ROOT = PROJECT_ROOT.parent
	if str(PROJECT_ROOT) not in sys.path:
		sys.path.insert(0, str(PROJECT_ROOT))
