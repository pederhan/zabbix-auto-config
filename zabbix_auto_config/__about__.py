import os
import importlib.metadata

__version__ = importlib.metadata.version(os.path.basename(os.path.dirname(__file__)))