#!/usr/bin/env bash
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

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

"$(dirname "${BASH_SOURCE[0]}")/init_submodules.sh" vr
# shellcheck source=scripts/data_collection/dora_cli.sh
source "$(dirname "${BASH_SOURCE[0]}")/dora_cli.sh"
setup_dora_path
export PATH
install_dora_nodes vr
DORA="$(resolve_dora_cmd)"
DATAFLOW="dataflow-vr-isaac.yaml"

echo "[dataflow] Building node dependencies..."
"$DORA" build "$DATAFLOW"
echo "[dataflow] Starting VR Isaac data collection..."
exec "$DORA" run "$DATAFLOW" "$@"
