/* adapter.c for CWE126_Buffer_Overread__char_declare_memcpy_01 (Linux)
 * Scenario wrapper. Assumes CB.plane was set by the scenario harness.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "state.h"

int CWE126_Buffer_Overread__char_declare_memcpy_01_bad(void);
#ifdef EMIT_GOOD
int CWE126_Buffer_Overread__char_declare_memcpy_01_good(void);
#endif

int chainbench_run_CWE126_Buffer_Overread__char_declare_memcpy_01_bad(void){
  uint32_t rid = cb_region(SEG_STACK, 0, 1);
  cb_effect_push(rid, 0, 0, ACT_WRITE);
  (void)CWE126_Buffer_Overread__char_declare_memcpy_01_bad();
  return 0;
}
#ifdef EMIT_GOOD
int chainbench_run_CWE126_Buffer_Overread__char_declare_memcpy_01_good(void){
  uint32_t rid = cb_region(SEG_STACK, 0, 1);
  cb_effect_push(rid, 0, 0, ACT_WRITE);
  (void)CWE126_Buffer_Overread__char_declare_memcpy_01_good();
  return 0;
}
#endif
