const MAX_STOPS = 300;
const MAX_FOCUS_SHOTS = 80;

export default {
	id: "keyboard",
	covers: { "2.1.1": "partial", "2.1.2": "measured", "2.4.3": "partial", "2.4.7": "measured", "2.4.11": "measured", "3.2.1": "partial", "2.4.1": "partial", "2.4.13": "partial" },
	async run(page) {
		const findings = [];
		const meta = await page.eval(
			() => {
				const tabbable = __w.tabbable();
				const radios = new Map();
				const expected = [];
				for (const el of tabbable) {
					if (el.type === "radio" && el.name) {
						const group = el.form?.id + "|" + el.name;
						if (radios.has(group) && !el.checked) continue;
						radios.set(group, el);
					}
					expected.push(__w.ref(el));
				}
				const positive = tabbable.filter((el) => parseInt(el.getAttribute("tabindex") ?? "0", 10) > 0).map((el) => ({ selector: __w.cssPath(el), snippet: __w.snippet(el) }));
				return { expected, count: tabbable.length, positive };
			},
			null,
		);

		for (const p of meta.positive)
			findings.push({ sc: "2.4.3", kind: "review", check: "keyboard:positive-tabindex", selector: p.selector, snippet: p.snippet, message: "positive tabindex overrides the document's focus order" });

		await page.eval(() => {
			window.scrollTo(0, 0);
			if (document.activeElement && document.activeElement !== document.body) document.activeElement.blur();
			window.__w_start = { href: location.href, title: document.title };
		});

		const stops = [];
		const seen = new Map();
		let stuck = 0;
		const limit = Math.min(MAX_STOPS, meta.count + 8);
		let lastRef = -2;
		let trap = null;
		let contextChange = null;

		for (let i = 0; i < limit; i++) {
			await page.key("Tab");
			const now = await page.eval(() => {
				const el = document.activeElement;
				if (!el || el === document.body || el === document.documentElement) return { body: true, href: location.href };
				const r = el.getBoundingClientRect();
				return {
					ref: __w.ref(el),
					selector: __w.cssPath(el),
					snippet: __w.snippet(el),
					rect: { x: r.left, y: r.top, width: r.width, height: r.height },
					inFrame: el.tagName === "IFRAME",
					href: location.href,
					title: document.title,
					dialogs: document.querySelectorAll("dialog[open],[role=dialog]:not([hidden]),[aria-modal=true]").length,
				};
			});
			if (now.href !== undefined && now.href !== stops.at(-1)?.href && stops.length && stops.at(-1).href !== undefined && !contextChange) {
				contextChange = { selector: stops.at(-1).selector, from: stops.at(-1).href, to: now.href };
			}
			if (now.body) {
				if (stops.length > 1) break;
				continue;
			}
			if (now.ref === lastRef) {
				stuck++;
				if (stuck >= 2 && meta.count > 1 && !now.inFrame) {
					trap = now;
					break;
				}
			} else stuck = 0;
			lastRef = now.ref;
			if (seen.has(now.ref)) {
				if (stops.length >= meta.expected.length) break;
			}
			seen.set(now.ref, (seen.get(now.ref) ?? 0) + 1);
			stops.push(now);
		}

		if (trap)
			findings.push({
				sc: "2.1.2",
				kind: "fail",
				check: "keyboard:trap",
				selector: trap.selector,
				snippet: trap.snippet,
				message: "Tab pressed three times in a row and focus did not leave this element",
			});
		if (contextChange)
			findings.push({
				sc: "3.2.1",
				kind: "fail",
				check: "keyboard:context-change-on-focus",
				selector: contextChange.selector,
				snippet: "",
				message: `moving focus changed the page URL from ${contextChange.from} to ${contextChange.to}`,
			});

		const visited = new Set(stops.map((s) => s.ref));
		if (!trap) {
			const missed = meta.expected.filter((r) => !visited.has(r));
			if (missed.length && stops.length >= 1) {
				const info = await page.eval((refs) => refs.slice(0, 15).map((r) => ({ selector: __w.cssPath(__w.at(r)), snippet: __w.snippet(__w.at(r)) })), missed);
				for (const m of info)
					findings.push({ sc: "2.1.1", kind: "review", check: "keyboard:not-reached", selector: m.selector, snippet: m.snippet, message: "natively focusable element was not reached by Tab (check for a modal, hidden panel, or roving tabindex)" });
			}
		}

		let backwards = 0;
		let firstBack = null;
		for (let i = 1; i < stops.length; i++) {
			const a = stops[i - 1].rect;
			const b = stops[i].rect;
			if (b.y + b.height < a.y - 120 && b.y < a.y) {
				backwards++;
				firstBack ??= stops[i];
			}
		}
		if (backwards > 1 && firstBack)
			findings.push({
				sc: "2.4.3",
				kind: "review",
				check: "keyboard:order-vs-visual",
				selector: firstBack.selector,
				snippet: firstBack.snippet,
				message: `focus jumped up the page ${backwards} times during the Tab walk; confirm the order still makes sense`,
			});

		const first = stops[0];
		const skip = first && (await page.eval((ref) => {
			const el = __w.at(ref);
			if (el.localName !== "a") return null;
			const h = el.getAttribute("href") ?? "";
			if (!h.startsWith("#") || h.length < 2) return null;
			const id = decodeURIComponent(h.slice(1));
			const t = document.getElementById(id) ?? document.querySelector(`a[name="${CSS.escape(id)}"]`);
			return { target: !!t, targetSelector: t ? __w.cssPath(t) : null };
		}, first.ref));
		if (skip && !skip.target)
			findings.push({ sc: "2.4.1", kind: "fail", check: "keyboard:skip-link-target-missing", selector: first.selector, snippet: first.snippet, message: "first focusable element is an in-page link whose target id does not exist" });

		let shots = 0;
		const obscuredChecked = new Set();
		for (const s of stops) {
			const obscured = await page.eval((ref) => {
				const el = __w.at(ref);
				el.scrollIntoView({ block: "nearest", inline: "nearest" });
				el.focus({ preventScroll: true });
				const r = el.getBoundingClientRect();
				const x0 = Math.max(0, r.left);
				const y0 = Math.max(0, r.top);
				const x1 = Math.min(innerWidth, r.right);
				const y1 = Math.min(innerHeight, r.bottom);
				if (x1 <= x0 || y1 <= y0) return { offscreen: true };
				let total = 0;
				let hidden = 0;
				for (let i = 0; i < 5; i++)
					for (let j = 0; j < 5; j++) {
						const x = x0 + ((x1 - x0) * (i + 0.5)) / 5;
						const y = y0 + ((y1 - y0) * (j + 0.5)) / 5;
						const top = document.elementFromPoint(x, y);
						total++;
						if (top && !(el === top || el.contains(top) || top.contains(el))) hidden++;
					}
				const cover = hidden ? document.elementFromPoint((x0 + x1) / 2, (y0 + y1) / 2) : null;
				return { total, hidden, by: hidden && cover ? __w.cssPath(cover) : null };
			}, s.ref);
			if (obscured.offscreen || obscuredChecked.has(s.ref)) continue;
			obscuredChecked.add(s.ref);
			if (obscured.hidden === obscured.total)
				findings.push({ sc: "2.4.11", kind: "fail", check: "keyboard:focus-obscured", selector: s.selector, snippet: s.snippet, message: `focused element is entirely covered by ${obscured.by}` });
			else if (obscured.hidden > 0)
				findings.push({ sc: "2.4.11", kind: "review", check: "keyboard:focus-partly-obscured", selector: s.selector, snippet: s.snippet, message: `${obscured.hidden} of ${obscured.total} sampled points of the focused element are covered by ${obscured.by}` });
		}

		for (const s of stops) {
			if (shots >= MAX_FOCUS_SHOTS) break;
			const geometry = await page.eval((ref) => {
				const el = __w.at(ref);
				el.scrollIntoView({ block: "center", inline: "nearest" });
				const r = el.getBoundingClientRect();
				const pad = 10;
				return { x: r.left - pad, y: r.top - pad, width: r.width + 2 * pad, height: r.height + 2 * pad };
			}, s.ref);
			if (geometry.width * geometry.height > 3_000_000 || geometry.width < 4) continue;
			await page.eval((ref) => { __w.at(ref).blur(); return __w.settle(); }, s.ref);
			const before = await page.shot(geometry);
			await page.eval((ref) => { __w.at(ref).focus({ preventScroll: true }); return __w.settle(); }, s.ref);
			await page.eval(() => { document.documentElement.dataset.wcagKbd = ""; });
			const after = await page.shot(geometry);
			shots++;
			const d = await page.eval((a) => __w.diff(a.before, a.after), { before, after });
			if (d.changed === 0) {
				findings.push({ sc: "2.4.7", kind: "fail", check: "keyboard:no-focus-indicator", selector: s.selector, snippet: s.snippet, message: "no pixel changed within 10px of the element when it received focus" });
			} else if (d.changed > 0 && d.maxRatio < 3) {
				findings.push({ sc: "2.4.7", kind: "review", check: "keyboard:faint-focus-indicator", selector: s.selector, snippet: s.snippet, message: `focus changes ${d.changed} pixels but the strongest focused-versus-unfocused contrast is ${d.maxRatio}:1 (3:1 expected for a visible indicator, 1.4.11)`, measured: d });
			}
		}

		await page.eval(() => {
			if (document.activeElement) document.activeElement.blur();
			delete document.documentElement.dataset.wcagKbd;
		});

		return { findings, note: `${stops.length} Tab stops walked of ${meta.count} natively focusable, ${shots} focus indicators compared by pixels` };
	},
};
