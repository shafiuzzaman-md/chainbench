/* adapter.c for CWE415_Double_Free__malloc_free_wchar_t_01 (Linux)
 * Scenario wrapper. Assumes CB.plane was set by the scenario harness.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "state.h"

int CWE415_Double_Free__malloc_free_wchar_t_01_bad(void);
#ifdef EMIT_GOOD
int CWE415_Double_Free__malloc_free_wchar_t_01_good(void);
#endif

int chainbench_run_CWE415_Double_Free__malloc_free_wchar_t_01_bad(void){
  uint32_t rid = cb_region(SEG_HEAP, 0, 1);
  cb_effect_push(rid, 0, 0, ACT_READ);
  (void)CWE415_Double_Free__malloc_free_wchar_t_01_bad();
  return 0;
}
#ifdef EMIT_GOOD
int chainbench_run_CWE415_Double_Free__malloc_free_wchar_t_01_good(void){
  uint32_t rid = cb_region(SEG_HEAP, 0, 1);
  cb_effect_push(rid, 0, 0, ACT_READ);
  (void)CWE415_Double_Free__malloc_free_wchar_t_01_good();
  return 0;
}
#endif
