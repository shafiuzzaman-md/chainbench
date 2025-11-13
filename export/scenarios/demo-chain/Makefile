CC ?= cc
CFLAGS ?= -O2 -g -std=c11 -Wall -Wextra
# POSIX prototypes for fileno(), etc.
CFLAGS += -D_POSIX_C_SOURCE=200809L

INCLUDE = -I ../../include -I ../../src
INCLUDE += -include ../../include/cb_interpose.h

SUPPORT_SRCS = $(wildcard ../../support/*.c)
SRCS = main.c ../../src/state.c ../../src/cb_io.c $(SUPPORT_SRCS) ../../items/CWE121_Stack_Based_Buffer_Overflow__CWE129_fgets_01/source.c ../../items/CWE121_Stack_Based_Buffer_Overflow__CWE129_fgets_01/adapter.c ../../items/CWE126_Buffer_Overread__malloc_char_memcpy_01/source.c ../../items/CWE126_Buffer_Overread__malloc_char_memcpy_01/adapter.c

all: scenario

scenario:
	$(CC) $(CFLAGS) $(INCLUDE) $(SRCS) -o scenario

clean:
	rm -f scenario
