#ifndef __SYSTEMFUNC_H
#define __SYSTEMFUNC_H

#include "main.h"


/* Private variables ---------------------------------------------------------*/
extern USART_HandleTypeDef husart1;
extern USART_HandleTypeDef husart2;
/* USER CODE BEGIN PV */

/* USER CODE END PV */

/* Private function prototypes -----------------------------------------------*/
void SystemClock_Config(void);
static void MX_GPIO_Init(void);
static void MX_USART1_Init(void);
static void MX_USART2_Init(void);
static void MPU_Config(void);

#ifdef __cplusplus
extern "C" {
#endif

void MX_Init_System(void);

#ifdef __cplusplus
}
#endif

#endif 