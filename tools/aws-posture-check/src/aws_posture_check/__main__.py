"""Allow ``python -m aws_posture_check``."""

import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
