#include "rct_memory_provider.h"

#include <dirent.h>
#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/uio.h>

#define GUESTS_OFFSET 0x69c9f8U
#define PARK_RATING_OFFSET 0x69ce64U
#define CASH_OFFSET 0x69c590U

static int is_decimal(const char* text) {
  if (text == NULL || *text == '\0') return 0;
  while (*text != '\0') {
    if (*text < '0' || *text > '9') return 0;
    ++text;
  }
  return 1;
}

static pid_t find_rct_pid(void) {
  DIR* directory = opendir("/proc");
  struct dirent* entry;
  if (directory == NULL) return (pid_t)-1;
  while ((entry = readdir(directory)) != NULL) {
    char path[512];
    char name[64];
    FILE* file;
    if (!is_decimal(entry->d_name)) continue;
    snprintf(path, sizeof(path), "/proc/%s/comm", entry->d_name);
    file = fopen(path, "r");
    if (file == NULL) continue;
    name[0] = '\0';
    if (fgets(name, sizeof(name), file) == NULL) name[0] = '\0';
    fclose(file);
    name[strcspn(name, "\r\n")] = '\0';
    if (strcmp(name, "RCT.EXE") == 0) {
      closedir(directory);
      return (pid_t)strtol(entry->d_name, NULL, 10);
    }
  }
  closedir(directory);
  return (pid_t)-1;
}

static uintptr_t find_module_base(pid_t pid) {
  char path[128];
  char line[1024];
  FILE* file;
  snprintf(path, sizeof(path), "/proc/%d/maps", (int)pid);
  file = fopen(path, "r");
  if (file == NULL) return 0;
  while (fgets(line, sizeof(line), file) != NULL) {
    uintptr_t start;
    uintptr_t end;
    uintptr_t file_offset;
    char permissions[8];
    char mapped_path[512];
    mapped_path[0] = '\0';
    if (sscanf(line, "%" SCNxPTR "-%" SCNxPTR " %7s %" SCNxPTR " %*s %*s %511s",
               &start, &end, permissions, &file_offset, mapped_path) >= 4 &&
        strstr(line, "/RCT.EXE") != NULL) {
      fclose(file);
      return start - file_offset;
    }
  }
  fclose(file);
  return 0;
}

int rct_memory_provider_open(rct_memory_provider_t* provider) {
  if (provider == NULL) return 0;
  provider->pid = find_rct_pid();
  provider->module_base = provider->pid > 0 ? find_module_base(provider->pid) : 0;
  return provider->pid > 0 && provider->module_base != 0;
}

uint32_t rct_memory_provider_read(const rct_memory_provider_t* provider,
                                  uint32_t logical_address, uint8_t* buffer,
                                  uint32_t num_bytes) {
  struct iovec local;
  struct iovec remote;
  ssize_t bytes_read;
  if (provider == NULL || buffer == NULL || num_bytes == 0 ||
      provider->pid <= 0 || provider->module_base == 0) return 0;
  local.iov_base = buffer;
  local.iov_len = num_bytes;
  remote.iov_base = (void*)(provider->module_base + logical_address);
  remote.iov_len = num_bytes;
  bytes_read = process_vm_readv(provider->pid, &local, 1, &remote, 1, 0);
  return bytes_read > 0 ? (uint32_t)bytes_read : 0;
}

int rct_memory_provider_read_state(const rct_memory_provider_t* provider,
                                   rct_state_snapshot_t* snapshot) {
  struct iovec local[3];
  struct iovec remote[3];
  ssize_t bytes_read;
  size_t total_size;

  if (snapshot == NULL) return 0;
  memset(snapshot, 0, sizeof(*snapshot));
  if (provider == NULL || provider->pid <= 0 || provider->module_base == 0) return 0;

  local[0].iov_base = &snapshot->guests;
  local[0].iov_len = sizeof(snapshot->guests);
  local[1].iov_base = &snapshot->park_rating;
  local[1].iov_len = sizeof(snapshot->park_rating);
  local[2].iov_base = &snapshot->cash_raw;
  local[2].iov_len = sizeof(snapshot->cash_raw);

  remote[0].iov_base = (void*)(provider->module_base + GUESTS_OFFSET);
  remote[0].iov_len = sizeof(snapshot->guests);
  remote[1].iov_base = (void*)(provider->module_base + PARK_RATING_OFFSET);
  remote[1].iov_len = sizeof(snapshot->park_rating);
  remote[2].iov_base = (void*)(provider->module_base + CASH_OFFSET);
  remote[2].iov_len = sizeof(snapshot->cash_raw);

  total_size = sizeof(snapshot->guests) + sizeof(snapshot->park_rating) +
               sizeof(snapshot->cash_raw);
  bytes_read = process_vm_readv(provider->pid, local, 3, remote, 3, 0);
  if (bytes_read != (ssize_t)total_size) return 0;

  snapshot->guests_valid = 1;
  snapshot->park_rating_valid = 1;
  snapshot->cash_valid = 1;
  return 1;
}
