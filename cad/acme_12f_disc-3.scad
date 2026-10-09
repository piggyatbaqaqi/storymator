// ACME 12F animation disc, rev 3
// 1/4" cast acrylic, frosted on top, clear on bottom.
// Z = 0 is the clear underside, Z = disc_t is the frosted working surface.
// Peg bar sits in a shallow slot on the top face; +Y is "up" (north) on the disc.
//
// Rev 3 is the cost-and-weight revision, and it is also the disc that drops
// into the 24-to-16.5 inch stepped overhang flange cap: the sheet halves to
// 1/4", the mounting pattern drops from six holes to four, and the outer edge
// is left square because the flange's step pocket is what the rim now
// registers against.
//
// 16.5 in x 1/4 in is 1.03 kg of acrylic against rev 2's 2.07 kg at 1/2 in,
// half the weight, and the hole count and the square rim are machining time.
//
// The screws sit 5/8 in in from the rim, which is the constraint the operator
// stated, so the bolt circle is derived from it rather than typed in.  On a
// 16.5 in disc that lands on the 15.25 in bolt circle that
// flange_ring_24_to_16_half.scad specifies, and the assert below keeps the two
// files from drifting apart: change the disc diameter and the flange has to be
// told, because the screws stay 5/8 in from a rim that has moved.

$fn = 160;

/* [Disc] */
disc_d = 16.5 * 25.4;  // 16-1/2 in (419.1 mm), the 12F standard diameter
disc_t = 6.35;         // 1/4 in nominal. Measure your sheet; cast acrylic often runs a bit off.
                       // The outer edge is deliberately square -- see the header.

/* [Peg bar slot, cut from top face] */
slot_len      = 234;    // 233.5 - 234
slot_w        = 31.5;
slot_depth    = 1.5;
slot_corner_r = 3;      // router bit radius; stamped bar corners must be >= this
peg_offset    = 4 * 25.4;  // center of center peg to disc center (101.6 mm)

/* [Peg bar mounting holes, M2 clearance] */
bar_hole_y  = peg_offset; // ASSUMED: holes on the center-peg line. Change if the bar's holes are offset from it.
bar_hole_sp = 133.55;   // center-to-center spacing of the two holes
bar_hole_dx = [-bar_hole_sp / 2, bar_hole_sp / 2];
m2_clear    = 2.4;

/* [Flange mounting, M4 countersunk] */
ls_rim_inset = 0.625 * 25.4;          // 5/8 in (15.875 mm), rim to hole CENTER
ls_r         = disc_d / 2 - ls_rim_inset;   // 193.675 mm, so an 15.25 in bolt circle
ls_count     = 4;
ls_start     = 90;  // first hole due north, on the +Y axis beyond the peg bar;
                    // the pattern then runs N, W, S, E at 90 deg
m4_clear  = 4.5;    // 4 mm bolt with acrylic-friendly clearance.
                    // The flange specifies #8 screws through 3/16 in holes; if the
                    // fastener follows the flange rather than rev 2, this is 4.7625
                    // and the countersink wants a #8 head.
m4_csk_d  = 9.2;    // head is ~8.96 max, so it sits just below flush
m4_csk_a  = 90;     // countersink included angle

eps = 0.01;

module rounded_rect(w, h, r) {
    offset(r = r) square([w - 2*r, h - 2*r], center = true);
}

module disc_body() {
    cylinder(d = disc_d, h = disc_t);
}

module peg_slot() {
    translate([0, peg_offset, disc_t - slot_depth])
        linear_extrude(slot_depth + eps)
            rounded_rect(slot_len, slot_w, slot_corner_r);
}

module bar_holes() {
    for (dx = bar_hole_dx) {
        assert(abs(bar_hole_y - peg_offset) < slot_w / 2 - 2 && abs(dx) < slot_len / 2 - 5,
               str("M2 hole at x=", dx, " falls outside the slot"));
        translate([dx, bar_hole_y, -eps]) cylinder(d = m2_clear, h = disc_t + 2*eps, $fn = 48);
    }
}

module m4_hole() {
    csk_h = (m4_csk_d - m4_clear) / 2 / tan(m4_csk_a / 2);
    translate([0, 0, -eps]) cylinder(d = m4_clear, h = disc_t + 2*eps, $fn = 64);
    translate([0, 0, disc_t - csk_h])
        cylinder(d1 = m4_clear, d2 = m4_csk_d, h = csk_h + eps, $fn = 64);
}

module flange_holes() {
    for (i = [0 : ls_count - 1])
        rotate([0, 0, ls_start + i * 360 / ls_count])
            translate([ls_r, 0, 0]) m4_hole();
}

// The mating part names a bolt circle; this file derives one from the rim
// inset.  They have to agree, and the one that is wrong is whichever file was
// edited without the other.
flange_bolt_circle_d = 15.25 * 25.4;    // flange_ring_24_to_16_half.scad
assert(abs(2 * ls_r - flange_bolt_circle_d) < 0.1,
       str("Bolt circle is ", 2 * ls_r, " mm but the flange is cut for ",
           flange_bolt_circle_d, " mm: a 5/8 in inset on a ", disc_d / 25.4,
           " in disc does not match flange_ring_24_to_16_half.scad"));

// The inset has to leave real material at the rim, which is the check rev 2
// never needed because its pattern sat well inside the disc.
assert(ls_rim_inset - m4_csk_d / 2 > 5,
       str("Inset leaves only ", ls_rim_inset - m4_csk_d / 2,
           " mm between countersink and rim"));

// A 1/4 in sheet is thin enough that the countersink and the slot are no
// longer obviously free, so both are now checked.
assert((m4_csk_d - m4_clear) / 2 / tan(m4_csk_a / 2) < disc_t - 2,
       "Countersink leaves under 2 mm of land in this sheet");
assert(disc_t - slot_depth > 3,
       "Peg bar slot leaves under 3 mm under the bar");

assert(disc_d / 2 > norm([slot_len / 2, peg_offset + slot_w / 2]) + 5,
       "Slot corner is too close to the disc edge");

difference() {
    disc_body();
    peg_slot();
    bar_holes();
    flange_holes();
}
