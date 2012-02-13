#include <stdio.h>
#include <unistd.h>
#include <sys/io.h>

#define PORT 0x378

int main(int argc, char *const argv[], char *const envp[]) {
    uid_t realuid = getuid();
    setuid(0);
    if (ioperm(PORT, 3, 1) < 0)
        fprintf(stderr, "problem?");
    setuid(realuid);
    execve(&argv[1], argv + 2, envp);
}
