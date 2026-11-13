# Performance: Largest Contentful Paint (LCP)

Summarized from the upstream `debug-optimize-lcp` skill. Use when the user reports slow
page loads, Core Web Vitals, or a slow hero image or main content.

LCP is the time until the largest image or text block renders in the viewport. Good is
2.5 s or less, needs improvement is 2.5 to 4.0 s, poor is over 4.0 s (judged at the 75th
percentile of visits in the field). On most mobile pages the LCP element is an image.

## The four subparts

They are sequential, with no gaps, and sum to the LCP time.

| Subpart | Ideal share | Starts / ends |
|---|---|---|
| Time to First Byte (TTFB) | ~40% | navigation start to first HTML byte |
| Resource load delay | under 10% | TTFB to the browser starting the LCP resource |
| Resource load duration | ~40% | download of the LCP resource |
| Element render delay | under 10% | resource downloaded to element painted |

Find the bottleneck subpart *before* optimizing. Shrinking an image while render delay
is the real problem just moves the time into render delay. A text-only LCP element has
0 load delay and duration.

Elements that can be the LCP: `<img>`, SVG `<image>`, `<video>` poster or first frame,
`url()` background images, and block elements with text. Chromium ignores opacity 0,
full-viewport backgrounds, and placeholder or low-entropy images. Size is the visible
area only (images use the smaller of visible and intrinsic size; margin, padding and
borders don't count).

## Workflow

1. `navigate_page`, then `performance_start_trace` with `reload: true`, `autoStop: true`.
   Note the insight set IDs in the output.
2. `performance_analyze_insight` (page, insight set ID, insight name) for:
   `LCPBreakdown` (the four subparts), `DocumentLatency` (server/TTFB),
   `RenderBlocking`, `LCPDiscovery` (was the resource discoverable early).
3. Identify the element with `evaluate_script`:
   ```js
   async () => await new Promise(resolve => {
     new PerformanceObserver(list => {
       const e = list.getEntries().at(-1);
       resolve({element: e.element?.tagName, id: e.element?.id,
         className: e.element?.className, url: e.url, startTime: e.startTime,
         renderTime: e.renderTime, loadTime: e.loadTime, size: e.size});
     }).observe({type: 'largest-contentful-paint', buffered: true});
   })
   ```
   An empty `url` means a text LCP with no resource to load.
4. Waterfall: `list_network_requests` filtered by `resourceTypes` (`image`, `font`),
   then `get_network_request` for the LCP resource. A late start relative to the first
   resource is load delay; a long duration means a big file or slow server.
5. HTML audit via `evaluate_script`: lazy-loaded images inside the viewport
   (`img[loading="lazy"]` whose `getBoundingClientRect().top < innerHeight`), large
   viewport images without `fetchpriority`, and `head script:not([async]):not([defer]):not([type=module])[src]`.

## Fixes, by bottleneck

| Bottleneck | Fixes |
|---|---|
| Load delay (most common) | Plain `<img src>` discoverable in the HTML (not JS/CSS-injected, no `data-src`); never `loading="lazy"` on the LCP image; `fetchpriority="high"`; `<link rel="preload" fetchpriority="high">` if not discoverable; same origin or `preconnect` |
| Render delay | Inline critical CSS, defer the rest; no sync scripts in `<head>`; break up long tasks; SSR so the element is in the initial HTML |
| Load duration | AVIF/WebP and `srcset`; CDN; `Cache-Control`; `fetchpriority="high"` to cut contention; `font-display: swap` for font-blocked text |
| TTFB | Fewer redirects; faster server response; edge-cache HTML; make pages bfcache-eligible |

## Verify

Re-run the same trace and compare the subpart breakdown; the bottleneck should shrink.
Lab numbers differ from real users, so also test under constraints:
`emulate` with `networkConditions: "Fast 3G"` and `cpuThrottlingRate: 4`. State whether
each figure is lab or field data. By default a trace may query the CrUX API for field
data; start the server with `--no-performance-crux` to disable that.
