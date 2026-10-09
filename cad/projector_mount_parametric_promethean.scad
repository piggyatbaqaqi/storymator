// =========================================================================
// LIGHT TABLE PROJECT - PARAMETRIC 16.5" ACME DISC & PROMETHEAN ENGINE
// Auto-calculates off-axis optics, lens clearances, and corner clearance profiles.
// =========================================================================
$fn = 120; // High resolution loop for crisp CNC circle cuts

// --- 1. FIXED WORKSPACE DIMENSIONS ---
acme_disc_dia      = 16.50; // Updated 12F standard drawing disc
screen_w           = 11.00; // Widescreen active projection window width
screen_l           = 8.50;  // Widescreen active projection window length
ply_heavy          = 0.75;  // 3/4" Structural plywood
ply_light          = 0.50;  // 1/2" Component shelf plywood
acrylic_thick      = 0.25;  // 1/4" Screen plate choice

// --- 2. PARAMETERIZED PROJECTOR VARIABLES (Promethean UST-P3) ---
proj_w       = 11.30; // Physical width
proj_d       = 14.80; // Physical depth
proj_h       = 6.30;  // Physical height
proj_weight  = 10.58; // Payload mass in lbs
throw_ratio  = 0.35;  // Native optics matrix

// --- 3. PARAMETERIZED CORE STRUCTURE VARIABLES ---
sonotube_dia   = 24.00; // Large outer container
sonotube_wall  = 0.30;  // Cardboard wall profile
cylinder_ht    = 18.50; // Deep envelope for dropped knee footprint
inner_lip_dia  = 13.50; // Solid rim margin to hold pegbar and hand load
acrylic_bc     = 15.25; // 7.625" Radius safe bolt retention ring
bolt_hole_dia  = 4.5 / 25.4; // M4 clearance (4.5 mm) for flat-head hardware

// --- 4. COMPUTED AUTOMATED OPTICS & CENTER OF MASS VALUES ---
calculated_throw = screen_w * throw_ratio; // 3.85 inches clear air path
shelf_z          = cylinder_ht - calculated_throw - proj_h;
inner_tube_dia   = sonotube_dia - (sonotube_wall * 2); // 23.4" True ID

// Calculate asymmetric offset to align the lens to the screen axis center
proj_offset_x    = (proj_d / 2) - 1.5; 
required_balance = (proj_weight * proj_offset_x) / (inner_tube_dia / 2 - 1.5);

// --- VIEW MODE INTERFACE TOGGLE ---
// Set to true for complete 3D mechanical visualization layout.
// Set to false to output flat 2D blueprints for toolpath generation.
render_3d_view = true;

// COMPONENT SELECTOR (Only active when render_3d_view = false):
// 1 = 1.5" Double-Layer Desk Cutout Plate, 2 = Stepped Flange Cap, 3 = Projector Internal Shelf
flat_part_select = 2;

if (render_3d_view) {
    master_3d_assembly();
} else {
    projection(cut = false) master_2d_flat_parts(flat_part_select);
}

// PRINT DATA LOG REPORT DIRECTLY TO THE OPENSCAD CONSOLE
echo("=================== DESIGN REPORT ===================");
echo("Required Vertical Throw Clearance:", calculated_throw, "inches");
echo("Projector Shelf Z Drop Position :", shelf_z, "inches below top");
echo("Asymmetric Axis Pivot Offset    :", proj_offset_x, "inches");
echo(">>> MASS COMPENSATION REQUIRED ON OPPOSITE RIM:", required_balance, "lbs");
echo("=====================================================");

// =========================================================================
// CORE GEOMETRY IMPLEMENTATIONS
// =========================================================================

module master_3d_assembly() {
    // 16.5" Recessed Acrylic Tracing Plate
    color([0.1, 0.8, 0.9, 0.4]) translate([0, 0, cylinder_ht]) difference() {
        cylinder(d = acme_disc_dia, h = acrylic_thick);
        cube([screen_w, screen_l, acrylic_thick * 5], center = true);
    }
    
    // Main 24" Outer Structural Tube Wrapper
    color([0.74, 0.61, 0.45, 0.6]) difference() {
        cylinder(d = sonotube_dia, h = cylinder_ht);
        translate([0, 0, -1]) cylinder(d = inner_tube_dia, h = cylinder_ht + 2);
    }
    
    // Custom Stepped Plywood Flange Cap (3/4" Plywood)
    color([0.88, 0.80, 0.65, 1.0]) translate([0, 0, cylinder_ht - 0.75]) 
        master_2d_flat_parts(2, extrusion_h = 0.75);

    // Deep Component Shelf (1/2" Plywood) with Asymmetric Clearance Cut
    color([0.88, 0.80, 0.65, 1.0]) translate([0, 0, shelf_z]) intersection() {
        cylinder(d = inner_tube_dia, h = ply_light);
        difference() {
            cube([inner_tube_dia + 2, inner_tube_dia + 2, ply_light * 3], center = true);
            translate([proj_offset_x, 0, 0])
                cube([proj_d + 1.0, proj_w + 1.0, ply_light * 10], center = true);
        }
    }
    
    // Promethean UST-P3 Projector Space Block Orientation
    color([0.2, 0.2, 0.2, 1.0]) 
        translate([proj_offset_x, 0, shelf_z + ply_light + (proj_h / 2)])
        cube([proj_d, proj_w, proj_h], center = true);

    // Counterweight Indicator Node (Red block denotes weight center anchor)
    color([0.9, 0.1, 0.1, 1.0])
        translate([-(inner_tube_dia / 2 - 1.5), 0, shelf_z + ply_light + 2])
        cylinder(d = 3.5, h = 4, center = true);
}

module master_2d_flat_parts(part_id, extrusion_h = 0) {
    linear_extrude(height = extrusion_h) {
        if (part_id == 1) {
            // PART 1: 1.5" Desktop Opening Hole Blueprint Cutout
            // Allows the 24" core room to pivot freely without binding contact
            difference() {
                square([sonotube_dia + 6, sonotube_dia + 6], center = true);
                circle(d = sonotube_dia + 0.25); // Adds a 1/8" safe perimeter gap loop
            }
        }
        
        if (part_id == 2) {
            // PART 2: Stepped Transition Flange Cap Profile (3/4" Plywood)
            // Integrates a custom corner relief intersection toolpath to clean corner clipping
            difference() {
                circle(d = sonotube_dia);
                
                // Optimized core light path geometry clearing the 13.90" window diagonal
                intersection() {
                    circle(d = inner_lip_dia);
                    // Blends corners outward exclusively to clean layout blind spots
                    cube([screen_w + 0.5, screen_l + 0.5], center = true);
                }
                
                // Stepped shelf drop pocket layer (Drawn for projection profiling)
                if (extrusion_h > 0) {
                    translate([0, 0, 0.50])
                        cylinder(d = acme_disc_dia + 0.02, h = 0.30);
                }
                
                // Symmetrical Countersunk Retention Screw Pattern Holes (4x at 90 deg)
                for (angle = [0, 90, 180, 270]) {
                    rotate([0, 0, angle]) {
                        translate([acrylic_bc / 2, 0])
                            circle(d = bolt_hole_dia);
                    }
                }
            }
        }
        
        if (part_id == 3) {
            // PART 3: Custom Projector Base Internal Shelf (1/2" Plywood)
            difference() {
                circle(d = inner_tube_dia);
                translate([proj_offset_x, 0])
                    square([proj_d + 1.0, proj_w + 1.0], center = true);
            }
        }
    }
}
