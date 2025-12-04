#ifndef CB_STATE_H
#define CB_STATE_H
#include <stdint.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

/* segments & actions */
enum cb_segment { SEG_HEAP, SEG_STACK, SEG_DATA, SEG_CODE, SEG_PROTECTED };
enum cb_action  { ACT_READ, ACT_WRITE, ACT_EXEC, ACT_CALL, ACT_TRIGGER };

/* address class for chaining */
enum cb_addr_class { ADDR_FIXED, ADDR_ARBITRARY, ADDR_EXPANDABLE };

struct cb_region {
  uint32_t id;
  enum cb_segment seg;
  uint64_t base;         /* default base for the region */
  uint32_t size;         /* default size */
  int      growth;       /* 1=can expand */
  enum cb_addr_class cls;
};

struct cb_effect {
  uint32_t region;
  uint32_t off;
  uint32_t len;
  enum cb_action   act;

  /* NEW: snapshot of address config FOR THIS EFFECT */
  uint64_t         base;     /* 0 => inherit region.base */
  uint32_t         size;     /* 0 => inherit region.size */
  enum cb_addr_class cls;    /* inheritable */
};

struct cb_state {
  unsigned char plane[1<<16];
  uint32_t plane_len;

  struct cb_region regions[32];
  uint32_t region_count;

  struct cb_effect effects[64];
  uint32_t effect_count;
};

extern struct cb_state CB;

/* API */
void cb_reset(void);

uint32_t cb_region_addr(enum cb_segment seg, uint64_t base,
                        uint32_t size, int growth,
                        enum cb_addr_class cls);

/* Legacy shim */
static inline uint32_t cb_region(enum cb_segment seg, uint32_t size, int growth){
  return cb_region_addr(seg, 0, size, growth, ADDR_ARBITRARY);
}

/* OLD: push without address override (kept for compatibility) */
void cb_effect_push(uint32_t region, uint32_t off, uint32_t len, enum cb_action act);

/* NEW: push WITH address override/snapshot at effect time */
void cb_effect_push_fixed(uint32_t region, uint32_t off, uint32_t len,
                          enum cb_action act,
                          uint64_t base_override, uint32_t size_override,
                          enum cb_addr_class cls_override);

#ifdef __cplusplus
}
#endif
#endif /* CB_STATE_H */
