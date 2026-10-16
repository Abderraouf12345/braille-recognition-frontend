import { NextResponse } from "next/server";
import { recordVisitor } from "@/lib/tracker";

export async function POST(request: Request) {
  let deviceId: string | null = null;
  try {
    const body = await request.json();
    if (body && typeof body.deviceId === "string") {
      deviceId = body.deviceId;
    }
  } catch {
    // Body is not JSON or empty, ignore
  }

  const result = await recordVisitor(request.headers, deviceId);
  return NextResponse.json({ status: "ok", data: result });
}

export async function GET(request: Request) {
  const result = await recordVisitor(request.headers);
  return NextResponse.json({ status: "ok", data: result });
}
