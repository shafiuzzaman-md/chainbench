#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "state.h"
#include "cb_io.h"

char* cb_fgets_log(char* s, int size, FILE* stream) {
  char* r = fgets(s, size, stream);
  if (!r) return r;
  size_t n = strnlen(s, (size_t)size);
  cb_taint_add(s, n, TAINT_STDIN, "stdin");
  return r;
}

char* cb_getenv_log(const char* name) {
  const char* v = getenv(name);
  if (!v) return NULL;
  size_t n = strlen(v);
  char* copy = (char*)malloc(n + 1);
  if (!copy) return NULL;
  memcpy(copy, v, n + 1);
  cb_taint_add(copy, n, TAINT_ENV, name);
  return copy;
}

size_t cb_fread_log(void* ptr, size_t sz, size_t nmemb, FILE* stream) {
  size_t got = fread(ptr, sz, nmemb, stream);
  cb_taint_add(ptr, got * sz, TAINT_FILE, "file");
  return got;
}
