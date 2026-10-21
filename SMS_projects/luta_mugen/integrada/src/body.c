/* body.c — ver inc/body.h. Uma chamada por quadro, O(1), sem alocar. */
#include "body.h"

unsigned char body_separate(Body *a, Body *b, unsigned int x_min,
                            unsigned int x_max) {
    Body *left, *right;
    unsigned int gap, total, cap, need, overlap, dl, dr, room;

    if (a->y || b->y) return 0u;                    /* so na linha de piso */
    if (a->x <= b->x) { left = a; right = b; }      /* empate: a fica a esquerda */
    else              { left = b; right = a; }

    gap = (unsigned int)(right->x - left->x);
    total = (unsigned int)a->half_w + (unsigned int)b->half_w;
    cap = (unsigned int)((x_max - x_min) >> 8);     /* px disponiveis na arena */
    if (total > cap) total = cap;                   /* corpos mais largos que a arena */
    need = (unsigned int)(total << 8);
    if (gap >= need) return 0u;

    overlap = (unsigned int)(need - gap);
    dl = (unsigned int)(overlap >> 1);
    dr = (unsigned int)(overlap - dl);

    /* Cada lado so anda ate a propria borda; o que sobra passa para o outro.
     * Assim nenhum valor intermediario sai de [x_min, x_max] (16 bits). */
    room = (unsigned int)(left->x - x_min);
    if (dl > room) {
        dr = (unsigned int)(dr + (dl - room));
        dl = room;
    }
    room = (unsigned int)(x_max - right->x);
    if (dr > room) dr = room;                       /* o resto fica sobreposto */

    left->x = (unsigned int)(left->x - dl);
    right->x = (unsigned int)(right->x + dr);
    return 1u;
}

unsigned char body_facing(unsigned int self_x, unsigned int other_x,
                          unsigned char current) {
    if (other_x > self_x) return 0u;
    if (other_x < self_x) return 1u;
    return current;
}
