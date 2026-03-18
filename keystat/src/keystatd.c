#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <errno.h>
#include <signal.h>
#include <sys/epoll.h>
#include <sys/stat.h>
#include <linux/input.h>
#include <libevdev/libevdev.h>
#include <pthread.h>
#include <time.h>

#define MAX_DEVICES 32
#define STATS_FILE_PATH ".local/share/keystat/stats.json"
#define SAVE_INTERVAL 30
#define MAX_KEYS 768

typedef struct {
    int fd;
    struct libevdev *dev;
    char name[256];
} device_t;

static volatile int running = 1;
static int key_counts[MAX_KEYS];
static pthread_mutex_t stats_mutex = PTHREAD_MUTEX_INITIALIZER;
static char stats_file[512];
static int pipefd[2];

static const int MODIFIER_KEYS[] = {
    KEY_LEFTCTRL, KEY_RIGHTCTRL,
    KEY_LEFTSHIFT, KEY_RIGHTSHIFT,
    KEY_LEFTALT, KEY_RIGHTALT,
    KEY_LEFTMETA, KEY_RIGHTMETA,
};
#define NUM_MODIFIERS (sizeof(MODIFIER_KEYS) / sizeof(MODIFIER_KEYS[0]))

static int modifier_state[NUM_MODIFIERS];

static int get_modifier_index(int code) {
    for (size_t i = 0; i < NUM_MODIFIERS; i++) {
        if (MODIFIER_KEYS[i] == code) return i;
    }
    return -1;
}

static void signal_handler(int sig) {
    (void)sig;
    running = 0;
    if (write(pipefd[1], "x", 1) == -1) {}
}

static void create_daemon() {
    if (fork() != 0) exit(0);
    setsid();
    if (fork() != 0) exit(0);
    chdir("/");
    umask(0);
    
    close(STDIN_FILENO);
    close(STDOUT_FILENO);
    close(STDERR_FILENO);
}

static char* get_stats_file_path() {
    const char *home = getenv("HOME");
    if (!home) home = "/root";
    
    static char path[512];
    snprintf(path, sizeof(path), "%s/%s", home, STATS_FILE_PATH);
    
    char *last_slash = strrchr(path, '/');
    if (last_slash) {
        *last_slash = '\0';
        mkdir(path, 0755);
        *last_slash = '/';
    }
    
    return path;
}

static void load_stats() {
    FILE *fp = fopen(stats_file, "r");
    if (!fp) return;
    
    char line[1024];
    while (fgets(line, sizeof(line), fp)) {
        char key_name[128];
        int count;
        if (sscanf(line, "\"%127[^\"]\": %d", key_name, &count) == 2) {
            int key_code = libevdev_event_code_from_name(EV_KEY, key_name);
            if (key_code >= 0 && key_code < MAX_KEYS) {
                key_counts[key_code] = count;
            }
        }
    }
    fclose(fp);
}

static void save_stats() {
    FILE *fp = fopen(stats_file, "w");
    if (!fp) return;
    
    fprintf(fp, "{\n");
    fprintf(fp, "  \"keys\": {\n");
    
    pthread_mutex_lock(&stats_mutex);
    int first = 1;
    for (int i = 0; i < MAX_KEYS; i++) {
        if (key_counts[i] > 0) {
            const char *key_name = libevdev_event_code_get_name(EV_KEY, i);
            if (key_name) {
                fprintf(fp, "%s    \"%s\": %d", first ? "" : ",\n", key_name, key_counts[i]);
                first = 0;
            }
        }
    }
    pthread_mutex_unlock(&stats_mutex);
    
    fprintf(fp, "\n  },\n");
    fprintf(fp, "  \"last_updated\": %ld\n", (long)time(NULL));
    fprintf(fp, "}\n");
    
    fclose(fp);
}

static void* save_thread(void *arg) {
    (void)arg;
    while (running) {
        sleep(SAVE_INTERVAL);
        if (running) {
            save_stats();
        }
    }
    save_stats();
    return NULL;
}

static int open_keyboard_device(const char *path) {
    int fd = open(path, O_RDONLY | O_NONBLOCK);
    if (fd < 0) return -1;
    
    struct libevdev *dev = NULL;
    int rc = libevdev_new_from_fd(fd, &dev);
    if (rc < 0) {
        close(fd);
        return -1;
    }
    
    if (!libevdev_has_event_type(dev, EV_KEY)) {
        libevdev_free(dev);
        close(fd);
        return -1;
    }
    
    return fd;
}

static void scan_devices(device_t *devices, int *device_count) {
    char path[64];
    *device_count = 0;
    
    for (int i = 0; i < MAX_DEVICES; i++) {
        snprintf(path, sizeof(path), "/dev/input/event%d", i);
        
        int fd = open_keyboard_device(path);
        if (fd < 0) continue;
        
        struct libevdev *dev;
        libevdev_new_from_fd(fd, &dev);
        
        devices[*device_count].fd = fd;
        devices[*device_count].dev = dev;
        
        const char *name = libevdev_get_name(dev);
        if (name) {
            strncpy(devices[*device_count].name, name, sizeof(devices[*device_count].name) - 1);
        } else {
            devices[*device_count].name[0] = '\0';
        }
        
        fprintf(stderr, "Monitoring: %s (%s)\n", path, devices[*device_count].name);
        (*device_count)++;
    }
}

int main(int argc, char *argv[]) {
    int daemon_mode = 1;
    
    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "-f") == 0) {
            daemon_mode = 0;
        }
    }
    
    if (daemon_mode) {
        create_daemon();
    }
    
    signal(SIGINT, signal_handler);
    signal(SIGTERM, signal_handler);
    
    if (pipe(pipefd) == -1) return 1;
    
    strcpy(stats_file, get_stats_file_path());
    load_stats();
    
    pthread_t save_tid;
    pthread_create(&save_tid, NULL, save_thread, NULL);
    
    device_t devices[MAX_DEVICES];
    int device_count = 0;
    scan_devices(devices, &device_count);
    
    if (device_count == 0) {
        fprintf(stderr, "No keyboard devices found!\n");
        if (daemon_mode) exit(1);
    }
    
    int epoll_fd = epoll_create1(0);
    if (epoll_fd < 0) return 1;
    
    struct epoll_event ev;
    ev.events = EPOLLIN;
    
    for (int i = 0; i < device_count; i++) {
        ev.data.fd = devices[i].fd;
        epoll_ctl(epoll_fd, EPOLL_CTL_ADD, devices[i].fd, &ev);
    }
    
    ev.data.fd = pipefd[0];
    epoll_ctl(epoll_fd, EPOLL_CTL_ADD, pipefd[0], &ev);
    
    while (running) {
        int n = epoll_wait(epoll_fd, &ev, 1, 1000);
        if (n <= 0) continue;
        
        if (ev.data.fd == pipefd[0]) {
            char buf[64];
            read(pipefd[0], buf, sizeof(buf));
            break;
        }
        
        for (int d = 0; d < device_count; d++) {
            if (devices[d].fd == ev.data.fd) {
                struct input_event ev;
                int rc = libevdev_next_event(devices[d].dev, LIBEVDEV_READ_FLAG_NORMAL, &ev);
                
                while (rc == LIBEVDEV_READ_STATUS_SUCCESS || rc == LIBEVDEV_READ_STATUS_SYNC) {
                    if (ev.type == EV_KEY && ev.code < MAX_KEYS) {
                        int mod_idx = get_modifier_index(ev.code);
                        
                        if (mod_idx >= 0) {
                            if (ev.value == 1) {
                                modifier_state[mod_idx] = 1;
                            } else if (ev.value == 0) {
                                modifier_state[mod_idx] = 0;
                            }
                        } else if (ev.value == 1) {
                            pthread_mutex_lock(&stats_mutex);
                            key_counts[ev.code]++;
                            for (size_t i = 0; i < NUM_MODIFIERS; i++) {
                                if (modifier_state[i]) {
                                    key_counts[MODIFIER_KEYS[i]]++;
                                }
                            }
                            pthread_mutex_unlock(&stats_mutex);
                        }
                    }
                    rc = libevdev_next_event(devices[d].dev, LIBEVDEV_READ_FLAG_NORMAL, &ev);
                }
                break;
            }
        }
    }
    
    for (int i = 0; i < device_count; i++) {
        close(devices[i].fd);
        libevdev_free(devices[i].dev);
    }
    close(epoll_fd);
    close(pipefd[0]);
    close(pipefd[1]);
    
    pthread_join(save_tid, NULL);
    
    return 0;
}
