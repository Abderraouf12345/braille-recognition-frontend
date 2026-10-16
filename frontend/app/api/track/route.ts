import { NextResponse } from "next/server";
import { recordVisitor, recordUserAction, UserActionType } from "@/lib/tracker";

export async function POST(request: Request) {
  let deviceId: string | null = null;
  let action: UserActionType | null = null;

  try {
    const body = await request.json();
    if (body && typeof body.deviceId === "string") {
      deviceId = body.deviceId;
    }
    if (body && typeof body.action === "string") {
      action = body.action as UserActionType;
    }
  } catch {
    // Body is not JSON or empty, ignore
  }

  // If specific action is provided, record action; otherwise record page visit
  if (action) {
    await recordUserAction(request.headers, action, deviceId);
    return NextResponse.json({ status: "ok", action });
  }

  const result = await recordVisitor(request.headers, deviceId);
  return NextResponse.json({ status: "ok", data: result });
}

export async function GET(request: Request) {
  const result = await recordVisitor(request.headers);
  return NextResponse.json({ status: "ok", data: result });
}
