import type { Plugin } from "@kilocode/plugin";
import { appendFile, mkdir, readFile, writeFile } from "node:fs/promises";
import { join } from "node:path";

/**
 * First-pass logger for Kilo Code.
 * It records sanitized raw events. Treat it as unverified until the smoke test
 * proves that the installed Kilo version exposes prompt and visible response content.
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
      const report = `# AI Interaction Log\n\n` +
        `- Member: ${memberId}\n- Agent: Kilo Code\n- Session ID: ${sessionId}\n` +
        `- Updated at: ${new Date().toISOString()}\n- Raw evidence: [${rawPath}](../raw/${memberId}/${sessionId}.jsonl)\n\n` +
        `## Recorded event counts\n\n| Event | Count |\n|---|---:|\n${countsMarkdown}\n\n` +
        `## Verification status\n\n` +
        `- [ ] Confirm the unique test prompt is present in raw JSONL.\n` +
        `- [ ] Confirm the visible assistant response is present in raw JSONL.\n` +
        `- [ ] Check that no secrets or sensitive data are present.\n` +
        `- [ ] Link related GitHub Issue/PR and verify test outcomes.\n\n` +
        `> This report is generated from Kilo events. Event counts alone do not prove full prompt/response capture; complete the smoke test before relying on this logger for graded evidence.\n`;
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
