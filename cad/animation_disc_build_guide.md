# Custom 17 1/2-Inch Animation Disc & Desk Cutout Guide

## Project Specifications & Geometry
* **Outer Disc Diameter:** 17 1/2 inches (1 inch total thickness, 1/8-inch radius rounded top edge)
* **Bottom Step-Down Diameter:** 16 1/2 inches (~16 7/16 inches target for smooth rotation) to fit a 16 1/2-inch hole in a 3/4-inch nominal (0.7585-inch actual) desk
* **Clear Viewing Opening (Bottom Layer):** 12 inches × 9 inches
* **Removable Acrylic Window:** 1/4-inch thick clear cast acrylic cut to **12 inches × 9 3/4 inches** (provides a 3/8-inch supporting ledge at the top and bottom, 0-inch overlap on the left/right edges, and 1/8-inch radius rounded corners)
* **Top Layer Window Recess:** **12 1/32 inches × 9 25/32 inches** (provides a 1/32-inch total expansion gap)
* **Corner Clearance:** Outermost window corners sit 7.73 inches from the disc center, leaving **1.02 inches** of solid wood rim at the narrowest points
* **Window Centring:** the window is centred on the 12F sheet's **12" × 9" image area**, which runs 1.00"–10.00" from the punched edge (optical centre 5.50" from it) — not on the 12 1/2" × 10 1/2" sheet
* **ACME Peg Bar Channel:** for the **Honbay** bar this project uses (`honbay_0001`, https://www.amazon.com/dp/B0721MR5TM). Peg bars are not standardised in width or length, so another bar needs its own numbers. **252.3 mm × 20.3 mm × 1.5 mm deep** (the 9 7/8" × 20 mm bar plus 1.5 mm of end and 0.3 mm of side clearance), R1/8" (3.175 mm) corners, centred on the peg line **5 5/32" south** of the disc centre (pegs 11/32" from the punched edge), so running from **5.556" to 4.757" south**. The bar is symmetric: its pegs are centred across it to 0.2 mm. The bar's own corners are R2.0 mm; the clearances let them sit inside the channel's R1/8" corners with under 0.1 mm to spare, so pare a corner with a chisel if it binds
* **Grab Holes:** two 1" holes on the 12 and 6 o'clock axis, 6.50" north and 6.89" south of centre; ChArUco targets sit beside them, not on them — see `docs/planning/disc-grab-holes-and-targets.md`
* **Primary Router:** Bosch 1617EVSPK (1/4-inch collet, 12-Amp, 2.25-HP variable speed combo fixed/plunge router) with Milescraft Circle Guide Kit

---

## 1. Rationale for the 2-Piece Laminated Design

Building the 1-inch thick disc from **two laminated pieces of plywood (1/4-inch top layer + 3/4-inch bottom layer)** is recommended over a 1-piece or 3-piece construction. Laminating a 1/4-inch top sheet to a 3/4-inch bottom sheet creates the exact 1/4-inch deep window recess automatically and delivers a dead-flat, factory-smooth supporting ledge without requiring a router sled.

### Comparison of Layering Methods

| Build Method | Layer Breakdown | Pros | Cons |
| :--- | :--- | :--- | :--- |
| **2 Pieces (Recommended)** | **1/4" Top + 3/4" Bottom** | Exact 1/4" window depth; flat factory surface for acrylic ledge; standard sheet thicknesses. | Requires clamping a full-surface glue-up without shifting. |
| **1 Piece** | Single 1" Slab | Zero glue-ups required. | 1" plywood is rare; routing a flat 1/4" interior shelf is tedious; higher warp risk. |
| **3 Pieces** | 1/4" Top + 1/2" Mid + 1/4" Bot | Can form both the window ledge and bottom step via cutouts. | Extra glue seams; harder to keep thin rings flat and aligned during clamping. |

---

## 2. Step-by-Step Execution Instructions

### Phase A: Prepare the Acrylic Window
1. **Cut Acrylic to Size:** Apply blue painter's tape along the cut lines (leaving the protective paper film intact). Using a fine-tooth skip-tooth or metal-cutting blade at a slow speed on your scroll saw, cut the 12" × 12" acrylic stock down to **12" × 9 3/4"**.
2. **Round the Four Corners:**
   * Rough-snip or sand the four corners close to shape so the router only takes a light skim pass.
   * Attach the **R1/8" aluminum corner radius jig** to one corner using double-sided woodworking/carpet tape.
   * Set your Bosch router to **Speed 1–2 (8,000–12,000 RPM)** with a **top-bearing flush-trim bit** and make one smooth, continuous pass around the corner. Repeat for all four corners.
3. **Drill & Countersink Mounting Holes:**
   * Mark 4 fastener locations centered along the top and bottom 3/8-inch overlap margins (3/16" from the top and bottom edges), **5.5" either side of centre** (11" apart). At 4.5" the two south screws would sit under the peg bar.
   * Drill oversized **5/32-inch** clearance holes (to allow thermal expansion without cracking) and recess each hole with an **82-degree countersink bit** so #6-32 flat-head screws sit dead flush.

### Phase B: Cut the Window Openings & Laminate the Plywood Disc
1. **Prepare MDF Spoilboard & Template Strips:** Cut a **20" × 20" sacrificial spoilboard** from your 2' × 4' sheet of 1/2-inch MDF, and cut the remaining MDF into four straight strips for your rectangular window template frame.
2. **Rout the Top 1/4-Inch Layer Cutout:**
   * Clamp/tape the four MDF template strips around a **12 1/32" × 9 25/32"** opening onto your 1/4-inch plywood blank (resting on the MDF spoilboard).
   * Using a **1/4-inch solid carbide downcut spiral bit** at **Speed 4–5 (18,000–21,000 RPM)**, rout the through-hole in **2 shallow passes**, vacuuming the kerf between passes.
3. **Rout the Bottom 3/4-Inch Layer Cutout:**
   * Reconfigure the MDF template strips to **12" × 9"** on your 3/4-inch plywood blank.
   * Rout the light-pass-through hole in **4 shallow passes (~0.20" each)**, vacuuming compacted sawdust out of the groove after every pass.
4. **Test-Fit & Glue the Layers:**
   * Dry-fit the acrylic window into the 1/4-inch top plywood layer and sand any tight spots before gluing.
   * Apply PVA wood glue between the 1/4-inch and 3/4-inch layers and align the cutouts. Drive two 5/8-inch brad nails into the **outer corners** (well outside the 17 1/2-inch circle line) to prevent sliding under clamp pressure.
   * Place wax paper or painter's tape over two 2×4 clamping cauls, lay them across the center of the blank, and tighten 4–6 bar clamps around the outer perimeter and across the interior window ledges.

### Phase C: Shape the 17 1/2-Inch Disc & Bottom Step-Down
1. **Cut the 17 1/2-Inch Outer Circle:**
   * Mount your Bosch plunge router to your circle jig and secure the glued blank to the sacrificial MDF spoilboard.
   * Using the **1/4-inch downcut spiral bit** at **Speed 4–5**, cut the 1-inch laminated blank to a **17 1/2-inch diameter** in 4 to 5 shallow passes, vacuuming the channel between every pass.
   * *Caution:* Where the window corners approach within ~1 inch of the outer rim, feed steadily against bit rotation (counter-clockwise around an outside cut) and avoid climb-cutting to prevent blowout.
2. **Rout the 16 1/2-Inch Bottom Step-Down:**
   * Flip the disc upside down. Adjust your circle jig (or use a bearing-guided rabbet bit) to cut a 1/2-inch wide rabbet ~3/4-inch deep around the bottom perimeter so the lower step measures **~16 7/16 inches** in diameter (allowing smooth rotation inside the 16 1/2-inch desk hole).
3. **Round the Top Outer Edge:**
   * Flip the disc right-side up. Install the **1/8-inch radius round-over bit** at **Speed 5 (~21,000 RPM)** and feed counter-clockwise around the top perimeter in one smooth pass.
4. **Install Brass Threaded Inserts:**
   * Align the acrylic window in the top recess and mark the 4 screw centers onto the 3/8-inch top and bottom ledges of the 3/4-inch plywood layer.
   * Drill pilot holes per the insert manufacturer's spec and thread **#6-32 brass knife-thread inserts** flush into the plywood (sand ~1/16" off the tip of each insert first if needed so they cannot poke through the underside).

5. **Rout the Peg Bar Channel (after the inserts, with the acrylic screwed in):**
   * The bar overlaps the acrylic's south strip by ~3.3 mm, so the channel must cross the seam. Screw the acrylic in place first so wood and acrylic are cut flush in one pass.
   * Clamp MDF template strips around a 252.3 × 20.3 mm opening whose south side is **5.556"** south of centre (north side 4.757"), and rout 1.5 mm deep with the 1/4" bit (R1/8" corners). Use Speed 1–2 where the bit crosses into the acrylic. Check the template against the bar itself before routing: the bar is 19.92–19.99 mm wide in a 20.3 mm channel.
   * Seat the bar in the channel and transfer-punch its two screw holes; the holes are 58.05 mm from each end, but their position across the bar has not been measured.
   * **Set M2 brass inserts in epoxy, located by the bar.** The bar's holes are 2.0 mm and countersunk, which leaves an M2 screw (1.86–1.98 mm thread) almost no float, so the inserts must land exactly on the holes' axes. Drill a **4.0 mm pocket 6 mm deep** below the channel floor at each punch mark (about 4.7 mm of wood remains to the acrylic recess). Wax two M2 × 6 flat-head screws. Put a ~3.2–3.5 mm OD knurled brass insert on each, part-fill the pockets with slow-set epoxy, seat the bar in the channel and screw it down through the inserts so they hang in the pockets on the screws' axes. Let it cure fully, then back the screws out.
   * Use **metric 90° flat heads**: a countersink for 2 mm screws is most likely 90°, though the bar's has not been measured; #2-56 flat heads are 82°. Check that the heads sit flush or below the bar's surface, because the sheet lies on it.
   * The acrylic now comes out only after the bar is unscrewed.
6. **Drill the Grab Holes:** 1" Forstner bit at 6.50" north and 6.89" south of centre on the centre line, through both plies over a backer (or 1/2" deep for blind finger cups, which also keeps light from leaking through).

### Phase D: Cut the 16 1/2-Inch Hole in the Desk (Router Safety & Tab Method)
1. **Secure the Sacrificial MDF Backer Board:**
   * Place the desk flat on sawhorses or floor blocks (do not rout on a tilted surface).
   * Locate the exact center point on top of the desk and lightly trace the 16 1/2-inch cutout circle.
   * Hold the 20" × 20" piece of 1/2-inch MDF flush against the underside of the desk and drive four **1-inch coarse-thread screws** straight up through the MDF into the **interior waste area** (1–2 inches inside the cut line, avoiding the dead-center pivot pin). This prevents bottom veneer blowout without requiring deep-reach clamps.
2. **Configure Speed, Turret Stops & Feed Direction:**
   * Install the **1/4-inch downcut spiral bit** (protects top veneer from tear-out) and set your Bosch router to **Speed 4–5 (18,000–21,000 RPM)**.
   * Set the revolving depth turret on your plunge base for 4 passes: **0.20"**, **0.40"**, **0.60"**, and **0.80"** (which cuts ~0.04" into the MDF backer).
   * For an **inside circle cutout**, always move the router **clockwise** around the pivot pin so the bit pulls outward against the jig's radius limit rather than diving inward.
   * Move briskly and steadily; vacuum compacted sawdust out of the narrow groove after every pass.
3. **Prevent the Center Waste Disc from Dropping ("Tab & Bridge" Method):**
   * Complete full 360-degree circles on **Passes 1, 2, and 3 (0.20", 0.40", 0.60")**, leaving ~0.16" of solid material holding the 6–8 lb center plug level.
   * On **Pass 4 (0.80" full depth)**, rout clockwise around the circle, **stopping 1 inch short** of your starting point. Lift the plunge base, skip over a **1-inch uncut tab**, plunge back down, and leave a **second 1-inch uncut tab** 180 degrees opposite the first.
   * Wait for the bit to stop completely before lifting the router.
   * Support the center plug from underneath with scrap blocks or a box, then sever the two 1-inch tabs from above using a flush-cut pull saw or utility knife.
   * Clean up the two tab spots with one zero-load skim pass using your top-bearing flush-trim bit.

---

## 3. Complete Shopping List

### Router Bits & Corner Jig (1/4-Inch Shank)
* **1/4-Inch Solid Carbide Downcut Spiral Router Bit (1/4-Inch Cutting Diameter):** e.g., POWERTEC 73004 — protects top veneer on both the desk and birch plywood while cutting circles and window openings.
* **Top & Bottom Bearing Flush-Trim Router Bit (1/4-Inch Shank):** e.g., Yonico 14982q — rides along the corner jig and MDF templates to flush-trim acrylic corners and plywood openings.
* **1/8-Inch Radius Round-Over Router Bit (1/4-Inch Shank):** e.g., Yonico 13060q — eases the top outer edge of the 17 1/2-inch disc.
* **7-Piece Aluminum Router Corner Radius Jig Set:** e.g., WEN RA001R — includes the **R1/8"** template profile to match your 1/4-inch router bit corners.

### Sheet Goods & Clamping Cauls
* **1/4-Inch Baltic Birch or Cabinet-Grade Plywood (2' × 2' or 2' × 4' panel):** Measure in-store with calipers to confirm actual thickness is close to 0.235"–0.250" to match the acrylic.
* **3/4-Inch Cabinet-Grade Plywood (2' × 2' or 2' × 4' panel):** Bottom structural layer of the disc.
* **1/2-Inch MDF Handy Panel (2' × 4'):** Cut into one 20" × 20" sacrificial spoilboard/desk backer and four window template strips.
* **Scrap 2×4 Offcut (18–24 inches long):** Cut into two clamping cauls to distribute clamp pressure across the middle of the disc during glue-up.

### Fasteners, Adhesives & Shop Consumables
* **#6-32 Brass Knife-Thread Inserts (Pack of 25):** e.g., E-Z Lok 400-006 (install 4 inserts flush into the top and bottom 3/8-inch plywood ledges).
* **#6-32 × 1/2" Stainless Steel Flat-Head Machine Screws (4+ screws):** For removable, flush mounting of the acrylic window.
* **M2 × 6 mm Stainless Flat-Head (90°) Machine Screws (2+) and M2 Knurled Brass Inserts, ~3.2–3.5 mm OD (2+):** for the removable peg bar. The bar comes off whenever the acrylic does, and wood screws would strip the plywood after a few removals.
* **Slow-Set Epoxy and Paste Wax:** epoxy sets the bar's inserts; wax on the screws keeps them from being glued in.
* **82-Degree Countersink Drill Bit:** For recessing the #6-32 screw heads flush into the acrylic.
* **1-Inch Coarse-Thread Wood or Drywall Screws (1 small box):** For fastening the 1/2-inch MDF backer up into the waste center of the 3/4-inch desk without poking through the top veneer.
* **5/8-Inch Brad Nails (or small alignment screws):** Driven into the outer waste corners of the plywood blanks to prevent sliding during glue-up.
* **PVA Wood Glue:** e.g., Titebond II or III.
* **Double-Sided Woodworking / Carpet Tape:** For securing the aluminum corner jig and MDF templates.
* **Blue Painter's Tape & Wax Paper:** Painter's tape protects acrylic during scroll-sawing; wax paper keeps glue squeeze-out from sticking to 2×4 clamping cauls.

### Clamps & Dust Extraction
* **24-Inch Capacity Bar Clamps (Quantity: 4 to 6):** e.g., BESSEY Clutch Style Bar Clamps (GSCC2.524) — spans the 20-inch blanks and reaches inside the window opening.
* **Cordless Handheld Vacuum with Crevice Nozzle & Hose:** e.g., RYOBI ONE+ 18V Cordless GoGoVac Kit (PCL731K) — clears compacted sawdust from the narrow 1/4-inch downcut router kerf between passes.
