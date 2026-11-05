#!/usr/bin/env node
// review.mjs — visual critique and inspection via OpenAI-compatible vision endpoint.
//
// Usage:
//   node review.mjs <image-path> [--prompt TEXT] [--base URL] [--model NAME]
//
// Key resolution (first non-empty wins):
//   1. VISION_API_KEY / OPENAI_API_KEY / GEMINI_API_KEY env var
//   2. Loopback placeholder if base is localhost/127.0.0.1

import { readFileSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";

const LOOPBACK_KEY = "loopback-placeholder";

const DEFAULT_PROMPT = [
	"Inspect this UI screenshot or diagram thoroughly. ",
	"Structure your response into four sections: ",
	"1. Layout & Hierarchy: grid alignment, spacing consistency, focal order, visual rhythm. ",
	"2. Typography & Contrast: font scale hierarchy, readable line lengths, apparent contrast issues. ",
	"3. Elements & State: interactive affordances, label legibility, missing focus/hover indicators, clipping or overflow. ",
	"4. Actionable Fixes: concrete, ranked recommendations with specific CSS/DOM suggestions. ",
	"State facts concisely without filler. Never guess contrast ratios; identify suspect pairs for deterministic measurement.",
].join("");

function parseArgs(argv) {
	const opts = {
		prompt: DEFAULT_PROMPT,
		base: process.env.VISION_BASE_URL ?? process.env.OPENAI_BASE_URL ?? "https://api.openai.com",
		model: process.env.VISION_MODEL ?? "gpt-4o",
		image: null,
	};
	for (let i = 0; i < argv.length; i += 1) {
		const arg = argv[i];
		if (arg === "--prompt") opts.prompt = argv[++i];
		else if (arg === "--base") opts.base = argv[++i];
		else if (arg === "--model") opts.model = argv[++i];
		else if (arg.startsWith("--")) {
			console.error(`unknown flag: ${arg}`);
			process.exit(2);
		} else opts.image = arg;
	}
	return opts;
}

const opts = parseArgs(process.argv.slice(2));

function isLoopback(base) {
	try {
		const host = new URL(base).hostname.replace(/^\[|\]$/g, "");
		return host === "127.0.0.1" || host === "localhost" || host === "::1";
	} catch {
		return false;
	}
}

function resolveApiKey() {
	const envKey = process.env.VISION_API_KEY || process.env.OPENAI_API_KEY || process.env.GEMINI_API_KEY;
	if (envKey) return envKey.trim();

	// Check local env files if present
	const envFiles = [
		join(process.cwd(), ".env"),
		join(homedir(), ".config", "vision", "env"),
	];
	for (const file of envFiles) {
		try {
			for (const line of readFileSync(file, "utf8").split("\n")) {
				const m = line.match(/^\s*(?:VISION_API_KEY|OPENAI_API_KEY|GEMINI_API_KEY)\s*=\s*(.+)$/);
				if (m) {
					const val = m[1].replace(/^["']|["']\s*$/g, "").trim();
					if (val) return val;
				}
			}
		} catch {}
	}

	if (isLoopback(opts.base)) return LOOPBACK_KEY;
	return null;
}

if (!opts.image) {
	console.error("Usage: node review.mjs <image-path> [--prompt TEXT] [--base URL] [--model NAME]");
	process.exit(1);
}

let bytes;
try {
	bytes = readFileSync(opts.image);
} catch (err) {
	console.error(`failed to read image '${opts.image}': ${err.message}`);
	process.exit(1);
}

const apiKey = resolveApiKey();
if (!apiKey) {
	console.error("error: no API key found. Set VISION_API_KEY or OPENAI_API_KEY in environment.");
	process.exit(1);
}

const isJpeg = /\.jpe?g$/i.test(opts.image);
const isWebp = /\.webp$/i.test(opts.image);
const mime = isJpeg ? "image/jpeg" : (isWebp ? "image/webp" : "image/png");

const body = {
	model: opts.model,
	messages: [{
		role: "user",
		content: [
			{ type: "text", text: opts.prompt },
			{ type: "image_url", image_url: { url: `data:${mime};base64,${bytes.toString("base64")}` } },
		],
	}],
};

try {
	const endpoint = `${opts.base.replace(/\/+$/, "")}/v1/chat/completions`;
	const response = await fetch(endpoint, {
		method: "POST",
		headers: {
			"Content-Type": "application/json",
			"Authorization": `Bearer ${apiKey}`,
		},
		body: JSON.stringify(body),
	});

	if (!response.ok) {
		const text = await response.text();
		console.error(`vision endpoint error ${response.status} from ${endpoint}: ${text.slice(0, 500)}`);
		process.exit(1);
	}

	const data = await response.json();
	const content = data.choices?.[0]?.message?.content ?? "";
	console.log(content.trim());
} catch (err) {
	console.error(`network error calling vision endpoint: ${err.message}`);
	process.exit(1);
}
