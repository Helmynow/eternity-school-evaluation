"""
Deprecated Flask entrypoint.
Use FastAPI instead: `uvicorn backend.fastapi_app:app --host 0.0.0.0 --port 8000 --reload`
"""

import sys


def main() -> None:
    print("backend/app.py is deprecated. " "Use FastAPI: uvicorn backend.fastapi_app:app --host 0.0.0.0 --port 8000 --reload")
    sys.exit(1)


if __name__ == "__main__":
    main()
