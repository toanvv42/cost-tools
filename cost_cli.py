#!/usr/bin/env python3

"""Legacy CLI wrapper.

This script now delegates to the packaged entry point `aws_cost_tools.cli:main`.
Use `uv run cost-tools ...` or install the package and use the `cost-tools` command.
"""

from aws_cost_tools.cli import main


if __name__ == "__main__":
    main()