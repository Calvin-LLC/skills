const SPACING_CSS = `*{line-height:1.5!important;letter-spacing:.12em!important;word-spacing:.16em!important}p,li,dd,blockquote{margin-bottom:2em!important}`;

async function snapshot(page) {
	return page.eval(() => {
		const cutoff = innerWidth + 1;
		const wide = [];
		for (const el of __w.deepAll()) {
			if (!__w.visible(el)) continue;
			const r = el.getBoundingClientRect();
			if (r.right <= cutoff || r.right + scrollX <= 0) continue;
			let scrolled = false;
			for (let n = el.parentElement; n && n !== document.documentElement; n = n.parentElement) {
				const cs = getComputedStyle(n);
				if (/(auto|scroll|hidden|clip)/.test(cs.overflowX) && n.getBoundingClientRect().right <= cutoff) {
					scrolled = true;
					break;
				}
			}
			if (scrolled) continue;
			if (el.closest("table,pre,canvas,svg,[role=grid],[role=table]")) continue;
			wide.push({ selector: __w.cssPath(el), snippet: __w.snippet(el), right: Math.round(r.right), left: Math.round(r.left) });
		}
		const doc = document.documentElement;
		return {
			innerWidth,
			scrollWidth: doc.scrollWidth,
			horizontal: doc.scrollWidth > innerWidth + 1,
			wide: wide.slice(0, 12),
			clipped: __w.clipped(),
		};
	});
}

export default {
	id: "reflow",
	covers: { "1.4.4": "measured", "1.4.10": "measured", "1.4.12": "measured", "1.3.4": "partial" },
	async run(page, ctx) {
		const findings = [];
		const base = await snapshot(page);
		const baseClipped = new Set(Object.keys(base.clipped));

		const clippedNew = (snap, sc, label, check) => {
			for (const [selector, c] of Object.entries(snap.clipped)) {
				if (baseClipped.has(selector) || c.ellipsis) continue;
				findings.push({ sc, kind: c.axis === "y" || c.axis === "both" ? "fail" : "review", check, selector, snippet: c.snippet, message: `content is cut off (overflow hidden) ${label}` });
			}
		};

		await page.setViewport(320, 256);
		await page.settle();
		const narrow = await snapshot(page);
		if (narrow.horizontal) {
			const culprit = narrow.wide[0];
			findings.push({
				sc: "1.4.10",
				kind: "fail",
				check: "reflow:horizontal-scroll-320",
				selector: culprit?.selector ?? "html",
				snippet: culprit?.snippet ?? "",
				message: `at 320 CSS px wide the page scrolls horizontally (scrollWidth ${narrow.scrollWidth}); first element past the edge reaches x=${culprit?.right ?? "?"}`,
				measured: { scrollWidth: narrow.scrollWidth, viewport: 320 },
			});
			for (const w of narrow.wide.slice(1, 6))
				findings.push({ sc: "1.4.10", kind: "fail", check: "reflow:horizontal-scroll-320", selector: w.selector, snippet: w.snippet, message: `extends past the 320 px edge (right=${w.right}, left=${w.left})` });
		}
		clippedNew(narrow, "1.4.10", "at 320 CSS px wide", "reflow:clipped-320");

		await page.setViewport(640, 400);
		await page.settle();
		const zoomed = await snapshot(page);
		if (zoomed.horizontal && !narrow.horizontal)
			findings.push({ sc: "1.4.4", kind: "fail", check: "reflow:horizontal-scroll-200", selector: zoomed.wide[0]?.selector ?? "html", snippet: zoomed.wide[0]?.snippet ?? "", message: `at 200% zoom (640 CSS px) the page scrolls horizontally (scrollWidth ${zoomed.scrollWidth})` });
		clippedNew(zoomed, "1.4.4", "at 200% zoom", "reflow:clipped-200");

		await page.setViewport(ctx.viewport.width, ctx.viewport.height);
		await page.settle();
		await page.eval((css) => {
			const s = document.createElement("style");
			s.id = "__w_spacing";
			s.textContent = css;
			document.head.append(s);
			return __w.settle();
		}, SPACING_CSS);
		const spaced = await snapshot(page);
		await page.eval(() => document.getElementById("__w_spacing")?.remove());
		clippedNew(spaced, "1.4.12", "when the user text-spacing overrides are applied (line height 1.5, letter 0.12em, word 0.16em, paragraph 2em)", "reflow:clipped-text-spacing");

		await page.setViewport(568, 320, { mobile: true });
		await page.settle();
		const landscape = await page.eval(() => document.body.innerText.length);
		const landscapeHint = await page.eval(() => /rotate|turn your (device|phone)|portrait (mode )?(only|required)|landscape (mode )?(only|required)|please use (portrait|landscape)/i.test(document.body.innerText));
		await page.setViewport(320, 568, { mobile: true });
		await page.settle();
		const portrait = await page.eval(() => document.body.innerText.length);
		const portraitHint = await page.eval(() => /rotate|turn your (device|phone)|portrait (mode )?(only|required)|landscape (mode )?(only|required)|please use (portrait|landscape)/i.test(document.body.innerText));
		const bigGap = Math.min(landscape, portrait) < 0.5 * Math.max(landscape, portrait);
		if ((landscapeHint !== portraitHint) || (bigGap && (landscapeHint || portraitHint)))
			findings.push({ sc: "1.3.4", kind: "fail", check: "reflow:orientation-locked", selector: "body", snippet: "", message: `content changes with orientation: ${portrait} characters of text in portrait, ${landscape} in landscape, and a rotate-your-device message appears in one of them` });
		else if (bigGap)
			findings.push({ sc: "1.3.4", kind: "review", check: "reflow:orientation-differs", selector: "body", snippet: "", message: `visible text differs by more than half between portrait (${portrait} characters) and landscape (${landscape})` });

		await page.setViewport(ctx.viewport.width, ctx.viewport.height);
		await page.settle();
		return { findings, note: `scrollWidth ${base.scrollWidth}/${narrow.scrollWidth}/${zoomed.scrollWidth} at ${ctx.viewport.width}/320/640 CSS px` };
	},
};
