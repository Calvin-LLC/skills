import { INPAGE } from "./inpage.mjs";

const KEYS = {
	Tab: { code: "Tab", keyCode: 9 },
	Enter: { code: "Enter", keyCode: 13, text: "\r" },
	Escape: { code: "Escape", keyCode: 27 },
	Space: { code: "Space", keyCode: 32, key: " ", text: " " },
	ArrowDown: { code: "ArrowDown", keyCode: 40 },
	ArrowUp: { code: "ArrowUp", keyCode: 38 },
	ArrowLeft: { code: "ArrowLeft", keyCode: 37 },
	ArrowRight: { code: "ArrowRight", keyCode: 39 },
};

export class Page {
	constructor(connection, sessionId, targetId) {
		this.connection = connection;
		this.sessionId = sessionId;
		this.targetId = targetId;
		this.consoleErrors = [];
	}

	send(method, params = {}) {
		return this.connection.send(method, params, this.sessionId);
	}

	async init() {
		await Promise.all([
			this.send("Page.enable"),
			this.send("DOM.enable"),
			this.send("Runtime.enable"),
			this.send("Accessibility.enable"),
			this.send("Emulation.setFocusEmulationEnabled", { enabled: true }),
			this.send("Page.setLifecycleEventsEnabled", { enabled: true }),
		]);
		await this.send("Page.addScriptToEvaluateOnNewDocument", { source: INPAGE });
		this.connection.subscribe((m) => {
			if (m.sessionId !== this.sessionId) return;
			if (m.method === "Runtime.exceptionThrown") this.consoleErrors.push(m.params.exceptionDetails.text);
		});
		await this.setViewport(1280, 800);
	}

	async setViewport(width, height, { scale = 1, mobile = false } = {}) {
		await this.send("Emulation.setDeviceMetricsOverride", { width, height, deviceScaleFactor: scale, mobile });
	}

	async goto(url, timeoutMs = 30000) {
		const idle = new Set();
		const off = this.connection.subscribe((m) => {
			if (m.sessionId === this.sessionId && m.method === "Page.lifecycleEvent" && m.params.name === "networkIdle") idle.add(m.params.loaderId);
		});
		try {
			const nav = await this.send("Page.navigate", { url });
			if (nav.errorText) throw new Error(`navigation to ${url} failed: ${nav.errorText}`);
			if (!nav.loaderId) return { networkIdle: true };
			const deadline = Date.now() + timeoutMs;
			while (!idle.has(nav.loaderId)) {
				if (Date.now() > deadline) return { networkIdle: false };
				await new Promise((resolve) => setTimeout(resolve, 25));
			}
			return { networkIdle: true };
		} finally {
			off();
		}
	}

	async eval(fn, arg, { cli = false } = {}) {
		const source = typeof fn === "function" ? fn.toString() : fn;
		const expression = typeof fn === "function" ? `(${source})(${JSON.stringify(arg ?? null)})` : source;
		const res = await this.send("Runtime.evaluate", {
			expression,
			returnByValue: true,
			awaitPromise: true,
			includeCommandLineAPI: cli,
		});
		if (res.exceptionDetails) {
			const d = res.exceptionDetails;
			throw new Error(`in-page error: ${d.exception?.description ?? d.text}`);
		}
		return res.result.value;
	}

	async key(name, { shift = false } = {}) {
		const spec = KEYS[name];
		if (!spec) throw new Error(`unmapped key ${name}`);
		const base = {
			key: spec.key ?? name,
			code: spec.code,
			windowsVirtualKeyCode: spec.keyCode,
			nativeVirtualKeyCode: spec.keyCode,
			modifiers: shift ? 8 : 0,
		};
		await this.send("Input.dispatchKeyEvent", { type: "rawKeyDown", ...base });
		if (spec.text) await this.send("Input.dispatchKeyEvent", { type: "char", ...base, text: spec.text });
		await this.send("Input.dispatchKeyEvent", { type: "keyUp", ...base });
	}

	async mouseMove(x, y) {
		await this.send("Input.dispatchMouseEvent", { type: "mouseMoved", x, y });
	}

	async click(x, y) {
		await this.send("Input.dispatchMouseEvent", { type: "mouseMoved", x, y });
		await this.send("Input.dispatchMouseEvent", { type: "mousePressed", x, y, button: "left", clickCount: 1 });
		await this.send("Input.dispatchMouseEvent", { type: "mouseReleased", x, y, button: "left", clickCount: 1 });
	}

	async center(selector) {
		return this.eval((sel) => {
			const el = document.querySelector(sel);
			if (!el) return null;
			el.scrollIntoView({ block: "center", inline: "center" });
			const r = el.getBoundingClientRect();
			return { x: r.left + r.width / 2, y: r.top + r.height / 2 };
		}, selector);
	}

	async shot(rect) {
		const pos = await this.eval(() => ({ x: scrollX, y: scrollY }));
		const x = Math.max(0, Math.floor(rect.x + pos.x));
		const y = Math.max(0, Math.floor(rect.y + pos.y));
		const width = Math.max(1, Math.ceil(rect.width));
		const height = Math.max(1, Math.ceil(rect.height));
		const res = await this.send("Page.captureScreenshot", {
			format: "png",
			clip: { x, y, width, height, scale: 1 },
			captureBeyondViewport: true,
			fromSurface: true,
		});
		return res.data;
	}

	async axTree() {
		const { nodes } = await this.send("Accessibility.getFullAXTree");
		return nodes;
	}

	async waitFor(fn, arg, timeoutMs = 1500) {
		const deadline = Date.now() + timeoutMs;
		for (;;) {
			const v = await this.eval(fn, arg);
			if (v) return v;
			if (Date.now() > deadline) return false;
			await this.eval(() => new Promise((resolve) => requestAnimationFrame(resolve)));
		}
	}

	async settle() {
		await this.eval(() => __w.settle());
	}

	async blockWrites() {
		let blocked = 0;
		await this.send("Fetch.enable", { patterns: [{ urlPattern: "*" }] });
		const off = this.connection.subscribe((m) => {
			if (m.sessionId !== this.sessionId || m.method !== "Fetch.requestPaused") return;
			const { requestId, request } = m.params;
			if (request.method === "GET" || request.method === "HEAD" || request.method === "OPTIONS") {
				this.send("Fetch.continueRequest", { requestId }).catch(() => {});
			} else {
				blocked++;
				this.send("Fetch.failRequest", { requestId, errorReason: "BlockedByClient" }).catch(() => {});
			}
		});
		return {
			count: () => blocked,
			stop: async () => {
				off();
				await this.send("Fetch.disable").catch(() => {});
			},
		};
	}

	async emulateMedia(features) {
		await this.send("Emulation.setEmulatedMedia", { features });
	}

	async close() {
		try {
			await this.connection.send("Target.closeTarget", { targetId: this.targetId });
		} catch {}
	}
}
