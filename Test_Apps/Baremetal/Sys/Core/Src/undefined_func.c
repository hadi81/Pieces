#include <stdint.h>

void  _read(void) {}
void  _write(void) {}
void  _lseek(void) {}
void  _close(void) {}
void  _fstat(void) {}
void  _isatty(void) {}

void __attribute__((noreturn)) _exit(int status) {
    (void)status;
    while (1) { }
}

void  _kill(void) {}
void  _getpid(void) {}
void _init(void) {}
void _fini(void) {}


extern uint32_t _srtmkdata2, _ertmkdata, _lrtmkdata;
extern uint32_t _sshared_data, _eshared_data, _lshared_data;

void copy_rtmkdata(void) {
    uint32_t *src = &_lrtmkdata;
    uint32_t *dst = &_srtmkdata2;
    while (dst < &_ertmkdata) {
        *dst++ = *src++;
    }
}

void copy_shared_data(void) {
    uint32_t *src = &_lshared_data;
    uint32_t *dst = &_sshared_data;
    while (dst < &_eshared_data)
        *dst++ = *src++;
}

#include "monitor.h"

void copy_compartment_data(void) {
    for (int i = 0; i < total_secs; i++) {
        uint32_t *src      = (uint32_t *)section_loads[i];
        uint32_t *dst      = (uint32_t *)comp_info[i].dstart;
        uint32_t *data_end = (uint32_t *)end_loads[i];

        while (dst < data_end)
            *dst++ = *src++;

        uint32_t *bss_end = (uint32_t *)((uint32_t)comp_info[i].dstart
                                         + comp_info[i].dsize);
        while (dst < bss_end)
            *dst++ = 0;
    }
}