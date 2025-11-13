/* auto-generated adapter for CWE126_Buffer_Overread__malloc_char_memcpy_01 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#if defined(_WIN32)
  #include <io.h>
  #define dup2 _dup2
  #define fileno _fileno
#else
  #include <unistd.h>
#endif
#include "state.h"

/* Juliet entrypoints (from source.c) */
int CWE126_Buffer_Overread__malloc_char_memcpy_01_bad(void);
#ifdef EMIT_GOOD
int CWE126_Buffer_Overread__malloc_char_memcpy_01_good(void);
#endif

/* If payload.bin exists next to the app, mirror it to stdin and CB.plane */
static void cb_seed_stdin_from_payload(void){
  FILE* f = fopen("payload.bin","rb");
  if(!f) return;
  FILE* tmp = tmpfile();
  if(!tmp){ fclose(f); return; }

  unsigned char buf[4096]; size_t n;
  while((n=fread(buf,1,sizeof(buf),f))>0){ fwrite(buf,1,n,tmp); }
  fflush(tmp); fseek(tmp,0,SEEK_SET);
  dup2(fileno(tmp), fileno(stdin));

  fseek(tmp,0,SEEK_END); long L = ftell(tmp);
  fseek(tmp,0,SEEK_SET);
  if (L > 0) {
    if ((size_t)L > sizeof(CB.plane)) L = (long)sizeof(CB.plane);
    fread(CB.plane,1,(size_t)L,tmp);
    CB.plane_len = (unsigned)L;
  }
  fclose(f);
}

/* Run wrappers: create a region and log an abstract effect */
int chainbench_run_CWE126_Buffer_Overread__malloc_char_memcpy_01_bad(void){
  cb_reset();
  cb_seed_stdin_from_payload();
  uint32_t rid = cb_region_new(SEG_DATA, 0, 1);
  cb_effect_push(rid, 0, 0, ACT_READ);
  (void)CWE126_Buffer_Overread__malloc_char_memcpy_01_bad();
  return 0;
}
#ifdef EMIT_GOOD
int chainbench_run_CWE126_Buffer_Overread__malloc_char_memcpy_01_good(void){
  cb_reset();
  cb_seed_stdin_from_payload();
  uint32_t rid = cb_region_new(SEG_DATA, 0, 1);
  cb_effect_push(rid, 0, 0, ACT_READ);
  (void)CWE126_Buffer_Overread__malloc_char_memcpy_01_good();
  return 0;
}
#endif
