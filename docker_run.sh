docker run -it --rm -v "$(pwd)":/pieces -v "/home/cts/Documents/stm324_baremetal_check/stm324_baremetal":/stm324 -v "/home/cts/data/gcc-arm-none-eabi-10-2020-q4-major":/toolchains/gcc-arm-none-eabi-10-2020-q4-major pieces/pieces /bin/bash



docker run -it --rm -v "$(pwd)":/pieces -v "/home/hzm5471/repos/SVF":/home/SVF-tools/SVF -v "/home/hzm5471/repos/TensorFlow-with-Stm32f769-Clang":/stm324 -v "/home/hzm5471/tools/arm-gnu-toolchain-14.2.rel1-x86_64-arm-none-eabi/":/toolchains/arm-gnu-toolchain-14.2.rel1-x86_64-arm-none-eabi pieces/pieces /bin/bash
