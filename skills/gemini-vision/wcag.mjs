#!/usr/bin/env node
// wcag.mjs — WCAG 2.x contrast ratio checker. Deterministic math — never
// quote a model's number. Ported from wcag.py.
//
//   node wcag.mjs "#5E6B72" "#F6FBFE"      # one line per pair
//   node wcag.mjs --selftest                # built-in assertions
//
// Prints one line per pair: ratio, AA-normal (4.5) pass/fail,
// AA-large/UI (3.0) pass/fail.

const AA_NORMAL = 4.5;
const AA_LARGE_UI = 3.0;

function srgbChannel(c) {
	return c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
}

function relativeLuminance(hexColor) {
	let h = hexColor.trim().replace(/^#/, "");
	if (h.length === 3) h = [...h].map((ch) => ch + ch).join("");
	if (!/^[0-9a-fA-F]{6}$/.test(h)) throw new Error(`bad hex: ${JSON.stringify(hexColor)}`);
	const [r, g, b] = [0, 2, 4].map((i) => Number.parseInt(h.slice(i, i + 2), 16) / 255);
	return 0.2126 * srgbChannel(r) + 0.7152 * srgbChannel(g) + 0.0722 * srgbChannel(b);
}

function contrastRatio(fg, bg) {
	const [l1, l2] = [relativeLuminance(fg), relativeLuminance(bg)].sort((a, b) => b - a);
	return Math.round(((l1 + 0.05) / (l2 + 0.05)) * 100) / 100;
}

const argv = process.argv.slice(2);
if (argv.includes("--selftest")) {
	const close = (a, b) => Math.abs(a - b) < 0.01;
	if (!close(contrastRatio("#000000", "#FFFFFF"), 21.0)) throw new Error("selftest: black/white != 21");
	if (!close(contrastRatio("#FFFFFF", "#000000"), 21.0)) throw new Error("selftest: white/black != 21");
	if (!(contrastRatio("#767676", "#FFFFFF") >= AA_NORMAL)) throw new Error("selftest: #767676 should pass AA");
	if (!(contrastRatio("#777777", "#FFFFFF") < AA_NORMAL)) throw new Error("selftest: #777777 should fail AA");
	console.log("selftest OK");
	process.exit(0);
}
if (argv.length < 2 || argv.length % 2 !== 0) {
	console.log("usage: node wcag.mjs <fg> <bg> [fg bg ...]   |   node wcag.mjs --selftest");
	process.exit(1);
}
for (let i = 0; i < argv.length; i += 2) {
	const [fg, bg] = [argv[i], argv[i + 1]];
	const r = contrastRatio(fg, bg);
	const verdict = r >= AA_NORMAL
		? "PASS AA normal"
		: r >= AA_LARGE_UI
			? "large-text/UI only (>=3.0)"
			: "FAIL";
	console.log(`${fg} on ${bg}: ${r}:1 — ${verdict}`);
}
