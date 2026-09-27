CC ?= cc
# rcheevos v12.1.0 uses unsigned long long in a few portable arithmetic paths.
CFLAGS ?= -std=c99 -D_GNU_SOURCE -D_POSIX_C_SOURCE=200809L -Wall -Wextra -Werror -O2

RACHEEVOS_DIR := deps/rcheevos
INCLUDES := -I$(RACHEEVOS_DIR)/include -I$(RACHEEVOS_DIR)/src
RACHEEVOS_SOURCES := \
	$(RACHEEVOS_DIR)/src/rc_client.c \
	$(RACHEEVOS_DIR)/src/rc_compat.c \
	$(RACHEEVOS_DIR)/src/rc_util.c \
	$(RACHEEVOS_DIR)/src/rc_version.c \
	$(RACHEEVOS_DIR)/src/rhash/md5.c \
	$(wildcard $(RACHEEVOS_DIR)/src/rcheevos/*.c) \
	$(wildcard $(RACHEEVOS_DIR)/src/rapi/*.c)

.PHONY: all clean test

all: rc_client_spike

rc_client_spike: rc_client_spike.c local_evaluator.c local_evaluator.h rct_memory_provider.c rct_memory_provider.h $(RACHEEVOS_SOURCES)
	$(CC) $(CFLAGS) $(INCLUDES) -o $@ rc_client_spike.c local_evaluator.c rct_memory_provider.c $(RACHEEVOS_SOURCES) -lm

test: rc_client_spike
	@output=$$(./rc_client_spike --lifecycle); \
	printf '%s\n' "$$output"; \
	printf '%s\n' "$$output" | grep -q 'created=1 hardcore=0 network=disabled credentials=absent'; \
	printf '%s\n' "$$output" | grep -q 'processed_frames=3 destroyed=1'

clean:
	rm -f rc_client_spike
