#pragma once
#include "cb_io.h"

/* Define these via CFLAGS (per item or globally) to interpose gracefully */
#ifdef CHAINBENCH_INTERPOSE_FGETS
  #undef fgets
  #define fgets cb_fgets_log
#endif

#ifdef CHAINBENCH_INTERPOSE_GETENV
  #undef getenv
  #define getenv(name) cb_getenv_log(name)  /* note: returns heap copy */
#endif

#ifdef CHAINBENCH_INTERPOSE_FREAD
  #undef fread
  #define fread(ptr,sz,n,fp) cb_fread_log(ptr,sz,n,fp)
#endif
