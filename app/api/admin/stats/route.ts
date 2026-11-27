import { NextResponse } from "next/server";
import { getRedis } from "@/lib/redis";

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const key = searchParams.get("key") || request.headers.get("x-admin-key");
    const configuredKey = process.env.ADMIN_SECRET_KEY || "braille2026";

    if (key !== configuredKey) {
      return NextResponse.json({ error: "Unauthorized: Invalid admin key" }, { status: 401 });
    }

    const redis = getRedis();
    if (!redis) {
      return NextResponse.json({
        connected: false,
        message:
          "Upstash Redis is not connected yet. Please set UPSTASH_REDIS_REST_URL and UPSTASH_REDIS_REST_TOKEN in your Vercel Environment Variables.",
        totalUniqueDevices: 0,
        totalUniqueVisitors: 0,
        totalVisits: 0,
        totalExtractions: 0,
        totalTtsPlays: 0,
        totalActiveDevices: 0,
        totalVisitorCount: 0,
        countryUniqueVisitors: {},
        countryTotalVisits: {},
      });
    }

    // --- KPI counters only (all O(1) or O(N) on small hashes) ---
    const [
      totalUniqueDevicesRaw,
      totalUniqueIpsRaw,
      totalVisitsRaw,
      totalExtractionsRaw,
      totalTtsPlaysRaw,
      activeActionDevicesRaw,
      deviceSetCount,
      legacySetCount,
      countryUnique,
      countryTotal,
    ] = await Promise.all([
      redis.scard("all_unique_devices"),
      redis.scard("all_unique_ips"),
      redis.get<string | number>("total_page_visits"),
      redis.get<string | number>("total_extractions"),
      redis.get<string | number>("total_tts_plays"),
      redis.scard("active_action_devices"),
      redis.zcard("devices_by_last_seen"),
      redis.zcard("visitors_by_last_seen"),
      redis.hgetall<Record<string, number | string>>("country_unique_visitors"),
      redis.hgetall<Record<string, number | string>>("country_total_visits"),
    ]);

    const totalUniqueDevices = Number(totalUniqueDevicesRaw) || 0;
    const totalUniqueIps     = Number(totalUniqueIpsRaw)     || 0;
    const totalVisits        = Number(totalVisitsRaw)        || 0;
    const totalExtractions   = Number(totalExtractionsRaw)   || 0;
    const totalTtsPlays      = Number(totalTtsPlaysRaw)      || 0;
    const totalActiveDevices = Number(activeActionDevicesRaw)|| 0;

    // Best estimate of total visitor count across both sorted sets
    const totalVisitorCount = Math.max(
      totalUniqueDevices,
      (Number(deviceSetCount) || 0) + (Number(legacySetCount) || 0),
    );

    return NextResponse.json({
      connected: true,
      totalUniqueDevices: Math.max(totalUniqueDevices, totalVisitorCount),
      totalUniqueVisitors: totalUniqueIps,
      totalVisits,
      totalExtractions,
      totalTtsPlays,
      totalActiveDevices,
      totalVisitorCount,
      countryUniqueVisitors: countryUnique || {},
      countryTotalVisits:    countryTotal  || {},
    });
  } catch (error: any) {
    console.error("Error in /api/admin/stats:", error);
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
