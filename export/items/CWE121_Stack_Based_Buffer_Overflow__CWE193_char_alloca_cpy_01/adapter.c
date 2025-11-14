/* adapter.c for CWE121_Stack_Based_Buffer_Overflow__CWE193_char_alloca_cpy_01 (Linux)
 * Scenario wrapper. Assumes CB.plane was set by the scenario harness.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "state.h"

int CWE121_Stack_Based_Buffer_Overflow__CWE193_char_alloca_cpy_01_bad(void);
#ifdef EMIT_GOOD
int CWE121_Stack_Based_Buffer_Overflow__CWE193_char_alloca_cpy_01_good(void);
#endif

int chainbench_run_CWE121_Stack_Based_Buffer_Overflow__CWE193_char_alloca_cpy_01_bad(void){
  uint32_t rid = cb_region(SEG_DATA, 0, 1);
  cb_effect_push(rid, 0, 0, ACT_WRITE);
  (void)CWE121_Stack_Based_Buffer_Overflow__CWE193_char_alloca_cpy_01_bad();
  return 0;
}
#ifdef EMIT_GOOD
int chainbench_run_CWE121_Stack_Based_Buffer_Overflow__CWE193_char_alloca_cpy_01_good(void){
  uint32_t rid = cb_region(SEG_DATA, 0, 1);
  cb_effect_push(rid, 0, 0, ACT_WRITE);
  (void)CWE121_Stack_Based_Buffer_Overflow__CWE193_char_alloca_cpy_01_good();
  return 0;
}
#endif
