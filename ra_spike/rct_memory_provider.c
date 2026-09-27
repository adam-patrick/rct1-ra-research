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
  if (snapshot == NULL) return 0;
  memset(snapshot, 0, sizeof(*snapshot));
  snapshot->guests_valid = rct_memory_provider_read(provider, GUESTS_OFFSET,
      (uint8_t*)&snapshot->guests, sizeof(snapshot->guests)) == sizeof(snapshot->guests);
  snapshot->park_rating_valid = rct_memory_provider_read(provider, PARK_RATING_OFFSET,
      (uint8_t*)&snapshot->park_rating, sizeof(snapshot->park_rating)) == sizeof(snapshot->park_rating);
  snapshot->cash_valid = rct_memory_provider_read(provider, CASH_OFFSET,
      (uint8_t*)&snapshot->cash_raw, sizeof(snapshot->cash_raw)) == sizeof(snapshot->cash_raw);
  return snapshot->guests_valid || snapshot->park_rating_valid || snapshot->cash_valid;
}
