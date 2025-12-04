#include "state.h"
#include <string.h>

struct cb_state CB;

void cb_reset(void){
  memset(&CB, 0, sizeof(CB));
}

uint32_t cb_region_addr(enum cb_segment seg, uint64_t base,
                        uint32_t size, int growth,
                        enum cb_addr_class cls){
  uint32_t id = CB.region_count;
  if (id >= 32) return 31; /* clamp */
  CB.regions[id].id     = id;
  CB.regions[id].seg    = seg;
  CB.regions[id].base   = base;
  CB.regions[id].size   = size;
  CB.regions[id].growth = growth;
  CB.regions[id].cls    = cls;
  CB.region_count++;
  return id;
}

void cb_effect_push(uint32_t region, uint32_t off, uint32_t len, enum cb_action act){
  cb_effect_push_fixed(region, off, len, act, 0, 0, (enum cb_addr_class)-1);
}

void cb_effect_push_fixed(uint32_t region, uint32_t off, uint32_t len,
                          enum cb_action act,
                          uint64_t base_override, uint32_t size_override,
                          enum cb_addr_class cls_override){
  uint32_t i = CB.effect_count;
  if (i >= 64) return;
  CB.effects[i].region = region;
  CB.effects[i].off    = off;
  CB.effects[i].len    = len;
  CB.effects[i].act    = act;

  /* snapshot: inherit region defaults then apply overrides */
  const struct cb_region *R = (region < CB.region_count) ? &CB.regions[region] : NULL;
  CB.effects[i].base = base_override ? base_override : (R ? R->base : 0);
  CB.effects[i].size = size_override ? size_override : (R ? R->size : 0);
  CB.effects[i].cls  = (cls_override != (enum cb_addr_class)-1) ? cls_override
                                                                : (R ? R->cls : ADDR_ARBITRARY);
  CB.effect_count++;
}
