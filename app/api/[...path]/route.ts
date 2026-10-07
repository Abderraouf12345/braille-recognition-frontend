import { NextRequest, NextResponse } from "next/server";

export const dynamic = "force-dynamic";
export const maxDuration = 60; // Allow up to 60s for AI inference on Vercel

const DEFAULT_BACKEND_URL = "https://abderraouf27-braille-backend.hf.space";

async function proxyHandler(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  try {
    const resolvedParams = await params;
    const path = resolvedParams.path || [];

    // Backend target base URL
    const backendBase = (
      process.env.BACKEND_API_URL ||
      DEFAULT_BACKEND_URL
    ).replace(/\/+$/, "");

    const targetPath = path.join("/");
    const targetUrl = `${backendBase}/${targetPath}${request.nextUrl.search}`;

    // Prepare headers for the target backend
    const forwardHeaders = new Headers();
    request.headers.forEach((value, key) => {
      const lowerKey = key.toLowerCase();
      // Exclude hop-by-hop headers
      if (
        lowerKey !== "host" &&
        lowerKey !== "connection" &&
        lowerKey !== "content-length"
      ) {
        forwardHeaders.set(key, value);
      }
    });

    // Inject Hugging Face Private Access Token securely if configured
    const hfToken = process.env.HF_TOKEN;
    if (hfToken) {
      forwardHeaders.set("Authorization", `Bearer ${hfToken.trim()}`);
    }

    const isBodyMethod = ["POST", "PUT", "PATCH"].includes(request.method);
    const body = isBodyMethod ? request.body : undefined;

    // Send the proxied request to Hugging Face
    const backendResponse = await fetch(targetUrl, {
      method: request.method,
      headers: forwardHeaders,
      body,
      // @ts-expect-error duplex is required in node fetch when body is a ReadableStream
      duplex: isBodyMethod ? "half" : undefined,
      cache: "no-store",
    });

    // Prepare response headers
    const responseHeaders = new Headers();
    backendResponse.headers.forEach((value, key) => {
      const lowerKey = key.toLowerCase();
      if (
        lowerKey !== "content-encoding" &&
        lowerKey !== "transfer-encoding"
      ) {
        responseHeaders.set(key, value);
      }
    });

    // Stream the backend response (SSE events, JSON, audio, etc.) back to client
    return new Response(backendResponse.body, {
      status: backendResponse.status,
      statusText: backendResponse.statusText,
      headers: responseHeaders,
    });
  } catch (error: any) {
    console.error("[API Proxy Error]:", error);
    return NextResponse.json(
      {
        error: "Backend proxy error",
        message: error?.message || "Failed to reach backend service.",
      },
      { status: 502 }
    );
  }
}

export const GET = proxyHandler;
export const POST = proxyHandler;
export const PUT = proxyHandler;
export const DELETE = proxyHandler;
export const OPTIONS = proxyHandler;
