const MIN = 24;

export default {
	id: "targets",
	covers: { "2.5.8": "measured" },
	async run(page) {
		const data = await page.eval((min) => {
			const sel = "a[href],button,input:not([type=hidden]),select,textarea,summary,[role=button],[role=link],[role=checkbox],[role=radio],[role=switch],[role=tab],[role=menuitem],[role=menuitemcheckbox],[role=menuitemradio],[role=option],[role=slider],[role=treeitem],[tabindex]:not([tabindex^='-'])";
			const all = [];
			for (const el of __w.deepAll()) {
				if (!el.matches(sel)) continue;
				if (el.disabled || el.closest("[inert]")) continue;
				if (el.localName === "input" && el.labels?.length && ["checkbox", "radio"].includes(el.type)) {
					const lr = el.labels[0].getBoundingClientRect();
					const r0 = el.getBoundingClientRect();
					if (lr.width * lr.height > r0.width * r0.height && (r0.width < min || r0.height < min)) {
						el.__w_label = el.labels[0];
					}
				}
				if (!__w.visible(el)) continue;
				const box = (el.__w_label ?? el).getBoundingClientRect();
				if (box.right + scrollX <= 0 || box.bottom + scrollY <= 0) continue;
				all.push({ el, r: { x: box.left + scrollX, y: box.top + scrollY, w: box.width, h: box.height } });
			}
			const small = all.filter((t) => t.r.w < min - 0.01 || t.r.h < min - 0.01);
			const circles = small.map((t) => ({ cx: t.r.x + t.r.w / 2, cy: t.r.y + t.r.h / 2, t }));
			const rectHit = (c, o) => {
				const dx = Math.max(o.r.x - c.cx, 0, c.cx - (o.r.x + o.r.w));
				const dy = Math.max(o.r.y - c.cy, 0, c.cy - (o.r.y + o.r.h));
				return dx * dx + dy * dy < (min / 2) ** 2;
			};
			const out = [];
			for (const c of circles) {
				const el = c.t.el;
				let exception = null;
				const cs = getComputedStyle(el);
				const parentText = el.parentElement ? [...el.parentElement.childNodes].some((n) => n.nodeType === 3 && n.nodeValue.trim().length > 3) : false;
				if (el.localName === "a" && cs.display === "inline" && parentText) exception = "inline";
				else if (el.localName === "input" && ["checkbox", "radio"].includes(el.type) && el.__w_label) exception = "label-enlarges-target";
				else if (el.localName === "select" || (el.localName === "input" && ["date", "time", "datetime-local", "month", "week", "range", "color", "file"].includes(el.type))) exception = "user-agent-control";
				if (!exception) {
					const others = all.filter((o) => o.el !== el && !el.contains(o.el) && !o.el.contains(el));
					const hitsTarget = others.some((o) => rectHit(c, o));
					const hitsCircle = circles.some((o) => o !== c && Math.hypot(o.cx - c.cx, o.cy - c.cy) < min);
					if (!hitsTarget && !hitsCircle) exception = "spacing";
				}
				out.push({ selector: __w.cssPath(el), snippet: __w.snippet(el), w: Math.round(c.t.r.w * 10) / 10, h: Math.round(c.t.r.h * 10) / 10, exception });
			}
			return { total: all.length, small: out };
		}, MIN);

		const findings = [];
		for (const s of data.small) {
			if (s.exception) continue;
			findings.push({
				sc: "2.5.8",
				kind: "fail",
				check: "targets:too-small",
				selector: s.selector,
				snippet: s.snippet,
				message: `pointer target is ${s.w} by ${s.h} CSS px, below ${MIN} by ${MIN}, and no other target or undersized-target circle leaves room (spacing exception fails)`,
				measured: { width: s.w, height: s.h },
			});
		}
		const excused = data.small.filter((s) => s.exception).length;
		return { findings, note: `${data.total} targets measured, ${data.small.length} under ${MIN}px, ${excused} excused by an exception` };
	},
};
