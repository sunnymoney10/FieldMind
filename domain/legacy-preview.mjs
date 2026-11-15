import { assertWorkspace } from "./validate.mjs";
export const PREVIEW_LIMITS = Object.freeze({
  maxBytes: 16 * 1024 * 1024,
  maxAccounts: 10000,
  maxCandidatesPerItem: 20,
});
const plain = (v) => v !== null && typeof v === "object" && !Array.isArray(v);
const norm = (v) =>
  typeof v === "string"
    ? v
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, " ")
        .trim()
    : "";
/** Read-only report, deliberately not a domain snapshot or append command. Takes JSON text, never a storage handle. */
export function previewLegacy(
  rawText,
  { referenceWorkspace = null, context, limits = PREVIEW_LIMITS } = {},
) {
  if (typeof rawText !== "string")
    throw new TypeError("Exact legacy JSON text required");
  if (new TextEncoder().encode(rawText).length > limits.maxBytes)
    throw new RangeError("Legacy preview byte budget exceeded");
  let source;
  try {
    source = JSON.parse(rawText);
  } catch {
    return {
      kind: "legacy_preview",
      writable: false,
      rawText,
      source: null,
      items: [],
      diagnostics: [
        {
          code: "invalid_json",
          path: "$",
          message: "Original text retained; nothing converted",
        },
      ],
    };
  }
  const report = {
    kind: "legacy_preview",
    writable: false,
    rawText,
    source,
    items: [],
    orphanNotes: [],
    diagnostics: [],
    unknownRootFields: plain(source)
      ? Object.keys(source).filter(
          (k) => !["fieldmind", "accounts", "notes", "meta"].includes(k),
        )
      : [],
  };
  if (!plain(source) || !plain(source.accounts)) {
    report.diagnostics.push({
      code: "accounts_shape",
      path: "accounts",
      message: "Expected legacy account object; original retained",
    });
    return report;
  }
  const accounts = Object.entries(source.accounts);
  if (accounts.length > limits.maxAccounts)
    throw new RangeError("Legacy account budget exceeded");
  if (referenceWorkspace) assertWorkspace(referenceWorkspace, context);
  const groups = { name: new Map(), address: new Map() },
    refs = { business: new Map(), premise: new Map() };
  function add(index, k, id) {
    if (!k) return;
    if (!index.has(k)) index.set(k, []);
    index.get(k).push(id);
  }
  for (const [id, a] of accounts)
    if (plain(a)) {
      add(groups.name, norm(a.name), id);
      add(groups.address, norm(a.addr), id);
    }
  for (const b of referenceWorkspace?.businesses || []) {
    add(refs.business, norm(b.name), b.id);
    for (const alias of b.aliases) add(refs.business, norm(alias), b.id);
  }
  for (const p of referenceWorkspace?.premises || [])
    add(refs.premise, norm(p.addressRaw), p.id);
  const notes = plain(source.notes) ? source.notes : {};
  if (source.notes !== undefined && !plain(source.notes))
    report.diagnostics.push({
      code: "notes_shape",
      path: "notes",
      message: "Non-object notes preserved in source; not interpreted",
    });
  for (const [legacyKey, a] of accounts) {
    const note = Object.hasOwn(notes, legacyKey) ? notes[legacyKey] : null,
      item = {
        legacyKey,
        raw: a,
        notesRaw: note,
        acceptedIdentity: null,
        proposedDomainRecords: [],
        relationships: [],
        diagnostics: [],
        fields: plain(a)
          ? Object.keys(a).map((field) => ({
              field,
              disposition: ["name", "addr", "city", "zip"].includes(field)
                ? "candidate_only"
                : "raw_unresolved",
            }))
          : [],
      };
    if (!plain(a)) {
      item.diagnostics.push("invalid_account_shape");
      report.items.push(item);
      continue;
    }
    const sameName = groups.name.get(norm(a.name)) || [],
      sameAddress = groups.address.get(norm(a.addr)) || [];
    const related = [...new Set([...sameName, ...sameAddress])].filter(
        (id) => id !== legacyKey,
      ),
      business = [...new Set(refs.business.get(norm(a.name)) || [])],
      premise = [...new Set(refs.premise.get(norm(a.addr)) || [])];
    item.relationships = [
      {
        type: "legacy_review_candidates",
        ids: related.slice(0, limits.maxCandidatesPerItem),
        total: related.length,
      },
      {
        type: "business_review_candidates",
        ids: business.slice(0, limits.maxCandidatesPerItem),
        total: business.length,
      },
      {
        type: "premise_review_candidates",
        ids: premise.slice(0, limits.maxCandidatesPerItem),
        total: premise.length,
      },
    ];
    item.diagnostics.push(
      "identity_acceptance_required",
      "source_history_may_already_be_incomplete",
    );
    if (a.acct) item.diagnostics.push("external_id_unclassified");
    if (related.length || business.length || premise.length)
      item.diagnostics.push("candidate_is_not_an_accepted_relationship");
    if (a.device || a.list === "mimo")
      item.diagnostics.push("historical_mimo_account_scope_unresolved");
    if (a.suppressed || a.listStatus)
      item.diagnostics.push("manager_control_provenance_and_scope_review");
    if (plain(note)) {
      if (
        Array.isArray(note.evidence) &&
        note.evidence.some((e) => e?.verified)
      )
        item.diagnostics.push("legacy_verification_unattested");
      if (note.brief || note.dm)
        item.diagnostics.push("brief_and_contact_are_not_verified_authority");
    }
    report.items.push(item);
  }
  for (const id of Object.keys(notes))
    if (!Object.hasOwn(source.accounts, id))
      report.orphanNotes.push({
        legacyKey: id,
        raw: notes[id],
        disposition: "retained_unresolved",
      });
  return report;
}
