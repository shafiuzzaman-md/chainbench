#include "state.h"
#include <string.h>

cb_state_t CB;

void cb_reset(void){
  memset(&CB, 0, sizeof(CB));
  CB._next_rid = 1; /* start region ids at 1 */
}

static cb_region_t* find_region(uint32_t rid){
  for(uint32_t i=0;i<CB.region_count;i++){
    if (CB.regions[i].id == rid) return &CB.regions[i];
  }
  return NULL;
}

uint32_t cb_region_new(cb_segment_t seg, uint32_t size, int alive){
  if (CB.region_count >= CB_MAX_REGIONS) return 0;
  cb_region_t *r = &CB.regions[CB.region_count++];
  r->id = CB._next_rid++;
  r->seg = seg;
  r->size = size;
  r->alive = alive ? 1u : 0u;
  return r->id;
}

void cb_region_kill(uint32_t rid){
  cb_region_t *r = find_region(rid);
  if (r) r->alive = 0;
}

void cb_effect_push(uint32_t rid, uint32_t off, uint32_t size, cb_action_t act){
  if (CB.effect_count >= CB_MAX_EFFECTS) return;
  cb_effect_t *e = &CB.effects[CB.effect_count++];
  e->region_id = rid;
  e->offset = off;
  e->size = size;
  e->act = act;
}

void cb_taint_add(void* p, size_t n, uint8_t src, const char* label){
  if (!p || !n || CB.ta_cnt >= CB_TAINT_MAX) return;
  cb_taint_rec_t *r = &CB.ta[CB.ta_cnt++];
  r->p = p; r->n = n; r->src = src;
  size_t L = label ? strnlen(label, sizeof(r->label)-1) : 0;
  if (L) memcpy(r->label, label, L);
  r->label[L] = '\0';
}
