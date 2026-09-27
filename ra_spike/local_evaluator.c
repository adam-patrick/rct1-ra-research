#include "local_evaluator.h"

#include "rc_runtime.h"
#include "rc_runtime_types.h"

#include <stdio.h>

typedef struct local_eval_context {
  const rct_state_snapshot_t* snapshot;
  int triggered;
} local_eval_context_t;

static uint32_t RC_CCONV local_peek(uint32_t address, uint32_t num_bytes, void* userdata) {
  const local_eval_context_t* context = (const local_eval_context_t*)userdata;
  uint32_t value = 0;
  if (context == NULL || context->snapshot == NULL) return 0;

  /* Synthetic addresses are deliberately local to this experiment. */
  if (address == 0x0000U && num_bytes == 2U && context->snapshot->guests_valid)
    return context->snapshot->guests;
  if (address == 0x0001U && num_bytes == 2U && context->snapshot->park_rating_valid)
    return context->snapshot->park_rating;
  if (address == 0x0002U && num_bytes == 4U && context->snapshot->cash_valid)
    return context->snapshot->cash_raw;

  (void)value;
  return 0;
}

static void RC_CCONV local_event(const rc_runtime_event_t* event) {
  if (event == NULL) return;
  printf("local_event_type=%u id=%u\n", (unsigned)event->type, event->id);
  if (event->type == RC_RUNTIME_EVENT_ACHIEVEMENT_TRIGGERED)
    puts("local_evaluation=triggered");
}

int local_evaluator_run(const rct_state_snapshot_t* snapshot) {
  rc_runtime_t runtime;
  local_eval_context_t context;
  int result;

  if (snapshot == NULL || !snapshot->guests_valid || !snapshot->park_rating_valid)
    return 0;

  context.snapshot = snapshot;
  context.triggered = 0;
  rc_runtime_init(&runtime);

  /* Test-only condition: Guests >= 1 and Park Rating >= 1. */
  result = rc_runtime_activate_achievement(&runtime, 1,
      "0x 0000>=1_0x 0001>=1", NULL, 0);
  if (result != RC_OK) {
    rc_runtime_destroy(&runtime);
    return 0;
  }

  printf("local_activation_result=%d initial_state=%u\n", result,
         (unsigned)rc_runtime_get_achievement(&runtime, 1)->state);
  /* This isolated experiment starts from a loaded-game active state. */
  rc_runtime_get_achievement(&runtime, 1)->state = RC_TRIGGER_STATE_ACTIVE;

  rc_runtime_do_frame(&runtime, local_event, local_peek, &context, NULL);
  rc_runtime_destroy(&runtime);
  return 1;
}
