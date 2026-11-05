import { readFileSync } from "node:fs";

const criteriaUrl = new URL("../../data/criteria.json", import.meta.url);
export const CRITERIA = JSON.parse(readFileSync(criteriaUrl, "utf8"));
const byNum = new Map(CRITERIA.map((c) => [c.num, c]));

export function criterion(num) {
	return byNum.get(num);
}

export function axeTagToCriterion(tag) {
	const m = /^wcag(\d)(\d)(\d+)$/.exec(tag);
	return m ? `${m[1]}.${m[2]}.${m[3]}` : null;
}

export const STATUS = {
	fail: "fail",
	review: "review",
	clear: "no-failures-found",
	partial: "partial-no-failures",
	manual: "manual",
};

export function summarize(findings, modules) {
	const coverage = new Map();
	const rank = { measured: 2, partial: 1 };
	for (const mod of modules) {
		for (const [num, level] of Object.entries(mod.covers ?? {})) {
			const prev = coverage.get(num);
			if (!prev) coverage.set(num, { level, by: [mod.id] });
			else {
				if (rank[level] > rank[prev.level]) prev.level = level;
				prev.by.push(mod.id);
			}
		}
	}
	const rows = CRITERIA.map((c) => {
		const mine = findings.filter((f) => f.sc === c.num);
		const fails = mine.filter((f) => f.kind === "fail").length;
		const reviews = mine.filter((f) => f.kind === "review").length;
		const cov = coverage.get(c.num);
		let status = STATUS.manual;
		if (fails) status = STATUS.fail;
		else if (reviews) status = STATUS.review;
		else if (cov?.level === "measured") status = STATUS.clear;
		else if (cov) status = STATUS.partial;
		return { sc: c.num, level: c.level, title: c.title, status, automation: cov?.level ?? "none", checks: cov?.by ?? [], fails, reviews };
	});
	const count = (s) => rows.filter((r) => r.status === s).length;
	return { rows, totals: { fail: count(STATUS.fail), review: count(STATUS.review), clear: count(STATUS.clear), partial: count(STATUS.partial), manual: count(STATUS.manual) } };
}
