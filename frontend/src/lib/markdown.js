// Faithful port of the original admin-UI markdown / test-case renderer.
// Produces HTML strings consumed via dangerouslySetInnerHTML.

export function esc(v) {
  return String(v).replace(
    /[&<>"']/g,
    (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;" }[c]),
  );
}

function inlineFormat(text) {
  return esc(text)
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
    .replace(/\*([^*]+)\*/g, "<em>$1</em>");
}

function trimBlankLines(lines) {
  const copy = [...(lines || [])];
  while (copy.length && !copy[0].trim()) copy.shift();
  while (copy.length && !copy[copy.length - 1].trim()) copy.pop();
  return copy;
}

function firstFieldLine(lines) {
  return (trimBlankLines(lines || [])[0] || "").trim();
}

function renderLines(lines) {
  const html = [];
  let list = null;

  const closeList = () => {
    if (!list) return;
    html.push(`</${list}>`);
    list = null;
  };
  const openList = (tag) => {
    if (list === tag) return;
    closeList();
    list = tag;
    html.push(`<${tag}>`);
  };

  trimBlankLines(lines).forEach((raw) => {
    const line = raw.trim();
    if (!line) {
      closeList();
      return;
    }
    const bullet = line.match(/^[-*]\s+(.+)$/);
    if (bullet) {
      openList("ul");
      html.push(`<li>${inlineFormat(bullet[1])}</li>`);
      return;
    }
    const numbered = line.match(/^\d+[.)]\s+(.+)$/);
    if (numbered) {
      openList("ol");
      html.push(`<li>${inlineFormat(numbered[1])}</li>`);
      return;
    }
    closeList();
    if (/^---+$/.test(line)) html.push("<hr>");
    else html.push(`<p>${inlineFormat(line)}</p>`);
  });
  closeList();
  return html.join("");
}

function renderBasicMarkdown(text, fallbackTitle = "") {
  const lines = String(text || "").split("\n");
  const html = [];
  let bodyLines = lines;
  const first = (lines[0] || "").trim();

  if (/^#{1,6}\s+/.test(first)) {
    html.push(`<h3>${inlineFormat(first.replace(/^#{1,6}\s+/, ""))}</h3>`);
    bodyLines = lines.slice(1);
  } else if (fallbackTitle) {
    html.push(`<h3>${esc(fallbackTitle)}</h3>`);
  }

  html.push(renderLines(bodyLines));
  return html.join("");
}

const TC_FIELD_LABELS = [
  "Type",
  "Priority",
  "API / Layer",
  "Source references",
  "DB fixtures",
  "Auth fixtures",
  "Preconditions",
  "Test data",
  "Steps",
  "Expected result",
  "Assertions",
  "Automation notes",
  "Ticket reference",
];

function getFieldLine(line) {
  const stripped = line.trim().replace(/^[-*]\s*/, "");
  for (const label of TC_FIELD_LABELS) {
    if (stripped.toLowerCase().startsWith(`${label.toLowerCase()}:`)) {
      return { label, value: stripped.slice(label.length + 1).trim() };
    }
  }
  return null;
}

function parseTestCaseFields(lines) {
  const fields = {};
  const intro = [];
  let current = null;

  lines.forEach((line) => {
    const field = getFieldLine(line);
    if (field) {
      current = field.label;
      fields[current] = fields[current] || [];
      if (field.value) fields[current].push(field.value);
      return;
    }
    if (current) fields[current].push(line);
    else intro.push(line);
  });

  return { fields, intro: trimBlankLines(intro) };
}

function renderCaseSection(label, lines, full = false) {
  const cleaned = trimBlankLines(lines);
  if (!cleaned.length) return "";
  return `
    <section class="tc-case-section ${full ? "full" : ""}">
      <span class="tc-section-title">${esc(label)}</span>
      <div class="tc-section-body">${renderLines(cleaned)}</div>
    </section>
  `;
}

function renderTestCaseCard(block) {
  const lines = block.split("\n");
  const title = (lines.shift() || "").replace(/^#{1,6}\s*/, "").trim();
  const parsed = parseTestCaseFields(lines);
  const type = firstFieldLine(parsed.fields["Type"]);
  const priority = firstFieldLine(parsed.fields["Priority"]);

  const sections = [
    "API / Layer",
    "Source references",
    "DB fixtures",
    "Auth fixtures",
    "Preconditions",
    "Test data",
    "Steps",
    "Expected result",
    "Assertions",
    "Automation notes",
    "Ticket reference",
  ];

  const body = [];
  if (parsed.intro.length) {
    body.push(renderCaseSection("Notes", parsed.intro, true));
  }
  sections.forEach((label) => {
    const sectionLines = parsed.fields[label];
    if (!sectionLines || !sectionLines.length) return;
    const full = ["Source references", "DB fixtures", "Auth fixtures", "Steps", "Assertions"].includes(label);
    body.push(renderCaseSection(label, sectionLines, full));
  });

  return `
    <article class="tc-case">
      <div class="tc-case-head">
        <h3 class="tc-case-title">${inlineFormat(title)}</h3>
        <div class="tc-chip-row">
          ${type ? `<span class="tc-chip">${inlineFormat(type)}</span>` : ""}
          ${priority ? `<span class="tc-chip ${priority.toLowerCase()}">${inlineFormat(priority)}</span>` : ""}
        </div>
      </div>
      <div class="tc-case-grid">${body.join("")}</div>
    </article>
  `;
}

function renderStructuredTestCases(md) {
  const firstTc = md.search(/^(?:#{1,6}\s*)?TC-\d+[:-]/im);
  const overview = firstTc > 0 ? md.slice(0, firstTc).trim() : "";
  const rest = firstTc >= 0 ? md.slice(firstTc).trim() : md;
  const gapIndex = rest.search(/^(?:#{1,6}\s*)?(Gaps|Open Questions)\b/im);
  const casesText = gapIndex >= 0 ? rest.slice(0, gapIndex).trim() : rest;
  const gapText = gapIndex >= 0 ? rest.slice(gapIndex).trim() : "";
  const blocks = casesText
    .split(/(?=^(?:#{1,6}\s*)?TC-\d+[:-])/gim)
    .map((s) => s.trim())
    .filter(Boolean);

  const html = [];
  if (overview) html.push(`<section class="tc-overview">${renderBasicMarkdown(overview, "Summary")}</section>`);
  blocks.forEach((block) => html.push(renderTestCaseCard(block)));
  if (gapText) html.push(`<section class="tc-gap">${renderBasicMarkdown(gapText)}</section>`);
  return `<div class="tc-doc">${html.join("")}</div>`;
}

export function renderMarkdown(md) {
  const normalized = String(md || "")
    .replace(/\r\n/g, "\n")
    .replace(/\r/g, "\n")
    .trim();
  if (/^(?:#{1,6}\s*)?TC-\d+[:-]/im.test(normalized)) {
    return renderStructuredTestCases(normalized);
  }
  return `<div class="tc-doc">${renderBasicMarkdown(normalized)}</div>`;
}
