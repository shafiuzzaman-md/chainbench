/* ChainState: shared execution state for chaining vulnerable programs */
#pragma once
#include <stdint.h>
#include <string.h>


typedef struct {
  uintptr_t fp;              /* control slot for chaining */
  unsigned char msg[128];    /* attacker-controlled bytes (input) */
  unsigned msg_len;
  unsigned flags;            /* optional trigger bits */
} chain_state_t;

static inline void cs_reset(chain_state_t *s){ memset(s, 0, sizeof(*s)); }
static inline void cs_set_msg(chain_state_t *s, const void *p, unsigned n){
  if (n > sizeof(s->msg)) n = sizeof(s->msg);
  memcpy(s->msg, p, n); s->msg_len = n;
}

typedef int (*stage_fn_t)(chain_state_t *s);
static inline int run_stage(stage_fn_t f, chain_state_t *s){ return f(s); }

