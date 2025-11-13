#pragma once
#include <stdio.h>   /* FILE */
#include <stddef.h>
#include "state.h"

/* fgets that logs taint into CB.ta (returns fgets result) */
char* cb_fgets_log(char* s, int size, FILE* stream);

/* getenv that returns a heap copy and logs taint (caller free) */
char* cb_getenv_log(const char* name);

/* fread that logs taint for the destination buffer */
size_t cb_fread_log(void* ptr, size_t sz, size_t nmemb, FILE* stream);
