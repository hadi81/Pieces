CC                     =   clang-16
CXX                    =   clang++-16
GDB                    =   $(GCC_INSTALL)bin/arm-none-eabi-gdb
BIN                   :=    stm32App.elf

BUILD_DIR             :=    build

DEBUG += 1

GCC_INSTALL ?= /home/hzm5471/tools/arm-gnu-toolchain-14.2.rel1-x86_64-arm-none-eabi/
GCC_INSTALL_INCLUDE = $(GCC_INSTALL)arm-none-eabi/include/
GCC_INSTALL_LIB ?= $(GCC_INSTALL)arm-none-eabi/lib/thumb/v7+fp/hard
LIBGCC_PATH ?= $(GCC_INSTALL)lib/gcc/arm-none-eabi/14.2.1/thumb/v7+fp/hard

GCC_INSTALL_CPP_INCLUDE  = $(GCC_INSTALL_INCLUDE)c++/14.2.1/
GCC_INSTALL_CPP_INCLUDE2 = $(GCC_INSTALL_CPP_INCLUDE)arm-none-eabi/

LD_DIR                  := scripts
AUTO_GEN_DIR		  	:= autogen
CUBE_DIR         		:= Sys
APP_DIR          		:= App
RTMK_DIR         		:= rtmk
CORE_DIR         		:= $(CUBE_DIR)/Core/Src
CORE_INC         		:= $(CUBE_DIR)/Core/Inc
HAL_SRC          		:= $(CUBE_DIR)/Drivers/STM32F7xx_HAL_Driver/Src
HAL_INC          		:= $(CUBE_DIR)/Drivers/STM32F7xx_HAL_Driver/Inc
CMSIS_DEV_INC    		:= $(CUBE_DIR)/Drivers/CMSIS/Device/ST/STM32F7xx/Include
CMSIS_CORE_INC   		:= $(CUBE_DIR)/Drivers/CMSIS/Include

HAL_SRC_FILES		+= $(HAL_SRC)/stm32f7xx_hal_flash.c $(HAL_SRC)/stm32f7xx_hal_rcc_ex.c \
                       $(HAL_SRC)/stm32f7xx_hal_flash_ex.c $(HAL_SRC)/stm32f7xx_hal_usart.c \
                       $(HAL_SRC)/stm32f7xx_hal_rcc.c
HAL_SRC_FILES		+= $(HAL_SRC)/stm32f7xx_hal.c $(HAL_SRC)/stm32f7xx_hal_exti.c \
                       $(HAL_SRC)/stm32f7xx_hal_pwr_ex.c $(HAL_SRC)/stm32f7xx_hal_i2c_ex.c \
                       $(HAL_SRC)/stm32f7xx_hal_dma_ex.c $(HAL_SRC)/stm32f7xx_hal_pwr.c \
                       $(HAL_SRC)/stm32f7xx_hal_gpio.c
HAL_SRC_FILES		+= $(HAL_SRC)/stm32f7xx_hal_cortex.c $(HAL_SRC)/stm32f7xx_hal_dma.c \
                       $(HAL_SRC)/stm32f7xx_hal_i2c.c

SOURCE_FILES     	+= $(CORE_DIR)/stm32f7xx_hal_msp.c $(CORE_DIR)/stm32f7xx_it.c \
                       $(CORE_DIR)/sysmem.c $(CORE_DIR)/system_stm32f7xx.c
SOURCE_FILES     	+= $(HAL_SRC_FILES) $(CORE_DIR)/undefined_func.c \
                       $(CORE_DIR)/systemfunc.c \
                       $(AUTO_GEN_DIR)/autogen_heap.c $(AUTO_GEN_DIR)/autogen_data.c \
                       $(APP_DIR)/mpu_demo.c

SOURCE_FILES_CPP    += $(APP_DIR)/main.cpp $(RTMK_DIR)/rtmk.cpp

INCLUDE_DIRS     += -I$(CORE_INC) -I$(HAL_INC) -I$(HAL_INC)/Legacy \
                    -I$(CMSIS_DEV_INC) -I$(CMSIS_CORE_INC) \
                    -I$(GCC_INSTALL_INCLUDE) -I$(RTMK_DIR)
INCLUDE_DIRS_CPP += -I$(GCC_INSTALL_CPP_INCLUDE) -I$(GCC_INSTALL_CPP_INCLUDE2) \
                    -I$(GCC_INSTALL_INCLUDE)machine/

DEFINES          :=    -DSTM32F769xx -DUSE_HAL_DRIVER -D__MPU_PRESENT=1U

CPPFLAGS         +=    $(DEFINES) $(INCLUDE_DIRS)
CFLAGS           +=    -mcpu=cortex-m7 -mfpu=fpv5-d16 -mfloat-abi=hard -mthumb \
                       --target=arm-none-eabi \
                       -Wno-unused-variable -Wno-missing-field-initializers
CFLAGS           +=    -Wall -Wextra -Wno-error=implicit-function-declaration \
                       -Wno-error=address-of-packed-member -Wno-tautological-compare \
                       -Wno-unused-parameter -fstrict-aliasing -Wstrict-aliasing \
                       $(CPPFLAGS) -g -O0 -save-temps=obj
CFLAGS           +=    -emit-llvm -Wno-unknown-attributes -Wno-error=unknown-pragmas \
                       -Wno-return-type -Wno-sign-compare
CPPFLAGS         +=    -isystem $(GCC_INSTALL_CPP_INCLUDE)
CPPFLAGS         +=    -isystem $(GCC_INSTALL_INCLUDE)
CPPFLAGS         +=    -Wno-unused-variable -Wno-missing-field-initializers \
                       -Wno-unknown-attributes -Wno-error=unknown-pragmas \
                       -Wno-tautological-compare -Wno-error

LDFLAGS          +=    -mthumb -Xlinker -Map=${BUILD_DIR}/output.map -nostdlib
LDFLAGS          +=    -L$(GCC_INSTALL_LIB) -L./ -v
LDFLAGS          +=    -T $(LD_DIR)/STM32F769NIHX_FLASH_ld.ld \
                       -mfpu=fpv5-d16 -mfloat-abi=hard \
                       -Wl,--start-group -lm --specs=nosys.specs
LDFLAGS          +=    -stdlib=libstdc++ -rtlib=libgcc -lsupc++ \
                       -Wl,--end-group -static --specs=nano.specs -lstdc++

OBJ_FILES        :=    $(SOURCE_FILES:%.c=$(BUILD_DIR)/%.o)
OBJ_FILES_CPP    :=    $(SOURCE_FILES_CPP:%.cpp=$(BUILD_DIR)/%.o)

.PHONY: all clean bc exec debug

all: $(BUILD_DIR)/startup_stm32f769nihx.o $(OBJ_FILES) $(OBJ_FILES_CPP)

$(BUILD_DIR)/$(BIN): $(OBJ_FILES) $(OBJ_FILES_CPP)
	$(CXX) -ffunction-sections -std=gnu++17 -fdata-sections \
	       $(CFLAGS) $(LDFLAGS) $+ -o $(@)

$(BUILD_DIR)/startup_stm32f769nihx.o: $(CUBE_DIR)/Core/Startup/startup_stm32f769nihx.s
	clang-16 --target=arm-none-eabi -mthumb -mcpu=cortex-m7 -c $+ -o $(@)

${BUILD_DIR}/%.o: %.c Makefile
	-mkdir -p $(@D)
	$(CC) $(CFLAGS) $(CPPFLAGS) -MMD -c $< -o $@

${BUILD_DIR}/%.o: %.cpp Makefile
	-mkdir -p $(@D)
	$(CXX) $(CFLAGS) $(CPPFLAGS) -std=c++17 $(INCLUDE_DIRS_CPP) -MMD -c $< -o $@

bc: $(OBJ_FILES) $(OBJ_FILES_CPP)
	llvm-link-16 -v $+ -o $(BUILD_DIR)/$(BIN).bc
	llvm-dis-16 $(BUILD_DIR)/$(BIN).bc
	clang-16 --target=arm-none-eabi -mthumb -mcpu=cortex-m7 \
	         -c $(CUBE_DIR)/Core/Startup/startup_stm32f769nihx.s \
	         -o $(BUILD_DIR)/startup_stm32f769nihx.o

exec:
	llc-16 -filetype=obj build/$(BIN).bc -o build/$(BIN).o
	$(CXX) -fuse-ld=/usr/bin/ld.lld-16 --target=arm-none-eabi -mthumb -mcpu=cortex-m7 \
	       $(LDFLAGS) -lc -L$(LIBGCC_PATH) -lgcc \
	       -Xlinker -Map=build/rtmk.map \
	       build/$(BIN).o build/startup_stm32f769nihx.o \
	       -o ./build/$(BIN)
	size -A -d ./build/$(BIN) | tee ./build/sizeinfo

debug:
	openocd -f interface/stlink.cfg -f target/stm32f7x.cfg &
	$(GDB) build/$(BIN) \
	    -ex "target remote :3333" \
	    -ex "monitor reset halt" \
	    -ex "load"

clean:
	-rm -rf build
