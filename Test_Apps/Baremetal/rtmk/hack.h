#undef PRIVILEGED_FUNCTION
#undef PRIVILEGED_DATA
#undef FREERTOS_SYSTEM_CALL
#define PRIVILEGED_FUNCTION     __attribute__( ( section( "privileged_functions" ) ) )
#define PRIVILEGED_DATA         __attribute__( ( section( "privileged_data" ) ) ) 
#define FREERTOS_SYSTEM_CALL    __attribute__( ( section( "freertos_system_calls" ) ) )
