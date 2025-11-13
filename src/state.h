#pragma once
#include <stdint.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

/* ======= Abstract memory model (lean) ======= */

typedef enum {
  SEG_HEAP = 1, SEG_STACK = 2, SEG_DATA = 3, SEG_CODE = 4, SEG_PROTECTED = 5
} cb_segment_t;

typedef enum {
  ACT_READ = 1, ACT_WRITE = 2, ACT_EXEC = 3, ACT_CALL = 4, ACT_TRIGGER = 5
} cb_action_t;

/* ---- attacker-input taint records ---- */
typedef enum { TAINT_STDIN=1, TAINT_ENV=2, TAINT_FILE=3 } cb_taint_src_t;

typedef struct {
  void*   p;          /* start address of attacker-filled buffer */
  size_t  n;          /* length of attacker bytes */
  uint8_t src;        /* TAINT_STDIN / TAINT_ENV / TAINT_FILE */
  char    label[16];  /* optional label (e.g., "stdin", env key) */
} cb_taint_rec_t;

/* ---- caps ---- */
#define CB_TAINT_MAX    16u
#define CB_MAX_REGIONS  64u
#define CB_MAX_EFFECTS  128u
#define CB_PLANE_MAX    4096u

/* ---- region/effect ---- */
typedef struct {
  uint32_t     id;       /* opaque handle */
  cb_segment_t seg;      /* memory segment */
  uint32_t     size;     /* abstract size (0 = unknown/expandable) */
  uint8_t      alive;    /* lifetime: 1=live, 0=fini */
} cb_region_t;

typedef struct {
  uint32_t     region_id;  /* which region (by id) */
  uint32_t     offset;     /* abstract offset (0 if N/A) */
  uint32_t     size;       /* abstract size (0 if N/A) */
  cb_action_t  act;        /* READ / WRITE / EXEC / CALL / TRIGGER */
} cb_effect_t;

/* ---- global state ---- */
typedef struct {
  /* Regions & effects recorded for a single run */
  cb_region_t  regions[CB_MAX_REGIONS];
  cb_effect_t  effects[CB_MAX_EFFECTS];
  uint32_t     region_count;
  uint32_t     effect_count;

  /* next region id allocator */
  uint32_t     _next_rid;

  /* raw attacker payload mirror (e.g., payload.bin or piped stdin) */
  unsigned char plane[CB_PLANE_MAX];
  uint32_t      plane_len;

  /* taint records for buffers filled by fgets/getenv/fread */
  cb_taint_rec_t ta[CB_TAINT_MAX];
  uint32_t       ta_cnt;

} cb_state_t;

extern cb_state_t CB;

/* ======= API ======= */
void     cb_reset(void);
uint32_t cb_region_new(cb_segment_t seg, uint32_t size, int alive);
void     cb_region_kill(uint32_t rid);
void     cb_effect_push(uint32_t rid, uint32_t off, uint32_t size, cb_action_t act);
void     cb_taint_add(void* p, size_t n, uint8_t src, const char* label);

#ifdef __cplusplus
}
#endif
