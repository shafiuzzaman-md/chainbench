/* adapter.c for CWE457_Use_of_Uninitialized_Variable__int_01 (Linux)
 * Scenario wrapper. Assumes CB.plane was set by the scenario harness.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "state.h"

int CWE457_Use_of_Uninitialized_Variable__int_01_bad(void);
#ifdef EMIT_GOOD
int CWE457_Use_of_Uninitialized_Variable__int_01_good(void);
#endif

int chainbench_run_CWE457_Use_of_Uninitialized_Variable__int_01_bad(void){
  uint32_t rid = cb_region(SEG_DATA, 0, 1);
  cb_effect_push(rid, 0, 0, ACT_READ);
  (void)CWE457_Use_of_Uninitialized_Variable__int_01_bad();
  return 0;
}
#ifdef EMIT_GOOD
int chainbench_run_CWE457_Use_of_Uninitialized_Variable__int_01_good(void){
  uint32_t rid = cb_region(SEG_DATA, 0, 1);
  cb_effect_push(rid, 0, 0, ACT_READ);
  (void)CWE457_Use_of_Uninitialized_Variable__int_01_good();
  return 0;
}
#endif
