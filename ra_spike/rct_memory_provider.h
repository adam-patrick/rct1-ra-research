#ifndef RCT_MEMORY_PROVIDER_H
#define RCT_MEMORY_PROVIDER_H

#include <stdint.h>
#include <sys/types.h>

typedef struct rct_memory_provider {
  pid_t pid;
  uintptr_t module_base;
  int identity_valid;
} rct_memory_provider_t;

typedef struct rct_state_snapshot {
  uint16_t guests;
  uint16_t park_rating;
  uint32_t cash_raw;
  int guests_valid;
  int park_rating_valid;
  int cash_valid;
} rct_state_snapshot_t;

int rct_memory_provider_open(rct_memory_provider_t* provider);
uint32_t rct_memory_provider_read(const rct_memory_provider_t* provider,
                                  uint32_t logical_address, uint8_t* buffer,
                                  uint32_t num_bytes);
int rct_memory_provider_read_state(const rct_memory_provider_t* provider,
                                   rct_state_snapshot_t* snapshot);

#endif
