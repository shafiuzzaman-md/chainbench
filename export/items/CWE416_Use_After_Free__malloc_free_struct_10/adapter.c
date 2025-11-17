/* adapter.c for CWE416_Use_After_Free__malloc_free_struct_10 (Linux)
 * Scenario wrapper. Assumes CB.plane was set by the scenario harness.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "state.h"

int CWE416_Use_After_Free__malloc_free_struct_10_bad(void);
#ifdef EMIT_GOOD
int CWE416_Use_After_Free__malloc_free_struct_10_good(void);
#endif

int chainbench_run_CWE416_Use_After_Free__malloc_free_struct_10_bad(void){
  uint32_t rid = cb_region(SEG_HEAP, 0, 1);
  cb_effect_push(rid, 0, 0, ACT_READ);
  (void)CWE416_Use_After_Free__malloc_free_struct_10_bad();
  return 0;
}
#ifdef EMIT_GOOD
int chainbench_run_CWE416_Use_After_Free__malloc_free_struct_10_good(void){
  uint32_t rid = cb_region(SEG_HEAP, 0, 1);
  cb_effect_push(rid, 0, 0, ACT_READ);
  (void)CWE416_Use_After_Free__malloc_free_struct_10_good();
  return 0;
}
#endif
