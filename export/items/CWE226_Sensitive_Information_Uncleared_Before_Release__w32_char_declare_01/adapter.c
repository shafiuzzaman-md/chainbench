/* adapter.c for CWE226_Sensitive_Information_Uncleared_Before_Release__w32_char_declare_01 (Linux)
 * Scenario wrapper. Assumes CB.plane was set by the scenario harness.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "state.h"

int CWE226_Sensitive_Information_Uncleared_Before_Release__w32_char_declare_01_bad(void);
#ifdef EMIT_GOOD
int CWE226_Sensitive_Information_Uncleared_Before_Release__w32_char_declare_01_good(void);
#endif

int chainbench_run_CWE226_Sensitive_Information_Uncleared_Before_Release__w32_char_declare_01_bad(void){
  uint32_t rid = cb_region(SEG_DATA, 0, 1);
  cb_effect_push(rid, 0, 0, ACT_WRITE);
  (void)CWE226_Sensitive_Information_Uncleared_Before_Release__w32_char_declare_01_bad();
  return 0;
}
#ifdef EMIT_GOOD
int chainbench_run_CWE226_Sensitive_Information_Uncleared_Before_Release__w32_char_declare_01_good(void){
  uint32_t rid = cb_region(SEG_DATA, 0, 1);
  cb_effect_push(rid, 0, 0, ACT_WRITE);
  (void)CWE226_Sensitive_Information_Uncleared_Before_Release__w32_char_declare_01_good();
  return 0;
}
#endif
