#!/usr/bin/env node
// review.mjs: send one image and a prompt to a vision model and print its reply.
// Works with any model behind an OpenAI-compatible chat-completions endpoint.
//
// Usage:
//   node review.mjs <image-path> [--prompt TEXT] [--base URL] [--model NAME]
//
// Settings are read from flags, then environment variables, then `.env` in the
// working directory, then `~/.config/vision/env`.
//
// The endpoint and its key are chosen as a pair, so a key only goes to its own host:
//   1. --base or VISION_BASE_URL, with VISION_API_KEY (no key for a loopback host)
//   2. OPENAI_API_KEY, with OPENAI_BASE_URL or https://api.openai.com/v1
//   3. GEMINI_API_KEY, with https://generativelanguage.googleapis.com/v1beta/openai
// The model has no default, because model names go stale: set --model or VISION_MODEL.

import { readFileSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";

const LOOPBACK_KEY = "loopback-placeholder";
const OPENAI_BASE = "https://api.openai.com/v1";
const GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta/openai";
const SETTINGS = ["VISION_API_KEY", "VISION_BASE_URL", "VISION_MODEL", "OPENAI_API_KEY", "OPENAI_BASE_URL", "GEMINI_API_KEY"];

const DEFAULT_PROMPT = [
	"Inspect this UI screenshot or diagram thoroughly. ",
	"Structure your response into four sections: ",
	"1. Layout & Hierarchy: grid alignment, spacing consistency, focal order, visual rhythm. ",
	"2. Typography & Contrast: font scale hierarchy, readable line lengths, apparent contrast issues. ",
	"3. Elements & State: interactive affordances, label legibility, missing focus/hover indicators, clipping or overflow. ",
	"4. Actionable Fixes: concrete, ranked recommendations with specific CSS/DOM suggestions. ",
	"State facts concisely without filler. Never guess contrast ratios; identify suspect pairs for deterministic measurement.",
].join("");

function fail(message, code = 1) {
	console.error(message);
	process.exit(code);
}

function parseArgs(argv) {
	const opts = { prompt: DEFAULT_PROMPT, base: null, model: null, image: null };
	for (let i = 0; i < argv.length; i += 1) {
		const arg = argv[i];
		if (arg === "--prompt") opts.prompt = argv[++i];
		else if (arg === "--base") opts.base = argv[++i];
		else if (arg === "--model") opts.model = argv[++i];
		else if (arg.startsWith("--")) fail(`unknown flag: ${arg}`, 2);
		else opts.image = arg;
	}
	return opts;
}

// Environment variables win over the env files; the working directory's file wins over the home one.
function loadSettings() {
	const found = {};
	for (const file of [join(process.cwd(), ".env"), join(homedir(), ".config", "vision", "env")]) {
		let text;
		try {
			text = readFileSync(file, "utf8");
		} catch {
			continue;
		}
		for (const line of text.split(/\r?\n/)) {
			const m = line.match(/^\s*(?:export\s+)?([A-Z_]+)\s*=\s*(.*?)\s*$/);
			if (!m || !SETTINGS.includes(m[1]) || found[m[1]]) continue;
			const value = m[2].replace(/^(["'])(.*)\1$/, "$2");
			if (value) found[m[1]] = value;
		}
	}
	for (const name of SETTINGS) {
		const value = process.env[name]?.trim();
		if (value) found[name] = value;
	}
	return found;
}

function hostOf(base) {
	try {
		return new URL(base).hostname.replace(/^\[|\]$/g, "");
	} catch {
		return "";
	}
}

function isLoopback(base) {
	const host = hostOf(base);
	return host === "127.0.0.1" || host === "localhost" || host === "::1";
}

function resolveEndpoint(flagBase, s) {
	const providers = [
		{ base: s.OPENAI_BASE_URL ?? OPENAI_BASE, key: s.OPENAI_API_KEY },
		{ base: GEMINI_BASE, key: s.GEMINI_API_KEY },
	];
	const base = flagBase ?? s.VISION_BASE_URL;
	if (!base) {
		const provider = providers.find((p) => p.key);
		if (provider) return provider;
		if (s.VISION_API_KEY) fail("error: VISION_API_KEY is set but no endpoint. Set VISION_BASE_URL or pass --base.");
		fail("error: no API key found. Set OPENAI_API_KEY, GEMINI_API_KEY, or VISION_API_KEY with VISION_BASE_URL.");
	}
	const host = hostOf(base);
	if (!host) fail(`error: not a URL: ${base}`);
	// VISION_API_KEY belongs to VISION_BASE_URL's host when both are set, so --base to another host does not get it.
	const visionKey = !s.VISION_BASE_URL || hostOf(s.VISION_BASE_URL) === host ? s.VISION_API_KEY : null;
	const key = providers.find((p) => p.key && hostOf(p.base) === host)?.key ?? visionKey ?? (isLoopback(base) ? LOOPBACK_KEY : null);
	if (!key) fail(`error: no API key for ${host}. Set VISION_API_KEY together with VISION_BASE_URL for that host.`);
	return { base, key };
}

// A base that already names an API version (.../v1, .../v1beta/openai) is used as given; a bare host gets /v1.
function chatUrl(base) {
	const url = base.replace(/\/+$/, "");
	if (url.endsWith("/chat/completions")) return url;
	return /\/v\d+[a-z]*(\/|$)/.test(new URL(url).pathname) ? `${url}/chat/completions` : `${url}/v1/chat/completions`;
}

const opts = parseArgs(process.argv.slice(2));
if (!opts.image) fail("Usage: node review.mjs <image-path> [--prompt TEXT] [--base URL] [--model NAME]");

let bytes;
try {
	bytes = readFileSync(opts.image);
} catch (err) {
	fail(`failed to read image '${opts.image}': ${err.message}`);
}

const settings = loadSettings();
const { base, key } = resolveEndpoint(opts.base, settings);
const model = opts.model ?? settings.VISION_MODEL;
if (!model) fail("error: no model set. Pass --model or set VISION_MODEL to a vision-capable model on that endpoint.");

const isJpeg = /\.jpe?g$/i.test(opts.image);
const isWebp = /\.webp$/i.test(opts.image);
const mime = isJpeg ? "image/jpeg" : (isWebp ? "image/webp" : "image/png");

const body = {
	model,
	messages: [{
		role: "user",
		content: [
			{ type: "text", text: opts.prompt },
			{ type: "image_url", image_url: { url: `data:${mime};base64,${bytes.toString("base64")}` } },
		],
	}],
};

// After the request, failures set the exit code and let the process end by itself:
// process.exit() with a socket still open crashes Node on Windows (libuv assertion).
const endpoint = chatUrl(base);
try {
	const response = await fetch(endpoint, {
		method: "POST",
		headers: {
			"Content-Type": "application/json",
			"Authorization": `Bearer ${key}`,
		},
		body: JSON.stringify(body),
	});
	const raw = await response.text();
	if (!response.ok) throw new Error(`vision endpoint error ${response.status} from ${endpoint}: ${raw.slice(0, 500)}`);

	const content = JSON.parse(raw).choices?.[0]?.message?.content;
	const text = Array.isArray(content) ? content.map((part) => part.text ?? "").join("") : (content ?? "");
	if (!text.trim()) throw new Error(`vision endpoint returned no text from ${endpoint} (model ${model})`);
	console.log(text.trim());
} catch (err) {
	console.error(err.message.startsWith("vision endpoint") ? err.message : `request to ${endpoint} failed: ${err.message}`);
	process.exitCode = 1;
}
