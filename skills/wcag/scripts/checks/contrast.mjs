const LARGE_PX = 24;
const LARGE_BOLD_PX = 18.66;

export default {
	id: "contrast",
	covers: { "1.4.3": "measured", "1.4.11": "partial" },
	async run(page, ctx) {
		if (ctx.media.some((m) => m.name === "forced-colors")) return { findings: [], note: "skipped: forced colours replace the author colours" };
		const scan = await page.eval((K) => {
			const LARGE_PX = K.largePx;
			const LARGE_BOLD_PX = K.largeBoldPx;
			const text = [];
			const placeholders = [];
			const controls = [];
			const skipTags = new Set(["SCRIPT", "STYLE", "NOSCRIPT", "TEMPLATE", "OPTION", "OPTGROUP", "HEAD", "TITLE", "META"]);
			const floor2 = (v) => Math.floor(v * 100) / 100;
			const disabled = (el) => !!el.closest("[disabled],[aria-disabled='true'],fieldset:disabled") || (el.labels && [...el.labels].some((l) => l.control?.disabled));
			const range = document.createRange();
			const textRect = (el) => {
				let rect = null;
				for (const n of el.childNodes) {
					if (n.nodeType !== 3 || !n.nodeValue.trim()) continue;
					range.selectNodeContents(n);
					for (const r of range.getClientRects()) {
						if (r.width <= 0 || r.height <= 0) continue;
						rect = rect
							? { l: Math.min(rect.l, r.left), t: Math.min(rect.t, r.top), r: Math.max(rect.r, r.right), b: Math.max(rect.b, r.bottom) }
							: { l: r.left, t: r.top, r: r.right, b: r.bottom };
					}
				}
				if (!rect) return null;
				if (rect.r + scrollX <= 0 || rect.b + scrollY <= 0) return null;
				return { x: rect.l, y: rect.t, width: rect.r - rect.l, height: rect.b - rect.t };
			};
			for (const el of __w.deepAll()) {
				if (skipTags.has(el.tagName)) continue;
				const own = __w.ownText(el);
				const cs = getComputedStyle(el);
				if (own && __w.visible(el) && !disabled(el)) {
					const tr = textRect(el);
					if (tr) {
						const size = parseFloat(cs.fontSize);
						const weight = parseInt(cs.fontWeight, 10) || 400;
						const large = size >= LARGE_PX || (size >= LARGE_BOLD_PX && weight >= 700);
						const bg = __w.background(el);
						const fillRaw = cs.webkitTextFillColor || cs.color;
						const base = __w.rgba(fillRaw);
						const alpha = base[3] * __w.opacityChain(el);
						const clipText = cs.webkitBackgroundClip === "text" || cs.backgroundClip === "text";
						const fgRgb = __w.over([base[0], base[1], base[2], alpha], bg.rgb);
						const record = {
							selector: __w.cssPath(el),
							snippet: __w.snippet(el),
							sample: own.slice(0, 40),
							size: Math.round(size * 10) / 10,
							weight,
							need: large ? 3 : 4.5,
							fg: __w.hex(fgRgb),
							fgRaw: [base[0], base[1], base[2], alpha],
							bg: __w.hex(bg.rgb),
							rect: tr,
							why: clipText ? "background-clip:text" : bg.indeterminate,
						};
						if (record.why) text.push(record);
						else {
							record.ratio = floor2(__w.ratio(fgRgb, bg.rgb));
							text.push(record);
						}
					}
				}
				if ((el.tagName === "INPUT" || el.tagName === "TEXTAREA") && el.placeholder && !el.value && __w.visible(el) && !disabled(el)) {
					const ps = getComputedStyle(el, "::placeholder");
					const bg = __w.background(el);
					const base = __w.rgba(ps.color);
					const op = parseFloat(ps.opacity);
					const fgRgb = __w.over([base[0], base[1], base[2], base[3] * (Number.isNaN(op) ? 1 : op) * __w.opacityChain(el)], bg.rgb);
					const size = parseFloat(ps.fontSize);
					placeholders.push({
						selector: __w.cssPath(el),
						snippet: __w.snippet(el),
						ratio: floor2(__w.ratio(fgRgb, bg.rgb)),
						need: size >= LARGE_PX ? 3 : 4.5,
						fg: __w.hex(fgRgb),
						bg: __w.hex(bg.rgb),
						indeterminate: bg.indeterminate,
					});
				}
				const isField = el.tagName === "TEXTAREA" || el.tagName === "SELECT" || (el.tagName === "INPUT" && !["hidden", "checkbox", "radio", "submit", "button", "reset", "image", "range", "color", "file"].includes(el.type));
				if (isField && __w.visible(el) && !disabled(el)) {
					const parentBg = __w.background(el.parentElement ?? document.body);
					const own = __w.background(el);
					const sides = ["Top", "Right", "Bottom", "Left"].map((s) => ({
						width: parseFloat(cs["border" + s + "Width"]),
						style: cs["border" + s + "Style"],
						color: __w.rgba(cs["border" + s + "Color"]),
					}));
					let best = 1;
					for (const s of sides) if (s.width >= 1 && s.style !== "none" && s.style !== "hidden") best = Math.max(best, __w.ratio(__w.over(s.color, parentBg.rgb), parentBg.rgb));
					const fillRatio = __w.ratio(own.rgb, parentBg.rgb);
					const hasShadow = cs.boxShadow !== "none";
					const hasOutline = cs.outlineStyle !== "none" && parseFloat(cs.outlineWidth) > 0;
					controls.push({
						selector: __w.cssPath(el),
						snippet: __w.snippet(el),
						border: floor2(best),
						fill: floor2(fillRatio),
						decorated: hasShadow || hasOutline,
						indeterminate: own.indeterminate || parentBg.indeterminate,
					});
				}
			}
			return { text: text.slice(0, 3000), placeholders: placeholders.slice(0, 200), controls: controls.slice(0, 300) };
		}, { largePx: LARGE_PX, largeBoldPx: LARGE_BOLD_PX });

		const findings = [];
		const need = [];
		for (const t of scan.text) {
			if (t.why) {
				need.push(t);
				continue;
			}
			if (t.ratio < t.need) {
				findings.push({
					sc: "1.4.3",
					kind: "fail",
					check: "contrast:text",
					selector: t.selector,
					snippet: t.snippet,
					message: `text ${t.fg} on ${t.bg} is ${t.ratio}:1, needs ${t.need}:1 (${t.size}px, weight ${t.weight})`,
					measured: { ratio: t.ratio, need: t.need, fg: t.fg, bg: t.bg },
				});
			}
		}

		for (const p of scan.placeholders) {
			if (p.indeterminate) continue;
			if (p.ratio < p.need)
				findings.push({
					sc: "1.4.3",
					kind: "fail",
					check: "contrast:placeholder",
					selector: p.selector,
					snippet: p.snippet,
					message: `placeholder ${p.fg} on ${p.bg} is ${p.ratio}:1, needs ${p.need}:1`,
					measured: { ratio: p.ratio, need: p.need, fg: p.fg, bg: p.bg },
				});
		}

		for (const c of scan.controls) {
			if (c.indeterminate) continue;
			const strongest = Math.max(c.border, c.fill);
			if (strongest >= 3) continue;
			findings.push({
				sc: "1.4.11",
				kind: c.decorated ? "review" : "fail",
				check: "contrast:control-boundary",
				selector: c.selector,
				snippet: c.snippet,
				message: `form field boundary is ${c.border}:1 (border) and ${c.fill}:1 (fill) against its surroundings, needs 3:1${c.decorated ? "; a shadow or outline is present, check it by eye" : ""}`,
				measured: { border: c.border, fill: c.fill },
			});
		}

		if (need.length) {
			await page.eval(() => {
				const s = document.createElement("style");
				s.id = "__w_notext";
				s.textContent = "*,*::before,*::after{color:transparent!important;-webkit-text-fill-color:transparent!important;text-shadow:none!important;caret-color:transparent!important}";
				document.head.append(s);
				return __w.settle();
			});
			for (const t of need.slice(0, 80)) {
				const pad = 1;
				const rect = { x: t.rect.x - pad, y: t.rect.y - pad, width: t.rect.width + 2 * pad, height: t.rect.height + 2 * pad };
				if (rect.width * rect.height > 4_000_000) continue;
				const shot = await page.shot(rect);
				const m = await page.eval((a) => __w.pixelRatio(a.shot, a.fg), { shot, fg: t.fgRaw });
				if (m.min >= t.need) continue;
				const fail = m.p25 < t.need;
				findings.push({
					sc: "1.4.3",
					kind: fail ? "fail" : "review",
					check: "contrast:text-over-image",
					selector: t.selector,
					snippet: t.snippet,
					message: `text over ${t.why}: sampled backdrop pixels give min ${m.min}:1, 5th percentile ${m.p5}:1, 25th percentile ${m.p25}:1, median ${m.median}:1 against ${t.need}:1`,
					measured: { ...m, need: t.need },
				});
			}
			await page.eval(() => document.getElementById("__w_notext")?.remove());
			if (need.length > 80) findings.push({ sc: "1.4.3", kind: "review", check: "contrast:text-over-image", selector: "html", snippet: "", message: `${need.length - 80} more text runs over images or gradients were not sampled` });
		}

		return { findings, note: `${scan.text.length} text runs, ${need.length} over images or gradients, ${scan.controls.length} fields` };
	},
};
