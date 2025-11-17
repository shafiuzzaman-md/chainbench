/* adapter.c for CWE478_Missing_Default_Case_in_Switch__basic_01 (Linux)
 * Scenario wrapper. Assumes CB.plane was set by the scenario harness.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "state.h"

int CWE478_Missing_Default_Case_in_Switch__basic_01_bad(void);
#ifdef EMIT_GOOD
int CWE478_Missing_Default_Case_in_Switch__basic_01_good(void);
#endif

int chainbench_run_CWE478_Missing_Default_Case_in_Switch__basic_01_bad(void){
  uint32_t rid = cb_region(SEG_DATA, 0, 1);
  cb_effect_push(rid, 0, 0, ACT_READ);
  (void)CWE478_Missing_Default_Case_in_Switch__basic_01_bad();
  return 0;
}
#ifdef EMIT_GOOD
int chainbench_run_CWE478_Missing_Default_Case_in_Switch__basic_01_good(void){
  uint32_t rid = cb_region(SEG_DATA, 0, 1);
  cb_effect_push(rid, 0, 0, ACT_READ);
  (void)CWE478_Missing_Default_Case_in_Switch__basic_01_good();
  return 0;
}
#endif
