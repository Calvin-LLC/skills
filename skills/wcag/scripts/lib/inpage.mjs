export const INPAGE = `(() => {
	if (globalThis.__w) return;
	const w = (globalThis.__w = {});

	w.cssPath = (el) => {
		if (!(el instanceof Element)) return "";
		if (el.id && document.querySelectorAll("#" + CSS.escape(el.id)).length === 1) return "#" + CSS.escape(el.id);
		const parts = [];
		let node = el;
		while (node && node.nodeType === 1 && node !== document.documentElement && parts.length < 6) {
			let part = node.localName;
			if (node.id && document.querySelectorAll("#" + CSS.escape(node.id)).length === 1) {
				parts.unshift("#" + CSS.escape(node.id));
				break;
			}
			const parent = node.parentElement;
			if (parent) {
				const same = [...parent.children].filter((c) => c.localName === node.localName);
				if (same.length > 1) part += ":nth-of-type(" + (same.indexOf(node) + 1) + ")";
			}
			parts.unshift(part);
			node = parent;
		}
		return parts.join(" > ");
	};

	w.snippet = (el, max = 160) => {
		if (!(el instanceof Element)) return "";
		const open = el.cloneNode(false).outerHTML.replace(/<\\/[^>]+>$/, "");
		const text = (el.textContent || "").trim().replace(/\\s+/g, " ").slice(0, 40);
		return (open + text).slice(0, max);
	};

	w.visible = (el) => {
		const cs = getComputedStyle(el);
		if (cs.display === "none" || cs.visibility === "hidden" || cs.visibility === "collapse") return false;
		const r = el.getBoundingClientRect();
		if (r.width <= 0 || r.height <= 0) return false;
		for (let n = el; n && n.nodeType === 1; n = n.parentElement) {
			if (parseFloat(getComputedStyle(n).opacity) === 0) return false;
		}
		return true;
	};

	const cv = document.createElement("canvas");
	cv.width = cv.height = 1;
	const cx = cv.getContext("2d", { willReadFrequently: true });
	w.rgba = (css) => {
		const direct = /^rgba?\\(([^)]+)\\)$/.exec(css);
		if (direct) {
			const p = direct[1].split(/[\\s,/]+/).filter(Boolean).map(parseFloat);
			return [p[0], p[1], p[2], p.length > 3 ? p[3] : 1];
		}
		if (css === "transparent") return [0, 0, 0, 0];
		cx.clearRect(0, 0, 1, 1);
		cx.fillStyle = "#000";
		cx.fillStyle = css;
		cx.fillRect(0, 0, 1, 1);
		const d = cx.getImageData(0, 0, 1, 1).data;
		const m = /\\/\\s*([\\d.]+%?)\\s*\\)\\s*$/.exec(css);
		let a = d[3] / 255;
		if (m) a = m[1].endsWith("%") ? parseFloat(m[1]) / 100 : parseFloat(m[1]);
		return [d[0], d[1], d[2], a];
	};

	const lin = (v) => {
		v /= 255;
		return v <= 0.04045 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
	};
	w.lum = (c) => 0.2126 * lin(c[0]) + 0.7152 * lin(c[1]) + 0.0722 * lin(c[2]);
	w.ratio = (a, b) => {
		const x = w.lum(a);
		const y = w.lum(b);
		return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05);
	};
	w.over = (top, under) => {
		const a = top[3] ?? 1;
		return [top[0] * a + under[0] * (1 - a), top[1] * a + under[1] * (1 - a), top[2] * a + under[2] * (1 - a), 1];
	};
	w.hex = (c) => "#" + c.slice(0, 3).map((v) => Math.round(v).toString(16).padStart(2, "0")).join("");

	w.opacityChain = (el) => {
		let o = 1;
		for (let n = el; n && n.nodeType === 1; n = n.parentElement) o *= parseFloat(getComputedStyle(n).opacity);
		return o;
	};

	w.background = (el) => {
		const layers = [];
		let indeterminate = null;
		for (let n = el; n && n.nodeType === 1; n = n.parentElement) {
			const cs = getComputedStyle(n);
			if (cs.backgroundImage !== "none") indeterminate = indeterminate || "background-image on " + w.cssPath(n);
			if (cs.backdropFilter && cs.backdropFilter !== "none") indeterminate = indeterminate || "backdrop-filter on " + w.cssPath(n);
			if (cs.mixBlendMode && cs.mixBlendMode !== "normal") indeterminate = indeterminate || "mix-blend-mode on " + w.cssPath(n);
			const c = w.rgba(cs.backgroundColor);
			if (c[3] > 0) layers.push({ c, o: w.opacityChain(n) });
			if (c[3] >= 1 && w.opacityChain(n) >= 1 && cs.backgroundImage === "none") break;
		}
		let out = [255, 255, 255, 1];
		for (const layer of layers.reverse()) out = w.over([layer.c[0], layer.c[1], layer.c[2], layer.c[3] * layer.o], out);
		return { rgb: out, indeterminate };
	};

	w.foreground = (el, bg) => {
		const c = w.rgba(getComputedStyle(el).color);
		return w.over([c[0], c[1], c[2], c[3] * w.opacityChain(el)], bg);
	};

	w.ownText = (el) => {
		let t = "";
		for (const n of el.childNodes) if (n.nodeType === 3) t += n.nodeValue;
		return t.replace(/\\s+/g, " ").trim();
	};

	const registry = [];
	const registered = new Map();
	w.ref = (el) => {
		if (!registered.has(el)) {
			registered.set(el, registry.length);
			registry.push(el);
		}
		return registered.get(el);
	};
	w.at = (i) => registry[i];

	w.decode = async (b64) => {
		const bin = atob(b64);
		const bytes = new Uint8Array(bin.length);
		for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
		const bmp = await createImageBitmap(new Blob([bytes], { type: "image/png" }));
		const c = new OffscreenCanvas(bmp.width, bmp.height);
		const x = c.getContext("2d", { willReadFrequently: true });
		x.drawImage(bmp, 0, 0);
		return x.getImageData(0, 0, bmp.width, bmp.height);
	};

	w.diff = async (aB64, bB64) => {
		const a = await w.decode(aB64);
		const b = await w.decode(bB64);
		if (a.width !== b.width || a.height !== b.height) return { changed: -1, maxRatio: 0 };
		let changed = 0;
		let maxRatio = 1;
		for (let i = 0; i < a.data.length; i += 4) {
			if (a.data[i] === b.data[i] && a.data[i + 1] === b.data[i + 1] && a.data[i + 2] === b.data[i + 2]) continue;
			changed++;
			const r = w.ratio([a.data[i], a.data[i + 1], a.data[i + 2]], [b.data[i], b.data[i + 1], b.data[i + 2]]);
			if (r > maxRatio) maxRatio = r;
		}
		return { changed, maxRatio: Math.floor(maxRatio * 100) / 100 };
	};

	w.pixelRatio = async (b64, fg) => {
		const img = await w.decode(b64);
		const ratios = [];
		for (let i = 0; i < img.data.length; i += 4) {
			const px = [img.data[i], img.data[i + 1], img.data[i + 2], 1];
			ratios.push(w.ratio(w.over(fg, px), px));
		}
		ratios.sort((p, q) => p - q);
		const at = (f) => ratios[Math.min(ratios.length - 1, Math.floor(ratios.length * f))];
		const r2 = (v) => Math.floor(v * 100) / 100;
		return { min: r2(ratios[0]), p5: r2(at(0.05)), p25: r2(at(0.25)), median: r2(at(0.5)), n: ratios.length };
	};

	w.settle = () => new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)));

	w.clipped = () => {
		const out = {};
		for (const el of w.deepAll()) {
			if (el === document.body || el === document.documentElement) continue;
			const cs = getComputedStyle(el);
			const hx = cs.overflowX !== "visible" && cs.overflowX !== "auto" && cs.overflowX !== "scroll";
			const hy = cs.overflowY !== "visible" && cs.overflowY !== "auto" && cs.overflowY !== "scroll";
			if (!hx && !hy) continue;
			if (!(el.textContent || "").trim()) continue;
			const r = el.getBoundingClientRect();
			if (r.width <= 2 && r.height <= 2) continue;
			if (!w.visible(el)) continue;
			const cutX = hx && el.scrollWidth > el.clientWidth + 1;
			const cutY = hy && el.scrollHeight > el.clientHeight + 1;
			if (!cutX && !cutY) continue;
			out[w.cssPath(el)] = { snippet: w.snippet(el), ellipsis: cs.textOverflow === "ellipsis" && cutX && !cutY, axis: cutX && cutY ? "both" : cutX ? "x" : "y" };
		}
		return out;
	};

	w.deepAll = (root = document) => {
		const out = [];
		const walk = (node) => {
			for (const el of node.querySelectorAll("*")) {
				out.push(el);
				if (el.shadowRoot) walk(el.shadowRoot);
			}
		};
		walk(root);
		return out;
	};

	w.nativeTabbable = (el) => {
		if (el.disabled || el.hidden) return false;
		const t = el.localName;
		if (t === "a" || t === "area") return el.hasAttribute("href");
		if (t === "input") return el.type !== "hidden";
		if (["button", "select", "textarea", "summary"].includes(t)) return true;
		if (el.isContentEditable && el.getAttribute("contenteditable") !== "false") return true;
		if (["audio", "video"].includes(t)) return el.hasAttribute("controls");
		return el.hasAttribute("tabindex");
	};

	w.tabbable = () =>
		w.deepAll().filter((el) => {
			if (!w.nativeTabbable(el)) return false;
			const ti = el.getAttribute("tabindex");
			if (ti !== null && parseInt(ti, 10) < 0) return false;
			if (el.inert || el.closest("[inert]")) return false;
			return w.visible(el) || (el.type === "radio" || el.type === "checkbox");
		});
})();`;
