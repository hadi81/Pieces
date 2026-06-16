#include <stdint.h>
#include <string.h>
#include "systemfunc.h"
#include "monitor.h"

static void usart_print( const char *msg )
{
    HAL_USART_Transmit( &husart1, (uint8_t *)msg, strlen(msg), HAL_MAX_DELAY );
}

#define SHARED_MEMORY_SIZE    32

static uint8_t ucSharedMemory[ SHARED_MEMORY_SIZE ] __attribute__( ( aligned( SHARED_MEMORY_SIZE ) ) );

static volatile uint8_t ucROTaskFaultTracker[ SHARED_MEMORY_SIZE ] __attribute__( ( aligned( SHARED_MEMORY_SIZE ) ) ) = { 0 };

static void prvROAccessTask( void *pvParameters );
static void prvRWAccessTask( void *pvParameters );

int normal_call( void )
{
    usart_print( "normal_call (C1)\r\n" );
    return 0;
}

/*
 * prvRWAccessTask - C1
 * prvROAccessTask - C2
 * Modify according to your application.
 */
static void prvRWAccessTask( void *pvParameters )
{
    ( void ) pvParameters;

#if 0
    /* test 1 */
    unsigned int *p = (unsigned int *) 0x20000000;
    *p = 10;
#endif

#if 0
    /* test 2 - BUG in bridge */
    /* prvROAccessTask(NULL); */
#endif

#if 0
    /* test 3 - Cross compartment call without switch_view */
    int hello = 10;
    prvROAccessTask( &hello );
    /* Did we come back? */
    while ( 1 );
#endif

#if 01
    /* test 4 - It should be included in C1 */
    normal_call();
#endif

    // int a = 0;
    // for ( ; ; )
    // {
    //     /* This task has RW access to ucSharedMemory and therefore can write to it. */
    //     /* ucSharedMemory[ 0 ] = 0; */

    //     HAL_Delay( 1000 );
    //     a++;
    // }

    usart_print( "RWAccessTask (C1)\r\n" );

    int a = 0;
    /* This task has RW access to ucSharedMemory and therefore can write to it. */
    /* ucSharedMemory[ 0 ] = 0; */

    HAL_Delay( 1000 );
    a++;
}

static void prvROAccessTask( void *pvParameters )
{
    volatile uint8_t ucVal;

    ( void ) pvParameters;

    usart_print( "ROAccessTask (C2)\r\n" );

    /* Read from the shared memory region. */
    ucVal = ucSharedMemory[ 0 ];
    ( void ) ucVal;

    HAL_Delay( 1000 );
}

void vStartMPUDemo( void )
{
    for ( ; ; )
    {
        prvRWAccessTask( NULL );
        prvROAccessTask( NULL );
    }
}
