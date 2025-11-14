/* adapter.c for CWE127_Buffer_Underread__char_declare_memmove_01 (Linux)
 * Scenario wrapper. Assumes CB.plane was set by the scenario harness.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "state.h"

int CWE127_Buffer_Underread__char_declare_memmove_01_bad(void);
#ifdef EMIT_GOOD
int CWE127_Buffer_Underread__char_declare_memmove_01_good(void);
#endif

int chainbench_run_CWE127_Buffer_Underread__char_declare_memmove_01_bad(void){
  uint32_t rid = cb_region(SEG_STACK, 0, 1);
  cb_effect_push(rid, 0, 0, ACT_WRITE);
  (void)CWE127_Buffer_Underread__char_declare_memmove_01_bad();
  return 0;
}
#ifdef EMIT_GOOD
int chainbench_run_CWE127_Buffer_Underread__char_declare_memmove_01_good(void){
  uint32_t rid = cb_region(SEG_STACK, 0, 1);
  cb_effect_push(rid, 0, 0, ACT_WRITE);
  (void)CWE127_Buffer_Underread__char_declare_memmove_01_good();
  return 0;
}
#endif
