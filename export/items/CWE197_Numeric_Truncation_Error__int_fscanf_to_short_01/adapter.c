/* adapter.c for CWE197_Numeric_Truncation_Error__int_fscanf_to_short_01 (Linux)
 * Scenario wrapper. Assumes CB.plane was set by the scenario harness.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "state.h"

int CWE197_Numeric_Truncation_Error__int_fscanf_to_short_01_bad(void);
#ifdef EMIT_GOOD
int CWE197_Numeric_Truncation_Error__int_fscanf_to_short_01_good(void);
#endif

int chainbench_run_CWE197_Numeric_Truncation_Error__int_fscanf_to_short_01_bad(void){
  uint32_t rid = cb_region(SEG_DATA, 0, 1);
  cb_effect_push(rid, 0, 0, ACT_TRIGGER);
  (void)CWE197_Numeric_Truncation_Error__int_fscanf_to_short_01_bad();
  return 0;
}
#ifdef EMIT_GOOD
int chainbench_run_CWE197_Numeric_Truncation_Error__int_fscanf_to_short_01_good(void){
  uint32_t rid = cb_region(SEG_DATA, 0, 1);
  cb_effect_push(rid, 0, 0, ACT_TRIGGER);
  (void)CWE197_Numeric_Truncation_Error__int_fscanf_to_short_01_good();
  return 0;
}
#endif
