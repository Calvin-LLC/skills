import { readFileSync } from "node:fs";
import { axeTagToCriterion } from "../lib/criteria.mjs";

const AXE_SOURCE = readFileSync(new URL("../vendor/axe.min.js", import.meta.url), "utf8");
const TAGS = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"];
const OWNED_ELSEWHERE = new Set(["color-contrast", "color-contrast-enhanced", "target-size"]);

export default {
	id: "axe",
	async run(page) {
		await page.eval(AXE_SOURCE);
		const out = await page.eval(
			async (cfg) => {
				const tagged = axe.getRules(cfg.tags).map((r) => ({ id: r.ruleId, tags: r.tags }));
				const res = await axe.run(document, {
					runOnly: { type: "tag", values: cfg.tags },
					rules: { "label-content-name-mismatch": { enabled: true } },
					resultTypes: ["violations", "incomplete"],
					elementRef: false,
				});
				const slim = (list) =>
					list.map((r) => ({
						id: r.id,
						impact: r.impact,
						help: r.help,
						helpUrl: r.helpUrl,
						tags: r.tags,
						nodes: r.nodes.slice(0, 25).map((n) => ({
							target: n.target.map((t) => (Array.isArray(t) ? t.join(" ") : t)).join(" "),
							html: n.html.slice(0, 200),
							summary: (n.failureSummary || "").replace(/\\s+/g, " ").slice(0, 240),
						})),
						total: r.nodes.length,
					}));
				return { version: axe.version, tagged, violations: slim(res.violations), incomplete: slim(res.incomplete) };
			},
			{ tags: TAGS },
		);

		const findings = [];
		const covers = {};
		for (const r of out.tagged) {
			if (OWNED_ELSEWHERE.has(r.id)) continue;
			for (const tag of r.tags) {
				const sc = axeTagToCriterion(tag);
				if (sc) covers[sc] = "partial";
			}
		}
		const emit = (list, kind) => {
			for (const rule of list) {
				if (OWNED_ELSEWHERE.has(rule.id)) continue;
				const scs = rule.tags.map(axeTagToCriterion).filter(Boolean);
				const primary = scs.length ? scs : [null];
				for (const node of rule.nodes) {
					for (const sc of primary) {
						findings.push({
							sc,
							kind,
							check: `axe:${rule.id}`,
							selector: node.target,
							snippet: node.html,
							message: rule.help,
							detail: node.summary,
							impact: rule.impact,
							doc: rule.helpUrl,
						});
					}
				}
			}
		};
		emit(out.violations, "fail");
		emit(out.incomplete, "review");
		return { findings, covers, note: `axe-core ${out.version}` };
	},
};
