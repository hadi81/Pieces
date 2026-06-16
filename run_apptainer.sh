apptainer shell \
  --writable-tmpfs \
  --no-home \
  --env HOME=/home/hzm5471 \
  --bind /home/hzm5471:/home/hzm5471 \
  --bind "$(pwd)":/pieces \
  --bind /home/hzm5471/repos/SVF:/home/SVF-tools/SVF \
  --bind /home/hzm5471/repos/TensorFlow-with-Stm32f769-Clang:/stm324 \
  --bind /home/hzm5471/tools/arm-gnu-toolchain-14.2.rel1-x86_64-arm-none-eabi:/toolchains/arm-gnu-toolchain-14.2.rel1-x86_64-arm-none-eabi \
  pieces.sandbox
