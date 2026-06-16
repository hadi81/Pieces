#!/bin/bash
set -e

cd /home/hzm5471/repos/new_pieces/Pieces/Test_Apps/Baremetal
rm -rf build
mv /home/hzm5471/repos/new_pieces/Pieces/Test_Apps/Baremetal/comp/.policy \
   /home/hzm5471/repos/new_pieces/Pieces/Test_Apps/Baremetal/comp/.policy_bak
rm -rf pieces.pkl
. /home/hzm5471/repos/new_pieces/Pieces/pieces_env/bin/activate
/home/hzm5471/repos/new_pieces/Pieces/partitioner/scripts/autogen.py ./scripts/STM32F769NIHX_FLASH_overlay.ld
/home/hzm5471/repos/new_pieces/Pieces/partitioner/scripts/autogen.py
make bc
make exec
mv /home/hzm5471/repos/new_pieces/Pieces/Test_Apps/Baremetal/comp/.policy_bak \
   /home/hzm5471/repos/new_pieces/Pieces/Test_Apps/Baremetal/comp/.policy
/home/hzm5471/repos/new_pieces/Pieces/partitioner/scripts/autogen.py ./comp/.policy
make bc
make exec
./instrument.sh
make exec
/home/hzm5471/repos/new_pieces/Pieces/partitioner/scripts/autogen.py ./build/stm32App.elf
make exec
