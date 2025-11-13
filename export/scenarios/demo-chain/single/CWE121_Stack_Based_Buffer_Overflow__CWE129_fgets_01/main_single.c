#include <stdio.h>
#include "state.h"
int chainbench_run_CWE121_Stack_Based_Buffer_Overflow__CWE129_fgets_01_bad(void);
int main(void){
  (void)chainbench_run_CWE121_Stack_Based_Buffer_Overflow__CWE129_fgets_01_bad();
  printf("[CB] single_done effects=%u regions=%u payload_len=%u\n",
         CB.effect_count, CB.region_count, CB.plane_len);
  return 0;
}
