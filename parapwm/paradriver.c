#include <pthread.h>
#include <unistd.h>
#include <signal.h>
#include <stdio.h>
#include "paradriver.h"
#include <parapin.h>

static int pinlevels[25] = {-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1};
static pthread_t pinthreads[25] = {NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL};

const long PAUSE_NANO = 100000;

void *do_pin_thread(struct pwm_thread_info *info) {
    printf("%d = %d\n", info->pinNum, pinlevels[info->pinNum]);
    while (1) {
        int pin = info->pinNum, level = pinlevels[info->pinNum];
        if (level == 0) {
            struct timespec full_cycle;
            full_cycle.tv_sec = 0;
            full_cycle.tv_nsec = PAUSE_NANO * 256;
            clear_pin(LP_PIN[pin]);
            nanosleep(&full_cycle, NULL);
        }
        else if (level >= 255) {
            struct timespec full_cycle;
            full_cycle.tv_sec = 0;
            full_cycle.tv_nsec = PAUSE_NANO * 256;
            set_pin(LP_PIN[pin]);
            nanosleep(&full_cycle, NULL);
        }
        else {
            struct timespec pause;
            pause.tv_sec = 0;
            pause.tv_nsec = PAUSE_NANO;
            int i = 0;
            while (i < 256) {
                if (i == level) clear_pin(LP_PIN[pin]);
                else if (i == 0) set_pin(LP_PIN[pin]);
                nanosleep(&pause, NULL);
                i++;
            }
        }
    }
    free(info);
    return NULL;
}

int setPin(int pin, int value) {
    pinlevels[pin] = value;
    if (pinthreads[pin] == NULL) {
        struct pwm_thread_info *info = malloc(sizeof(struct pwm_thread_info));
        info->pinNum = pin;
        pthread_create(&pinthreads[pin], NULL, do_pin_thread, info);
    }
    return pin;
}

int main(const int argc, const char *argv) {
    if (pin_init_user(LPT1))
        fprintf(stderr, "oh snap\n");
    /*sleep(1);
    setPin(2, 127);
    sleep(1);
    setPin(4, 20);
    sleep(10);*/
    struct pwm_thread_info info;
    info.pinNum = 2;
    pinlevels[2] = 255;
    do_pin_thread(&info);
}
