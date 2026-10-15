import os
import sys
import tempfile
from pathlib import Path

# Keep test runs from touching your real settings, files and transcripts.
os.environ["COPILOT_DATA_DIR"] = tempfile.mkdtemp(prefix="copilot-test-")
for k in ("DEEPGRAM_API_KEY", "ANTHROPIC_API_KEY", "OPENAI_API_KEY"):
    os.environ[k] = ""
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
