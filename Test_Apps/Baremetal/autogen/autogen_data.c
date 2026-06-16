#include <monitor.h> 
LINKER_SYM(0);
LINKER_SYM(1);
LINKER_SYM(2);
PRIVILEGED_DATA SEC_INFO comp_info[] = {{(int)&_scsection0,(int) &_szcsection0,(int) &_sosection0data, (int) &_szosection0, 0,0,0,0,0},
{(int)&_scsection1,(int) &_szcsection1,(int) &_sosection1data, (int) &_szosection1, 0,0,0,0,0},
{(int)&_scsection2,(int) &_szcsection2,(int) &_sosection2data, (int) &_szosection2, 0,0,0,0,0}};
PRIVILEGED_DATA unsigned long section_loads[] = {
(long)&_sosection0datal,
(long)&_sosection1datal,
(long)&_sosection2datal};
PRIVILEGED_DATA unsigned long end_loads[] = {
(long)&_eosection0data,
(long)&_eosection1data,
(long)&_eosection2data};
PRIVILEGED_DATA int code_base;PRIVILEGED_DATA int code_size;PRIVILEGED_DATA int data_base;PRIVILEGED_DATA int data_size;PRIVILEGED_DATA int total_secs = sizeof(comp_info) / sizeof(comp_info[0]);