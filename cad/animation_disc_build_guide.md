# Custom 17 1/2-Inch Animation Disc & Desk Cutout Guide

## Project Specifications & Geometry
* **Outer Disc Diameter:** 17 1/2 inches (1 inch total thickness, 1/8-inch radius rounded top edge)
* **Bottom Step-Down Diameter:** 16 1/2 inches (~16 7/16 inches target for smooth rotation) to fit a 16 1/2-inch hole in a 3/4-inch nominal (0.7585-inch actual) desk
* **Clear Viewing Opening (Bottom Layer):** 12 inches × 9 inches
* **Removable Acrylic Window:** 1/4-inch thick clear cast acrylic cut to **12 inches × 9 29/32 inches** (0-inch overlap on the left/right edges, 1/8-inch radius rounded corners). It sits off-centre: it runs **4 63/64 in north** and **4 59/64 in south** of the optical centre, giving supporting ledges of **12.3 mm (north) and 10.7 mm (south)** beyond the 9 in opening. The ledges are as wide as the N ChArUco target and the peg bar's insert pockets allow; see docs/planning/disc-acrylic-ledge.md. Put back the wrong way up, its screw holes won't line up with the inserts.
* **Top Layer Window Recess:** **12 1/32 inches × 9 15/16 inches** (a 1/32-inch total expansion gap), running **5.000 in north** and **4 15/16 in south** of the disc centre, so it is centred 1/32 in north
* **Corner Clearance:** The recess's north corners (R1/8") sit 7.77 inches from the disc center, leaving **0.98 inches** of solid wood rim at the narrowest points
* **Window Centring:** the window is centred on the 12F sheet's **12" × 9" image area**, which runs 1.00"–10.00" from the punched edge (optical centre 5.50" from it) — not on the 12 1/2" × 10 1/2" sheet
* **ACME Peg Bar Channel:** for the **Honbay** bar this project uses (`honbay_0001`, https://www.amazon.com/dp/B0721MR5TM). Peg bars are not standardised in width or length, so another bar needs its own numbers. **252.3 mm × 20.3 mm × 1.4 mm deep**, flush with the 1.40 mm bar (the 9 7/8" × 20 mm bar plus 1.5 mm of end and 0.3 mm of side clearance), R1/8" (3.175 mm) corners, centred on the peg line **5 5/32" south** of the disc centre (pegs 11/32" from the punched edge), so running from **5.556" to 4.757" south**. The bar is symmetric: its pegs are centred across it to 0.2 mm. The bar's own corners are R2.0 mm; the clearances let them sit inside the channel's R1/8" corners with under 0.1 mm to spare, so pare a corner with a chisel if it binds
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
1. **Cut Acrylic to Size:** Apply blue painter's tape along the cut lines (leaving the protective paper film intact). Using a fine-tooth skip-tooth or metal-cutting blade at a slow speed on your scroll saw, cut the 12" × 12" acrylic stock down to **12" × 9 29/32"**. Mark the edge that will face north (away from the peg bar) on the protective film.
2. **Round the Four Corners:**
   * Rough-snip or sand the four corners close to shape so the router only takes a light skim pass.
   * Attach the **R1/8" aluminum corner radius jig** to one corner using double-sided woodworking/carpet tape.
   * Set your Bosch router to **Speed 1–2 (8,000–12,000 RPM)** with a **top-bearing flush-trim bit** and make one smooth, continuous pass around the corner. Repeat for all four corners.
3. **Drill & Countersink Mounting Holes:**
   * Mark 4 fastener locations **5.5" either side of centre** (11" apart), each centred on its ledge: **31/128 in (6.15 mm) in from the north edge** and **27/128 in (5.36 mm) in from the south edge**. They are not the same, because the ledges differ. At 4.5" the two south screws would sit under the peg bar.
   * Drill **3.2 mm (1/8")** holes only for now. They locate the inserts in Phase C step 4, and are opened to 4.0 mm and countersunk after that.
   * **Drilling acrylic:** an ordinary twist drill grabs acrylic as it breaks through and can crack it, and these holes are only 5–6 mm from the edge. Use a bit ground for plastics, or dub a woodworking twist bit: stone a tiny flat on each cutting lip so it scrapes rather than bites. Run slow, peck, keep the film on, and clamp the acrylic to a scrap backer. The Dremel (lowest speed) or the drill guide both work for these 1/8" holes.

### Phase B: Cut the Window Openings & Laminate the Plywood Disc
1. **Prepare MDF Spoilboard & Template Strips:** Cut a **20" × 20" sacrificial spoilboard** from your 2' × 4' sheet of 1/2-inch MDF, and cut the remaining MDF into four straight strips for your rectangular window template frame.
2. **Rout the Top 1/4-Inch Layer Cutout:**
   * Clamp/tape the four MDF template strips around a **12 1/32" × 9 15/16"** opening onto your 1/4-inch plywood blank, its north side **5.000"** and its south side **4 15/16"** from the disc centre (resting on the MDF spoilboard).
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
   * Align the acrylic window in the top recess and mark the 4 screw centers onto the north and south ledges of the 3/4-inch plywood layer.
   * **Set M3 brass inserts in epoxy, located by the acrylic.** The inserts are M3 × 7 mm long × 5 mm OD knurled brass heat-set inserts for 3D printing. Don't heat-set them, since wood won't melt round them; epoxy them.
     * **Why these:** hardwood #6-32 knife-thread inserts are sold as "not recommended for use in plywood", because their threads cut across cross-grain plies and glue lines. They also cut wider than their pilot, and these inserts sit only 6.15 mm (north) and 5.36 mm (south) from the window opening. Barbed "furniture nuts" wedge the hole open, which is what splits a thin wall, and the smallest are M4 with flanges as wide as the south ledge. An epoxied knurled insert puts no outward force on the wall.
     * **Drill the pockets:** **5.5 mm (or 7/32"), 7.5 mm deep**, square to the ledge in the portable drill guide, with its depth stop set from the bit's corners, not its point. Clamp a scrap block against the opening edge as a backer. Centre each pocket on a 1/8" transfer-punch mark made through the acrylic's 3.2 mm hole. A brad-point bit centres best; a twist bit is fine in the guide. That leaves 3.4 mm (north) and 2.6 mm (south) of wood to the opening.
     * **Set them:** press a little wax into the bottom end of each insert, since they are threaded through. Wax four **M3 × 12 flat-head** screws, and wax the underside of the acrylic around its holes. Part-fill the pockets with slow-set epoxy, and put the acrylic in its recess. Put each screw through its 3.2 mm hole, thread an insert on underneath, and tighten. Tightening pulls each insert up against the acrylic, so it ends flush with the ledge, centred on the hole to ±0.1 mm. Let it cure fully, then back the screws out.
     * **Then finish the acrylic's holes:** open them to **4.0 mm**, for 0.5 mm of float per side; over 20 °C the acrylic moves about 0.18 mm per side against the plywood. Countersink each with a **90° countersink** to 6.7 mm across, so the screw heads sit flush.

5. **Rout the Peg Bar Channel (after the inserts, with the acrylic screwed in):**
   * The bar overlaps the acrylic's south strip by ~4.6 mm, so the channel must cross the seam. Screw the acrylic in place first so wood and acrylic are cut flush in one pass.
   * Clamp MDF template strips around a 252.3 × 20.3 mm opening whose south side is **5.556"** south of centre (north side 4.757"), and rout **1.4 mm** deep with the 1/4" bit (R1/8" corners). Set the depth from the bar itself, not a scale: stand it on the router base beside the bit and bring the bit down to its top face. The bar is about 1.40 mm thick, and its top should finish flush with the disc, because the sheet's punched strip lies on it. Use Speed 1–2 where the bit crosses into the acrylic. Check the template against the bar itself before routing: the bar is 19.92–19.99 mm wide in a 20.3 mm channel.
   * Seat the bar in the channel and transfer-punch its two screw holes with a **3/32"** punch (2.38 mm, in the bar's 2.42 mm holes); the holes are 58.05 mm from each end, but their position across the bar has not been measured.
   * **Set M2 brass inserts in epoxy, located by the bar.** The bar's holes are 2.42 mm and countersunk, a standard M2 clearance that leaves the screw (1.86–1.98 mm thread) only 0.2–0.28 mm of float per side. A hand-drilled insert can be off by more than that, so let the bar place them. Drill a **4.5 mm (or 3/16") pocket 6.5 mm deep** below the channel floor at each punch mark, in the drill guide as for the window inserts (about 3.3 mm of wood remains to the acrylic recess). The inserts are M2 × 6 mm long × 4 mm OD knurled brass heat-set inserts for 3D printing. Don't heat-set them, since wood won't melt round them; epoxy them. They are threaded through, so press a little wax into the bottom end of each to keep epoxy out of the thread. Wax two M2 flat-head screws, and wax the underside of the bar around its holes. Thread an insert onto each screw, part-fill the pockets with slow-set epoxy, seat the bar in the channel and screw it down. Tightening pulls each insert up against the bar, so it ends flush with the channel floor, centred on the screw's axis. Let it cure fully, then back the screws out.
   * **Use M2 × 6 screws.** The bar is about 1.40 mm thick, so a flat-head length L needs 4.4 mm ≤ L ≤ 7.4 mm: at least 3 mm of thread engaged, and no deeper than the 6 mm insert. M2 × 6 engages 4.6 mm, more than twice the screw's diameter. M2 × 8 would reach 6.6 mm below the bar, past the 6.5 mm pocket floor, and bottom out before it clamps the bar. M2 × 10 is worse.
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

### Drilling: Bits, Punches & Guide
The Dremel is not a substitute for a drill press here. Its collets and chuck stop at 1/8" (3.2 mm) shanks, and twist and brad-point bits from 4 mm up have shanks as wide as the hole. It can drill the 1/8" acrylic pilots and nothing larger. For everything else, use a hand drill in a portable guide.
* **Portable Drill Guide with Depth Stop:** e.g., Milescraft DrillMate. It holds a hand drill square to the work and stops each pocket at its depth, which is what a drill press would be doing here. A pocket that is 0.3 mm off or tilted lets its insert touch the side before the screw centres it.
* **Metric HSS Jobber Drill Set, 1–10 mm in 0.5 mm steps:** gives the **4.0 mm** (acrylic clearance), **4.5 mm** (M2 pockets) and **5.5 mm** (M3 pockets). Dub the 4.0 mm for acrylic (Phase A step 3).
* **Brad-Point Bits, 1/8", 3/16" and 7/32" (optional):** they centre better in plywood than twist bits. **3/16"** (4.76 mm) may replace the 4.5 mm M2 pocket and **7/32"** (5.56 mm) the 5.5 mm M3 pocket. Both pass the SCAD's wall asserts: 3.2 mm of wood to the acrylic recess, and 2.58 mm to the window opening.
* **1/8" Bit for Plastics,** or a dubbed 1/8" twist bit: the acrylic's 3.2 mm pilots.
* **90° Countersink, Single- or Zero-Flute, 1/2" Body:** for recessing the M3 heads flush in the acrylic, opened to 6.7 mm across. Multi-flute countersinks chatter in acrylic. Try the depth on scrap first.
* **Transfer Punch Set, Inch (3/32"–1/2"):** **3/32"** marks the bar's 2.42 mm holes onto the channel floor; **1/8"** marks the acrylic's 3.2 mm holes onto the ledges.
* **1" Forstner Bit:** the grab holes, in the drill guide, over a backer.

### Sheet Goods & Clamping Cauls
* **1/4-Inch Baltic Birch or Cabinet-Grade Plywood (2' × 2' or 2' × 4' panel):** Measure in-store with calipers to confirm actual thickness is close to 0.235"–0.250" to match the acrylic.
* **3/4-Inch Cabinet-Grade Plywood (2' × 2' or 2' × 4' panel):** Bottom structural layer of the disc.
* **1/2-Inch MDF Handy Panel (2' × 4'):** Cut into one 20" × 20" sacrificial spoilboard/desk backer and four window template strips.
* **Scrap 2×4 Offcut (18–24 inches long):** Cut into two clamping cauls to distribute clamp pressure across the middle of the disc during glue-up.

### Fasteners, Adhesives & Shop Consumables
* **M3 × 7 mm × 5 mm OD Knurled Brass Heat-Set Inserts (4+; e.g. "Knurled Insert Nuts, 130pcs M3 x 7mm Length x 5mm OD"):** epoxied into the north and south plywood ledges.
* **M3 × 12 mm Stainless Flat-Head (90°, ISO 10642 / DIN 7991) Machine Screws (4+):** for removable, flush mounting of the acrylic window.
* **M2 × 6 mm Stainless Flat-Head (90°) Machine Screws (2+), and M2 × 6 mm × 4 mm OD Knurled Brass Heat-Set Inserts (2+; e.g. "Knurled Insert Nuts, 130pcs M2 x 6mm Length x 4mm OD"):** for the removable peg bar. The bar comes off whenever the acrylic does, and wood screws would strip the plywood after a few removals.
* **Slow-Set Epoxy and Paste Wax:** epoxy sets the bar's inserts; wax on the screws keeps them from being glued in.
* **1-Inch Coarse-Thread Wood or Drywall Screws (1 small box):** For fastening the 1/2-inch MDF backer up into the waste center of the 3/4-inch desk without poking through the top veneer.
* **5/8-Inch Brad Nails (or small alignment screws):** Driven into the outer waste corners of the plywood blanks to prevent sliding during glue-up.
* **PVA Wood Glue:** e.g., Titebond II or III.
* **Double-Sided Woodworking / Carpet Tape:** For securing the aluminum corner jig and MDF templates.
* **Blue Painter's Tape & Wax Paper:** Painter's tape protects acrylic during scroll-sawing; wax paper keeps glue squeeze-out from sticking to 2×4 clamping cauls.

### Clamps & Dust Extraction
* **24-Inch Capacity Bar Clamps (Quantity: 4 to 6):** e.g., BESSEY Clutch Style Bar Clamps (GSCC2.524) — spans the 20-inch blanks and reaches inside the window opening.
* **Cordless Handheld Vacuum with Crevice Nozzle & Hose:** e.g., RYOBI ONE+ 18V Cordless GoGoVac Kit (PCL731K) — clears compacted sawdust from the narrow 1/4-inch downcut router kerf between passes.
