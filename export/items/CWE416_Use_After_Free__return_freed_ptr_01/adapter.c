/* adapter.c for CWE416_Use_After_Free__return_freed_ptr_01 (Linux)
 * Scenario wrapper. Assumes CB.plane was set by the scenario harness.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "state.h"

int CWE416_Use_After_Free__return_freed_ptr_01_bad(void);
#ifdef EMIT_GOOD
int CWE416_Use_After_Free__return_freed_ptr_01_good(void);
#endif

int chainbench_run_CWE416_Use_After_Free__return_freed_ptr_01_bad(void){
  uint32_t rid = cb_region(SEG_HEAP, 0, 1);
  cb_effect_push(rid, 0, 0, ACT_WRITE);
  (void)CWE416_Use_After_Free__return_freed_ptr_01_bad();
  return 0;
}
#ifdef EMIT_GOOD
int chainbench_run_CWE416_Use_After_Free__return_freed_ptr_01_good(void){
  uint32_t rid = cb_region(SEG_HEAP, 0, 1);
  cb_effect_push(rid, 0, 0, ACT_WRITE);
  (void)CWE416_Use_After_Free__return_freed_ptr_01_good();
  return 0;
}
#endif
