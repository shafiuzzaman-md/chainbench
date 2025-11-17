/* adapter.c for CWE535_Info_Exposure_Shell_Error__w32_char_01 (Linux)
 * Scenario wrapper. Assumes CB.plane was set by the scenario harness.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "state.h"

int CWE535_Info_Exposure_Shell_Error__w32_char_01_bad(void);
#ifdef EMIT_GOOD
int CWE535_Info_Exposure_Shell_Error__w32_char_01_good(void);
#endif

int chainbench_run_CWE535_Info_Exposure_Shell_Error__w32_char_01_bad(void){
  uint32_t rid = cb_region(SEG_DATA, 0, 1);
  cb_effect_push(rid, 0, 0, ACT_WRITE);
  (void)CWE535_Info_Exposure_Shell_Error__w32_char_01_bad();
  return 0;
}
#ifdef EMIT_GOOD
int chainbench_run_CWE535_Info_Exposure_Shell_Error__w32_char_01_good(void){
  uint32_t rid = cb_region(SEG_DATA, 0, 1);
  cb_effect_push(rid, 0, 0, ACT_WRITE);
  (void)CWE535_Info_Exposure_Shell_Error__w32_char_01_good();
  return 0;
}
#endif
