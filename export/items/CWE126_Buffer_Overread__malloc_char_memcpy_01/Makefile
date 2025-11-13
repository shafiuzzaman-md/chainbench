CC ?= cc
CFLAGS ?= -O2 -g -std=c11 -Wall -Wextra
# POSIX prototypes for fileno(), etc.
CFLAGS += -D_POSIX_C_SOURCE=200809L

INCLUDE = -I ../../include -I ../../src
INCLUDE += -include ../../include/cb_interpose.h

SUPPORT_SRCS = $(wildcard ../../support/*.c)
SRCS = main_single.c source.c ../../src/state.c ../../src/cb_io.c adapter.c $(SUPPORT_SRCS)


all: app

app: $(SRCS)
	$(CC) $(CFLAGS) $(INCLUDE) $(SRCS) -o $@

clean:
	rm -f app
