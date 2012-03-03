#include <termios.h>
#include <fcntl.h>
#include <sys/ioctl.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <ctype.h>
#include <pthread.h>
#include <errno.h>
#include <parapin.h>

static int fd = 0;

static volatile int CYCLE[10] = {0, 0, 0, 0, 0, 0, 0, 0, 0, 0};

static pthread_t pwmthread = (pthread_t)0;

void *do_pwm(void *arg) {
    struct timespec pause;
    pause.tv_sec = 0;
    pause.tv_nsec = 25000;
    while (1) {
        int i = 0;
        while (i < 256) {
            int j;
            for (j = 2; j < 10; j++) {
                if (i == 0 && CYCLE[j] > 0) {set_pin(LP_PIN[j]);}
                if (i == CYCLE[j] && CYCLE[j] < 255) {clear_pin(LP_PIN[j]);}
            }
            nanosleep(&pause, NULL);
            i++;
        }
    }
    pthread_exit(NULL);
}

int got_input() {
    struct timeval tv;
    fd_set in_set;
    tv.tv_sec = tv.tv_usec = 0;
    FD_ZERO(&in_set);
    FD_SET(STDIN_FILENO, &in_set);
    select(STDIN_FILENO+1, &in_set, NULL, NULL, &tv);
    return FD_ISSET(STDIN_FILENO, &in_set);
}

/*int main(int argc, char **argv) {
    if (pin_init_user(LPT1)) {
        puts("aw snap");
        exit(-1);
    }
    pin_output_mode(LP_DATA_PINS);

    set_pin(LP_PIN[2]);
    sleep(2);
    clear_pin(LP_PIN[2]);
    sleep(2);

    pthread_t thread;
    if (pthread_create(&thread, NULL, do_pwm, NULL))
        fputs("can't make thread\n", stderr);
    
    char pin[2]; int cycle;
    while ((pin[0] = getchar())) {
        pin[1] = 0;
        char *num = malloc(20);
        size_t size = 20;
        if (! getline(&num, &size, stdin)) { fputs("problem?\n", stderr); break; }
        cycle = strtol(num, NULL, 10);
        if (errno == EINVAL) { fputs("problem?\n", stderr); break; }
        int pinnum = atoi(pin);
        if (pinnum >= 2 && pinnum <= 9) {
            CYCLE[pinnum] = cycle;
            printf("%1d = %d\n", pinnum, cycle);
        }
    }
    pthread_exit(NULL);
}*/

int setPin(int pin, int cycle) {
    if (pin >= 2 && pin <= 9) {
        CYCLE[pin] = cycle;
    }
    printf("paradriver: %1d = %d\n", pin, cycle);
    if ((int)pwmthread == 0)
        if (pthread_create(&pwmthread, NULL, do_pwm, NULL))
            fputs("can't make thread\n", stderr);
    puts("done");
}
