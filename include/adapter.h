#pragma once
#include "chain_state.h"

typedef struct {
  const char *id;       
  stage_fn_t  run;       
  const char *about;   
} adapter_t;

typedef const adapter_t* (*get_adapter_fn)(void);
