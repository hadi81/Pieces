#ifndef __RTMK_H
#define __RTMK_H
#include <stdint.h>
#include <inttypes.h>
#include <stddef.h>
#define RTMK_CODE   __attribute__((section(".rtmkcode"))) extern
#define PRIV   __attribute__((section(".privileged_functions"))) extern
#define DRIVER_CODE __attribute__((section(".driver"))) static inline 
#define RTMK_CODE_INTERNAL __attribute__((section(".rtmkcode")))  static inline
#define INIT       __attribute__((section(".init")))
#define RTMK_DATA  __attribute__((section(".rtmkdata")))
#define OPAQUE	    __attribute__ ((xcallsize("opaque")))
#define STRING		__attribute__ ((xcallsize("string")))
#define SHARED_DATA __attribute__((section(".shared_data")))
#define UTILITY 	__attribute__((xcallsize("utility")))
#define KERNEL		__attribute__((section(".kernel")))
#define KERNEL_THREAD __attribute__((section(".kernelthread")))
#define OWNER(ownerlist...) __attribute((section("olist:" #ownerlist )))
#define PINNED(PID)	__attribute((section("pinned:" #PID )))
#define CLONE		__attribute((section("clone")))
#define SECRET		__attribute((section("secret")))
#define CUSTOM_BRIDGE		__attribute((xcallsize("custom_bridge")))
// #define CUSTOM_BRIDGE		__attribute((xcallsize("custom_bridge")))

#ifdef __cplusplus
extern "C"
{
#endif

#include "hack.h"

typedef struct {
        int start;	//Start of code section
        int size;	//Size of code section
        int dstart;	//Start of data section
        int dsize;	//Size of data section
		int end;	//End of code
		int dend;	//End of data
		int devstart;	//Start of dev region
		int devsize;	//Size of dev region
		int devend;	//End of dev region
} SEC_INFO;


extern unsigned long section_loads[];
extern unsigned long end_loads[];
extern int total_secs;
#define LINKER_SYM(i) \
		extern unsigned long * _scsection##i;\
		extern unsigned long * _szcsection##i;\
		extern unsigned long * _sosection##i##data;\
		extern unsigned long * _szosection##i;\
		extern unsigned long * _sosection##i##datal;\
		extern unsigned long * _eosection##i##data;

typedef struct __attribute__((packed)) ContextStateFrame {
  uint32_t r0;
  uint32_t r1;
  uint32_t r2;
  uint32_t r3;
  uint32_t r12;
  uint32_t lr;
  uint32_t return_address;
  uint32_t xpsr;
} sContextStateFrame;


// #define DWT_CTRL        (*(volatile unsigned int *)0xE0001000)
// #define DWT_COMP0       (*(volatile unsigned int *)0xE0001020)
// #define DWT_MASK0       (*(volatile unsigned int *)0xE0001024)

// #define DWT_COMP1       (*(volatile unsigned int *)0xE0001030)
// #define DWT_MASK1       (*(volatile unsigned int *)0xE0001034)
// #define DWT_FUNCTION1   (*(volatile unsigned int *)0xE0001038)

// #define DWT_FUNCTION0   (*(volatile unsigned int *)0xE0001028)
// #define DEMCR           (*(volatile unsigned int *)0xE000EDFC)
// #define DHCSR           (*(volatile unsigned int *)0xE000EDF0)
// #define DFSR            (*(volatile unsigned int *)0xE000ED30)
// //DEBUG RANGE: 0xE000EDF0 - 0xE000EEFF
// //MPU RANGE: 0xE000ED90 - 0xE000EDEF
// #define MON_EN          (1<<16)
// #define C_DEBUGEN       (1<<0)
// #define TRCENA          (1<<24)
// #define MON_PEND        (1<<17)

PRIVILEGED_DATA
extern  SEC_INFO  comp_info[];
extern int code_base;
extern int code_size;
extern int data_base;
extern int data_size;

// todo switch_view
// RTMK_DATA
// extern int comp_current;

// RTMK_DATA
// extern int comp_last;

RTMK_CODE void switch_to_unprivileged(void);

// PMSP to UPSP
RTMK_CODE void switch_to_unprivileged_psp(void);

RTMK_CODE void request_privileged(void);

RTMK_CODE void request_privileged_msp(void);

RTMK_CODE void switch_unprivileged_from_privilege(void);

RTMK_CODE
void RTMK_MPU_Config(void);

RTMK_CODE
int lastCompart();

RTMK_CODE
void rtmk_init();

#define PUSH 1
RTMK_CODE
int switch_view(int to, int push);
RTMK_CODE unsigned long long curr_stamp();

RTMK_CODE int getCompartmentFromAddr(unsigned int addr);
#ifdef NORTMK
#define RTMK_TRAMPOLINE_ISR(func,suffix)\
void func(void)
#else 
#define RTMK_TRAMPOLINE_ISR(func,suffix) 							  \
__attribute__((section(".rtmkcode")))								  \
void func##suffix();												  \
void func(void){													  \
		int ret =switch_view(getCompartmentFromAddr(func##suffix),1); \
        func##suffix();												  \
        switch_view(ret, 0); 										  \
}																	  \
void func##suffix()										
#endif 
extern int bnch_init;
#ifdef MICROBNCH_DEBUG
static inline void BNCHSTART(unsigned long long counter, unsigned long long handle) \
{										\
	if (bnch_init)handle = curr_stamp();				\
}										\

static inline void  BNCHEND(unsigned long long counter,unsigned long long handle) 			
{												\
		if (bnch_init) {unsigned long long temp= curr_stamp();		\
		if (temp > handle) {counter = counter + (temp - handle);}}	\
}
#elif defined(MICROBNCH)
#define BNCHSTART(counter, handle) \
{                                       \
    if (bnch_init)handle = curr_stamp();                \
}                                       \

#define BNCHEND(counter,handle)             \
{                                               \
        if (bnch_init) {unsigned long long temp= curr_stamp();      \
        if (temp > handle) {counter = counter + (temp - handle);}  else while(1);}\
}
#else
#define BNCHSTART(counter, handle) (void)handle
#define BNCHEND(counter,handle) (void)handle
#endif /* MICROBNCH */

#ifdef __cplusplus
}
#endif
#endif 
