// Proposed interactive/batch limits, enforced before recursive B1 validation.
export const DOMAIN_LIMITS = Object.freeze({
  maxBytes: 64 * 1024 * 1024,
  maxRecords: 100000,
  maxClaims: 40000,
  maxEdges: 200000,
  maxDepth: 64,
});
export function graphBudget(workspace, limits = DOMAIN_LIMITS) {
  if (!workspace || typeof workspace !== "object")
    throw new TypeError("Expected domain workspace");
  let bytes;
  try {
    bytes = new TextEncoder().encode(JSON.stringify(workspace)).length;
  } catch {
    throw new TypeError("Snapshot must be JSON serializable");
  }
  if (bytes > limits.maxBytes)
    throw new RangeError("Snapshot byte budget exceeded");
  const records = Object.values(workspace)
      .filter(Array.isArray)
      .reduce((n, a) => n + a.length, 0),
    claims = workspace.claims;
  if (
    !Array.isArray(claims) ||
    records > limits.maxRecords ||
    claims.length > limits.maxClaims
  )
    throw new RangeError("Snapshot record/claim budget exceeded");
  const byId = new Map(claims.map((c) => [c?.id, c])),
    children = new Map(),
    incoming = new Map(),
    depth = new Map();
  let edges = 0;
  for (const c of claims) {
    if (!c || !Array.isArray(c.derivedFrom) || !Array.isArray(c.conflictsWith))
      throw new TypeError("Malformed claim graph");
    incoming.set(c.id, c.derivedFrom.filter((id) => byId.has(id)).length);
    depth.set(c.id, 1);
    edges += c.derivedFrom.length + c.conflictsWith.length;
    for (const id of c.derivedFrom) {
      if (!children.has(id)) children.set(id, []);
      children.get(id).push(c.id);
    }
  }
  if (edges > limits.maxEdges)
    throw new RangeError("Claim edge budget exceeded");
  const queue = claims.filter((c) => incoming.get(c.id) === 0).map((c) => c.id),
    order = [];
  for (let i = 0; i < queue.length; i++) {
    const id = queue[i];
    order.push(id);
    if (depth.get(id) > limits.maxDepth)
      throw new RangeError("Claim dependency depth budget exceeded");
    for (const child of children.get(id) || []) {
      depth.set(child, Math.max(depth.get(child), depth.get(id) + 1));
      incoming.set(child, incoming.get(child) - 1);
      if (incoming.get(child) === 0) queue.push(child);
    }
  }
  if (order.length !== claims.length)
    throw new RangeError("Claim graph cycle or duplicate IDs");
  return {
    bytes,
    records,
    claims: claims.length,
    edges,
    depth: Math.max(0, ...depth.values()),
    order,
  };
}
