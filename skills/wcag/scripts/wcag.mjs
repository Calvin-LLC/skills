#!/usr/bin/env node
import { mkdirSync, writeFileSync, existsSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { pathToFileURL } from "node:url";
import { openBrowser } from "./lib/browser.mjs";
import { summarize } from "./lib/criteria.mjs";
import axe from "./checks/axe.mjs";
import axTree from "./checks/ax-tree.mjs";
import contrast from "./checks/contrast.mjs";
import forms from "./checks/forms.mjs";
import dom from "./checks/dom.mjs";
import inputModel from "./checks/input-model.mjs";
import keyboard from "./checks/keyboard.mjs";
import reflow from "./checks/reflow.mjs";
import targets from "./checks/targets.mjs";

const MODULES = [dom, axTree, axe, contrast, targets, inputModel, keyboard, reflow, forms];
const USAGE = "usage: wcag.mjs <url|file.html>\nexit codes: 0 no failures, 2 failures found, 1 the run itself failed";

const PASSES = [
	{ name: "desktop", viewport: [1280, 800], media: [] },
	{ name: "phone", viewport: [390, 844], media: [] },
	{ name: "dark", viewport: [1280, 800], media: [{ name: "prefers-color-scheme", value: "dark" }] },
	{ name: "reduced-motion", viewport: [1280, 800], media: [{ name: "prefers-reduced-motion", value: "reduce" }] },
	{ name: "forced-colors", viewport: [1280, 800], media: [{ name: "forced-colors", value: "active" }] },
];
const REPORT_PATH = ".tmp/wcag/report.json";

function toUrl(target) {
	if (/^(https?|file|data):/i.test(target)) return target;
	const abs = resolve(target);
	if (!existsSync(abs)) throw new Error(`no such file: ${target}`);
	return pathToFileURL(abs).href;
}

const TOPICS = {
	"html-lang": ["dom:html-lang", "axe:html-has-lang", "axe:html-lang-valid", "axe:html-xml-lang-mismatch"],
	"viewport-zoom": ["dom:viewport-zoom-lock", "axe:meta-viewport", "axe:meta-viewport-large"],
	"accessible-name": ["ax-tree:nameless-control", "axe:button-name", "axe:link-name", "axe:input-button-name", "axe:input-image-alt", "axe:label", "axe:select-name", "axe:aria-command-name", "axe:aria-input-field-name", "axe:aria-toggle-field-name", "axe:aria-dialog-name", "axe:aria-meter-name", "axe:aria-progressbar-name", "axe:aria-tooltip-name", "axe:aria-treeitem-name", "axe:summary-name"],
	"image-alt": ["ax-tree:filename-alt", "axe:image-alt", "axe:role-img-alt", "axe:svg-img-alt", "axe:object-alt", "axe:area-alt"],
	"label-in-name": ["input:label-in-name", "axe:label-content-name-mismatch"],
	"page-title": ["dom:title", "axe:document-title"],
	"autoplay": ["dom:autoplay-audio", "dom:autoplay-no-controls", "axe:no-autoplay-audio"],
	"captions": ["dom:video-captions", "axe:video-caption"],
	"bypass": ["dom:bypass-blocks", "ax-tree:no-main", "axe:bypass", "axe:region", "axe:landmark-one-main"],
	"heading-order": ["ax-tree:heading-skip", "axe:heading-order", "axe:empty-heading", "ax-tree:empty-heading"],
	"autocomplete": ["dom:autocomplete-missing", "dom:autocomplete-invalid", "axe:autocomplete-valid"],
	"meta-refresh": ["dom:meta-refresh", "axe:meta-refresh", "axe:meta-refresh-no-exceptions"],
	"vague-link": ["ax-tree:vague-link", "axe:identical-links-same-purpose"],
};
const topicOf = new Map(Object.entries(TOPICS).flatMap(([topic, ids]) => ids.map((id) => [id, topic])));
const PREFER = ["axe", "ax-tree", "dom", "input"];

function dedupe(findings) {
	const groups = new Map();
	for (const f of findings) {
		const topic = topicOf.get(f.check) ?? f.check;
		const key = [f.sc, f.kind, topic, f.selector, topicOf.has(f.check) ? "" : f.message].join("\u0000");
		const group = groups.get(key) ?? [];
		group.push(f);
		groups.set(key, group);
	}
	const out = [];
	for (const group of groups.values()) {
		group.sort((a, b) => PREFER.indexOf(a.check.split(":")[0]) - PREFER.indexOf(b.check.split(":")[0]));
		const [head, ...rest] = group;
		const also = [...new Set(rest.map((r) => r.check).filter((c) => c !== head.check))];
		out.push(also.length ? { ...head, alsoFlaggedBy: also } : head);
	}
	return out;
}

function human(report) {
	const out = (line = "") => process.stdout.write(line + "\n");
	out(`wcag ${report.url}`);
	out(`browser ${report.browser}, passes ${report.passes.map((p) => p.name).join(", ")}`);
	out();
	for (const pass of report.passes) {
		out(`pass ${pass.name} (${pass.viewport.join("x")}${pass.media.length ? ", " + pass.media.map((m) => `${m.name}=${m.value}`).join(" ") : ""})`);
		for (const m of pass.checks) out(`  ${m.error ? "ERROR" : "ok   "}  ${m.id.padEnd(12)} ${m.error ?? m.note ?? ""}`);
	}
	out();
	const t = report.criteria.totals;
	out(`${t.fail} criteria with failures, ${t.review} to review by a person, ${t.clear} measured with no failures, ${t.partial} partly automated with no failures, ${t.manual} not testable by a script`);
	const order = { fail: 0, review: 1 };
	const list = [...report.findings].sort((a, b) => order[a.kind] - order[b.kind] || a.sc?.localeCompare(b.sc ?? "") || 0);
	const shown = list.slice(0, 40);
	for (const f of shown) {
		out();
		out(`${f.kind === "fail" ? "FAIL  " : "REVIEW"} ${f.sc ?? "-"}  ${f.check}  [${f.passes.join(", ")}]`);
		out(`   ${f.message}`);
		out(`   ${f.selector}`);
		if (f.snippet) out(`   ${f.snippet}`);
	}
	if (list.length > shown.length) out(`\n... ${list.length - shown.length} more in the JSON report`);
	out(`\nfull report: ${REPORT_PATH}`);
}

async function main() {
	const target = process.argv[2];
	if (!target || process.argv.length > 3) throw new Error(USAGE);
	const url = toUrl(target);

	const browser = await openBrowser();
	const page = await browser.newPage();
	try {
		const passes = [];
		const merged = new Map();
		const covers = new Map();
		let networkIdle = null;
		for (const [passIndex, pass] of PASSES.entries()) {
			await page.setViewport(pass.viewport[0], pass.viewport[1]);
			await page.emulateMedia(pass.media);
			const nav = await page.goto(url);
			if (passIndex === 0) networkIdle = nav.networkIdle;
			await page.settle();
			const ctx = { viewport: { width: pass.viewport[0], height: pass.viewport[1] }, url, first: passIndex === 0, media: pass.media };
			const active = MODULES.filter((m) => passIndex === 0 || !m.once);
			const checks = [];
			const found = [];
			for (const [index, mod] of active.entries()) {
				process.stderr.write(`[pass ${pass.name}] starting ${mod.id} (${index + 1}/${active.length})\n`);
				const tMod = Date.now();
				if (index > 0) {
					await page.send("Emulation.setDeviceMetricsOverride", { width: pass.viewport[0], height: pass.viewport[1], deviceScaleFactor: 1, mobile: false });
					await page.goto(url);
					await page.settle();
				}
				try {
					const res = await mod.run(page, ctx);
					for (const f of res.findings) found.push(f);
					checks.push({ id: mod.id, note: res.note, findings: res.findings.length });
					if (!covers.has(mod.id)) covers.set(mod.id, { ...(mod.covers ?? {}), ...(res.covers ?? {}) });
				} catch (e) {
					checks.push({ id: mod.id, error: e.message });
				}
				process.stderr.write(`[pass ${pass.name}] finished ${mod.id} in ${Date.now() - tMod}ms\n`);
			}
			passes.push({ name: pass.name, viewport: pass.viewport, media: pass.media, checks });
			for (const f of dedupe(found)) {
				const key = [f.sc, f.kind, f.check, f.selector, f.message].join("\u0000");
				const seen = merged.get(key);
				if (seen) seen.passes.push(pass.name);
				else merged.set(key, { ...f, passes: [pass.name] });
			}
		}
		const findings = [...merged.values()];
		const ran = [...covers].map(([id, c]) => ({ id, covers: c }));
		const criteria = summarize(findings, ran);
		const report = {
			url,
			browser: browser.product,
			networkIdle,
			startedAt: new Date().toISOString(),
			passes,
			criteria,
			findings,
			pageErrors: page.consoleErrors.slice(0, 10),
			limits: "A script cannot judge meaning. Rows marked manual need a person; rows marked review are candidates. Screen reader output, captions accuracy, alt-text quality, and cognitive load are never settled here.",
		};
		mkdirSync(dirname(resolve(REPORT_PATH)), { recursive: true });
		writeFileSync(REPORT_PATH, JSON.stringify(report, null, "	") + "\n");
		human(report);
		const broken = passes.some((p) => p.checks.some((c) => c.error));
		process.exitCode = broken ? 1 : criteria.totals.fail > 0 ? 2 : 0;
	} finally {
		await page.close();
		await browser.close();
	}
}

main().catch((e) => {
	process.stderr.write(`${e.message}\n`);
	process.exit(1);
});
