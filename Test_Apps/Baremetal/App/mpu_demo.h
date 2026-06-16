#ifndef __MPU_DEMO_H__
#define __MPU_DEMO_H__

/**
 * @brief Creates all the tasks for MPU demo.
 *
 * The MPU demo creates 2 unprivileged tasks - One of which has Read Only access
 * to a shared memory region while the other has Read Write access. The task
 * with Read Only access then tries to write to the shared memory which results
 * in a Memory fault. The fault handler examines that it is the fault generated
 * by the task with Read Only access and if so, it recovers from the fault
 * greacefully by moving the Program Counter to the next instruction to the one
 * which generated the fault. If any other memory access violation occurs, the
 * fault handler will get stuck in an infinite loop.
 */
void vStartMPUDemo( void );

#endif /* __MPU_DEMO_H__ */