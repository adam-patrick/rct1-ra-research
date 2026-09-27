#include "rc_client.h"
#include "local_evaluator.h"
#include "rct_memory_provider.h"

#include <inttypes.h>
#include <stdio.h>
#include <string.h>

/*
 * This executable intentionally has no network implementation.  It proves
 * that the pinned rc_client can be created, configured, serviced, and
 * destroyed without credentials, an RCT process, or achievement data.
 */

static const rct_memory_provider_t* active_provider;

static uint32_t RC_CCONV spike_read_memory(uint32_t address, uint8_t* buffer,
                                           uint32_t num_bytes, rc_client_t* client) {
  (void)client;
  return rct_memory_provider_read(active_provider, address, buffer, num_bytes);
}

static void RC_CCONV spike_server_call(const rc_api_request_t* request,
                                       rc_client_server_callback_t callback,
                                       void* callback_data, rc_client_t* client) {
  (void)request;
  (void)callback;
  (void)callback_data;
  (void)client;
  fprintf(stderr, "spike: network disabled; request rejected safely\n");
}

static void RC_CCONV spike_log(const char* message, const rc_client_t* client) {
  (void)client;
  fprintf(stderr, "rcheevos: %s\n", message ? message : "(null)");
}

static void RC_CCONV spike_event(const rc_client_event_t* event, rc_client_t* client) {
  (void)client;
  if (event != NULL) {
    printf("event type=%u\n", event->type);
  }
}

int main(int argc, char** argv) {
  rc_client_t* client;
  rct_memory_provider_t provider;
  rct_state_snapshot_t snapshot;
  int rct_state_mode = 0;
  int local_eval_mode = 0;
  int frames = 3;
  int i;

  if (argc > 1) {
    if (strcmp(argv[1], "--rct-state") == 0) {
      rct_state_mode = 1;
    } else if (strcmp(argv[1], "--local-eval") == 0) {
      local_eval_mode = 1;
    } else if (strcmp(argv[1], "--lifecycle") != 0 || argc > 2) {
      fprintf(stderr, "usage: %s [--lifecycle|--rct-state|--local-eval]\n", argv[0]);
      return 2;
    }
  }

  if (rct_state_mode || local_eval_mode) {
    if (!rct_memory_provider_open(&provider)) {
      fprintf(stderr, "spike: RCT.EXE not found or module mapping unavailable\n");
      return 3;
    }
    active_provider = &provider;
    if (!rct_memory_provider_read_state(&provider, &snapshot)) {
      fprintf(stderr, "spike: validated state fields unavailable\n");
      return 4;
    }
    printf("rct_pid=%d module_base=0x%" PRIxPTR " read_only=1\n",
           (int)provider.pid, provider.module_base);
    if (snapshot.guests_valid) printf("guests=%" PRIu16 "\n", snapshot.guests);
    if (snapshot.park_rating_valid) printf("park_rating=%" PRIu16 "\n", snapshot.park_rating);
    if (snapshot.cash_valid) printf("cash_raw=%" PRIu32 "\n", snapshot.cash_raw);
    puts("snapshot_coherent=1");
    if (local_eval_mode) {
      if (!local_evaluator_run(&snapshot)) {
        fprintf(stderr, "spike: local evaluator setup failed\n");
        return 6;
      }
      puts("local_evaluation=complete network=disabled unlock_submission=disabled");
      return 0;
    }
    client = rc_client_create(spike_read_memory, spike_server_call);
    if (client == NULL) {
      fprintf(stderr, "spike: rc_client_create failed for RCT provider\n");
      return 5;
    }
    rc_client_set_allow_background_memory_reads(client, 0);
    rc_client_set_hardcore_enabled(client, 0);
    rc_client_do_frame(client);
    rc_client_idle(client);
    rc_client_destroy(client);
    puts("rc_client_bridge=initialized network=disabled");
    return 0;
  }

  active_provider = NULL;
  client = rc_client_create(spike_read_memory, spike_server_call);
  if (client == NULL) {
    fprintf(stderr, "spike: rc_client_create failed\n");
    return 1;
  }

  rc_client_enable_logging(client, RC_CLIENT_LOG_LEVEL_INFO, spike_log);
  rc_client_set_event_handler(client, spike_event);
  rc_client_set_allow_background_memory_reads(client, 0);
  rc_client_set_hardcore_enabled(client, 0);

  printf("created=1 hardcore=%d network=disabled credentials=absent\n",
         rc_client_get_hardcore_enabled(client));

  for (i = 0; i < frames; ++i) {
    rc_client_do_frame(client);
  }
  rc_client_idle(client);

  printf("processed_frames=%d destroyed=1\n", frames);
  rc_client_destroy(client);
  return 0;
}
