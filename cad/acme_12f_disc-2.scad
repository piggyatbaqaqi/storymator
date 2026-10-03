// ACME 12F animation disc
// 1/2" cast acrylic, frosted on top, clear on bottom.
// Z = 0 is the clear underside, Z = disc_t is the frosted working surface.
// Peg bar sits in a shallow slot on the top face; +Y is "up" on the disc.

$fn = 160;

/* [Disc] */
disc_d      = 16.5 * 25.4;  // 16-1/2 in (419.1 mm)
disc_t      = 12.7;   // 1/2 in nominal. Measure your sheet; cast acrylic often runs a bit off.
chamfer_top = 2.0;    // 45 deg, on the working (frosted) edge
chamfer_bot = 1.0;    // 45 deg, just breaks the underside edge

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

/* [Lazy Susan mounting, M4 countersunk] */
ls_r      = 184.5;  // radius to center of outer ring
ls_count  = 6;
ls_start  = 0;      // rotate the pattern to match how you want it oriented
m4_clear  = 4.5;    // 4 mm bolt with acrylic-friendly clearance
m4_csk_d  = 9.2;    // head is ~8.96 max, so it sits just below flush
m4_csk_a  = 90;     // countersink included angle

eps = 0.01;

module rounded_rect(w, h, r) {
    offset(r = r) square([w - 2*r, h - 2*r], center = true);
}

module disc_body() {
    R = disc_d / 2;
    rotate_extrude()
        polygon([
            [0, 0],
            [R - chamfer_bot, 0],
            [R, chamfer_bot],
            [R, disc_t - chamfer_top],
            [R - chamfer_top, disc_t],
            [0, disc_t]
        ]);
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

module lazy_susan_holes() {
    for (i = [0 : ls_count - 1])
        rotate([0, 0, ls_start + i * 360 / ls_count])
            translate([ls_r, 0, 0]) m4_hole();
}

assert(disc_d / 2 > norm([slot_len / 2, peg_offset + slot_w / 2]) + 5,
       "Slot corner is too close to the disc edge");

difference() {
    disc_body();
    peg_slot();
    bar_holes();
    lazy_susan_holes();
}
