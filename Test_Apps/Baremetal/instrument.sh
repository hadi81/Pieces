#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

export SVF_BIN=/home/hzm5471/repos/SVF/Debug-build/bin

python3 /home/hzm5471/repos/new_pieces/Pieces/instrument.py \
    "$SCRIPT_DIR/build/stm32App.elf.bc" \
    "$SCRIPT_DIR/comp/.policy"

cp "$SCRIPT_DIR/temp.bc" "$SCRIPT_DIR/build/stm32App.elf.bc"
cp "$SCRIPT_DIR/temp.ll" "$SCRIPT_DIR/build/stm32App.elf.ll"

echo "Done: instrumented bitcode written to build/stm32App.elf.bc and build/stm32App.elf.ll"
