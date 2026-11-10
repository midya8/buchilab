export function parseJSON(raw) {
  if (new TextEncoder().encode(raw).length > 65536)
    throw Error("input exceeds65536 bytes");
  let p = 0;
  const ws = () => {
    while (/[ \t\r\n]/.test(raw[p] ?? "") && p < raw.length) p++;
  };
  function string() {
    const start = p++;
    while (p < raw.length) {
      if (raw[p] === "\\") {
        p += 2;
        continue;
      }
      if (raw[p++] === '"') return JSON.parse(raw.slice(start, p));
    }
    throw Error("unterminated string");
  }
  function value() {
    ws();
    const c = raw[p];
    if (c === '"') return string();
    if (c === "{") {
      p++;
      const keys = new Set(),
        out = Object.create(null);
      ws();
      if (raw[p] === "}") {
        p++;
        return out;
      }
      while (true) {
        ws();
        if (raw[p] !== '"') throw Error("object key must be string");
        const k = string();
        if (keys.has(k)) throw Error("duplicate JSON key");
        keys.add(k);
        ws();
        if (raw[p++] !== ":") throw Error("missing colon");
        out[k] = value();
        ws();
        const sep = raw[p++];
        if (sep === "}") return out;
        if (sep !== ",") throw Error("missing comma");
      }
    }
    if (c === "[") {
      p++;
      const out = [];
      ws();
      if (raw[p] === "]") {
        p++;
        return out;
      }
      while (true) {
        out.push(value());
        ws();
        const sep = raw[p++];
        if (sep === "]") return out;
        if (sep !== ",") throw Error("missing comma");
      }
    }
    for (const [token, v] of [
      ["true", true],
      ["false", false],
      ["null", null],
    ])
      if (raw.startsWith(token, p)) {
        p += token.length;
        return v;
      }
    const number = raw
      .slice(p)
      .match(/^-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?/);
    if (!number) throw Error("invalid JSON value");
    p += number[0].length;
    if (/[.eE]/.test(number[0])) throw Error("integer JSON number required");
    const n = Number(number[0]);
    if (!Number.isFinite(n)) throw Error("nonfinite JSON number");
    return n;
  }
  const result = value();
  ws();
  if (p !== raw.length) throw Error("trailing JSON content");
  return result;
}
