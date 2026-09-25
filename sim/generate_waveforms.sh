#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

OUT_DIR="../docs/waveforms"
mkdir -p "$OUT_DIR"

declare -A SCENARIOS=(
    [test_back_to_back_streaming]="Fill then drain (full/empty toggling)|fill_then_drain"
    [test_overlapping_write_and_read]="Overlapping write + read across domains|overlapping_write_and_read"
    [test_pointer_wraparound]="Pointer wraparound across three fill/drain rounds|pointer_wraparound"
)

for testcase in "${!SCENARIOS[@]}"; do
    IFS='|' read -r title outfile <<< "${SCENARIOS[$testcase]}"

    rm -rf sim_build results.xml
    make COCOTB_TESTCASE="$testcase" WAVES=1

    fst2vcd sim_build/Async_FIFO.fst -o "sim_build/${outfile}.vcd"
    python3 render_waveforms.py "sim_build/${outfile}.vcd" "$OUT_DIR/${outfile}.png" "$title"
done
