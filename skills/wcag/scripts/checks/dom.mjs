const PERSONAL = /^(name|full-?name|first-?name|last-?name|given-?name|family-?name|email|e-?mail|phone|tel|telephone|mobile|address|street|city|zip|postal|postcode|country|state|province|birth|dob|bday|username|user-?name|login|cc-?(number|name|exp|csc|cvc)|card-?number|organization|company)$/i;
const VALID_AUTOCOMPLETE = new Set("off on name honorific-prefix given-name additional-name family-name honorific-suffix nickname username new-password current-password one-time-code organization-title organization street-address address-line1 address-line2 address-line3 address-level4 address-level3 address-level2 address-level1 country country-name postal-code cc-name cc-given-name cc-additional-name cc-family-name cc-number cc-exp cc-exp-month cc-exp-year cc-csc cc-type transaction-currency transaction-amount language bday bday-day bday-month bday-year sex url photo tel tel-country-code tel-national tel-area-code tel-local tel-local-prefix tel-local-suffix tel-extension email impp webauthn".split(" "));
const GENERIC_TITLE = /^(untitled( document| page)?|document|home|index|page|new page|welcome|react app|vite app|localhost.*|\d+)$/i;

export default {
	id: "dom",
	covers: { "3.1.1": "measured", "2.4.2": "partial", "1.4.4": "partial", "1.3.5": "measured", "2.2.1": "partial", "1.4.2": "partial", "2.2.2": "partial", "1.2.1": "partial", "1.2.2": "partial", "1.2.3": "partial", "1.2.5": "partial", "3.3.8": "partial", "3.2.2": "partial", "2.4.1": "partial" },
	async run(page, ctx) {
		const reduce = (ctx?.media ?? []).some((m) => m.name === "prefers-reduced-motion" && m.value === "reduce");
		const d = await page.eval(
			(K) => {
				const out = { findings: [] };
				const add = (sc, kind, check, el, message, measured) =>
					out.findings.push({ sc, kind, check, selector: el ? __w.cssPath(el) : "html", snippet: el ? __w.snippet(el) : "", message, ...(measured ? { measured } : {}) });
				const html = document.documentElement;

				const lang = html.getAttribute("lang");
				if (!lang || !lang.trim()) add("3.1.1", "fail", "dom:html-lang", html, "html element has no lang attribute");
				else if (!/^[a-zA-Z]{2,3}(-[a-zA-Z0-9]{2,8})*$/.test(lang.trim())) add("3.1.1", "fail", "dom:html-lang", html, `lang="${lang}" is not a valid language tag`);

				const title = document.title.trim();
				if (!title) add("2.4.2", "fail", "dom:title", document.head, "page has no title");
				else if (new RegExp(K.generic, "i").test(title)) add("2.4.2", "review", "dom:title", document.head, `title "${title}" does not describe the page`);

				for (const m of document.querySelectorAll("meta[name=viewport]")) {
					const c = (m.getAttribute("content") || "").toLowerCase();
					const noScale = /user-scalable\s*=\s*(no|0)/.test(c);
					const max = /maximum-scale\s*=\s*([\d.]+)/.exec(c);
					if (noScale || (max && parseFloat(max[1]) < 2)) add("1.4.4", "fail", "dom:viewport-zoom-lock", m, `viewport meta blocks pinch zoom (${c})`);
				}

				for (const m of document.querySelectorAll("meta[http-equiv=refresh i]")) {
					const t = parseFloat((m.getAttribute("content") || "").split(/[;,]/)[0]);
					if (t > 0) add("2.2.1", "fail", "dom:meta-refresh", m, `page refreshes or redirects itself after ${t} s with no way to stop it`);
				}

				for (const el of document.querySelectorAll("marquee,blink")) if (__w.visible(el)) add("2.2.2", "fail", "dom:marquee", el, `<${el.localName}> moves or blinks with no way to stop it`);

				for (const el of document.querySelectorAll("input,select,textarea")) {
					if (!__w.visible(el) || el.type === "hidden") continue;
					const ac = (el.getAttribute("autocomplete") || "").trim().toLowerCase();
					if (ac) {
						const tokens = ac.split(/\s+/).filter((t) => !/^(section-|shipping|billing|home|work|mobile|fax|pager)/.test(t));
						const bad = tokens.filter((t) => !K.valid.includes(t));
						if (bad.length) add("1.3.5", "fail", "dom:autocomplete-invalid", el, `autocomplete token "${bad[0]}" is not in the HTML autofill list`);
						continue;
					}
					if (["checkbox", "radio", "submit", "button", "reset", "file", "image", "range", "color"].includes(el.type)) continue;
					const hint = [el.name, el.id, el.type, el.getAttribute("aria-label")].filter(Boolean).join(" ");
					const key = hint.split(/[\s_\[\]]+/).find((t) => new RegExp(K.personal, "i").test(t));
					if (key || el.type === "email" || el.type === "tel" || el.type === "password") {
						add("1.3.5", "fail", "dom:autocomplete-missing", el, `field looks like user data (${key || el.type}) but has no autocomplete attribute`);
					}
				}

				for (const v of document.querySelectorAll("video,audio")) {
					if (!__w.visible(v) && !v.hasAttribute("autoplay")) continue;
					if (v.hasAttribute("autoplay") && !v.muted && !v.hasAttribute("muted") && (v.duration > 3 || Number.isNaN(v.duration) || v.duration === Infinity))
						add("1.4.2", "fail", "dom:autoplay-audio", v, "media with sound starts by itself and runs longer than 3 seconds");
					if (v.localName === "video") {
						const kinds = [...v.querySelectorAll("track")].map((t) => t.kind);
						if (!kinds.includes("captions") && !kinds.includes("subtitles")) add("1.2.2", "review", "dom:video-captions", v, "video has no captions or subtitles track; confirm captions are provided another way or the video has no speech");
						if (!kinds.includes("descriptions")) add("1.2.5", "review", "dom:video-audio-description", v, "video has no descriptions track; confirm visual information is described in audio or a text alternative");
					} else if (!document.querySelector("a[href*=transcript i]") && !/transcript/i.test(document.body.innerText)) {
						add("1.2.1", "review", "dom:audio-transcript", v, "audio element and no transcript text or link found on the page");
					}
					if (!v.hasAttribute("controls") && v.hasAttribute("autoplay")) add("1.4.2", "fail", "dom:autoplay-no-controls", v, "autoplaying media has no controls to pause or mute it");
				}

				const infinite = document.getAnimations().filter((a) => {
					const t = a.effect?.getComputedTiming?.();
					return t && t.iterations === Infinity && a.playState === "running" && a.effect.target && __w.visible(a.effect.target);
				});
				const moving = new Map();
				for (const a of infinite) {
					const el = a.effect.target;
					const props = a.effect.getKeyframes().flatMap((k) => Object.keys(k)).filter((p) => !["offset", "easing", "composite", "computedOffset"].includes(p));
					if (props.some((p) => /opacity|transform|translate|rotate|scale|left|top|margin|background|color|filter|clip/i.test(p)) && !moving.has(el)) moving.set(el, a);
					const dur = a.effect.getComputedTiming().duration;
					if (typeof dur === "number" && dur > 0 && dur < 333 && !moving.has(el)) moving.set(el, a);
				}
				let n = 0;
				for (const [el, a] of moving) {
					if (n++ >= 8) break;
					if (K.reduce) {
						add("2.2.2", "review", "dom:reduced-motion-ignored", el, "animation still repeats forever while the user asks for reduced motion (prefers-reduced-motion: reduce). Remove spatial movement and keep state feedback");
						continue;
					}
					const dur = a.effect.getComputedTiming().duration;
					const hasPause = !!document.querySelector("[aria-label*=pause i],[aria-label*=stop i],button[class*=pause i]");
					const spinnerLike = el.closest("[role=progressbar],[aria-busy=true]") || /spin|load|progress|skeleton/i.test(el.className?.toString() || "");
					if (spinnerLike) continue;
					add("2.2.2", hasPause ? "review" : "review", "dom:looping-animation", el, `animation repeats forever (${Math.round(dur)} ms cycle). Auto-starting motion longer than 5 s needs a pause control; flashing faster than 3 times a second fails 2.3.1`);
				}

				for (const f of document.querySelectorAll("form")) {
					const hasSubmit = f.querySelector("button:not([type=button]):not([type=reset]),input[type=submit],input[type=image]");
					if (!hasSubmit && f.querySelectorAll("input:not([type=hidden]),select,textarea").length > 1 && __w.visible(f)) {
						const r = f.querySelector("input,select,textarea");
						add("3.2.2", "review", "dom:form-no-submit", r, "form has several fields and no submit button; confirm changes do not submit on input alone");
					}
				}
				for (const s of document.querySelectorAll("select[onchange],input[onchange]")) {
					const code = s.getAttribute("onchange") || "";
					if (/location|submit|href|window\.open/i.test(code) && __w.visible(s)) add("3.2.2", "fail", "dom:onchange-navigation", s, "changing this control navigates or submits without a separate button");
				}

				for (const p of document.querySelectorAll("input[type=password]")) {
					if (!__w.visible(p)) continue;
					const ev = new ClipboardEvent("paste", { bubbles: true, cancelable: true, clipboardData: new DataTransfer() });
					p.dispatchEvent(ev);
					if (ev.defaultPrevented) add("3.3.8", "fail", "dom:paste-blocked", p, "password field cancels paste, which blocks password managers and forces recall");
					const ac = (p.getAttribute("autocomplete") || "").toLowerCase();
					if (!/current-password|new-password|one-time-code|webauthn/.test(ac)) add("3.3.8", "review", "dom:password-autocomplete", p, "password field has no current-password or new-password autocomplete token");
				}
				const captcha = document.querySelector("iframe[src*=recaptcha i],iframe[src*=hcaptcha i],iframe[src*=captcha i],.g-recaptcha,.h-captcha,img[src*=captcha i],img[alt*=captcha i],[class*=captcha i]");
				if (captcha) add("3.3.8", "review", "dom:captcha", captcha, "a CAPTCHA is present; a text or puzzle test at login fails 3.3.8 unless an alternative that needs no recall or transcription is offered");

				const firstFocusable = __w.tabbable()[0];
				const hasSkip = firstFocusable && firstFocusable.localName === "a" && (firstFocusable.getAttribute("href") || "").startsWith("#");
				const landmarks = document.querySelectorAll("main,[role=main]").length;
				const navBlocks = document.querySelectorAll("nav,[role=navigation],header a").length;
				if (!hasSkip && !landmarks && navBlocks) add("2.4.1", "fail", "dom:bypass-blocks", html, "page has navigation but no skip link and no main landmark, so keyboard users must Tab through every repeated link");

				return out;
			},
			{ reduce, personal: PERSONAL.source, valid: [...VALID_AUTOCOMPLETE], generic: GENERIC_TITLE.source },
		);
		return { findings: d.findings, note: `${d.findings.length} page-level observations` };
	},
};
