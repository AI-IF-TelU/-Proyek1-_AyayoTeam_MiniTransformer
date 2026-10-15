import type { Plugin } from "@kilocode/plugin";
import { appendFile, mkdir, readFile, writeFile } from "node:fs/promises";
import { join } from "node:path";

/**
 * Event logger for Kilo sessions.
 * Records sanitized raw events to raw JSONL (evidence) and generates a
 * Markdown report following docs/AI_LOG_TEMPLATE.md from the same raw file.
 * Not accepted as operational until the README smoke test confirms
 * prompt and response capture in the installed Kilo version.
 */

type AnyRecord = Record<string, any>;

function sanitizeId(value: unknown, fallback: string): string {
  const raw = typeof value === "string" && value.trim() ? value : fallback;
  return raw.replace(/[^a-zA-Z0-9._-]/g, "_").slice(0, 120) || fallback;
}

function redactString(value: string): string {
  return value
    .replace(/\bBearer\s+[A-Za-z0-9._~+\/-]+=*/gi, "Bearer [REDACTED]")
    .replace(/\b(gh[pousr]_[A-Za-z0-9_]{20,})\b/g, "[REDACTED_GITHUB_TOKEN]")
    .replace(/\bgithub_pat_[A-Za-z0-9_]{20,}\b/g, "[REDACTED_GITHUB_TOKEN]")
    .replace(/\b(sk-[A-Za-z0-9_-]{16,})\b/g, "[REDACTED_API_KEY]")
    .replace(/((?:api[_ -]?key|access[_ -]?token|refresh[_ -]?token|password|passwd|client_secret)\s*[:=]\s*)([^\s,;"']+)/gi, "$1[REDACTED]");
}

function redactDeep(value: unknown, key = ""): unknown {
  if (/api.?key|access.?token|refresh.?token|password|passwd|secret|authorization|credential/i.test(key)) {
    return "[REDACTED]";
  }
  if (typeof value === "string") return redactString(value);
  if (Array.isArray(value)) return value.map((item) => redactDeep(item));
  if (value && typeof value === "object") {
    const result: AnyRecord = {};
    for (const [childKey, childValue] of Object.entries(value as AnyRecord)) {
      result[childKey] = redactDeep(childValue, childKey);
    }
    return result;
  }
  return value;
}

function getEventType(event: AnyRecord): string {
  return typeof event?.type === "string" ? event.type : "unknown";
}

function getProperties(event: AnyRecord): AnyRecord {
  if (event?.properties && typeof event.properties === "object") return event.properties;
  if (event?.payload?.properties && typeof event.payload.properties === "object") return event.payload.properties;
  return {};
}

function getSessionId(event: AnyRecord): string {
  const p = getProperties(event);
  const candidates = [
    p.sessionID, p.sessionId, p.info?.sessionID, p.info?.sessionId, p.info?.id,
    p.part?.sessionID, p.part?.sessionId, event?.sessionID, event?.sessionId,
    event?.payload?.properties?.info?.sessionID,
  ];
  const found = candidates.find((x) => typeof x === "string" && x.trim());
  return sanitizeId(found, "session-unresolved");
}

function isRelevantEvent(type: string): boolean {
  return type.startsWith("session.") || type.startsWith("message.") ||
    type.startsWith("tool.execute.") || type.startsWith("permission.") ||
    type === "file.edited" || type === "command.executed" ||
    type === "lsp.client.diagnostics";
}

interface ChronologyEntry {
  time: string;
  role: string;
  model: string;
  text: string;
  order: number;
}

function buildChronology(rawLines: string[]): ChronologyEntry[] {
  const messages = new Map<string, { role: string; time: string; model: string; order: number }>();
  const partText = new Map<string, Map<string, string>>();
  let order = 0;

  for (const line of rawLines) {
    let row: AnyRecord;
    try {
      row = JSON.parse(line);
    } catch {
      continue;
    }
    const type = String(row.event_type ?? "unknown");
    const props = (row.raw_event as AnyRecord)?.properties ?? {};
    if (type === "message.updated") {
      const info = (props as AnyRecord).info ?? {};
      if (info?.id) {
        const model =
          info.model?.providerID && info.model?.modelID
            ? `${info.model.providerID}/${info.model.modelID}`
            : info.providerID && info.modelID
              ? `${info.providerID}/${info.modelID}`
              : "";
        messages.set(String(info.id), {
          role: info.role ?? "unknown",
          time: row.timestamp ?? "",
          model,
          order: order++,
        });
      }
    } else if (type === "message.part.updated") {
      const part = (props as AnyRecord)?.part;
      if (part?.messageID && typeof part.text === "string") {
        const byPart = partText.get(String(part.messageID)) ?? new Map<string, string>();
        byPart.set(String(part.id), String(part.text));
        partText.set(String(part.messageID), byPart);
      }
    }
  }

  const seen = new Set<string>();
  const entries: ChronologyEntry[] = [];
  for (const line of rawLines) {
    let row: AnyRecord;
    try {
      row = JSON.parse(line);
    } catch {
      continue;
    }
    const type = String(row.event_type ?? "unknown");
    if (type === "message.part.updated") {
      const part = (row.raw_event as AnyRecord)?.properties?.part;
      if (part?.messageID && !seen.has(String(part.messageID))) {
        seen.add(String(part.messageID));
        const msg = messages.get(String(part.messageID));
        const parts = partText.get(String(part.messageID)) ?? new Map();
        const text = [...parts.values()].join("\n");
        entries.push({
          time: msg?.time ?? row.timestamp ?? "",
          role: msg?.role ?? "unknown",
          model: msg?.model ?? "",
          text,
          order: msg?.order ?? order++,
        });
      }
    }
  }
  return entries.sort((a, b) => (a.order - b.order) || a.time.localeCompare(b.time));
}

function roleLabel(role: string): string {
  if (role === "user") return "Prompt";
  if (role === "assistant") return "Respons";
  return role;
}

function buildReport(input: {
  memberId: string;
  sessionId: string;
  rawPath: string;
  rawLines: string[];
  models: string[];
}): string {
  const { memberId, sessionId, rawPath, rawLines, models } = input;

  const eventCounts = new Map<string, number>();
  for (const line of rawLines) {
    try {
      const parsed = JSON.parse(line) as AnyRecord;
      const eventType = String(parsed.event_type ?? "unknown");
      eventCounts.set(eventType, (eventCounts.get(eventType) ?? 0) + 1);
    } catch {
      // Keep processing remaining records.
    }
  }
  const countsMarkdown = [...eventCounts.entries()].sort(([a], [b]) => a.localeCompare(b))
    .map(([name, count]) => `| \`${name}\` | ${count} |`).join("\n") || "| Belum ada event | 0 |";

  const chronology = buildChronology(rawLines);
  const chronologyMarkdown = chronology.length
    ? chronology.map((c, i) =>
        `| ${i + 1} | ${c.time} | ${roleLabel(c.role)} | ${c.text.replace(/\|/g, "\\|").replace(/\n/g, "<br>")} |`).join("\n")
    : "| - | - | - | Belum ada prompt/respons terekam. |";

  const modelLine = [...new Set(models.filter(Boolean))].join(", ") || "[Isi manual: model tidak tersedia di event]";
  const manual = "[Isi manual]";

  return `# AI Interaction Log

> Laporan ini dihasilkan dari log otomatis dan diverifikasi terhadap raw JSONL. Jangan mengarang prompt, respons, hasil test, atau keputusan.

## Metadata

- Log ID: \`AI-LOG-${memberId}-${sessionId}\`
- Tanggal/waktu: ${new Date().toISOString()}
- Anggota: ${memberId}
- Agent/tool: Kilo
- Model (jika tersedia): ${modelLine}
- Session ID: ${sessionId}
- GitHub Issue/PR: ${manual}
- Target modul: ${manual}
- Raw log path: [${rawPath}](../raw/${memberId}/${sessionId}.jsonl)
- Share link (jika tersedia): ${manual}

## Kronologi prompt dan respons

| # | Waktu | Peran | Isi |
|---|---|---|---|
${chronologyMarkdown}

## Debugging

- Pesan error aktual: ${manual}
- Prompt debugging aktual: ${manual}
- Perubahan yang dilakukan: ${manual}
- Hasil setelah perbaikan: ${manual}

## Verifikasi

- Perintah test yang dijalankan: smoke test README (lihat \`README.md\`, bagian "Logging smoke-test prompt")
- Output aktual: ${rawLines.length} baris raw tercatat:
${countsMarkdown}
- Commit SHA: ${manual}
- Acceptance criteria yang terpenuhi: ${manual}
- Acceptance criteria yang belum terpenuhi: ${manual}

## Refleksi yang diverifikasi anggota

- Mengapa pendekatan dipilih: ${manual}
- Pelajaran teknis: ${manual}
- Keterbatasan dan langkah selanjutnya: ${manual}
`;
}

const MiniTransformerLogger: Plugin = async ({ directory }) => {
  const root = directory;
  let memberId = sanitizeId(process.env.MINITRANSFORMER_MEMBER_ID, "member-unset");
  try {
    const localConfigPath = join(root, ".kilo", "member.local.json");
    const localConfig = JSON.parse(await readFile(localConfigPath, "utf8")) as AnyRecord;
    memberId = sanitizeId(localConfig.member_id, memberId);
  } catch {
    // Environment variable or the explicit member-unset fallback is used.
  }

  async function writeEvent(event: AnyRecord): Promise<void> {
    const type = getEventType(event);
    if (!isRelevantEvent(type)) return;

    const sessionId = getSessionId(event);
    const rawDirectory = join(root, "docs", "ai-logs", "raw", memberId);
    await mkdir(rawDirectory, { recursive: true });

    const row = {
      timestamp: new Date().toISOString(),
      member_id: memberId,
      agent: "kilo-code",
      session_id: sessionId,
      event_type: type,
      source: "kilo-plugin-event",
      raw_event: redactDeep(event),
    };
    await appendFile(join(rawDirectory, `${sessionId}.jsonl`), `${JSON.stringify(row)}\n`, "utf8");

    if (type === "session.idle") {
      const reportsDir = join(root, "docs", "ai-logs", "reports");
      await mkdir(reportsDir, { recursive: true });
      const reportPath = join(reportsDir, `AI-LOG-${memberId}-${sessionId}.md`);
      const rawPath = `docs/ai-logs/raw/${memberId}/${sessionId}.jsonl`;
      let rawLines: string[] = [];
      try {
        rawLines = (await readFile(join(rawDirectory, `${sessionId}.jsonl`), "utf8")).trim().split(/\r?\n/).filter(Boolean);
      } catch {
        // Report still gets written with the evidence path.
      }
      const models: string[] = [];
      for (const line of rawLines) {
        try {
          const parsed = JSON.parse(line) as AnyRecord;
          if (parsed.event_type === "message.updated") {
            const info = (parsed.raw_event as AnyRecord)?.properties?.info;
            if (info?.model?.providerID && info?.model?.modelID) models.push(`${info.model.providerID}/${info.model.modelID}`);
            else if (info?.providerID && info?.modelID) models.push(`${info.providerID}/${info.modelID}`);
          }
        } catch {
          // Ignore malformed rows.
        }
      }
      const report = buildReport({ memberId, sessionId, rawPath, rawLines, models });
      await writeFile(reportPath, report, "utf8");
    }
  }

  return {
    event: async ({ event }: { event: AnyRecord }) => {
      try {
        await writeEvent(event);
      } catch (error) {
        // Fail visibly in Kilo's plugin logs; do not silently claim the log succeeded.
        console.error("[mini-transformer-ai-logger] Failed to write event:", error);
      }
    },
  };
};

export default { id: "mini-transformer-ai-logger", server: MiniTransformerLogger };