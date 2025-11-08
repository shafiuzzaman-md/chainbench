#include "../include/chain_state.h"
#include <stdlib.h>
#include <string.h>

static chain_state_t *g_chain = NULL;
void chainlab_bind_state(chain_state_t *st) { g_chain = st; }

/* Bounded ASCII→int, deterministic stand-in for atoi(sockdata). */
static int parse_int_ascii(const unsigned char *s, unsigned n){
    char tmp[64];
    if (n >= sizeof(tmp)) n = sizeof(tmp) - 1;
    memcpy(tmp, s, n); tmp[n] = '\0';
    return atoi(tmp);
}

void CWE121_Stack_Based_Buffer_Overflow__CWE129_connect_socket_01_bad(void)
{
    int data = -1;  /* Initialize like Juliet */

    /* SOURCE (adapted): read whatever the driver placed in ChainState.msg */
    if (g_chain && g_chain->msg_len > 0)
        data = parse_int_ascii(g_chain->msg, g_chain->msg_len);


    struct {
        int       buffer[10];   
        uintptr_t shadow_fp;   
    } frame = { .buffer = {0}, .shadow_fp = 0 };

    if (data >= 0) {
        frame.buffer[data] = 1; 
    } else {
    }

    /* OUTPUT (adapted): propagate possible corruption for chaining */
    if (g_chain) g_chain->fp = frame.shadow_fp;
}
