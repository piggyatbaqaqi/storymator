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
screw_x_offset    = 4.5;      // Horizontal spacing from center (+/- 4.5" -> 9" apart)
screw_y_offset    = 4.6875;   // Centered in the 3/8" top/bottom ledge (4.5" + 0.1875" = 4.6875")

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
    }
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
