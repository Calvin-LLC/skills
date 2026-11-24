const INTERACTIVE_ROLES = new Set([
	"button",
	"link",
	"textbox",
	"searchbox",
	"checkbox",
	"radio",
	"combobox",
	"listbox",
	"menuitem",
	"menuitemcheckbox",
	"menuitemradio",
	"option",
	"slider",
	"spinbutton",
	"switch",
	"tab",
	"treeitem",
	"scrollbar",
]);
const VAGUE_LINK = /^(click here|here|read more|more|learn more|link|this|details|continue|go|read|view|see more|more info)\.?$/i;
const FILENAME_NAME = /\.(png|jpe?g|gif|svg|webp|avif|bmp)(\?.*)?$|^(img|dsc|image|photo|screenshot)[-_ ]?\d+/i;

const prop = (node, name) => node.properties?.find((p) => p.name === name)?.value?.value;

export default {
	id: "ax-tree",
	covers: { "1.1.1": "partial", "4.1.2": "partial", "2.4.4": "partial", "1.3.1": "partial", "2.4.6": "partial", "3.3.2": "partial" },
	async run(page) {
		const nodes = await page.axTree();
		const findings = [];
		const byId = new Map(nodes.map((n) => [n.nodeId, n]));
		const live = nodes.filter((n) => !n.ignored && n.backendDOMNodeId);

		const describe = async (backendNodeId) => {
			try {
				const { object } = await page.send("DOM.resolveNode", { backendNodeId });
				const res = await page.send("Runtime.callFunctionOn", {
					objectId: object.objectId,
					functionDeclaration: `function () { return { selector: __w.cssPath(this), snippet: __w.snippet(this), visible: this.nodeType === 1 && __w.visible(this) }; }`,
					returnByValue: true,
				});
				await page.send("Runtime.releaseObject", { objectId: object.objectId });
				return res.result.value;
			} catch {
				return { selector: `backend:${backendNodeId}`, snippet: "", visible: true };
			}
		};

		const headings = [];
		const mains = [];
		const linkNames = new Map();

		for (const n of live) {
			const role = n.role?.value;
			const name = (n.name?.value ?? "").trim();
			if (role === "heading") headings.push({ n, level: Number(prop(n, "level") ?? 0), name });
			if (role === "main") mains.push(n);
			if (role === "link" && name) {
				const list = linkNames.get(name.toLowerCase()) ?? [];
				list.push(n);
				linkNames.set(name.toLowerCase(), list);
			}

			if (INTERACTIVE_ROLES.has(role) && !name && prop(n, "disabled") !== true) {
				const d = await describe(n.backendDOMNodeId);
				if (!d.visible) continue;
				const sc = role === "link" ? "2.4.4" : "4.1.2";
				findings.push({
					sc,
					kind: "fail",
					check: "ax-tree:nameless-control",
					selector: d.selector,
					snippet: d.snippet,
					message: `${role} has no accessible name in the browser's accessibility tree`,
				});
				if (role === "textbox" || role === "combobox" || role === "checkbox" || role === "radio")
					findings.push({ sc: "3.3.2", kind: "fail", check: "ax-tree:nameless-control", selector: d.selector, snippet: d.snippet, message: "form control has no label" });
			}

			if (role === "image" || role === "img") {
				if (name && FILENAME_NAME.test(name)) {
					const d = await describe(n.backendDOMNodeId);
					findings.push({
						sc: "1.1.1",
						kind: "fail",
						check: "ax-tree:filename-alt",
						selector: d.selector,
						snippet: d.snippet,
						message: `image text alternative is a file name (${name.slice(0, 40)})`,
					});
				}
			}

			if (role === "link" && name && VAGUE_LINK.test(name)) {
				const d = await describe(n.backendDOMNodeId);
				if (d.visible)
					findings.push({
						sc: "2.4.4",
						kind: "review",
						check: "ax-tree:vague-link",
						selector: d.selector,
						snippet: d.snippet,
						message: `link text "${name}" needs surrounding context to be understood`,
					});
			}

			if (role === "heading" && !name) {
				const d = await describe(n.backendDOMNodeId);
				if (d.visible)
					findings.push({ sc: "2.4.6", kind: "fail", check: "ax-tree:empty-heading", selector: d.selector, snippet: d.snippet, message: "heading has no text" });
			}
		}

		for (const [name, list] of linkNames) {
			const urls = new Set();
			for (const n of list) {
				const url = prop(n, "url");
				if (url) urls.add(url);
			}
			if (urls.size > 1 && list.length > 1) {
				const d = await describe(list[1].backendDOMNodeId);
				findings.push({
					sc: "2.4.4",
					kind: "review",
					check: "ax-tree:same-name-different-target",
					selector: d.selector,
					snippet: d.snippet,
					message: `${list.length} links named "${name.slice(0, 40)}" go to ${urls.size} different destinations`,
				});
			}
		}

		let prev = 0;
		for (const h of headings) {
			if (prev && h.level > prev + 1) {
				const d = await describe(h.n.backendDOMNodeId);
				findings.push({
					sc: "1.3.1",
					kind: "review",
					check: "ax-tree:heading-skip",
					selector: d.selector,
					snippet: d.snippet,
					message: `heading level jumps from h${prev} to h${h.level}`,
				});
			}
			prev = h.level || prev;
		}

		if (mains.length === 0 && live.length > 0)
			findings.push({ sc: "2.4.1", kind: "review", check: "ax-tree:no-main", selector: "html", snippet: "", message: "no main landmark; bypass blocks needs a skip link or landmarks" });
		if (mains.length > 1)
			findings.push({ sc: "1.3.1", kind: "review", check: "ax-tree:multiple-main", selector: "html", snippet: "", message: `${mains.length} main landmarks` });

		void byId;
		return { findings, note: `${live.length} nodes in the accessibility tree` };
	},
};
