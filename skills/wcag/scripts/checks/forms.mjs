const MAX_FORMS = 6;

export default {
	id: "forms",
	once: true,
	covers: { "3.3.1": "partial", "3.3.3": "partial", "4.1.3": "partial", "3.3.2": "partial" },
	async run(page) {
		const findings = [];
		const writes = await page.blockWrites();

		try {
			const forms = await page.eval((max) => {
				const out = [];
				for (const f of document.forms) {
					if (!__w.visible(f)) continue;
					const fields = [...f.elements].filter((e) => ["INPUT", "SELECT", "TEXTAREA"].includes(e.tagName) && e.type !== "hidden" && __w.visible(e));
					const constrained = fields.filter((e) => e.required || e.getAttribute("aria-required") === "true" || e.pattern || ["email", "url", "number"].includes(e.type));
					if (!constrained.length) continue;
					if (fields.some((e) => e.type === "password" && !e.required && f.querySelectorAll("input[type=password]").length > 1)) continue;
					const submit = f.querySelector("button:not([type=button]):not([type=reset]),input[type=submit],input[type=image]");
					if (!submit || !__w.visible(submit)) continue;
					out.push({ selector: __w.cssPath(f), submit: __w.cssPath(submit), novalidate: f.noValidate });
					if (out.length >= max) break;
				}
				return out;
			}, MAX_FORMS);

			for (const form of forms) {
				await page.eval(() => {
					window.__w_live = [];
					window.__w_obs?.disconnect();
					window.__w_obs = new MutationObserver((list) => {
						for (const r of list) {
							for (const n of r.addedNodes) {
								const el = n.nodeType === 1 ? n : n.parentElement;
								if (!el) continue;
								const region = el.closest("[role=alert],[role=status],[role=log],[aria-live]:not([aria-live=off])");
								window.__w_live.push({ inRegion: !!region, text: (n.textContent || "").trim().slice(0, 80) });
							}
							if (r.type === "characterData" || r.type === "attributes") {
								const el = r.target.nodeType === 1 ? r.target : r.target.parentElement;
								const region = el?.closest("[role=alert],[role=status],[role=log],[aria-live]:not([aria-live=off])");
								if (region) window.__w_live.push({ inRegion: true, text: (region.textContent || "").trim().slice(0, 80) });
							}
						}
					});
					window.__w_obs.observe(document.body, { subtree: true, childList: true, characterData: true });
				});
				await page.eval((sel) => {
					const f = document.querySelector(sel);
					window.__w_before = new Set((f?.innerText || "").split("\n").map((l) => l.trim()).filter(Boolean));
				}, form.selector);
				const pos = await page.center(form.submit);
				if (!pos) continue;
				await page.click(pos.x, pos.y);
				await page.settle();
				await page.eval(() => new Promise((r) => setTimeout(r, 250)));

				const result = await page.eval((sel) => {
					const f = document.querySelector(sel);
					if (!f) return null;
					const invalid = [...f.elements].filter((e) => e.willValidate && !e.checkValidity() && __w.visible(e) && e.type !== "hidden");
					const ariaInvalid = [...f.elements].filter((e) => e.getAttribute("aria-invalid") === "true" && __w.visible(e));
					const all = new Set([...invalid, ...ariaInvalid]);
					const rows = [];
					for (const e of all) {
						const ids = (e.getAttribute("aria-describedby") || "").split(/\s+/).concat((e.getAttribute("aria-errormessage") || "").split(/\s+/)).filter(Boolean);
						const text = ids.map((id) => document.getElementById(id)).filter((n) => n && __w.visible(n)).map((n) => n.textContent.trim()).filter(Boolean);
						const fresh = (f.innerText || "").split("\n").map((l) => l.trim()).filter((l) => l && !window.__w_before.has(l));
						const near = fresh.length ? fresh : [...f.querySelectorAll("[role=alert]")].filter((n) => __w.visible(n) && n.textContent.trim()).map((n) => n.textContent.trim());
						rows.push({
							selector: __w.cssPath(e),
							snippet: __w.snippet(e),
							native: !f.noValidate && !!e.validationMessage,
							flagged: e.getAttribute("aria-invalid") === "true",
							linked: text.length > 0,
							adjacentOnly: text.length === 0 && near.length > 0,
							message: (text[0] || near[0] || e.validationMessage || "").slice(0, 80),
						});
					}
					const active = document.activeElement;
					const firstInvalid = [...all][0];
					return { rows, focusOnInvalid: !!active && all.has(active), focusInForm: !!active && f.contains(active), firstInvalid: firstInvalid ? __w.cssPath(firstInvalid) : null, live: window.__w_live || [] };
				}, form.selector);
				if (!result || !result.rows.length) continue;

				for (const row of result.rows) {
					if (row.native && !result.rows.some((r) => r.linked)) continue;
					if (!row.linked && !row.adjacentOnly && !row.native)
						findings.push({ sc: "3.3.1", kind: "fail", check: "forms:error-not-identified", selector: row.selector, snippet: row.snippet, message: "after submitting an empty form this field is invalid but no error text is shown or linked to it" });
					else if (row.adjacentOnly && !row.native)
						findings.push({ sc: "3.3.1", kind: "fail", check: "forms:error-not-linked", selector: row.selector, snippet: row.snippet, message: `error text "${row.message}" appears near the field but is not tied to it with aria-describedby or aria-errormessage, and the field is not marked aria-invalid`.replace(", and the field is not marked aria-invalid", row.flagged ? "" : ", and the field is not marked aria-invalid") });
					else if (!row.flagged && !row.native && row.linked)
						findings.push({ sc: "4.1.2", kind: "review", check: "forms:no-aria-invalid", selector: row.selector, snippet: row.snippet, message: "field has linked error text but is not marked aria-invalid, so its invalid state is not exposed as a state" });
				}
				const announced = result.live.some((l) => l.inRegion && l.text);
				const errorTextShown = result.rows.some((r) => r.linked || r.adjacentOnly);
				if (errorTextShown && !announced && !result.focusOnInvalid)
					findings.push({ sc: "4.1.3", kind: "fail", check: "forms:error-not-announced", selector: form.selector, snippet: "", message: "validation errors appeared in the page but not inside a live region, and focus did not move to an invalid field, so a screen reader user hears nothing" });
				if (errorTextShown && !result.focusInForm && !announced)
					findings.push({ sc: "3.3.1", kind: "review", check: "forms:focus-left-form", selector: form.selector, snippet: "", message: "after a failed submit focus is outside the form; confirm the user is told where the errors are" });
			}
		} finally {
			await writes.stop();
			await page.eval(() => window.__w_obs?.disconnect());
		}
		return { findings, note: `submitted empty forms with writes blocked (${writes.count()} blocked requests)` };
	},
};
