"""
Level 2 Pipeline (Root Forwarder Shim)
---------------------------------------
Forwards all calls to `backend.pipeline.lvl2_pipeline` for backward compatibility.
"""

import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from pipeline import lvl2_pipeline, _convert_to_markdown_placeholder

__all__ = ["lvl2_pipeline"]

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
        description="Run Level 2 Pipeline (Forwarder to backend.pipeline)"
    )
    default_rfp = "data/rfp/rfp_nordframe.md"
    default_resp = "data/response/response_2_medium.md"

    parser.add_argument("rfp_file", nargs="?", default=default_rfp)
    parser.add_argument("response_file", nargs="?", default=default_resp)
    parser.add_argument("--output-file", "-o", default=None)
    parser.add_argument("--criteria-file", "-c", default="criteria.json")

    args = parser.parse_args()
    lvl2_pipeline(
        rfp_file=args.rfp_file,
        response_file=args.response_file,
        output_file=args.output_file,
        criteria_file=args.criteria_file,
    )
