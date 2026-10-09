// =========================================================================
// LIGHT TABLE PROJECT - 16.5" ACME DISC STEPPED OVERHANG FLANGE CAP
// Custom adaptation ring for 24" Sonotube foundation core
// =========================================================================
$fn = 180;

sonotube_outer_dia  = 24.00; 
acrylic_disc_dia    = 16.50; // Updated 12F standard diameter
inner_clearance_dia = 13.50; // Narrowed to provide perimeter structural lip
acrylic_bolt_circle = 15.25; // Adjusted 7.625" bolt radius
bolt_hole_dia       = 4.5 / 25.4; // M4 clearance, 4.5 mm expressed in this file's inches

render_3d_preview = true; 

if (render_3d_preview) {
    stepped_flange_cap_3d();
} else {
    projection(cut = false) stepped_flange_cap_2d();
}

module stepped_flange_cap_3d() {
    difference() {
        // Main structural plywood transition blank
        color([0.88, 0.80, 0.65, 1.0])
            cylinder(d = sonotube_outer_dia, h = 0.75, center = false);
        
        // 1. Recalculated central light path window
        translate([0, 0, -1])
            cylinder(d = inner_clearance_dia, h = 3.0, center = false);
            
        // 2. Swapped Drop-In Step Pocket for the 16.5" disc
        translate([0, 0, 0.50]) 
            cylinder(d = acrylic_disc_dia + 0.02, h = 0.30, center = false);
            
        // 3. 4x Symmetrical Countersunk Fasteners at 15.25" BC
        for (angle = [0, 90, 180, 270]) {
            rotate([0, 0, angle]) {
                translate([acrylic_bolt_circle / 2, 0, -1])
                    cylinder(d = bolt_hole_dia, h = 3.0);
            }
        }
    }
}

module stepped_flange_cap_2d() {
    difference() {
        circle(d = sonotube_outer_dia);
        circle(d = inner_clearance_dia);
        for (angle = [0, 90, 180, 270]) {
            rotate([0, 0, angle]) {
                translate([acrylic_bolt_circle / 2, 0])
                    circle(d = bolt_hole_dia);
            }
        }
    }
}
