import { NextResponse } from "next/server";
import {
  recordVisitor,
  recordUserAction,
  recordHeartbeat,
  UserActionType,
} from "@/lib/tracker";

export async function POST(request: Request) {
  let deviceId: string | null = null;
  let action: UserActionType | null = null;
  let referrer: string | undefined;
  let campaign: string | undefined;
  let heartbeat: boolean = false;
  let durationSeconds: number = 0;

  try {
    const body = await request.json();
    if (body && typeof body.deviceId === "string") {
      deviceId = body.deviceId;
    }
    if (body && typeof body.action === "string") {
      action = body.action as UserActionType;
    }
    if (body && typeof body.referrer === "string") {
      referrer = body.referrer;
    }
    if (body && typeof body.campaign === "string") {
      campaign = body.campaign;
    }
    if (body && body.heartbeat === true) {
      heartbeat = true;
    }
    if (body && typeof body.durationSeconds === "number") {
      durationSeconds = body.durationSeconds;
    }
  } catch {
    // Body is not JSON or empty, ignore
  }

  // 1. Heartbeat ping (Live online status & duration update)
  if (heartbeat && deviceId) {
    await recordHeartbeat(deviceId, durationSeconds);
    return NextResponse.json({ status: "ok", heartbeat: true });
  }

  // 2. Specific action beacon (extraction, copy, tts, download)
  if (action) {
    await recordUserAction(request.headers, action, deviceId);
    return NextResponse.json({ status: "ok", action });
  }

  // 3. Regular page visit with referrer & campaign
  const result = await recordVisitor(request.headers, deviceId, {
    referrer,
    campaign,
  });
  return NextResponse.json({ status: "ok", data: result });
}

export async function GET(request: Request) {
  const result = await recordVisitor(request.headers);
  return NextResponse.json({ status: "ok", data: result });
}
