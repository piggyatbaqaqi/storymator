// ============================================================================
// Parametric 17.5-Inch 2-Piece Laminated Animation Disc & Removable Acrylic Window
// Units: Inches (scale by 25.4 if exporting STL for metric slicers/CAD)
// ============================================================================

$fn = 180; // Smooth circular resolution

// --- Primary Dimensions (Inches) ---
outer_dia         = 17.5;     // 17 1/2" outer top flange diameter
step_dia          = 16.4375;  // 16 7/16" bottom step diameter (fits 16.5" desk hole with 1/16" total clearance)
top_ply_thick     = 0.25;     // 1/4" nominal top plywood layer
bot_ply_thick     = 0.75;     // 3/4" nominal bottom plywood layer
step_depth        = 0.75;     // Depth of bottom step-down rabbet (matches ~0.7585" desk thickness)
top_round_r       = 0.125;    // 1/8" radius round-over on top outer edge

// --- Window & Acrylic Dimensions (Inches) ---
view_w            = 12.0;     // 12" clear viewing width (bottom layer cutout)
view_h            = 9.0;      // 9" clear viewing height (bottom layer cutout)
acrylic_w         = 12.0;     // 12" acrylic width (0" side overlap)
acrylic_h         = 9.75;     // 9 3/4" acrylic height (3/8" overlap top & bottom)
acrylic_thick     = 0.25;     // 1/4" clear cast acrylic thickness
expansion_gap     = 0.03125;  // 1/32" total play in top plywood recess
corner_r          = 0.125;    // 1/8" corner radius (matches 1/4" diameter router bit)

// --- Fastener Dimensions (#6-32 Flat-Head Screws & Brass Inserts) ---
screw_clearance_d = 0.15625;  // 5/32" clearance hole in acrylic
csink_top_d       = 0.28;     // 82-degree countersink top diameter for #6 flat-head
csink_depth       = 0.085;    // Countersink depth
insert_pilot_d    = 0.1875;   // 3/16" pilot hole for #6-32 brass knife-thread insert
insert_depth      = 0.375;    // 3/8" insert depth
// The inserts sit at screw_y_offset, 3/16" from the 9" window opening's edge,
// so a 3/16" pilot leaves only ~2.4 mm of wood to that edge, and the knife
// threads cut beyond the pilot.  Hardwood knife inserts are also sold as "not
// recommended for plywood", so the build guide sets them in epoxy.  The
// insert's outside diameter is unmeasured, so no wall-thickness assert yet.
screw_x_offset    = 5.5;      // +/- 5.5" -> 11" apart. Was 4.5", which put the two south
                              // screws under the peg bar; 5.5" clears its ends (see asserts).
screw_y_offset    = 4.6875;   // Centered in the 3/8" top/bottom ledge (4.5" + 0.1875" = 4.6875")

// --- 12F sheet & ACME peg bar (Inches) ---
// The window is centred on the sheet's 12" x 9" IMAGE AREA, not on the sheet.
// Operator's figures, 2026-11-20: the image area runs 1.00" to 10.00" from the
// punched edge, so its optical centre is 5.50" from that edge.  The disc
// origin is that optical centre; the punched edge, and so the bar, is south (-Y).
sheet_w           = 12.5;     // 12F sheet, along the bar
sheet_h           = 10.5;     // 12F sheet, into the sheet from the punched edge
image_lo          = 1.00;     // image area start, from the punched edge
image_hi          = 10.00;    // image area end, from the punched edge
optical_ctr       = (image_lo + image_hi) / 2;   // 5.50"
// Punched edge to peg line.  Operator, ruler, 2026-11-20, on a 12F sheet on
// honbay_0001: 11/32" (8.73 mm), +/- 1/64" reading.  It replaces the 12 mm
// nominal SheetModel.punch_offset_mm still carries.
punch_offset      = 11 / 32;
peg_line_y        = -(optical_ctr - punch_offset);   // -5.15625"

// Peg bar channel, cut 1.5 mm into the top face.  Peg bars are not
// standardised in width or length: this channel is for honbay_0001, a Honbay
// stainless bar (https://www.amazon.com/dp/B0721MR5TM), and another bar needs
// its own numbers.  Calipers, operator, 2026-11-20 (pegs/honbay_0001/README.md):
//   width 19.92 / 19.99 mm (nominal 20); pegs centred across it to 0.13-0.21 mm,
//   so it is symmetric and has no orientation; screw holes 58.05 mm from each end.
// Length 9 7/8" (250.8 mm), ordinary ruler, operator, 2026-11-20.  rev 3's
// 234 x 31.5 mm outline was not this bar; its 133.55 mm hole spacing implies
// 249.65 mm, 1.2 mm short of the ruler, about one graduation.
bar_len           = 9.875;
bar_hole_from_end = 58.05 / 25.4;   // operator, 2026-11-20
bar_hole_sp       = bar_len - 2 * bar_hole_from_end;   // 134.7 mm (rev 3: 133.55)
// Channel clearance over the bar.  Length: 1.5 mm total (operator), so
// 0.75 mm at each end for router error.  Width: 0.3 mm total (operator),
// against a bar measured at 19.92-19.99 mm.
slot_len_clear    = 1.5 / 25.4;
slot_w_clear      = 0.3 / 25.4;
slot_len          = bar_len + slot_len_clear;   // 252.3 mm
slot_w            = 20.0 / 25.4 + slot_w_clear; // 20.3 mm
slot_depth        = 1.5 / 25.4;
slot_corner_r     = 1 / 8;        // the 1/4" bit's radius, 3.175 mm
// The bar's corners are R2.0 mm (operator), tighter than the channel's.  It
// still seats if its corner arc fits inside the channel's corner arc, which
// the clearances make possible: see the assert.  The margin is under 0.1 mm,
// so if a corner binds, pare it square with a chisel.
bar_corner_r      = 2.0 / 25.4;
slot_ctr_y        = peg_line_y;   // centred, as measured
// The bar's punched-side edge then lands 10.0 - 8.73 = 1.27 mm past the paper
// edge, against the 1/32" (0.79 mm) read with a ruler: 0.48 mm apart, inside
// two ruler readings of +/- 1/64" each.
// The bar reaches 10 mm north of the peg line: clear of the 9" window by
// 6.7 mm, but 3.3 mm into the acrylic recess.  The channel is therefore still
// cut across the acrylic's south strip as well as the wood, in one pass with
// the acrylic screwed in, so the bar beds flat across the seam.
// ASSUMED: the holes are on the bar's centreline, which is the peg line.
// Transfer-punch them through the seated bar rather than drilling to these
// coordinates.
//
// The bar is removed whenever the acrylic comes out, so it is held by M2
// flat-head machine screws (90 deg, metric) in brass inserts, not wood screws.
// Its holes are 2.42 mm (inside calipers, operator, 2026-11-20; an earlier
// 2.0 mm reading was rough) and countersunk: a standard M2 clearance, leaving
// the 1.86-1.98 mm thread 0.2-0.28 mm of float per side.  A hand-drilled
// insert can easily be off by more than that, so the inserts are still set in
// EPOXY in an oversize pocket, with the bar screwed down on them while it
// cures, so the bar locates them.  Wax the screws first.
//
// Chosen insert (operator, 2026-11-20): "Knurled Insert Nuts, M2 x 6 mm
// Length x 4 mm OD" brass heat-set inserts for 3D printing.  Wood won't
// melt round them, so they are epoxied, not heat-set.  They are threaded
// through, so plug the bottom with wax before setting.  The screw pulls each
// insert up against the bar's underside, so its top finishes flush with the
// channel floor; wax the bar's underside as well as the screws.
bar_pilot_d       = 4.5 / 25.4;     // 4 mm OD insert + 0.25 mm per side for
                                    // epoxy and the bar-located float
bar_pilot_depth   = 6.5 / 25.4;     // below the channel floor: 6 mm insert +
                                    // 0.5 mm for the wax plug and epoxy
// Screw length L (flat head, overall) must satisfy bar_thick + 3 mm <= L <=
// bar_thick + 6 mm: at least 3 mm (1.5 d) of thread engaged, and no deeper
// than the insert.  bar_thick is unmeasured, so M2 x 6 is provisional.

// --- Grab holes, for turning the disc (Inches) ---
// On the 12 and 6 o'clock axis.  The N and S ChArUco targets slide sideways to
// make room; see docs/planning/disc-grab-holes-and-targets.md.
grab_d            = 1.0;            // ASSUMED finger-hole size; change to taste
grab_y            = [165.0 / 25.4, -175.0 / 25.4];   // N, S
grab_through      = true;           // false = 1/2" deep finger cups, no light leak

// --- ChArUco target keep-outs (Inches) ---
// ref 2 pieces: 3x3 boards cut 53.5 mm square (data/calibration/targets/).
// Not cut into the disc: these are layout ghosts and clearance checks only.
target_piece      = 53.5 / 25.4;
target_gap        = 3.0 / 25.4;     // to paper or bar edge
target_dx_ns      = 60.0 / 25.4;    // N target sits +X of the hole, S target -X
show_layout       = false;          // ghost the sheet, bar footprint and targets

// --- Display Mode Selector ---
// Options: "assembled", "exploded", "parts_grid", "top_ply", "bot_ply", "acrylic", "desk_ring"
view_mode         = "assembled";

// ============================================================================
// Helper Modules
// ============================================================================

module rounded_rect_2d(w, h, r) {
    offset(r = r)
        square([w - 2*r, h - 2*r], center = true);
}

module screw_positions() {
    for (sx = [-1, 1], sy = [-1, 1]) {
        translate([sx * screw_x_offset, sy * screw_y_offset, 0])
            children();
    }
}

// Peg bar channel, for a part whose top face is at local z = top_z.
module peg_channel(top_z) {
    translate([0, slot_ctr_y, top_z - slot_depth])
        linear_extrude(height = slot_depth + 0.05)
            rounded_rect_2d(slot_len, slot_w, slot_corner_r);
}

// Bar screw pilots, from the channel floor of a part whose top is at top_z.
module bar_pilots(top_z, depth) {
    for (sx = [-1, 1])
        translate([sx * bar_hole_sp / 2, peg_line_y, top_z - slot_depth - depth])
            cylinder(d = bar_pilot_d, h = depth + 0.05, $fn = 32);
}

module grab_holes(h) {
    for (gy = grab_y)
        translate([0, gy, 0]) cylinder(d = grab_d, h = h, $fn = 96);
}

// Derived layout, in disc coordinates (origin = optical centre).
sheet_far_y   = peg_line_y - punch_offset + sheet_h;   // +5.00"
sheet_edge_y  = peg_line_y - punch_offset;             // -5.50"
slot_lo_y     = slot_ctr_y - slot_w / 2;
slot_hi_y     = slot_ctr_y + slot_w / 2;
target_centres = [
    [ target_dx_ns, sheet_far_y + target_gap + target_piece / 2],      // N
    [ sheet_w / 2 + target_gap + target_piece / 2, 0],                 // E
    [-target_dx_ns, slot_lo_y - target_gap - target_piece / 2],        // S
    [-(sheet_w / 2 + target_gap + target_piece / 2), 0],               // W
];

// ============================================================================
// Individual Part Modules
// ============================================================================

// 1. Top 1/4" Plywood Layer (with 1/8" top outer round-over & recessed window cutout)
module part_top_plywood() {
    color("BurlyWood")
    difference() {
        // Outer profile with 1/8" top edge round-over
        rotate_extrude(convexity = 10) {
            union() {
                square([outer_dia/2 - top_round_r, top_ply_thick]);
                square([outer_dia/2, top_ply_thick - top_round_r]);
                translate([outer_dia/2 - top_round_r, top_ply_thick - top_round_r])
                    circle(r = top_round_r);
            }
        }
        // Through-cutout for acrylic window (includes 1/32" expansion gap)
        translate([0, 0, -0.05])
            linear_extrude(height = top_ply_thick + 0.1)
                rounded_rect_2d(acrylic_w + expansion_gap, acrylic_h + expansion_gap, corner_r);

        // ACME peg bar channel and the bar's screw pilots
        peg_channel(top_ply_thick);
        bar_pilots(top_ply_thick, top_ply_thick);

        // Grab holes.  A 1/2" cup is deeper than this ply, so it goes
        // through here either way; grab_through decides the bottom ply.
        translate([0, 0, -0.05])
            grab_holes(top_ply_thick + 0.1);
    }
}

// 2. Bottom 3/4" Plywood Layer (with 16 7/16" bottom step-down, 12x9 viewing hole, & insert pilot holes)
module part_bottom_plywood() {
    color("Peru")
    difference() {
        union() {
            // Lower stepped-down section (fits inside 16.5" desk hole)
            cylinder(d = step_dia, h = step_depth);
            // Upper lip section if step_depth < bot_ply_thick
            if (bot_ply_thick > step_depth) {
                translate([0, 0, step_depth])
                    cylinder(d = outer_dia, h = bot_ply_thick - step_depth);
            }
        }
        // 12" x 9" clear viewing window through-hole
        translate([0, 0, -0.05])
            linear_extrude(height = bot_ply_thick + 0.1)
                rounded_rect_2d(view_w, view_h, corner_r);

        // Pilot holes for #6-32 brass knife-thread inserts on top face of 3/8" ledges
        screw_positions() {
            translate([0, 0, bot_ply_thick - insert_depth])
                cylinder(d = insert_pilot_d, h = insert_depth + 0.05);
        }

        // Rest of the bar screw pilots, continuing down from the top ply.
        // The channel floor is in the top ply, so this layer carries
        // bar_pilot_depth - (top_ply_thick - slot_depth) of the hole.
        bar_pilots(bot_ply_thick + top_ply_thick, bar_pilot_depth);

        // Grab holes: through, or the lower part of a 1/2" cup
        translate([0, 0, grab_through ? -0.05
                                      : bot_ply_thick + top_ply_thick - 0.5])
            grab_holes(bot_ply_thick + 0.1);
    }
}

// 3. Removable 1/4" Clear Acrylic Window (12" x 9 3/4" with R1/8" corners & countersunk holes)
module part_acrylic_window() {
    color([0.75, 0.92, 1.0, 0.55])
    difference() {
        linear_extrude(height = acrylic_thick)
            rounded_rect_2d(acrylic_w, acrylic_h, corner_r);

        // 4 oversized clearance holes + 82-degree countersinks
        screw_positions() {
            // Clearance hole
            translate([0, 0, -0.05])
                cylinder(d = screw_clearance_d, h = acrylic_thick + 0.1);
            // Countersink cone at top surface
            translate([0, 0, acrylic_thick - csink_depth])
                cylinder(d1 = screw_clearance_d, d2 = csink_top_d, h = csink_depth + 0.01);
        }

        // The peg bar overlaps the acrylic's south strip, so the channel
        // continues across it (rout it with the acrylic screwed in place).
        peg_channel(acrylic_thick);
    }
}

// 5. Layout ghosts: sheet, image area and target pieces, on the top face.
module layout_ghosts(z) {
    translate([0, 0, z + 0.01]) {
        color([1, 1, 1, 0.35])
            translate([-sheet_w / 2, sheet_edge_y, 0])
                cube([sheet_w, sheet_h, 0.005]);
        color([0.2, 0.6, 1.0, 0.35])
            translate([-view_w / 2, -view_h / 2, 0.005])
                cube([view_w, view_h, 0.005]);
        for (c = target_centres)
            color([0.1, 0.1, 0.1, 0.6])
                translate([c[0] - target_piece / 2, c[1] - target_piece / 2, 0])
                    cube([target_piece, target_piece, 0.01]);
    }
}

// ============================================================================
// Clearance checks
// ============================================================================

assert(abs((image_hi - image_lo) - view_h) < 1e-6,
       str("Image area is ", image_hi - image_lo, " in tall; the window is ", view_h));
assert(image_lo >= 0 && image_hi <= sheet_h, "Image area falls off the sheet");

// The south screws must clear the bar: either beyond its ends or off its width.
assert(screw_x_offset - csink_top_d / 2 > slot_len / 2 + 0.25
       || screw_y_offset - csink_top_d / 2 > -slot_lo_y
       || screw_y_offset + csink_top_d / 2 < -slot_hi_y,
       str("A #6 countersink at x=", screw_x_offset, " lands under the peg bar"));
assert(screw_x_offset + csink_top_d / 2 < acrylic_w / 2 - 0.25,
       "Window screws too close to the acrylic's side edge");

// Bar screw pilots land in wood, south of the acrylic recess.
assert(-peg_line_y - bar_pilot_d / 2 - (acrylic_h + expansion_gap) / 2 > 3 / 25.4,
       str("Bar insert pocket leaves under 3 mm of wood to the acrylic recess"));
assert(top_ply_thick - slot_depth > 3 / 25.4, "Channel leaves under 3 mm of top ply");
// The bar's edge overhangs the punched edge by the measured 1/32", to within
// two ruler readings (+/- 1/64" each, so 0.04" combined).
assert(abs((sheet_edge_y - slot_lo_y) - 1 / 32) < 0.04,
       str("Bar overhangs the punched edge by ", sheet_edge_y - slot_lo_y,
           " in; measured 1/32 in"));
// The rect pegs must clear the bar's ends: outer ends at 102.722 mm spacing
// plus half a 12.75 mm peg.
// A centred bar's R2 corner arc must sit inside the channel's corner arc.
bar_corner_gap = slot_corner_r - bar_corner_r
                 - norm([(slot_len - bar_len) / 2 - (slot_corner_r - bar_corner_r),
                         (slot_w - 20.0 / 25.4) / 2 - (slot_corner_r - bar_corner_r)]);
assert(bar_corner_gap >= 0,
       str("Bar's corners foul the channel's by ", -bar_corner_gap * 25.4, " mm"));
assert(bar_len / 2 > (102.722 + 12.75 / 2) / 25.4,
       "Bar is shorter than its own rect pegs");
assert(norm([slot_len / 2, slot_lo_y]) < step_dia / 2 - 0.25,
       "Channel corner is too close to the step");

// Grab holes: inside the step (so a through hole opens into the desk hole,
// not onto the desk), and clear of the sheet, the bar and every target.
function sq_dist(p, c, half) =
    norm([max(abs(p[0] - c[0]) - half, 0), max(abs(p[1] - c[1]) - half, 0)]);
for (gy = grab_y) {
    assert(abs(gy) + grab_d / 2 < step_dia / 2 - 0.25,
           str("Grab hole at y=", gy, " reaches the step"));
    assert(gy > 0 ? gy - grab_d / 2 > sheet_far_y + 0.5
                  : gy + grab_d / 2 < slot_lo_y - 0.5,
           str("Grab hole at y=", gy, " is within 1/2 in of the paper or bar"));
    for (c = target_centres)
        assert(sq_dist([0, gy], c, target_piece / 2) - grab_d / 2 > 0.5,
               str("Grab hole at y=", gy, " is within 1/2 in of a target"));
}

// Targets: on the top face, and clear of the paper's corners.
for (c = target_centres) {
    far = max([for (sx = [-1, 1], sy = [-1, 1])
               norm([c[0] + sx * target_piece / 2, c[1] + sy * target_piece / 2])]);
    assert(far < outer_dia / 2 - top_round_r,
           str("Target at ", c, " runs onto the round-over"));
}

// 4. Reference Section of 3/4" Desk Top with 16 1/2" Cutout Hole
module part_desk_section() {
    desk_thick = 0.7585;
    desk_hole_dia = 16.5;
    color([0.45, 0.48, 0.52, 0.35])
    difference() {
        translate([-11, -11, 0])
            cube([22, 22, desk_thick]);
        translate([0, 0, -0.05])
            cylinder(d = desk_hole_dia, h = desk_thick + 0.1);
    }
}

// ============================================================================
// Assemblies & Layout Views
// ============================================================================

module assembly_complete(include_desk = false) {
    // Bottom 3/4" plywood layer (Z = 0 to 0.75)
    part_bottom_plywood();

    // Top 1/4" plywood layer (Z = 0.75 to 1.00)
    translate([0, 0, bot_ply_thick])
        part_top_plywood();

    // Removable 1/4" acrylic window seated flush in top recess (Z = 0.75 to 1.00)
    translate([0, 0, bot_ply_thick])
        part_acrylic_window();

    // Optional reference desk section showing flush fit
    if (include_desk) {
        part_desk_section();
    }

    if (show_layout) {
        layout_ghosts(bot_ply_thick + top_ply_thick);
    }
}

module assembly_exploded() {
    part_bottom_plywood();

    translate([0, 0, bot_ply_thick + 1.25])
        part_top_plywood();

    translate([0, 0, bot_ply_thick + 2.75])
        part_acrylic_window();
}

module parts_laid_out() {
    // Bottom plywood layer at origin
    part_bottom_plywood();

    // Top plywood layer to the right
    translate([outer_dia + 2.0, 0, 0])
        part_top_plywood();

    // Acrylic window below
    translate([0, -(outer_dia/2 + acrylic_h/2 + 2.0), 0])
        part_acrylic_window();
}

// ============================================================================
// Render Dispatcher
// ============================================================================

if (view_mode == "assembled") {
    assembly_complete(include_desk = false);
} else if (view_mode == "assembled_in_desk") {
    assembly_complete(include_desk = true);
} else if (view_mode == "exploded") {
    assembly_exploded();
} else if (view_mode == "parts_grid") {
    parts_laid_out();
} else if (view_mode == "top_ply") {
    part_top_plywood();
} else if (view_mode == "bot_ply") {
    part_bottom_plywood();
} else if (view_mode == "acrylic") {
    part_acrylic_window();
}
