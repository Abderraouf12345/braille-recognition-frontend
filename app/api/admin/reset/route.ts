import { NextResponse } from "next/server";
import { getRedis } from "@/lib/redis";

export async function POST(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const key = searchParams.get("key") || request.headers.get("x-admin-key");
    const configuredKey = process.env.ADMIN_SECRET_KEY || "braille2026";

    if (key !== configuredKey) {
      return NextResponse.json({ error: "Unauthorized: Invalid admin key" }, { status: 401 });
    }

    const redis = getRedis();
    if (!redis) {
      return NextResponse.json({ error: "Redis not configured" }, { status: 500 });
    }

    // Flush all keys in the database to start with a completely clean slate
    await redis.flushdb();

    return NextResponse.json({
      status: "ok",
      message: "Database reset successfully! All visitor and IP records have been cleared.",
    });
  } catch (error: any) {
    console.error("Error resetting database:", error);
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
