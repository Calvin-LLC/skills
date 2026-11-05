import { spawn } from "node:child_process";
import { existsSync, mkdtempSync, readFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { delimiter, join } from "node:path";
import { setTimeout as sleep } from "node:timers/promises";
import { Connection } from "./cdp.mjs";
import { Page } from "./page.mjs";

const CANDIDATES = [
	"chromium",
	"chromium-browser",
	"google-chrome",
	"google-chrome-stable",
	"chrome",
	"msedge",
	"microsoft-edge",
	"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
	"/Applications/Chromium.app/Contents/MacOS/Chromium",
	"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
	"C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
];

function findChrome() {
	const wanted = process.env.CHROME_BIN;
	if (wanted) {
		if (!existsSync(wanted)) throw new Error(`browser not found: ${wanted}`);
		return wanted;
	}
	const dirs = (process.env.PATH ?? "").split(delimiter).filter(Boolean);
	for (const name of CANDIDATES) {
		if (name.includes("/") || name.includes("\\")) {
			if (existsSync(name)) return name;
			continue;
		}
		for (const dir of dirs) {
			for (const ext of process.platform === "win32" ? [".exe", ".cmd", ""] : [""]) {
				const full = join(dir, name + ext);
				if (existsSync(full)) return full;
			}
		}
	}
	throw new Error("no Chromium-based browser on PATH; set CHROME_BIN to its path");
}

function killGroup(child) {
	try {
		if (process.platform === "win32") child.kill("SIGKILL");
		else process.kill(-child.pid, "SIGKILL");
	} catch {}
}

function groupAlive(child) {
	if (process.platform === "win32") return child.exitCode === null;
	try {
		process.kill(-child.pid, 0);
		return true;
	} catch {
		return false;
	}
}

function removeProfile(profile) {
	try {
		rmSync(profile, { recursive: true, force: true, maxRetries: 5, retryDelay: 100 });
	} catch (e) {
		process.stderr.write(`warning: could not remove ${profile}: ${e.message}\n`);
	}
}

function killOnExit(child, profile) {
	process.once("exit", () => {
		killGroup(child);
		removeProfile(profile);
	});
	for (const [signal, code] of [["SIGINT", 130], ["SIGTERM", 143], ["SIGHUP", 129]]) process.once(signal, () => process.exit(code));
}

function waitForFile(path, child, timeoutMs) {
	return new Promise((resolve, reject) => {
		const deadline = Date.now() + timeoutMs;
		let exited = false;
		child.once("exit", (code) => {
			exited = true;
			reject(new Error(`browser exited with code ${code} before opening a DevTools port`));
		});
		const poll = () => {
			if (exited) return;
			if (existsSync(path)) {
				try {
					const lines = readFileSync(path, "utf8").trim().split("\n");
					if (lines.length >= 2) return resolve(lines);
				} catch {}
			}
			if (Date.now() > deadline) return reject(new Error(`no DevTools port file after ${timeoutMs} ms`));
			setTimeout(poll, 20);
		};
		poll();
	});
}

export async function openBrowser() {
	let child = null;
	let profile = null;
	let endpoint;
	const bin = findChrome();
	profile = mkdtempSync(join(process.env.TMPDIR ?? tmpdir(), "wcag-profile-"));
	const args = [
		"--headless=new",
		"--remote-debugging-port=0",
		`--user-data-dir=${profile}`,
		"--no-first-run",
		"--no-default-browser-check",
		"--disable-extensions",
		"--disable-background-networking",
		"--hide-scrollbars=false",
		"--force-color-profile=srgb",
		"about:blank",
	];
	if (process.getuid?.() === 0 || process.env.WCAG_NO_SANDBOX) args.splice(1, 0, "--no-sandbox");
	child = spawn(bin, args, { stdio: "ignore", detached: process.platform !== "win32" });
	killOnExit(child, profile);
	const [port, path] = await waitForFile(join(profile, "DevToolsActivePort"), child, 20000);
	endpoint = `ws://127.0.0.1:${port}${path}`;
	const connection = await Connection.open(endpoint);
	const version = await connection.send("Browser.getVersion");
	return {
		connection,
		product: version.product,
		async newPage() {
			const { targetId } = await connection.send("Target.createTarget", { url: "about:blank" });
			const { sessionId } = await connection.send("Target.attachToTarget", { targetId, flatten: true });
			const page = new Page(connection, sessionId, targetId);
			await page.init();
			return page;
		},
		async close() {
			try {
				connection.close();
			} catch {}
			if (child) {
				killGroup(child);
				const deadline = Date.now() + 10000;
				while (groupAlive(child) && Date.now() < deadline) await sleep(20);
			}
			if (profile) removeProfile(profile);
		},
	};
}
