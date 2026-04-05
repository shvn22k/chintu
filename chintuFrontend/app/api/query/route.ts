import { NextRequest, NextResponse } from "next/server";
import {
  mapChintuCompleteToBackendResponse,
  type ChintuChatCompleteResponse,
} from "@/lib/chintuAdapter";

function backendBaseUrl(): string {
  const raw = process.env.CHINTU_BACKEND_URL || "http://127.0.0.1:5000";
  return raw.replace(/\/$/, "");
}

const CHAT_COMPLETE_PATH = "/api/v1/chat/complete";

export async function POST(request: NextRequest) {
  let body: { message?: string; question?: string };
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: "invalid_json" }, { status: 400 });
  }

  const question = (body.question ?? body.message ?? "").trim();
  if (!question) {
    return NextResponse.json({ error: "missing_question", detail: "Send `question` or `message`." }, { status: 400 });
  }

  const url = `${backendBaseUrl()}${CHAT_COMPLETE_PATH}`;
  const timeoutMs = Math.min(
    Math.max(Number(process.env.CHINTU_BACKEND_TIMEOUT_MS) || 180000, 30000),
    300000
  );

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify({ question }),
      signal: controller.signal,
      cache: "no-store",
    });
    clearTimeout(timer);

    const ct = res.headers.get("content-type") || "";
    const payloadText = await res.text();

    if (!ct.includes("application/json")) {
      return NextResponse.json(
        {
          error: "backend_non_json",
          detail: payloadText.slice(0, 400) || `HTTP ${res.status} from ${url}`,
        },
        { status: 502 }
      );
    }

    let raw: ChintuChatCompleteResponse;
    try {
      raw = JSON.parse(payloadText) as ChintuChatCompleteResponse;
    } catch {
      return NextResponse.json(
        { error: "backend_invalid_json", detail: payloadText.slice(0, 300) },
        { status: 502 }
      );
    }

    if (!res.ok) {
      return NextResponse.json(
        {
          error: "backend_http_error",
          detail: raw.answer || payloadText.slice(0, 500),
          status: res.status,
        },
        { status: 502 }
      );
    }

    const mapped = mapChintuCompleteToBackendResponse(raw);
    return NextResponse.json(mapped);
  } catch (e) {
    clearTimeout(timer);
    const msg = e instanceof Error ? e.message : String(e);
    const aborted = e instanceof Error && e.name === "AbortError";
    return NextResponse.json(
      {
        error: aborted ? "backend_timeout" : "backend_unreachable",
        detail: aborted
          ? `No response within ${timeoutMs}ms. Is the Flask API running at ${backendBaseUrl()}?`
          : msg,
      },
      { status: 502 }
    );
  }
}
