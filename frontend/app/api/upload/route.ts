import { NextRequest } from "next/server";

const AGUI_ENDPOINT = process.env.AGUI_ENDPOINT ?? "http://127.0.0.1:8001";

export async function POST(req: NextRequest) {
  const formData = await req.formData();
  let upstream: Response;
  try {
    upstream = await fetch(`${AGUI_ENDPOINT}/upload`, {
      method: "POST",
      body: formData,
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Failed to reach upload service";
    return new Response(JSON.stringify({ error: message, endpoint: AGUI_ENDPOINT }), {
      status: 502,
      headers: { "content-type": "application/json" },
    });
  }

  const contentType = upstream.headers.get("content-type") ?? "application/json";
  const body = await upstream.text();

  return new Response(body, {
    status: upstream.status,
    headers: {
      "content-type": contentType,
    },
  });
}
