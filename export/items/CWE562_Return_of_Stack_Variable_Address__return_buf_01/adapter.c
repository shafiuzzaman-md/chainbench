/* adapter.c for CWE562_Return_of_Stack_Variable_Address__return_buf_01 (Linux)
 * Scenario wrapper. Assumes CB.plane was set by the scenario harness.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "state.h"

int CWE562_Return_of_Stack_Variable_Address__return_buf_01_bad(void);
#ifdef EMIT_GOOD
int CWE562_Return_of_Stack_Variable_Address__return_buf_01_good(void);
#endif

int chainbench_run_CWE562_Return_of_Stack_Variable_Address__return_buf_01_bad(void){
  uint32_t rid = cb_region(SEG_DATA, 0, 1);
  cb_effect_push(rid, 0, 0, ACT_WRITE);
  (void)CWE562_Return_of_Stack_Variable_Address__return_buf_01_bad();
  return 0;
}
#ifdef EMIT_GOOD
int chainbench_run_CWE562_Return_of_Stack_Variable_Address__return_buf_01_good(void){
  uint32_t rid = cb_region(SEG_DATA, 0, 1);
  cb_effect_push(rid, 0, 0, ACT_WRITE);
  (void)CWE562_Return_of_Stack_Variable_Address__return_buf_01_good();
  return 0;
}
#endif
