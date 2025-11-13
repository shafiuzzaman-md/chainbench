#pragma once
#include "cb_io.h"

/* Enable per-binary via CFLAGS (no effect unless defined) */
#ifdef CHAINBENCH_INTERPOSE_FGETS
  #undef fgets
  #define fgets cb_fgets_log
#endif

#ifdef CHAINBENCH_INTERPOSE_GETENV
  #undef getenv
  #define getenv(name) cb_getenv_log(name)  /* returns heap copy */
#endif

#ifdef CHAINBENCH_INTERPOSE_FREAD
  #undef fread
  #define fread(ptr,sz,n,fp) cb_fread_log(ptr,sz,n,fp)
#endif
