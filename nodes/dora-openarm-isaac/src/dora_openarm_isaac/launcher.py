# Copyright 2026 Enactic, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Entry point that bootstraps Isaac Lab before importing isaaclab."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def _find_isaaclab_sh() -> Path | None:
    candidates = []
    if env := os.environ.get("ISAACLAB_PATH"):
        candidates.append(Path(env) / "isaaclab.sh")
    candidates.extend(
        [
            Path("/workspace/isaaclab/isaaclab.sh"),
            Path.home() / "IsaacLab/isaaclab.sh",
        ]
    )
    for path in candidates:
        if path.is_file():
            return path
    return None


def cli_main() -> None:
    """Console entrypoint used by dora.

    In Isaac Lab Docker, dora spawns the kit ``python`` directly. That
    environment lacks Isaac Lab dependencies (``toml``, ``torch``, etc.).
    Re-exec through ``isaaclab.sh -p`` when available, matching Phase 1 verify.
    """
    main_py = Path(__file__).resolve().parent / "main.py"
    isaaclab_sh = _find_isaaclab_sh()

    if isaaclab_sh is not None:
        os.execvp(
            "bash",
            ["bash", str(isaaclab_sh), "-p", str(main_py), *sys.argv[1:]],
        )

    # Local conda install with Isaac Lab already configured.
    from dora_openarm_isaac.main import cli_main as run_cli_main

    run_cli_main()


if __name__ == "__main__":
    cli_main()
