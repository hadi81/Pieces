#include "monitor.h"
#include "main.h"

#define __MPU_PRESENT 1U
// #include "core_cm4.h"
#define PROTO
// #include "autogen_data.c"

#define NUM_COMPARTMENTS 4
#define REGION_ENABLE   (1U)

extern "C" {

extern uint32_t _srtmkdata, _ertmkdata, _lrtmkdata, _srtmkcode, _srtmkdata;
extern uint32_t _sshared_func, _sshared_data;
extern uint32_t _sheap_stack;

RTMK_DATA uint32_t psp_stack[1024] __attribute__((aligned(8))); 


RTMK_CODE void switch_to_unprivileged_psp(void) {
    // Set PSP to new stack
    __set_PSP((uint32_t)(psp_stack + 1024));

    // Switch to PSP + unprivileged
    __asm volatile (
        "mrs r0, CONTROL   \n"
        "orr r0, r0, #3    \n"  // bit1=1 → PSP, bit0=1 → unprivileged
        "msr CONTROL, r0   \n"
		"mov r0, #0        \n"
        "isb               \n"
        :::"r0"
    );
}

RTMK_CODE void switch_to_unprivileged_msp(void) {

    // Drop to unprivileged, stay on MSP (bit1/SPSEL unchanged)
    __asm volatile (
        "mrs r0, CONTROL   \n"
        "orr r0, r0, #1    \n"  // bit0=1 → unprivileged, bit1 unchanged (stay on MSP)
        "msr CONTROL, r0   \n"
        "isb               \n"
        :::"r0"
    );
}

// void SVC_Handler(void) {
//     // Back in privileged mode inside handler
//     __asm volatile (
//         "mrs r0, CONTROL   \n"
//         "bic r0, r0, #1    \n"  // clear nPRIV bit
//         "msr CONTROL, r0   \n"
//         "isb               \n"
//         :::"r0"
//     );
// }

RTMK_CODE void request_privileged(void) {
    __asm volatile ("svc 0");
}


// Only following two being used
RTMK_CODE void request_privileged_msp(void) {
    __asm volatile ("svc 0");

	__asm volatile (
        "mrs r0, CONTROL   \n"
        "bic r0, r0, #3    \n"  // clear SPSEL (bit1) and nPRIV (bit0)
        "msr CONTROL, r0   \n"
        "isb               \n"
        :::"r0"
    );
}

// No stack management, switches from privilege to unprivilege by writing
// to the control register
RTMK_CODE void switch_unprivileged_from_privilege(void) {

__asm volatile (
    "mrs r0, CONTROL   \n"
    "bic r0, r0, #3    \n"  // clear SPSEL and nPRIV bits
    "orr r0, r0, #1    \n"  // set SPSEL=1 (PSP), keep nPRIV=0 (privileged)
    "msr CONTROL, r0   \n"
    "isb               \n"
    :::"r0"
);
}


extern int comp_current; /* defined below as RTMK_DATA */

/* ---- Debug UART helpers (USART must be initialized before calling) ---- */
RTMK_CODE void dbg_str(const char *s) {
    extern USART_HandleTypeDef husart1;
    while (*s)
        HAL_USART_Transmit(&husart1, (uint8_t *)s++, 1, 100);
}

RTMK_CODE void dbg_hex(uint32_t v) {
    const char *hex = "0123456789ABCDEF";
    char buf[11] = "0x00000000";
    for (int i = 9; i >= 2; i--) { buf[i] = hex[v & 0xF]; v >>= 4; }
    dbg_str(buf);
}

RTMK_CODE void dbg_dec(int v) {
    char buf[12];
    int i = 10;
    buf[11] = '\0'; buf[10] = '\0';
    if (v == 0) { dbg_str("0"); return; }
    while (v > 0 && i > 0) { buf[--i] = '0' + (v % 10); v /= 10; }
    dbg_str(&buf[i]);
}



RTMK_CODE void RTMK_Reprogram_MPU_Region_for_Compartment(int comp);

RTMK_CODE void RTMK_MPU_Config(void)
{
    HAL_MPU_Disable();

    MPU_Region_InitTypeDef r;
    r.SubRegionDisable = 0x00;
    r.TypeExtField     = MPU_TEX_LEVEL0;
    r.IsShareable      = MPU_ACCESS_NOT_SHAREABLE;
    r.IsCacheable      = MPU_ACCESS_CACHEABLE;
    r.IsBufferable     = MPU_ACCESS_NOT_BUFFERABLE;
    r.Enable           = MPU_REGION_ENABLE;

    /* Region 0: RAM — Privileged R/W only, no execute */
    r.Number           = MPU_REGION_NUMBER0;
    r.BaseAddress      = 0x20000000;
    r.Size             = MPU_REGION_SIZE_512KB;
    r.AccessPermission = MPU_REGION_PRIV_RW;
    r.DisableExec      = MPU_INSTRUCTION_ACCESS_DISABLE;
    HAL_MPU_ConfigRegion(&r);

    /* Region 1: Flash — Privileged R/O, executable */
    r.Number           = MPU_REGION_NUMBER1;
    r.BaseAddress      = 0x08000000;
    r.Size             = MPU_REGION_SIZE_2MB;
    r.AccessPermission = MPU_REGION_PRIV_RO;
    r.DisableExec      = MPU_INSTRUCTION_ACCESS_ENABLE;
    HAL_MPU_ConfigRegion(&r);

    /* Region 2: Heap+Stack — Unprivileged R/W, no execute (128KB at 0x20060000..0x20080000) */
    r.Number           = MPU_REGION_NUMBER2;
    r.BaseAddress      = (uint32_t)&_sheap_stack;
    r.Size             = MPU_REGION_SIZE_128KB;
    r.AccessPermission = MPU_REGION_FULL_ACCESS;
    r.DisableExec      = MPU_INSTRUCTION_ACCESS_DISABLE;
    HAL_MPU_ConfigRegion(&r);

    /* Region 3: RTMK Code + Shared Code — Unprivileged R/O, executable
     * .rtmkcode (16KB) and .shared_func (16KB) are contiguous at _srtmkcode,
     * combining into one naturally-aligned 32KB region. */
    r.Number           = MPU_REGION_NUMBER3;
    r.BaseAddress      = (uint32_t)&_srtmkcode;
    r.Size             = MPU_REGION_SIZE_32KB;
    r.AccessPermission = MPU_REGION_PRIV_RO_URO;
    r.DisableExec      = MPU_INSTRUCTION_ACCESS_ENABLE;
    HAL_MPU_ConfigRegion(&r);

    /* Region 4: RTMK Data — Unprivileged R/W, no execute */
    r.Number           = MPU_REGION_NUMBER4;
    r.BaseAddress      = (uint32_t)&_srtmkdata;
    r.Size             = MPU_REGION_SIZE_8KB;
    r.AccessPermission = MPU_REGION_FULL_ACCESS;
    r.DisableExec      = MPU_INSTRUCTION_ACCESS_DISABLE;
    HAL_MPU_ConfigRegion(&r);

    /* Region 5: Shared Data — Unprivileged R/W, no execute */
    r.Number           = MPU_REGION_NUMBER5;
    r.BaseAddress      = (uint32_t)&_sshared_data;
    r.Size             = MPU_REGION_SIZE_8KB;
    r.AccessPermission = MPU_REGION_FULL_ACCESS;
    r.DisableExec      = MPU_INSTRUCTION_ACCESS_DISABLE;
    HAL_MPU_ConfigRegion(&r);

    /* Regions 6-7: pre-programmed for compartment 1 (first to run) */
    // for (uint32_t i = MPU_REGION_NUMBER6; i <= MPU_REGION_NUMBER7; i++)
    //     HAL_MPU_DisableRegion(i);
    RTMK_Reprogram_MPU_Region_for_Compartment(1);

    HAL_MPU_Enable(MPU_PRIVILEGED_DEFAULT);
    __DSB();
    __ISB();
}

// uint32_t val = comp_info[0].start;
// /* MPU table specifying MPU regions for all Zones */
// ARM_MPU_Region_t mpu_table[ZONES_NUM][MPU_REGIONS] = {
//   /* Zone 'zone0' */
//   { 
//     { 
//       .RBAR = ARM_MPU_RBAR(0U, val),
//       .RASR = ARM_MPU_RASR(
//         1U,                 // XN: Execute Never
//         ARM_MPU_AP_FULL,   // Full Access (Priv + Unpriv RW)
//         0U, 0U, 0U, 0U,     // TEX, S, C, B = 0
//         (const uint32_t)comp_info[0].size,  // Size = 128 bytes
//         REGION_ENABLE      // Enable this region
//       )
//     },
//     { .RBAR = ARM_MPU_RBAR(1U, 0U), .RASR = 0U },
//     { .RBAR = ARM_MPU_RBAR(2U, 0U), .RASR = 0U },
//     { .RBAR = ARM_MPU_RBAR(3U, 0U), .RASR = 0U },
//     { .RBAR = ARM_MPU_RBAR(4U, 0U), .RASR = 0U },
//     { .RBAR = ARM_MPU_RBAR(5U, 0U), .RASR = 0U },
//     { .RBAR = ARM_MPU_RBAR(6U, 0U), .RASR = 0U },
//     { .RBAR = ARM_MPU_RBAR(7U, 0U), .RASR = 0U }
//   }
// };


// static ARM_MPU_Region_t mpu_table[NUM_COMPARTMENTS][NUM_COMPARTMENTS];

// int current_comp = -1;

RTMK_DATA
int comp_current=0; /* 0 = privileged context (vStartMPUDemo), transitions happen via switch_view */

RTMK_DATA
int comp_last=0;



void init_mpu();
RTMK_DATA
int selectedFunction = 0;
RTMK_DATA
int arg = 0;
RTMK_DATA
int sret = 0;
RTMK_CODE
void SVC_Handler_Main( unsigned int *svc_args );
//extern unsigned char * _shared_region;
RTMK_CODE void* rtmkcpy(void * dest, void * src, int size);

RTMK_DATA
int shadow_stack[64];

RTMK_DATA 
int sp;

RTMK_DATA
volatile unsigned long long bridge_time;

RTMK_DATA
int goff=0;//Global offset across xcalls for shared memory


RTMK_CODE
int switch_view(int to, int push);

RTMK_DATA
char _shared_region[1024];
#if 0
RTMK_CODE 
void SVC_Handler(void ) {
		__asm(
						"TST lr, #4\n"
						"ITE EQ\n"
						"MRSEQ r0, MSP\n"
						"MRSNE r0, PSP\n"
						"B SVC_Handler_Main\n"
			 );
}

RTMK_CODE
void SVC_Handler_Main( unsigned int *svc_args ) {
		switch(selectedFunction) {
				case 10:
						init_mpu();
						break;
				case 29012:
						SVC_Handler();
						break;
				case 123123123:
						sret = switch_view(123123);
						break;
				case 123123124:
						sret = switch_view(1231233);
						break;
				case 123123126:
						sret = switch_view(1231232);
						break;
				case 1:
						sret = switch_view(123123);
						break;
				case 2:
						sret = switch_view(123123);
						break;
				case 3:
						sret = switch_view(123123);
						break;
				case 4:
						sret = switch_view(123123);
						break;
				case 5:
						sret = switch_view(123123);
						break;
				case 6:
						sret = switch_view(123123);
						break;
				case 7:
						sret = switch_view(123123);
						break;
				case 8:
						sret = switch_view(123123);
						break;
				case 19:
						sret = switch_view(123123);
						break;
				case 123123:
						sret = switch_view(arg);
						break;
				default:
						break;
		}
		return;

}
#endif 

#define STACK_LEN
// RTMK_DATA
// int current=0;

// RTMK_DATA
// int last=-1;



RTMK_CODE
int lastCompart() {
		// return comp_last;
}
typedef void (*xfunction0)(void);
typedef int  (*ifunction0)(void);
typedef int  (*ifunction1i)(int);
typedef int  (*ifunction1p)(void *);
typedef void  (*xfunction1i)(int);
typedef void  (*xfunction1p)(void *);
typedef void  (*xfunction2pi)(void *, int);
typedef void  (*xfunction3pii)(void *, int, int);
typedef void* (*pfunction1i)(int);
typedef void* (*pfunction3iii)(int, int, int);
typedef void* (*pfunction0)();
// typedef void* (*pfunction1p)(void *);
typedef void  (*xfunction2ii)(int, int);
typedef void  (*xfunction2pp)(void *, void *);
typedef void  (*xfunction2ip)(int, void *);
typedef int  (*ifunction2pi)(void *, int);
typedef int  (*ifunction2pp)(void *, void *);
typedef int  (*ifunction2ppi)(void *, void *, int);
typedef int  (*ifunction3pii)(void *, int, int);
typedef int  (*ifunction2ppii)(void *, void *, int, int);
typedef int  (*ifunction2pppi)(void *, void *, void *, int);
typedef int  (*ifunction5iiipi)(int, int, int, void*, int);
typedef int  (*ifunction6ppipip)(void *, void *,int, void*,int, void*);
typedef int  (*ifunction6piiipp)(void *, int, int, int, void*, void *);

// mbed specific
typedef void (*xfunction4piii)(void *, int, int, int);
typedef int (*ifunction3ppi)(void *, void *, int);
typedef int (*ifunction3ppp)(void*, void*, void*);
typedef int (*ifunction1p)(void *);
typedef int (*ifunction5ipipi)(int, int, void*, int, void*);
typedef int (*ifunction5pipip)(void *, int, void *, int, void *);
typedef int (*ifunction3ipi)(int, void *, int);
typedef void (*xfunction2ii)(int, int);
typedef void* (*pfunction1p)(void*);
typedef int (*ifunction4pppi)(void *, void *, void *, int);
typedef int (*ifunction3pii)(void*, int, int);
typedef void (*xfunction1i)(int);
typedef void (*xfunction2pp)(void *, void *);
typedef void* (*pfunction2pp)(void*, void*);
typedef void* (*pfunction2pi)(void*, int);
typedef void* (*pfunction4piii)(void *, int, int, int);
typedef void* (*pfunction3ppi)(void*, void*, int);



#define MK_METHOD
RTMK_CODE void xcall_arg0(int to, xfunction0 funcp) {
		unsigned long long handle;
		BNCHSTART(bridge_time, handle);
		int ret= switch_view(to, 1);
		xfunction0 func = (xfunction0)funcp;
		BNCHEND(bridge_time, handle);
		func();
		BNCHSTART(bridge_time, handle);
		switch_view(ret, 0);
		BNCHEND(bridge_time, handle);
}

// xcalls code for cmsis rtx

RTMK_CODE void xcall_arg4_noidpiii (void *, void *, int, int, int, int, int, int, int) ;
RTMK_CODE int  icall_arg3ppp (int, void*, void*, int, void*, int, void*, int);
RTMK_CODE int icall_arg3_noidppi (void *, void *, int, void *, int, int, int);
RTMK_CODE int icall_arg1_noidp(void *funcp, void *arg0, int size0);
RTMK_CODE int icall_arg5ipipi(int to, void *funcp,
                    int arg0,
                    int arg1,
                    void *arg2, int size2,
                    int arg3, int size3,
                    void *arg4, int size4,
                    int arg5, int size5);
RTMK_CODE int icall_arg5pipip(int to, void *funcp,
                    void *arg0, int size0,
                    int arg1, int size1,
                    void *arg2, int size2,
                    int arg3, int size3,
                    void *arg4, int size4);

RTMK_CODE int icall_arg3ipi(int to, void *funcp,
                  int arg0, int size0,
                  void *arg1, int size1,
                  int arg2, int size2);

RTMK_CODE void xcall_arg2_noidii(void *funcp, int arg0, int size0, int arg1, int size1);
RTMK_CODE void* pcall_arg1_noidp(void *funcp, void *arg0, int size0);


RTMK_CODE int icall_arg4_noidpppi(void *funcp,
                        void *arg0, int size0,
                        void *arg1, int size1,
                        void *arg2, int size2,
                        int arg3, int size3);

RTMK_CODE int icall_arg3_noidpii(void *funcp,
                       void *arg0, int size0,
                       int arg1, int size1,
                       int arg2, int size2);

RTMK_CODE void xcall_arg1_noidi(void *funcp, int arg0, int size0);

RTMK_CODE void xcall_arg2_noidpp(void *funcp,
                       void *arg0, int size0,
                       void *arg1, int size1);

RTMK_CODE void* pcall_arg2_noidpp(void *funcp,
                        void *arg0, int size0,
                        void *arg1, int size1);

RTMK_CODE void* pcall_arg2pi(int to, void *funcp,
                   void *arg0, int size0,
                   int arg1, int size1);

RTMK_CODE void* pcall_arg4_noidpiii(void *funcp,
                          void *arg0, int size0,
                          int arg1, int size1,
                          int arg2, int size2,
                          int arg3, int size3);

RTMK_CODE void* pcall_arg0_noid(void *funcp);

RTMK_CODE void* pcall_arg8_noidppppippp(void *funcp,
                                        void *arg0, int size0,
                                        void *arg1, int size1,
                                        void *arg2, int size2,
                                        void *arg3, int size3,
                                        void *arg4, int size4,
                                        void *arg5, int size5,
                                        void *arg6, int size6,
                                        void *arg7, int size7)
										{}

RTMK_CODE void* pcall_arg2_noidpi(void *funcp,
                                   void *arg0, int size0,
                                   int arg1, int size1)
								   {}

//  TFLM xcalls
RTMK_CODE void *pcall_arg2pp(int a0, void *p1, void *p2, int a3, void *p4, int a5)
{};

RTMK_CODE void icall_arg3pip ()
{

}


// RTMK_CODE void icall_arg3ppp ()
// {

// }

// RTMK_CODE int custom__ZN6tflite22MicroMutableOpResolverILj2EE17AddFullyConnectedERK16TFLMRegistration()
// {

// }


// RTMK_CODE int custom__ZN6tflite22MicroMutableOpResolverILj2EE10AddSoftmaxERK16TFLMRegistration()
// {

// }

// RTMK_CODE int custom__ZNK6tflite5Model7versionEv_table (flatbuffers::Table * this_)
// {
// 	request_privileged_msp();

// 	int val = this_->GetField<unsigned int>(4, 0);


// 	switch_unprivileged_from_privilege();
// 	return val;
// }

// RTMK_CODE int custom__ZNK6tflite5Model7versionEv (tflite::Operator * this_)
// {
// 	request_privileged_msp();
// 	int val = custom__ZNK6tflite5Model7versionEv_table(reinterpret_cast<flatbuffers::Table*>(this_));

// 	switch_unprivileged_from_privilege();
// 	return val;
// }


// RTMK_CODE TfLiteTensor* custom__ZN6tflite16MicroInterpreter5inputEj (tflite::MicroInterpreter * this_, size_t index)
// {
// 	request_privileged_msp();
// 	volatile int i=0;
// 	i++;
// 	TfLiteTensor *input = this_->input(index);

// 	switch_unprivileged_from_privilege();
// 	return input;
// }

// RTMK_CODE TfLiteTensor* custom__ZN6tflite16MicroInterpreter6outputEj (tflite::MicroInterpreter * this_, size_t index)
// {
// 	request_privileged_msp();
// 	volatile int i=0;
// 	i++;

// 	TfLiteTensor *output = this_->input(index);
// 	switch_unprivileged_from_privilege();
// 	return output;
// }

// RTMK_CODE int custom__ZN6tflite16MicroInterpreter6InvokeEv (tflite::MicroInterpreter * this_)
// {
// 	request_privileged_msp();
// 	auto status = this_->Invoke();
// 	volatile int i=0;
// 	i++;

// 	switch_unprivileged_from_privilege();
// 	return status;
// }

// RTMK_CODE int custom__ZN6tflite16MicroInterpreter15AllocateTensorsEv (tflite::MicroInterpreter * this_)
// {
// 	request_privileged_msp();
// 	auto status = this_->AllocateTensors();
// 	volatile int i=0;
// 	i++;

// 	switch_unprivileged_from_privilege();
// 	return status;
// }


// ==============Mbed xcalls start here ==========================
RTMK_CODE void xcall_arg4_noidpiii(void *funcp, void *arg0, int size0,
                                   int arg1, int size1,
                                   int arg2, int size2,
                                   int arg3, int size3) {
    unsigned long long handle;
    BNCHSTART(bridge_time, handle);

    // Calculate starting memory usage
    unsigned long mem_used = (unsigned long)(&_shared_region) + goff;

    // Copy arg0 to shared memory
    void *p0 = rtmkcpy(&_shared_region[goff], arg0, size0);

    // Update goff based on how much memory we just used
    if (size0 > 0)
        mem_used = ((unsigned long)p0 + size0) - mem_used;
    else
        mem_used = 0;

    goff += mem_used;

    // Cast and call the function
    xfunction4piii func = (xfunction4piii)funcp;
    func(p0, arg1, arg2, arg3);

    // Copy shared memory back to original buffer if needed
    goff -= mem_used;
    rtmkcpy(arg0, &_shared_region[goff], size0);

    BNCHEND(bridge_time, handle);
}

RTMK_CODE int icall_arg3ppp(int to,
                            void *funcp,
                            void *arg1, int size1,
                            void *arg2, int size2,
                            void *arg3, int size3)
{
    unsigned long long handle;
    BNCHSTART(bridge_time, handle);

    unsigned long mem_used = (unsigned long)(&_shared_region) + goff;
    unsigned long offset = goff;

    // Copy all pointer args to shared region
    void *p1 = rtmkcpy(&_shared_region[offset], arg1, size1);
    if (size1 > 0) offset += size1;

    void *p2 = rtmkcpy(&_shared_region[offset], arg2, size2);
    if (size2 > 0) offset += size2;

    void *p3 = rtmkcpy(&_shared_region[offset], arg3, size3);
    if (size3 > 0)
        mem_used = ((unsigned long)p3 + size3) - mem_used;
    else if (size2 > 0)
        mem_used = ((unsigned long)p2 + size2) - mem_used;
    else if (size1 > 0)
        mem_used = ((unsigned long)p1 + size1) - mem_used;
    else
        mem_used = 0;

    goff += mem_used;

    int prev = switch_view(to, 1);

    ifunction3ppp func = (ifunction3ppp)funcp;
    BNCHEND(bridge_time, handle);

    int ret = func(p1, p2, p3);

    BNCHSTART(bridge_time, handle);
    goff -= mem_used;

    rtmkcpy(arg1, &_shared_region[goff], size1);
    switch_view(prev, 0);
    BNCHEND(bridge_time, handle);

    return ret;
}



RTMK_CODE int icall_arg1_noidp(void *funcp, void *arg0, int size0)
{
    unsigned long long handle;
    BNCHSTART(bridge_time, handle);

    unsigned long mem_used = (unsigned long)(&_shared_region) + goff;

    // Copy arg0 into shared region
    void *p0 = rtmkcpy(&_shared_region[goff], arg0, size0);

    if (size0 > 0)
        mem_used = ((unsigned long)p0 + size0) - mem_used;
    else
        mem_used = 0;

    goff += mem_used;

    // Switch to the secure context
    int prev = switch_view(1, 1);  // Hardcoded target context 1, can be parameterized

    // Call the real function
    ifunction1p func = (ifunction1p)funcp;
    BNCHEND(bridge_time, handle);

    int realRet = func(p0);

    BNCHSTART(bridge_time, handle);
    goff -= mem_used;

    // Copy back to original buffer
    rtmkcpy(arg0, &_shared_region[goff], size0);
    switch_view(prev, 0);
    BNCHEND(bridge_time, handle);

    return realRet;
}

RTMK_CODE int icall_arg5ipipi(int to, void *funcp,
                              int arg0,
                              int arg1,
                              void *arg2, int size2,
                              int arg3, int size3,
                              void *arg4, int size4,
                              int arg5, int size5)
{
    unsigned long long handle;
    BNCHSTART(bridge_time, handle);

    unsigned long mem_used = (unsigned long)(&_shared_region) + goff;
    unsigned long offset = goff;

    void *p2 = rtmkcpy(&_shared_region[offset], arg2, size2);
    if (size2 > 0) offset += size2;

    void *p4 = rtmkcpy(&_shared_region[offset], arg4, size4);
    if (size4 > 0) offset += size4;

    if (size4 > 0)
        mem_used = ((unsigned long)p4 + size4) - mem_used;
    else if (size2 > 0)
        mem_used = ((unsigned long)p2 + size2) - mem_used;
    else
        mem_used = 0;

    goff += mem_used;

    int prev = switch_view(to, 1);
    ifunction5ipipi func = (ifunction5ipipi)funcp;
    BNCHEND(bridge_time, handle);

    int result = func(arg0, arg1, p2, arg3, p4);

    BNCHSTART(bridge_time, handle);
    goff -= mem_used;

    rtmkcpy(arg2, &_shared_region[goff], size2);
    switch_view(prev, 0);
    BNCHEND(bridge_time, handle);

    return result;
}


RTMK_CODE int icall_arg5pipip(int to, void *funcp,
                              void *arg0, int size0,
                              int arg1, int size1,
                              void *arg2, int size2,
                              int arg3, int size3,
                              void *arg4, int size4)
{
    unsigned long long handle;
    BNCHSTART(bridge_time, handle);

    unsigned long mem_used = (unsigned long)(&_shared_region) + goff;
    unsigned long offset = goff;

    void *p0 = rtmkcpy(&_shared_region[offset], arg0, size0);
    if (size0 > 0) offset += size0;

    void *p2 = rtmkcpy(&_shared_region[offset], arg2, size2);
    if (size2 > 0) offset += size2;

    void *p4 = rtmkcpy(&_shared_region[offset], arg4, size4);
    if (size4 > 0) offset += size4;

    if (size4 > 0)
        mem_used = ((unsigned long)p4 + size4) - mem_used;
    else if (size2 > 0)
        mem_used = ((unsigned long)p2 + size2) - mem_used;
    else if (size0 > 0)
        mem_used = ((unsigned long)p0 + size0) - mem_used;
    else
        mem_used = 0;

    goff += mem_used;

    int prev = switch_view(to, 1);
    ifunction5pipip func = (ifunction5pipip)funcp;
    BNCHEND(bridge_time, handle);

    int result = func(p0, arg1, p2, arg3, p4);

    BNCHSTART(bridge_time, handle);
    goff -= mem_used;

    rtmkcpy(arg0, &_shared_region[goff], size0);
    switch_view(prev, 0);
    BNCHEND(bridge_time, handle);

    return result;
}

RTMK_CODE int icall_arg3ipi(int to, void *funcp,
                            int arg0, int size0,
                            void *arg1, int size1,
                            int arg2, int size2)
{
    unsigned long long handle;
    BNCHSTART(bridge_time, handle);

    unsigned long mem_used = (unsigned long)(&_shared_region) + goff;
    unsigned long offset = goff;

    void *p1 = rtmkcpy(&_shared_region[offset], arg1, size1);
    if (size1 > 0)
        mem_used = ((unsigned long)p1 + size1) - mem_used;
    else
        mem_used = 0;

    goff += mem_used;

    int prev = switch_view(to, 1);
    ifunction3ipi func = (ifunction3ipi)funcp;
    BNCHEND(bridge_time, handle);

    int result = func(arg0, p1, arg2);

    BNCHSTART(bridge_time, handle);
    goff -= mem_used;

    rtmkcpy(arg1, &_shared_region[goff], size1);
    switch_view(prev, 0);
    BNCHEND(bridge_time, handle);

    return result;
}


RTMK_CODE void xcall_arg2_noidii(void *funcp, int arg0, int size0,
                                 int arg1, int size1)
{
    unsigned long long handle;
    BNCHSTART(bridge_time, handle);

    // No pointer copying is needed; just cast and call
    xfunction2ii func = (xfunction2ii)funcp;
    func(arg0, arg1);

    BNCHEND(bridge_time, handle);
}


RTMK_CODE void* pcall_arg1_noidp(void *funcp, void *arg0, int size0)
{
    unsigned long long handle;
    BNCHSTART(bridge_time, handle);

    unsigned long mem_used = (unsigned long)(&_shared_region) + goff;

    // Copy arg0 into shared memory
    void *p0 = rtmkcpy(&_shared_region[goff], arg0, size0);

    if (size0 > 0)
        mem_used = ((unsigned long)p0 + size0) - mem_used;
    else
        mem_used = 0;

    goff += mem_used;

    // Switch to the privileged view
    int prev = switch_view(1, 1);  // hardcoded `to = 1`
    pfunction1p func = (pfunction1p)funcp;
    BNCHEND(bridge_time, handle);

    void *result = func(p0);

    // Restore view and copy memory back if needed
    BNCHSTART(bridge_time, handle);
    goff -= mem_used;
    rtmkcpy(arg0, &_shared_region[goff], size0);
    switch_view(prev, 0);
    BNCHEND(bridge_time, handle);

    return result;
}


RTMK_CODE int icall_arg4_noidpppi(void *funcp,
                                  void *arg0, int size0,
                                  void *arg1, int size1,
                                  void *arg2, int size2,
                                  int arg3, int size3)
{
    unsigned long long handle;
    BNCHSTART(bridge_time, handle);

    unsigned long mem_used = (unsigned long)(&_shared_region) + goff;
    unsigned long offset = goff;

    // Copy three pointer args to shared memory
    void *p0 = rtmkcpy(&_shared_region[offset], arg0, size0);
    if (size0 > 0) offset += size0;

    void *p1 = rtmkcpy(&_shared_region[offset], arg1, size1);
    if (size1 > 0) offset += size1;

    void *p2 = rtmkcpy(&_shared_region[offset], arg2, size2);
    if (size2 > 0)
        mem_used = ((unsigned long)p2 + size2) - mem_used;
    else if (size1 > 0)
        mem_used = ((unsigned long)p1 + size1) - mem_used;
    else if (size0 > 0)
        mem_used = ((unsigned long)p0 + size0) - mem_used;
    else
        mem_used = 0;

    goff += mem_used;

    // Switch to target view
    int prev = switch_view(1, 1);  // `1` is hardcoded view ID
    ifunction4pppi func = (ifunction4pppi)funcp;
    BNCHEND(bridge_time, handle);

    int result = func(p0, p1, p2, arg3);

    BNCHSTART(bridge_time, handle);
    goff -= mem_used;

    // Copy back results
    rtmkcpy(arg0, &_shared_region[goff], size0);
    switch_view(prev, 0);
    BNCHEND(bridge_time, handle);

    return result;
}

RTMK_CODE int icall_arg3_noidpii(void *funcp,
                                 void *arg0, int size0,
                                 int arg1, int size1,
                                 int arg2, int size2)
{
    unsigned long long handle;
    BNCHSTART(bridge_time, handle);

    unsigned long mem_used = (unsigned long)(&_shared_region) + goff;

    // Copy arg0 into shared memory
    void *p0 = rtmkcpy(&_shared_region[goff], arg0, size0);

    if (size0 > 0)
        mem_used = ((unsigned long)p0 + size0) - mem_used;
    else
        mem_used = 0;

    goff += mem_used;

    // Switch context
    int prev = switch_view(1, 1);  // target view hardcoded to 1
    ifunction3pii func = (ifunction3pii)funcp;
    BNCHEND(bridge_time, handle);

    int result = func(p0, arg1, arg2);

    BNCHSTART(bridge_time, handle);
    goff -= mem_used;

    rtmkcpy(arg0, &_shared_region[goff], size0);
    switch_view(prev, 0);
    BNCHEND(bridge_time, handle);

    return result;
}


RTMK_CODE void xcall_arg1_noidi(void *funcp, int arg0, int size0)
{
    unsigned long long handle;
    BNCHSTART(bridge_time, handle);

    xfunction1i func = (xfunction1i)funcp;
    func(arg0);

    BNCHEND(bridge_time, handle);
}

RTMK_CODE void xcall_arg2_noidpp(void *funcp,
                                 void *arg0, int size0,
                                 void *arg1, int size1)
{
    unsigned long long handle;
    BNCHSTART(bridge_time, handle);

    void *p0 = rtmkcpy(&_shared_region[goff], arg0, size0);
    goff += size0;

    void *p1 = rtmkcpy(&_shared_region[goff], arg1, size1);
    goff += size1;

    xfunction2pp func = (xfunction2pp)funcp;
    func(p0, p1);

    goff -= (size0 + size1);  // restore offset
    BNCHEND(bridge_time, handle);
}


RTMK_CODE void* pcall_arg2_noidpp(void *funcp,
                                  void *arg0, int size0,
                                  void *arg1, int size1)
{
    unsigned long long handle;
    BNCHSTART(bridge_time, handle);

    unsigned long mem_used = (unsigned long)(&_shared_region) + goff;
    unsigned long offset = goff;

    // Copy both pointer arguments into the shared region
    void *p0 = rtmkcpy(&_shared_region[offset], arg0, size0);
    if (size0 > 0) offset += size0;

    void *p1 = rtmkcpy(&_shared_region[offset], arg1, size1);
    if (size1 > 0)
        mem_used = ((unsigned long)p1 + size1) - mem_used;
    else if (size0 > 0)
        mem_used = ((unsigned long)p0 + size0) - mem_used;
    else
        mem_used = 0;

    goff += mem_used;

    int prev = switch_view(1, 1);
    pfunction2pp func = (pfunction2pp)funcp;
    BNCHEND(bridge_time, handle);

    void *ret = func(p0, p1);

    BNCHSTART(bridge_time, handle);
    goff -= mem_used;

    rtmkcpy(arg0, &_shared_region[goff], size0);
    switch_view(prev, 0);
    BNCHEND(bridge_time, handle);

    return ret;
}

RTMK_CODE void* pcall_arg2pi(int to, void *funcp,
                              void *arg0, int size0,
                              int arg1, int size1)
{
    unsigned long long handle;
    BNCHSTART(bridge_time, handle);

    unsigned long mem_used = (unsigned long)(&_shared_region) + goff;

    // Copy first argument (object pointer) into shared memory
    void *p0 = rtmkcpy(&_shared_region[goff], arg0, size0);

    if (size0 > 0)
        mem_used = ((unsigned long)p0 + size0) - mem_used;
    else
        mem_used = 0;

    goff += mem_used;

    int prev = switch_view(to, 1);

    pfunction2pi func = (pfunction2pi)funcp;
    BNCHEND(bridge_time, handle);

    void *result = func(p0, arg1);

    BNCHSTART(bridge_time, handle);
    goff -= mem_used;

    rtmkcpy(arg0, &_shared_region[goff], size0);
    switch_view(prev, 0);
    BNCHEND(bridge_time, handle);

    return result;
}


RTMK_CODE void* pcall_arg4_noidpiii(void *funcp,
                                    void *arg0, int size0,
                                    int arg1, int size1,
                                    int arg2, int size2,
                                    int arg3, int size3)
{
    unsigned long long handle;
    BNCHSTART(bridge_time, handle);

    unsigned long mem_used = (unsigned long)(&_shared_region) + goff;

    // Copy arg0 (`this` pointer) into shared memory
    void *p0 = rtmkcpy(&_shared_region[goff], arg0, size0);

    if (size0 > 0)
        mem_used = ((unsigned long)p0 + size0) - mem_used;
    else
        mem_used = 0;

    goff += mem_used;

    int prev = switch_view(1, 1);
    pfunction4piii func = (pfunction4piii)funcp;
    BNCHEND(bridge_time, handle);

    void *result = func(p0, arg1, arg2, arg3);

    BNCHSTART(bridge_time, handle);
    goff -= mem_used;

    rtmkcpy(arg0, &_shared_region[goff], size0);
    switch_view(prev, 0);
    BNCHEND(bridge_time, handle);

    return result;
}


RTMK_CODE void* pcall_arg3_noidppi(void *funcp,
                                   void *arg0, int size0,
                                   void *arg1, int size1,
                                   int arg2, int size2)
{
    unsigned long long handle;
    BNCHSTART(bridge_time, handle);

    unsigned long mem_used = (unsigned long)(&_shared_region) + goff;
    unsigned long offset = goff;

    void *p0 = rtmkcpy(&_shared_region[offset], arg0, size0);
    if (size0 > 0) offset += size0;

    void *p1 = rtmkcpy(&_shared_region[offset], arg1, size1);
    if (size1 > 0)
        mem_used = ((unsigned long)p1 + size1) - mem_used;
    else if (size0 > 0)
        mem_used = ((unsigned long)p0 + size0) - mem_used;
    else
        mem_used = 0;

    goff += mem_used;

    int prev = switch_view(1, 1);
    pfunction3ppi func = (pfunction3ppi)funcp;
    BNCHEND(bridge_time, handle);

    void *ret = func(p0, p1, arg2);

    BNCHSTART(bridge_time, handle);
    goff -= mem_used;

    rtmkcpy(arg0, &_shared_region[goff], size0);
    switch_view(prev, 0);
    BNCHEND(bridge_time, handle);

    return ret;
}


RTMK_CODE void* pcall_arg0_noid(void *funcp)
{
    unsigned long long handle;
    BNCHSTART(bridge_time, handle);

    int prev = switch_view(1, 1);  // privileged context
    pfunction0 func = (pfunction0)funcp;
    BNCHEND(bridge_time, handle);

    void *ret = func();

    BNCHSTART(bridge_time, handle);
    switch_view(prev, 0);
    BNCHEND(bridge_time, handle);

    return ret;
}


// RTMK_CODE int icall_arg3pii(int to, void *funcp,
//                             char *arg0, int size,
//                             int arg1, int size1,
//                             int arg2, int size2) {
//     unsigned long long handle;
//     BNCHSTART(bridge_time, handle);

//     // Copy arg0 to shared memory
//     unsigned long mem_used = (unsigned long)(&_shared_region) + goff;
//     void *pt = rtmkcpy(&_shared_region[goff], arg0, size);

//     // Switch to target view
//     int original_view = switch_view(to, 1);

//     ifunction3pii func = (ifunction3pii)funcp;

//     // Track memory usage
//     if (size > 0)
//         mem_used = ((unsigned long)pt + size) - mem_used;
//     else
//         mem_used = 0;

//     goff += mem_used;
//     BNCHEND(bridge_time, handle);

//     // Call actual function
//     int realRet = func(pt, arg1, arg2);

//     // Switch back and copy data back if needed
//     BNCHSTART(bridge_time, handle);
//     goff -= mem_used;
//     rtmkcpy(arg0, &_shared_region[goff], size);

//     switch_view(original_view, 0);
//     BNCHEND(bridge_time, handle);

//     return realRet;
// }


RTMK_CODE int icall_arg3_noidppi(void *funcp,
                                 void *arg0, int size0,
                                 void *arg1, int size1,
                                 int arg2, int size2) {
    unsigned long long handle;
    BNCHSTART(bridge_time, handle);

    unsigned long mem_used = (unsigned long)(&_shared_region) + goff;
    unsigned long offset = goff;

    // Copy arg0 to shared region
    void *p0 = rtmkcpy(&_shared_region[goff], arg0, size0);
    if (size0 > 0) {
        offset += size0;
    }

    // Copy arg1 to shared region
    void *p1 = rtmkcpy(&_shared_region[offset], arg1, size1);
    if (size1 > 0) {
        offset += size1;
    }

    // Compute used memory
    if (size1 > 0)
        mem_used = ((unsigned long)p1 + size1) - mem_used;
    else if (size0 > 0)
        mem_used = ((unsigned long)p0 + size0) - mem_used;
    else
        mem_used = 0;

    goff += mem_used;

    // Switch to target context
    int ret = switch_view(1, 1);  // 1 = target ID, could be a parameter
    ifunction3ppi func = (ifunction3ppi)funcp;
    BNCHEND(bridge_time, handle);

    int realRet = func(p0, p1, arg2);

    // Restore
    BNCHSTART(bridge_time, handle);
    goff -= mem_used;

    // Copy back to arg0 (if needed)
    rtmkcpy(arg0, &_shared_region[goff], size0);
    switch_view(ret, 0);
    BNCHEND(bridge_time, handle);

    return realRet;
}


// RTMK_CODE void xcall_arg1_noidp(int to, void * funcp, char * arg0, int size) {
// }

RTMK_CODE void xcall_arg1_noidp(void *funcp, void *arg0, int size0)
{
    unsigned long long handle;
    BNCHSTART(bridge_time, handle);

    // Copy arg0 into shared region
    void *p0 = rtmkcpy(&_shared_region[goff], arg0, size0);
    goff += size0;

    // Call the function
    xfunction1p func = (xfunction1p)funcp;
    func(p0);

    // Restore state
    goff -= size0;
    BNCHEND(bridge_time, handle);
}



RTMK_CODE void xcall_arg3ppp(int to, void * funcp, void * arg0, int size, void * arg1, int size1, void * arg2, int size2) {

	while(1)
	{}
}

RTMK_CODE void pcall_arg1p(int to, void * funcp, char * arg0, int size0) {

    unsigned long long handle;
    BNCHSTART(bridge_time, handle);

    unsigned long mem_used = (unsigned long)(&_shared_region) + goff;

    // Copy first argument (object pointer) into shared memory
    void *p0 = rtmkcpy(&_shared_region[goff], arg0, size0);

    if (size0 > 0)
        mem_used = ((unsigned long)p0 + size0) - mem_used;
    else
        mem_used = 0;

    goff += mem_used;

    int prev = switch_view(to, 1);

    pfunction1p func = (pfunction1p)funcp;
    BNCHEND(bridge_time, handle);

    func(p0);

    BNCHSTART(bridge_time, handle);
    goff -= mem_used;

    rtmkcpy(arg0, &_shared_region[goff], size0);
    switch_view(prev, 0);
    BNCHEND(bridge_time, handle);

}

RTMK_CODE void xcall_arg2_noidpi(int to, void * funcp, void* arg0, int size, int arg1, int size1)
{
	while(1)
	{}
}
RTMK_CODE void xcall_arg1i(int to, void * funcp, int arg0, int size) {
		unsigned long long handle;
		BNCHSTART(bridge_time, handle);
		int ret= switch_view(to, 1);
		xfunction1i func = (xfunction1i)funcp;
		BNCHEND(bridge_time, handle);
		func(arg0);
		BNCHSTART(bridge_time, handle);
		switch_view(ret, 0);
		BNCHEND(bridge_time, handle);
}
RTMK_CODE void * pcall_arg0(int to, void * funcp) {
		unsigned long long handle;
		BNCHSTART(bridge_time, handle);
		int ret= switch_view(to,1);
		pfunction0 func = (pfunction0)funcp;
		BNCHEND(bridge_time, handle);
		void * bret = func();
		BNCHSTART(bridge_time, handle);
		switch_view(ret,0);
		BNCHEND(bridge_time, handle);
		return bret;
}
RTMK_CODE void *  pcall_arg3iii(int to, void * funcp, int arg0, int size, int arg1, int size1, int arg2, int size2) {
		unsigned long long handle;
		BNCHSTART(bridge_time, handle);
		int ret= switch_view(to,1);
		pfunction3iii func = (pfunction3iii)funcp;
		BNCHEND(bridge_time, handle);
		void * bret = func(arg0,arg1,arg2);
		BNCHSTART(bridge_time, handle);
		switch_view(ret,0);
		BNCHEND(bridge_time, handle);
		return bret;
}
#ifdef STACK_SWITCH
RTMK_DATA
char stack[19][512];
RTMK_DATA
void * ret_temp_stack;
#endif 

//RTMK_CODE void* rtmkcpy(void * dest, void * src, int size);
RTMK_CODE void * pcall_arg1i(int to, void * funcp, int arg0, int size) {
		unsigned long long handle;
		BNCHSTART(bridge_time, handle);
#ifdef STACK_SWITCH
		int sp = 0;
		int comp = getCompartmentFromAddr(&sp);
#endif 
		int ret;
		pfunction1i func; 
		void * bret;
#ifdef STACK_SWITCH
		if (comp && comp!= to) {
				sp = ((unsigned)&bret -sizeof(bret));
				rtmkcpy(&stack[to][(sizeof(stack)/19) - (36)],((unsigned)&bret -sizeof(bret)), 40);
				/* Move to shared stack */
				//switch_stack();
				asm ("mov sp, %0\n\t"
								:
								: "r" (&stack[to][(sizeof(stack)/19) - 36]));
		}

#endif
		ret= switch_view(to,1);
		func = (pfunction1i)funcp;
		BNCHEND(bridge_time, handle);
		bret = func(arg0);
		BNCHSTART(bridge_time, handle);
#ifdef STACK_SWITCH
		ret_temp_stack = bret;
#endif
		switch_view(ret,0);
#ifdef STACK_SWITCH
		if (comp && comp != to) {
				asm ("mov sp, %0\n\t"
								:
								: "r" (sp));
		}
		bret = ret_temp_stack;
#endif 
		BNCHEND(bridge_time, handle);
		return bret;
}
RTMK_CODE void xcall_arg2ii(int to, void * funcp, int arg0, int size, int arg1, int size1) {
		unsigned long long handle;
		BNCHSTART(bridge_time, handle);
		int ret= switch_view(to,1);
		xfunction2ii func = (xfunction2ii)funcp;
		BNCHEND(bridge_time, handle);
		func(arg0, arg1);
		BNCHSTART(bridge_time, handle);
		switch_view(ret,0);
		BNCHEND(bridge_time, handle);
}

RTMK_CODE void xcall_arg2ip(int to, void * funcp, int arg0, int size, void * arg1, int size1) {
		unsigned long long handle;
		BNCHSTART(bridge_time, handle);
		unsigned long mem_used = (unsigned long) (&_shared_region) + goff;
		void * pt = rtmkcpy((&_shared_region) + goff, arg1, size1);
		int ret= switch_view(to,1);
		xfunction2ip func = (xfunction2ip)funcp;
		if (size1 > 0)
				mem_used = ((unsigned long )pt + size1 - mem_used);
		else 
				mem_used = 0;
		goff += mem_used;
		BNCHEND(bridge_time, handle);
		func(arg0, pt);
		BNCHSTART(bridge_time, handle);
		rtmkcpy(arg1,  (&_shared_region) + goff, size1);
		goff -= mem_used;
		switch_view(ret,0);
		BNCHEND(bridge_time, handle);
}
//__attribute__((always_inline))
RTMK_CODE void* rtmkcpy(void * dest, void * src, int size) {
		if (size<=0) {
				return src;
		}
		// Typecast src and dest addresses to (char *)
		char *csrc = (char *)src;
		char *cdest = (char *)dest;

		// Copy contents of src[] to dest[]
		for (int i=0; i<size; i++)
				cdest[i] = csrc[i];

		return dest;
}
RTMK_CODE void xcall_arg1p(int to, void * funcp, char * arg0, int size) {
        unsigned long long handle;
        BNCHSTART(bridge_time, handle);
        int ret = switch_view(to, 1);
        xfunction1p func = (xfunction1p)funcp;
        BNCHEND(bridge_time, handle);
        func(arg0);
        BNCHSTART(bridge_time, handle);
        switch_view(ret, 0);
        BNCHEND(bridge_time, handle);
}

RTMK_CODE void xcall_arg2pi(int to, void * funcp, char * arg0, int size, int arg1, int size1) {
		unsigned long long handle;
		BNCHSTART(bridge_time, handle);
		unsigned long mem_used = (unsigned long) (&_shared_region) + goff;
		void * pt = rtmkcpy((&_shared_region) + goff, arg0, size);
		int ret= switch_view(to,1);
		xfunction2pi func = (xfunction2pi)funcp;
		if (size > 0)
				mem_used = ((unsigned long )pt + size - mem_used);
		else
				mem_used = 0;
		goff += mem_used;
		BNCHEND(bridge_time, handle);
		func(pt, arg1);
		BNCHSTART(bridge_time, handle);
		rtmkcpy((&_shared_region) + goff, arg0, size);
		goff -= mem_used;
		switch_view(ret,0);
		BNCHEND(bridge_time, handle);
}

RTMK_CODE void xcall_arg3pii(int to, void * funcp, char * arg0, int size, int arg1, int size1, int arg2, int size2) {
		unsigned long long handle;
		BNCHSTART(bridge_time, handle);
		unsigned long mem_used = (unsigned long) (&_shared_region) + goff;
		void * pt = rtmkcpy((&_shared_region) + goff, arg0, size);
		int ret= switch_view(to,1);
		xfunction3pii func = (xfunction3pii)funcp;
		if (size > 0)
				mem_used = ((unsigned long )pt + size - mem_used);
		else
				mem_used = 0;
		goff += mem_used;
		BNCHEND(bridge_time, handle);
		func(pt, arg1, arg2);
		BNCHSTART(bridge_time, handle);
		rtmkcpy(arg0, (&_shared_region) + goff, size);
		goff -= mem_used;
		switch_view(ret,0);
		BNCHEND(bridge_time, handle);
}
RTMK_CODE int icall_arg3pii(int to, void * funcp, char * arg0, int size, int arg1, int size1, int arg2, int size2) {
		unsigned long long handle;
		BNCHSTART(bridge_time, handle);
		unsigned long mem_used = (unsigned long) (&_shared_region) + goff;
		void * pt = rtmkcpy((&_shared_region) + goff, arg0, size);
		int ret= switch_view(to,1);
		ifunction3pii func = (ifunction3pii)funcp;
		if (size > 0)
				mem_used = ((unsigned long )pt + size - mem_used);
		else
				mem_used = 0;
		goff += mem_used;
		BNCHEND(bridge_time, handle);
		int realRet = func(pt, arg1, arg2);
		BNCHSTART(bridge_time, handle);
		goff -= mem_used;
		rtmkcpy(arg0, (&_shared_region) + goff, size);
		switch_view(ret,0);
		BNCHEND(bridge_time, handle);
		return realRet;
}
RTMK_CODE void xcall_arg2pp(int to, void * funcp, char * arg0, int size, char * arg1, int size1) {
		unsigned long long handle;
		BNCHSTART(bridge_time, handle);
		unsigned long mem_used = (unsigned long) (&_shared_region) + goff;
		void *pt  = rtmkcpy((&_shared_region) + goff, arg0, size);
		int offset = 0;
		if (size>0) 
				offset += size;
		void *pt1 = rtmkcpy((void *)((unsigned int)&_shared_region + offset), arg1, size1);
		if (size1 > 0)
				mem_used = ((unsigned long )pt1 + size1 - mem_used);
		else {
				if (size > 0)
						mem_used = ((unsigned long )pt + size - mem_used);
				else 
						mem_used =0; // Both pointers are opaque 
		}

		goff += mem_used;
		int ret= switch_view(to,1);
		xfunction2pp func = (xfunction2pp)funcp;
		BNCHEND(bridge_time, handle);
		func(pt, pt1);
		BNCHSTART(bridge_time, handle);
		rtmkcpy(arg1, (void *)((unsigned int)&_shared_region + offset), size1);
		rtmkcpy(arg0, (&_shared_region) + goff, size);
		goff -= mem_used;
		switch_view(ret,0);
		BNCHEND(bridge_time, handle);
}

RTMK_CODE int switch_view_svc(int param) {
		selectedFunction = 123123;
		arg = param;
		// prvPortStartFirstTask
		__asm volatile (
						" cpsie i               \n"/* Globally enable interrupts. */
						" cpsie f               \n"
						" dsb                   \n"
						" isb                   \n"
						" svc 0                 \n"
						" nop                   \n"
					   );
		int ret = sret;
		return ret;
}
RTMK_CODE int icall_arg0(int to, ifunction0  funcp) {
		unsigned long long handle;
#ifdef MK_METHOD
		BNCHSTART(bridge_time, handle);
		int ret= switch_view(to,1);
		ifunction0 func = reinterpret_cast<ifunction0>(funcp);
		BNCHEND(bridge_time, handle);
		int retReal = func();
		BNCHSTART(bridge_time, handle);
		switch_view(ret,0);
		BNCHEND(bridge_time, handle);
		return retReal;
#elif defined(AC_METHOD)
		BNCHSTART(bridge_time, handle);
		int ret = switch_view_svc(to);
		BNCHEND(bridge_time, handle);
		int retReal = func();
		BNCHSTART(bridge_time, handle);
		switch_view_svc(ret);
		BNCHEND(bridge_time, handle);
		return retReal;
#endif
}

RTMK_CODE int icall_arg1i(int to, void * funcp, int arg0, int size) {
		unsigned long long handle;
		BNCHSTART(bridge_time, handle);
		int ret= switch_view(to,1);
		ifunction1i func = reinterpret_cast<ifunction1i>(funcp);
		BNCHEND(bridge_time, handle);
		int retReal = func(arg0);
		BNCHSTART(bridge_time, handle);
		switch_view(ret,0);
		BNCHEND(bridge_time, handle);
		return retReal;
}

RTMK_CODE int icall_arg1i_noid(void * func, int arg0, int size) {
		return icall_arg1i(getCompartmentFromAddr((unsigned int)func), func, arg0, size);
}

RTMK_CODE int icall_arg1p(int to, void * funcp, void * arg0, int size) {
		unsigned long long handle;
		BNCHSTART(bridge_time, handle);
		unsigned long mem_used = 0;
		void * pt = rtmkcpy((&_shared_region ) + goff, arg0, size);
		if (size > 0)
				mem_used = size;
		int ret= switch_view(to,1);
		/* TODO: How to copy? */
		ifunction1p func = reinterpret_cast<ifunction1p>(funcp);	
		goff += mem_used;
		BNCHEND(bridge_time, handle);
		int retReal = func(pt);
		BNCHSTART(bridge_time, handle);
		rtmkcpy(arg0, (&_shared_region ) + goff, size);
		goff -= mem_used;
		switch_view(ret,0);
		BNCHEND(bridge_time, handle);
		return retReal;
}
RTMK_CODE int icall_arg1p_noid(void * func, void * arg0, int size) {
		return icall_arg1p(getCompartmentFromAddr((unsigned int)func), func, arg0, size);
}
RTMK_CODE int getCompartmentFromAddr(unsigned int addr) {
		unsigned long long handle;
		BNCHSTART(bridge_time, handle);
		//int ret;
		int compartment = 0;
		/* TODO: Binary search would be far superior here */
#if 1
		for (int i =0; i< (total_secs); i++) {
				if (addr > comp_info[i].start && addr < comp_info[i].end) {
						compartment = i;
						break;
				}
				if (addr > comp_info[i].dstart && addr < comp_info[i].dend) {
						compartment = i;
						break;
				}
		}
#endif 
		BNCHEND(bridge_time, handle);
		return compartment;
}

RTMK_CODE int icall_arg0_noid(ifunction0 func) {
		return icall_arg0(getCompartmentFromAddr((unsigned int)func), func);
}

RTMK_CODE void xcall_arg0_noid(xfunction0 func) {
		xcall_arg0(getCompartmentFromAddr((unsigned int)func), func);
}

RTMK_CODE void xcall_arg1p_noid(char * function, void * arg0, int size) {
		xcall_arg1p(getCompartmentFromAddr((unsigned int)function), function, (char *)arg0, size);
}


RTMK_CODE int icall_arg2pi(int to, void * funcp, void * arg0, int size, int arg1, int size1) {
		unsigned long long handle;
		BNCHSTART(bridge_time, handle);
		unsigned long mem_used = (unsigned long) (&_shared_region) + goff;
		void * pt = rtmkcpy((&_shared_region) + goff, arg0, size);
		int ret= switch_view(to,1);
		ifunction2pi fun = reinterpret_cast<ifunction2pi>(funcp);
		if (size > 0)
				mem_used = ((unsigned long )pt + size - mem_used);
		else
				mem_used = 0;
		goff += mem_used;
		BNCHEND(bridge_time, handle);
		int retReal = fun(pt, arg1);
		BNCHSTART(bridge_time, handle);
		rtmkcpy(arg0, (&_shared_region) + goff, size);
		goff -= mem_used;
		switch_view(ret,0);
		BNCHEND(bridge_time, handle);
		return retReal;
}

RTMK_CODE int icall_arg2pp(int to, void * funcp, void * arg0, int size, void * arg1, int size1) {
		unsigned long long handle;
		BNCHSTART(bridge_time, handle);
		unsigned long mem_used = (unsigned long) (&_shared_region) + goff;
		void *pt  = rtmkcpy((&_shared_region) + goff, arg0, size);
		int offset = goff;
		if (size>0)
				offset += size;
		void *pt1 = rtmkcpy((void *)((unsigned int)&_shared_region + offset), arg1, size1);
		if (size1 > 0)
				mem_used = ((unsigned long )pt1 + size1 - mem_used);
		else {
				if (size>0) {
						mem_used = ((unsigned long )pt + size - mem_used);
				}
				else {
						mem_used =0;
				}
		}
		goff += mem_used;
		int ret= switch_view(to,1);
		ifunction2pp fun = reinterpret_cast<ifunction2pp>(funcp);
		BNCHEND(bridge_time, handle);
		int retReal = fun(pt,pt1);
		BNCHSTART(bridge_time, handle);
		rtmkcpy(arg1, (void *)((unsigned int)&_shared_region + offset), size1);
        rtmkcpy(arg0, (&_shared_region) + goff, size);
		goff -= mem_used;
		switch_view(ret,0);
		BNCHEND(bridge_time, handle);
		return retReal;
}

RTMK_CODE int icall_arg3ppi(int to, void * funcp, void * arg0, int size, void * arg1, int size1, int arg2, int size2) {
		unsigned long long handle;
		BNCHSTART(bridge_time, handle);
		int offset = goff;
		unsigned long mem_used = (unsigned long) (&_shared_region) + goff;
		void * p0 =rtmkcpy((&_shared_region) +goff, arg0, size);
		if (size>0)
				offset += size;
		void * p1 =rtmkcpy((void *)((unsigned int)&_shared_region + offset), arg1, size1);
		if (size1 > 0)
				mem_used = ((unsigned long )p1 + size1 - mem_used);
		else {
				if (size > 0) {
						mem_used = ((unsigned long )p0 +size - mem_used);
				} else {
						mem_used = 0;
				}
		}
		goff += mem_used;
		int ret= switch_view(to,1);
		ifunction2ppi fun = reinterpret_cast<ifunction2ppi>(funcp);
		BNCHEND(bridge_time, handle);
		int retReal = fun(p0,p1, arg2);
		BNCHSTART(bridge_time, handle);
		goff -= mem_used;
		rtmkcpy(arg1, (void *)((unsigned int)&_shared_region + offset), size1);
        rtmkcpy(arg0, (&_shared_region) + goff, size);
		switch_view(ret,0);
		BNCHEND(bridge_time, handle);
		return retReal;
}

RTMK_CODE int icall_arg4ppii(int to, void * funcp, void * arg0, int size, void * arg1, int size1, int arg2, int size2, int arg3, int size3) {
		unsigned long long handle;
		BNCHSTART(bridge_time, handle);
		unsigned long mem_used = (unsigned long) (&_shared_region) + goff;
		void *pt  = rtmkcpy((&_shared_region) + goff, arg0, size);
		int offset = goff;
		if (size>0)
				offset += size;
		void *pt1 = rtmkcpy((void *)((unsigned int)&_shared_region + offset), arg1, size1);

		if (size1 > 0)
				mem_used = ((unsigned long )pt1 + size1 - mem_used);
		else {
				if (size > 0) {
						mem_used = ((unsigned long )pt + size - mem_used);
				} else {
						mem_used = 0;
				}
		}
		goff += mem_used;
		int ret= switch_view(to,1);
		ifunction2ppii fun = reinterpret_cast<ifunction2ppii>(funcp);
		BNCHEND(bridge_time, handle);
		int retReal = fun(pt, pt1, arg2, arg3);
		BNCHSTART(bridge_time, handle);
		rtmkcpy(arg1, (void *)((unsigned int)&_shared_region + offset), size1);
        rtmkcpy(arg0, (&_shared_region) + goff, size);
		goff -= mem_used;
		switch_view(ret,0);
		BNCHEND(bridge_time, handle);
		return retReal;
}

RTMK_CODE int icall_arg4pppi(int to, void * funcp, void * arg0, int size, void * arg1, int size1, void * arg2, int size2, int arg3, int size3) {
		unsigned long long handle;
		BNCHSTART(bridge_time, handle);
		int offset = goff;
		unsigned long mem_used = (unsigned long) (&_shared_region) + goff;
		void * p0 =rtmkcpy((&_shared_region) + goff, arg0, size);
		if (size>0)
				offset += size;
		void * p1 =rtmkcpy((void *)((unsigned int)&_shared_region + offset), arg1, size1);
		if (size1>0)
				offset += size1;
		void * p2 =rtmkcpy((void *)((unsigned int)&_shared_region + offset), arg2, size2);

		if (size2 > 0)
				mem_used = ((unsigned long )p2 + size2 - mem_used);
		else {
				if (size1>0) {
						mem_used = ((unsigned long )p1 + size1 - mem_used);
				} else if (size > 0) {
						mem_used = ((unsigned long )p0 + size - mem_used);
				}
				else {
						mem_used = 0;
				}
		}
		goff += mem_used;
		int ret= switch_view(to,1);
		ifunction2pppi fun = reinterpret_cast<ifunction2pppi>(funcp);
		BNCHEND(bridge_time, handle);
		int retReal = fun(p0, p1, p2, arg3);
		BNCHSTART(bridge_time, handle);
		goff -= mem_used;
		switch_view(ret,0);
		while(1); // Fix
		BNCHEND(bridge_time, handle);
		return retReal;
}

RTMK_CODE int icall_arg6ppipip(int to, void * funcp, void * arg0, int size, void * arg1, int size1, int arg2, int size2, void * arg3, int size3, 
				int arg4, int size4, void * arg5, int size5) {
		unsigned long long handle;
		BNCHSTART(bridge_time, handle);
		unsigned long mem_used = (unsigned long) (&_shared_region) + goff;
		int offset = goff;
		void * p0 =rtmkcpy((&_shared_region) + goff, arg0, size);
		unsigned long offset_ptr = (unsigned long) (&_shared_region) + goff;
		unsigned long offset_size = 0;
		if (size>0) {
				offset += size;
				offset_ptr = (unsigned long)p0;
				offset_size = size;
		}
		void * p1 =rtmkcpy((void *)((unsigned int)&_shared_region + offset), arg1, size1);
		if (size1>0) {
				offset += size1;
				offset_ptr = (unsigned long)p1;
				offset_size = size1;
		}
		void * p2 =rtmkcpy((void *)((unsigned int)&_shared_region + offset), arg3, size3);
		if (size3>0) {
				offset += size3;
				offset_ptr = (unsigned long)p2;
				offset_size = size3;
		}
		void * p3 =rtmkcpy((void *)((unsigned int)&_shared_region + offset), arg5, size5);

		if (size5 > 0)
				mem_used = ((unsigned long )p3 + size5 - mem_used);
		else 
				mem_used = ((unsigned long )offset_ptr +offset_size - mem_used);
		goff += mem_used;
		int ret= switch_view(to,1);
		ifunction6ppipip fun = reinterpret_cast<ifunction6ppipip>(funcp);
		BNCHEND(bridge_time, handle);
		int retReal = fun(p0, p1, arg2, p2, arg4, p3);
		BNCHSTART(bridge_time, handle);
		while(1); //fix
		goff -= mem_used;
		switch_view(ret,0);
		BNCHEND(bridge_time, handle);
		return retReal;
}
RTMK_CODE int icall_arg6piiipp(int to, void * funcp, void * arg0, int size, int arg1, int size1, int arg2, int size2, int arg3, int size3,
				void* arg4, int size4, void * arg5, int size5) {
		unsigned long long handle;
		BNCHSTART(bridge_time, handle);
		unsigned long mem_used = (unsigned long) (&_shared_region) + goff;
		int offset = goff;
		unsigned long offset_ptr = (unsigned long) (&_shared_region) + goff;
		unsigned long offset_size = 0;
		void * p0 =rtmkcpy((&_shared_region) + goff, arg0, size);
		if (size>0) {
				offset += size;
				offset_ptr = (unsigned long)p0;
				offset_size = size;
		}
		void * p4 =rtmkcpy((void *)((unsigned int)&_shared_region + offset), arg4, size4);
		if (size4>0) {
				offset += size4;
				offset_ptr = (unsigned long)p4;
				offset_size = size4;
		}
		void * p5 =rtmkcpy((void *)((unsigned int)&_shared_region + offset), arg5, size5);
		if (size5 > 0)
				mem_used = ((unsigned long )p5 + size5 - mem_used);
		else
				mem_used = ((unsigned long )offset_ptr + offset_size - mem_used);
		goff += mem_used;
		int ret= switch_view(to,1);
		ifunction6piiipp fun = reinterpret_cast<ifunction6piiipp>(funcp);
		BNCHEND(bridge_time, handle);
		int retReal = fun(p0, arg1, arg2, arg3, p4, p5);
		BNCHSTART(bridge_time, handle);
		while(1); //Fix
		goff -= mem_used;
		switch_view(ret,0);
		BNCHEND(bridge_time, handle);
		return retReal;
}
RTMK_CODE int icall_arg5iiipi(int to, void * funcp, int arg0, int size, int arg1, int size1, int arg2, int size2, void * arg3, int size3,
				int arg4, int size4) {
		unsigned long long handle;
		BNCHSTART(bridge_time, handle);
		unsigned long mem_used = (unsigned long) (&_shared_region) + goff;
		void * p2 =rtmkcpy((&_shared_region) + goff, arg3, size3);
		if (size3 > 0)
				mem_used = ((unsigned long )p2 + size3 - mem_used);
		else
				mem_used = ((unsigned long )p2 - mem_used);
		goff += mem_used;
		int ret= switch_view(to,1);
		ifunction5iiipi fun = reinterpret_cast<ifunction5iiipi>(funcp);
		BNCHEND(bridge_time, handle);
		int retReal = fun(arg0, arg1, arg2, p2, arg4);
		BNCHSTART(bridge_time, handle);
		while(1); //Fix
		goff -= mem_used;
		switch_view(ret,0);
		BNCHEND(bridge_time, handle);
		return retReal;
}

RTMK_CODE 
unsigned int mystrlen(const char *str) {
		int i =0;
		while(*str++!= '\0') {
				i++;
		}
		return i;
}

		RTMK_CODE
int mymemcmp(const void *m1, const void *m2, unsigned int n)
{
		const char *c1 = static_cast<const char*>(m1);
		const char *c2 = static_cast<const char*>(m2);

		if (!n) {
				return 0;
		}

		while ((--n > 0) && (*c1 == *c2)) {
				c1++;
				c2++;
		}

		return *c1 - *c2;
}

RTMK_DATA unsigned long stmpF;
RTMK_DATA unsigned long i;
RTMK_CODE
void write_number(unsigned long stmp) {
		stmpF += stmp; 
		i++;
		if (i == 4) while(1);
}

#define CURRENT     ((volatile unsigned int *)0xE000E018) 
RTMK_CODE unsigned long long curr_stamp(){
		unsigned long stmp = 0;
#ifdef FREERTOS
		//  __asm volatile ("cpsid i");
		unsigned long add = (0x4e1f - *CURRENT);
		unsigned long tick = xTaskGetTickCount();
		unsigned long stmp = ((tick * 0x4e1f) + add);
		//  __asm volatile ("cpsie i");
#endif 
		return stmp;
}


/* Read back and print all 8 MPU regions over UART. Call after USART init. */
RTMK_CODE void rtmk_dump_mpu(void) {
    dbg_str("\r\n[MPU] Startup region dump:\r\n");
    for (uint32_t i = 0; i < 8; i++) {
        MPU->RNR  = i;
        uint32_t rbar = MPU->RBAR;
        uint32_t rasr = MPU->RASR;
        uint32_t base = rbar & 0xFFFFFFE0;
        uint32_t en   = rasr & 1;
        uint32_t sz   = (rasr >> 1) & 0x1F;
        uint32_t ap   = (rasr >> 24) & 0x7;
        uint32_t xn   = (rasr >> 28) & 0x1;
        dbg_str("  R"); dbg_dec(i); dbg_str(": ");
        if (!en) { dbg_str("DISABLED\r\n"); continue; }
        dbg_str("base="); dbg_hex(base);
        dbg_str(" size_enc="); dbg_dec(sz);
        dbg_str(" AP="); dbg_dec(ap);
        dbg_str(xn ? " XN" : " XA");
        dbg_str("\r\n");
    }
}

RTMK_CODE
void RTMK_Reprogram_MPU_Region_for_Compartment(int comp) {
    if (comp == 0) {
        /* Returning to privileged kernel — disable compartment regions */
        HAL_MPU_DisableRegion(MPU_REGION_NUMBER6);
        HAL_MPU_DisableRegion(MPU_REGION_NUMBER7);
        dbg_str("[MPU] comp=0 (kernel): R6/R7 disabled\r\n");
        return;
    }

    /* comp_info is indexed directly by compartment number */
    SEC_INFO *info = &comp_info[comp];

    /* autogen.py guarantees power-of-2 sizes and natural alignment for all compartment sections */
    uint32_t code_base = (uint32_t)info->start;
    uint8_t  code_enc  = (uint8_t)(__builtin_ctz((uint32_t)info->size) - 1);
    uint32_t data_base = (uint32_t)info->dstart;
    uint8_t  data_enc  = (info->dsize != 0) ? (uint8_t)(__builtin_ctz((uint32_t)info->dsize) - 1) : 4;

    dbg_str("[MPU] comp="); dbg_dec(comp);
    dbg_str(" code@"); dbg_hex((uint32_t)info->start);
    dbg_str(" sz="); dbg_dec((uint32_t)info->size);
    dbg_str(" R6base="); dbg_hex(code_base); dbg_str(" enc="); dbg_dec(code_enc);
    dbg_str("\r\n       data@"); dbg_hex((uint32_t)info->dstart);
    dbg_str(" dsz="); dbg_dec((uint32_t)info->dsize);
    dbg_str(" R7base="); dbg_hex(data_base); dbg_str(" enc="); dbg_dec(data_enc);
    dbg_str("\r\n");

    /*
     * Write MPU registers directly instead of via HAL_MPU_ConfigRegion.
     * If a base address has bit 4 set, writing it to RBAR sets the VALID flag,
     * which would redirect the write to region 0 instead of R6/R7.
     * autogen.py aligns compartment section bases to their own size (>= 32-byte),
     * so bits[4:0] are always 0 and the VALID flag cannot be accidentally set.
     */

    /* Region 6: Compartment Code — Unprivileged R/O, executable */
    MPU->RNR  = MPU_REGION_NUMBER6;
    MPU->RBAR = code_base;   /* aligned, VALID bit = 0 */
    MPU->RASR = ((uint32_t)0                     << MPU_RASR_XN_Pos)   |   /* XN=0: executable */
                ((uint32_t)MPU_REGION_PRIV_RO_URO << MPU_RASR_AP_Pos)  |
                ((uint32_t)MPU_TEX_LEVEL0         << MPU_RASR_TEX_Pos) |
                ((uint32_t)0                      << MPU_RASR_S_Pos)   |   /* not shareable */
                ((uint32_t)1                      << MPU_RASR_C_Pos)   |   /* cacheable */
                ((uint32_t)0                      << MPU_RASR_B_Pos)   |
                ((uint32_t)code_enc               << MPU_RASR_SIZE_Pos)|
                MPU_RASR_ENABLE_Msk;

    /* Region 7: Compartment Data — Unprivileged R/W, no execute (disabled if dsize=0) */
    MPU->RNR  = MPU_REGION_NUMBER7;
    if (info->dsize == 0) {
        MPU->RBAR = 0;
        MPU->RASR = 0;
        dbg_str("       R7 disabled (dsize=0)\r\n");
    } else {
        MPU->RBAR = data_base;
        MPU->RASR = ((uint32_t)1                    << MPU_RASR_XN_Pos)   |   /* XN=1: no execute */
                    ((uint32_t)MPU_REGION_FULL_ACCESS << MPU_RASR_AP_Pos) |
                    ((uint32_t)MPU_TEX_LEVEL0         << MPU_RASR_TEX_Pos)|
                    ((uint32_t)0                      << MPU_RASR_S_Pos)  |
                    ((uint32_t)1                      << MPU_RASR_C_Pos)  |
                    ((uint32_t)0                      << MPU_RASR_B_Pos)  |
                    ((uint32_t)data_enc               << MPU_RASR_SIZE_Pos)|
                    MPU_RASR_ENABLE_Msk;
    }

    __DSB();
    __ISB();
}

RTMK_CODE
int switch_view(int to, int push) {
    /*
     * Raise to privileged MSP first — must come before any debug print or MPU
     * write, because this can be called from unprivileged compartment code where
     * USART and SCS registers are not in any MPU region.
     */
    request_privileged_msp();

    dbg_str("[SV] comp "); dbg_dec(comp_current);
    dbg_str(" -> "); dbg_dec(to); dbg_str("\r\n");

    int last = comp_current;
    comp_last = last;
    comp_current = to;

    /*
     * TODO: privilege downgrade to unprivileged requires implementing the
     * MSP→PSP transition in assembly (not mid-C-function) so the return
     * address is on the right stack.  Until then, compartments stay
     * privileged and rely on MPU region reprogramming for isolation.
     */
    if (to != 0)
    {
        RTMK_Reprogram_MPU_Region_for_Compartment(to);
        switch_to_unprivileged_msp();
    }

    return last;
}

}
// void _init () {}
// void _kill () {}
// void _getpid () {}