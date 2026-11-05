export class Connection {
	#ws;
	#nextId = 0;
	#pending = new Map();
	#listeners = new Set();

	static async open(url) {
		const ws = new WebSocket(url);
		await new Promise((resolve, reject) => {
			ws.addEventListener("open", resolve, { once: true });
			ws.addEventListener("error", () => reject(new Error(`cannot reach DevTools endpoint ${url}`)), { once: true });
		});
		return new Connection(ws);
	}

	constructor(ws) {
		this.#ws = ws;
		ws.addEventListener("message", (event) => this.#dispatch(JSON.parse(event.data)));
		ws.addEventListener("close", () => {
			for (const { reject } of this.#pending.values()) reject(new Error("DevTools connection closed"));
			this.#pending.clear();
		});
	}

	#dispatch(message) {
		if (message.id !== undefined) {
			const entry = this.#pending.get(message.id);
			if (!entry) return;
			this.#pending.delete(message.id);
			if (message.error) entry.reject(new Error(`${entry.method}: ${message.error.message}`));
			else entry.resolve(message.result);
			return;
		}
		for (const listener of this.#listeners) listener(message);
	}

	send(method, params = {}, sessionId) {
		const id = ++this.#nextId;
		return new Promise((resolve, reject) => {
			this.#pending.set(id, { resolve, reject, method });
			this.#ws.send(JSON.stringify({ id, method, params, sessionId }));
		});
	}

	subscribe(listener) {
		this.#listeners.add(listener);
		return () => this.#listeners.delete(listener);
	}

	waitFor(predicate, timeoutMs, label) {
		return new Promise((resolve, reject) => {
			const timer = setTimeout(() => {
				off();
				reject(new Error(`timed out after ${timeoutMs} ms waiting for ${label}`));
			}, timeoutMs);
			const off = this.subscribe((message) => {
				if (!predicate(message)) return;
				clearTimeout(timer);
				off();
				resolve(message);
			});
		});
	}

	close() {
		this.#ws.close();
	}
}
