extern "C" {
#include "systemfunc.h"
#include "main.h"
#include "mpu_demo.h"
}

#include <cstring>

extern "C" void rtmk_dump_mpu(void);

int main(void)
{
    /* USART is now initialized — dump MPU region config for verification */
    rtmk_dump_mpu();

    const char *msg = "Hello World!\r\n";

    HAL_USART_Transmit(&husart1,
                    (uint8_t*)msg,
                    strlen(msg),
                    HAL_MAX_DELAY);
    
    
    while(1)
    {
        vStartMPUDemo();
        HAL_Delay(1000);
    }
}
