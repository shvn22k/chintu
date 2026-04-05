import { NextRequest, NextResponse } from "next/server";

function newsletterBaseUrl(): string | null {
  const raw = process.env.NEWSLETTER_SERVICE_URL?.trim();
  if (!raw) return null;
  return raw.replace(/\/$/, "");
}

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export async function POST(request: NextRequest) {
  const base = newsletterBaseUrl();
  if (!base) {
    return NextResponse.json(
      { ok: false, error: "newsletter_not_configured", detail: "Set NEWSLETTER_SERVICE_URL in .env (e.g. http://127.0.0.1:3001)." },
      { status: 503 }
    );
  }

  let body: { name?: string; email?: string };
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ ok: false, error: "invalid_json" }, { status: 400 });
  }

  const name = (body.name ?? "").trim();
  const email = (body.email ?? "").trim();
  if (!name || !email) {
    return NextResponse.json({ ok: false, error: "missing_fields", detail: "Name and email are required." }, { status: 400 });
  }
  if (!EMAIL_RE.test(email)) {
    return NextResponse.json({ ok: false, error: "invalid_email" }, { status: 400 });
  }

  const url = `${base}/subscribe`;
  try {
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify({ name, email }),
      cache: "no-store",
    });

    const text = await res.text();
    let payload: { ok?: boolean; error?: string; detail?: string } = {};
    try {
      payload = text ? (JSON.parse(text) as typeof payload) : {};
    } catch {
      if (!res.ok) {
        return NextResponse.json(
          { ok: false, error: "subscribe_failed", detail: text.slice(0, 300) || `HTTP ${res.status}` },
          { status: 502 }
        );
      }
    }

    if (!res.ok) {
      const status = res.status >= 400 && res.status < 600 ? res.status : 502;
      return NextResponse.json(
        {
          ok: false,
          error: payload.error || "subscribe_failed",
          detail: payload.detail || text.slice(0, 200),
        },
        { status }
      );
    }

    return NextResponse.json({ ok: true, ...payload });
  } catch (e) {
    const message = e instanceof Error ? e.message : "fetch failed";
    return NextResponse.json({ ok: false, error: "newsletter_unreachable", detail: message }, { status: 502 });
  }
}
