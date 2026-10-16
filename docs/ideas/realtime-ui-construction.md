Monte — something surfaced this week that seems very germane to what we're building, and it triggered another thought based on the old digital pencil-test systems.

Google has been showing Gemini 4 Argon inside its Antigravity environment. The distinction that finally clicked for me is that Argon is the reasoning/coding model, while Antigravity is the agentic workspace around it — the model can write and run code, build custom interfaces, use other tools/models, inspect results, and iterate.

The demo that caught my attention is from Matías Piña Aguilera. He created real-time animation and music through code, then asked the system to build him a custom control interface so he could manipulate the result directly rather than continually prompting it to regenerate things.

Video:
https://www.youtube.com/watch?v=T2Wfds62ZjM

That immediately reminded me of the first digital animation stands we started seeing in the 1990s. Before that we were shooting pencil tests through a VAS-type controller onto 3/4-inch video. Then the digital stands came in: camera over the drawings, computer timeline, dynamic X-sheet, and those crude black/white threshold-style captures where you adjusted controls until enough of the drawing appeared to judge the motion. The image quality wasn't the point — the point was that it was fast enough to let the animator judge timing and change exposures interactively.

That suggests a possible architecture for our Desk:

Don't make the high-quality AI inbetween the thing the animator has to wait for.

Give the system two or more key/breakdown drawings plus the timing chart. Have the reasoning model first interpret the chart and build the animator-facing controls. Then generate a very fast proxy inbetween pass using whatever low-latency method works — line extraction, geometry, correspondence, warping, interpolation, thresholded representations, etc. It doesn't have to look good. It only needs to preserve enough structure for the animator to flip/scrub and judge spacing and timing immediately.

So the animator could be drawing ahead while those crude proxy inbetweens appear almost in real time. They could scrub through them, change spacing, alter holds, move a breakdown, or adjust the timing chart without waiting for a diffusion render.

Once the timing/spacing of those proxy drawings is approved, then the system sends those approved intermediates into the slower synthesis pipeline — ComfyUI/diffusion/whatever model is appropriate — and progressively replaces the crude placeholders with drawings approximating the animator's rough style. The same idea could eventually work again between rough and clean line.

In other words:

Key drawings + timing chart → instant low-fidelity proxy animation → animator approves timing/spacing → slower high-fidelity synthesis progressively replaces the proxies.

That might solve the current latency issue you mentioned, where an inbetween can take roughly a minute. The animator wouldn't have to stop and wait a minute. The machine could keep refining behind them while they continue working.

What I especially like is that it separates two problems that don't actually need to be solved at the same speed:

1. Temporal decision-making: timing, spacing, holds, breakdown placement, rhythm — needs to be nearly instantaneous.

2. Drawing synthesis: matching the animator's forms and rough-line character — can happen asynchronously and take longer.

And this could potentially be built without committing to Google's ecosystem. Since you're already working with Claude and ComfyUI, I'm wondering whether Claude could build the animator-facing instrument and interpret the timing-chart logic, while ComfyUI remains the higher-fidelity rendering/inbetween engine underneath it.

The Google example is mainly interesting because it demonstrates the idea of the model building the artist's tool dynamically, rather than merely generating the artist's output.

I'm not planning to disappear into testing this right now — I've got the course, the BSD book launch, the website, books, stickers, etc. — but this struck me as worth putting in front of you because your current setup may already be close enough to test the architecture.

Curious whether this maps onto what you're already doing, or whether there's an obvious technical reason the fast-proxy / slow-refinement split would or wouldn't work.

