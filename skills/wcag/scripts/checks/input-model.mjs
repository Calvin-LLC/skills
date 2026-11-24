const DOWN_EVENTS = new Set(["pointerdown", "mousedown", "touchstart"]);
const MAX_TRIGGERS = 40;

export default {
	id: "input-model",
	covers: { "2.1.1": "partial", "2.5.2": "partial", "2.5.1": "partial", "2.5.7": "partial", "2.5.4": "partial", "2.1.4": "partial", "1.4.13": "partial", "2.5.3": "partial", "4.1.2": "partial" },
	async run(page, ctx) {
		const findings = [];
		await page.send("DOM.enable");
		const { result } = await page.send("Runtime.evaluate", {
			expression: `(() => __w.deepAll().filter((el) => __w.visible(el)).map((el) => __w.ref(el)))()`,
			returnByValue: true,
		});
		const refs = result.value;

		const info = async (ref) => {
			const res = await page.send("Runtime.evaluate", { expression: `__w.at(${ref})` });
			return res.result.objectId;
		};

		const listenersOf = async (ref) => {
			const objectId = await info(ref);
			const { listeners } = await page.send("DOMDebugger.getEventListeners", { objectId });
			await page.send("Runtime.releaseObject", { objectId });
			return listeners.map((l) => l.type);
		};

		const candidates = await page.eval(
			(all) =>
				all
					.map((ref) => {
						const el = __w.at(ref);
						const interactiveNative = __w.nativeTabbable(el);
						const role = el.getAttribute("role");
						const tag = el.localName;
						const cs = getComputedStyle(el);
						return {
							ref,
							tag,
							role,
							interactiveNative,
							pointer: cs.cursor === "pointer",
							tabindex: el.getAttribute("tabindex"),
							text: (el.textContent || "").trim().length,
							hasChildInteractive: !!el.querySelector("a[href],button,input,select,textarea,[tabindex]"),
							insideInteractive: !!el.parentElement?.closest("a[href],button,[role=button],[role=link],label,summary,[tabindex]"),
						};
					})
					.filter((c) => c.pointer || c.interactiveNative || c.role),
			refs,
		);

		let inspected = 0;
		const downOnly = [];
		const mouseOnly = [];
		for (const c of candidates) {
			if (inspected++ > 600) break;
			let types;
			try {
				types = await listenersOf(c.ref);
			} catch {
				continue;
			}
			const set = new Set(types);
			const hasClick = set.has("click") || set.has("mouseup") || set.has("pointerup");
			const hasKey = set.has("keydown") || set.has("keyup") || set.has("keypress");
			const hasDown = [...set].some((t) => DOWN_EVENTS.has(t));
			const where = await page.eval((ref) => ({ selector: __w.cssPath(__w.at(ref)), snippet: __w.snippet(__w.at(ref)) }), c.ref);

			if (hasDown && !hasClick && c.interactiveNative === false && c.role !== null)
				downOnly.push({ ...where, types: [...set] });
			if (hasDown && !hasClick)
				findings.push({ sc: "2.5.2", kind: "review", check: "input:down-event-only", ...where, message: `acts on ${[...set].filter((t) => DOWN_EVENTS.has(t)).join("/")} with no click or pointerup handler; the action fires before the user can cancel by moving off` });

			const genericTag = ["div", "span", "li", "td", "img", "svg", "p", "section", "article", "i", "b"].includes(c.tag);
			const clickable = hasClick && genericTag && !c.role && c.tabindex === null && !c.insideInteractive && !c.hasChildInteractive;
			if (clickable && (c.pointer || set.has("click")))
				findings.push({ sc: "2.1.1", kind: "fail", check: "input:click-without-keyboard", ...where, message: `<${c.tag}> has a click handler and no role, tabindex, or key handler, so keyboard users cannot reach or activate it` });
			if (genericTag && c.role && /^(button|link|menuitem|tab|checkbox|switch|option)$/.test(c.role) && !c.interactiveNative && c.tabindex === null)
				findings.push({ sc: "2.1.1", kind: "fail", check: "input:role-without-tabindex", ...where, message: `role="${c.role}" on <${c.tag}> with no tabindex: it is announced as a control but cannot take focus` });
			if (genericTag && c.role && /^(button|link|menuitem|tab|checkbox|switch)$/.test(c.role) && c.tabindex !== null && hasClick && !hasKey)
				findings.push({ sc: "2.1.1", kind: "fail", check: "input:role-without-keyhandler", ...where, message: `role="${c.role}" is focusable and has a click handler but no keydown/keyup handler for Enter or Space` });
			if (set.has("devicemotion") || set.has("deviceorientation"))
				findings.push({ sc: "2.5.4", kind: "review", check: "input:motion-actuation", ...where, message: "listens to device motion; confirm every motion-triggered action has an on-screen control and can be switched off" });
			if (set.has("dragstart") || set.has("dragover") || set.has("drop"))
				mouseOnly.push(where);
		}
		for (const m of mouseOnly.slice(0, 6))
			findings.push({ sc: "2.5.7", kind: "review", check: "input:drag-handlers", ...m, message: "element takes part in a drag-and-drop interaction; confirm the same result can be reached with single clicks or taps" });

		const gesture = await page.eval(() => {
			const out = [];
			for (const el of __w.deepAll()) {
				if (!__w.visible(el)) continue;
				const ta = getComputedStyle(el).touchAction;
				if (/pinch-zoom|pan-x|pan-y|manipulation|none/.test(ta) && ta !== "auto" && (el.matches("canvas,.map,[class*=map],[class*=carousel],[class*=slider]") || ta === "none"))
					out.push({ selector: __w.cssPath(el), snippet: __w.snippet(el), ta });
			}
			return out.slice(0, 6);
		});
		for (const g of gesture)
			findings.push({ sc: "2.5.1", kind: "review", check: "input:touch-action", selector: g.selector, snippet: g.snippet, message: `touch-action:${g.ta} suggests a custom gesture surface; confirm pinch, swipe, and path gestures have single-pointer alternatives` });

		const keys = await page.eval(() => {
			const out = [];
			for (const el of __w.deepAll()) {
				const ak = el.getAttribute("accesskey");
				if (ak && ak.length === 1) out.push({ selector: __w.cssPath(el), snippet: __w.snippet(el), ak });
			}
			return out.slice(0, 5);
		});
		for (const k of keys)
			findings.push({ sc: "2.1.4", kind: "review", check: "input:accesskey", selector: k.selector, snippet: k.snippet, message: `accesskey="${k.ak}" is a single-character shortcut; confirm it can be remapped or only works while the element has focus` });

		if (ctx.first) {
			const writes = await page.blockWrites();
			const keys = "abcdefghijklmnopqrstuvwxyz0123456789/?.,;'[]-=".split("");
			const fired = [];
			await page.eval(() => {
				if (document.activeElement && document.activeElement !== document.body) document.activeElement.blur();
				window.__w_mut = 0;
				window.__w_obs?.disconnect();
				window.__w_obs = new MutationObserver((l) => (window.__w_mut += l.length));
				window.__w_obs.observe(document, { subtree: true, childList: true, attributes: true, characterData: true });
			});
			for (const k of keys) {
				const before = await page.eval(() => ({ href: location.href, active: document.activeElement?.tagName, mut: window.__w_mut, y: scrollY }));
				await page.send("Input.dispatchKeyEvent", { type: "keyDown", key: k, text: k, unmodifiedText: k });
				await page.send("Input.dispatchKeyEvent", { type: "keyUp", key: k });
				await page.settle();
				const after = await page.eval(() => ({ href: location.href, active: document.activeElement?.tagName, mut: window.__w_mut, y: scrollY }));
				if (before.href !== after.href || before.active !== after.active || before.mut !== after.mut) fired.push(k);
				if (before.href !== after.href) await page.goto(ctx.url);
			}
			await page.eval(() => window.__w_obs?.disconnect());
			await writes.stop();
			if (fired.length)
				findings.push({ sc: "2.1.4", kind: "review", check: "input:single-key-shortcut", selector: "document", snippet: "", message: `pressing ${fired.map((k) => `"${k}"`).join(", ")} with nothing focused changed the page; confirm each shortcut can be turned off or remapped, or only works while its component has focus` });
		}

		const labels = await page.eval(() => {
			const out = [];
			for (const el of __w.deepAll()) {
				if (!__w.visible(el)) continue;
				const al = el.getAttribute("aria-label");
				if (!al) continue;
				const tag = el.localName;
				const role = el.getAttribute("role");
				const isControl = ["button", "a", "input", "select", "textarea", "summary"].includes(tag) || /^(button|link|checkbox|radio|switch|tab|menuitem|textbox|combobox)$/.test(role || "");
				if (!isControl) continue;
				if (tag === "select" || tag === "textarea") continue;
				const buttonLike = tag !== "input" || ["button", "submit", "reset"].includes(el.type);
				const visible = (tag === "input" ? (buttonLike ? el.value : "") : el.innerText || "").trim();
				const labelEl = el.labels?.[0]?.innerText?.trim();
				const vis = (visible || labelEl || "").replace(/\s+/g, " ").toLowerCase();
				if (!vis || !/[a-z0-9]/i.test(vis)) continue;
				const name = al.replace(/\s+/g, " ").toLowerCase();
				const norm = (s) => s.replace(/[^\p{L}\p{N} ]/gu, "").trim();
				if (!norm(name).includes(norm(vis))) out.push({ selector: __w.cssPath(el), snippet: __w.snippet(el), visible: vis.slice(0, 40), name: al.slice(0, 60) });
			}
			return out.slice(0, 20);
		});
		for (const l of labels)
			findings.push({ sc: "2.5.3", kind: "fail", check: "input:label-in-name", selector: l.selector, snippet: l.snippet, message: `visible label "${l.visible}" is not contained in the accessible name "${l.name}", so voice-control users cannot say what they see` });

		const triggers = await page.eval(
			(max) => {
				const sel = "[aria-describedby],[aria-haspopup]:not([aria-haspopup=false]),[data-tooltip],[data-tippy-content],[data-bs-toggle=tooltip],[data-bs-toggle=popover],[aria-expanded=false],[title]:not(iframe):not(html):not(head *)";
				const out = [];
				const pool = new Set([...document.querySelectorAll(sel), ...__w.tabbable()]);
				for (const el of pool) {
					if (!__w.visible(el)) continue;
					if (el.closest("nav") && el.matches("[title]:not([aria-describedby])")) continue;
					const r = el.getBoundingClientRect();
					if (r.bottom < 0 || r.top > innerHeight * 3) continue;
					out.push(__w.ref(el));
					if (out.length >= max) break;
				}
				return out;
			},
			MAX_TRIGGERS,
		);

		const snapshotOverlay = () => {
			const set = new Set();
			for (const el of __w.deepAll()) {
				if (!__w.visible(el)) continue;
				const cs = getComputedStyle(el);
				if (cs.position !== "absolute" && cs.position !== "fixed") continue;
				const r = el.getBoundingClientRect();
				if (r.width < 8 || r.height < 8 || r.width * r.height > innerWidth * innerHeight * 0.6) continue;
				if ((el.textContent || "").trim().length === 0 && !el.querySelector("img,svg")) continue;
				set.add(__w.ref(el));
			}
			return [...set];
		};

		let hoverTested = 0;
		for (const ref of triggers) {
			const base = await page.eval(`(${snapshotOverlay.toString()})()`);
			const pos = await page.eval((r) => {
				const el = __w.at(r);
				el.scrollIntoView({ block: "center", inline: "center" });
				const b = el.getBoundingClientRect();
				return { x: b.left + b.width / 2, y: b.top + b.height / 2 };
			}, ref);
			await page.mouseMove(2, 2);
			await page.mouseMove(pos.x, pos.y);
			await page.settle();
			const afterRefs = await page.eval(`(${snapshotOverlay.toString()})()`);
			const fresh = afterRefs.filter((r) => !base.includes(r));
			if (!fresh.length) continue;
			hoverTested++;
			const popup = await page.eval((a) => {
				const trigger = __w.at(a.ref);
				const cands = a.fresh.map((r) => __w.at(r)).filter((e) => !e.contains(trigger));
				if (!cands.length) return null;
				const el = cands[0];
				const r = el.getBoundingClientRect();
				return { ref: a.fresh[0], x: r.left + r.width / 2, y: r.top + r.height / 2, selector: __w.cssPath(el), snippet: __w.snippet(el) };
			}, { ref, fresh });
			if (!popup) continue;
			const tr = await page.eval((r) => ({ selector: __w.cssPath(__w.at(r)), snippet: __w.snippet(__w.at(r)) }), ref);

			await page.key("Escape");
			await page.settle();
			const dismissed = await page.eval((r) => !__w.visible(__w.at(r)) || !document.contains(__w.at(r)), popup.ref);
			if (!dismissed)
				findings.push({ sc: "1.4.13", kind: "fail", check: "hover:not-dismissible", ...tr, message: `content revealed on hover (${popup.selector}) stays visible after Escape, so a low-vision user cannot clear it without moving the pointer` });

			await page.mouseMove(2, 2);
			await page.mouseMove(pos.x, pos.y);
			await page.settle();
			const stillThere = await page.eval((r) => __w.visible(__w.at(r)), popup.ref);
			if (stillThere) {
				await page.mouseMove(popup.x, popup.y);
				await page.settle();
				const hoverable = await page.eval((r) => __w.visible(__w.at(r)), popup.ref);
				if (!hoverable)
					findings.push({ sc: "1.4.13", kind: "fail", check: "hover:not-hoverable", ...tr, message: `content revealed on hover (${popup.selector}) disappears when the pointer moves onto it` });
			}
			await page.mouseMove(2, 2);
			await page.key("Escape");
		}

		await page.mouseMove(2, 2);
		return { findings, note: `${inspected} interactive elements' event listeners read, ${hoverTested} hover popups exercised` };
	},
};
