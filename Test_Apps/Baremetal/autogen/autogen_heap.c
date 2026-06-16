#include <stdint.h>
#include <stddef.h>
uint8_t* ucHeap[] = {NULL,NULL,NULL}; 
uint8_t ucHeapInitFlag[3]; 
size_t xNextFreeByte [3]; 
size_t heapSize [3] = {0,0,0}; 
