import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))

from mangum import Mangum
from app import app

handler = Mangum(app)
