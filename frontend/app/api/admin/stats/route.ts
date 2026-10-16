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
        countryUniqueVisitors: {},
        countryTotalVisits: {},
        visitors: [],
      });
    }

    // Retrieve aggregate statistics
    const [
      totalUniqueDevicesRaw,
      totalUniqueIpsRaw,
      totalVisitsRaw,
      totalExtractionsRaw,
      totalTtsPlaysRaw,
      activeActionDevicesRaw,
      countryUnique,
      countryTotal,
      recentDeviceIds,
      recentIps,
    ] = await Promise.all([
      redis.scard("all_unique_devices"),
      redis.scard("all_unique_ips"),
      redis.get<string | number>("total_page_visits"),
      redis.get<string | number>("total_extractions"),
      redis.get<string | number>("total_tts_plays"),
      redis.scard("active_action_devices"),
      redis.hgetall<Record<string, number | string>>("country_unique_visitors"),
      redis.hgetall<Record<string, number | string>>("country_total_visits"),
      redis.zrange<string[]>("devices_by_last_seen", 0, 99, { rev: true }),
      redis.zrange<string[]>("visitors_by_last_seen", 0, 99, { rev: true }),
    ]);

    const totalUniqueDevices = Number(totalUniqueDevicesRaw) || 0;
    const totalUniqueIps = Number(totalUniqueIpsRaw) || 0;
    const totalVisits = Number(totalVisitsRaw) || 0;
    const totalExtractions = Number(totalExtractionsRaw) || 0;
    const totalTtsPlays = Number(totalTtsPlaysRaw) || 0;
    const totalActiveDevices = Number(activeActionDevicesRaw) || 0;

    // Fetch device records
    const visitorsMap = new Map<string, any>();

    if (recentDeviceIds && recentDeviceIds.length > 0) {
      const devPipeline = redis.pipeline();
      for (const devId of recentDeviceIds) {
        devPipeline.hgetall(`device:${devId}`);
      }
      const devResults = await devPipeline.exec();
      devResults.forEach((res: any, idx: number) => {
        if (res && Object.keys(res).length > 0) {
          visitorsMap.set(recentDeviceIds[idx], res);
        }
      });
    }

    // Also load any legacy IP records that don't have a device record yet
    if (recentIps && recentIps.length > 0) {
      const ipPipeline = redis.pipeline();
      for (const ip of recentIps) {
        ipPipeline.hgetall(`visitor:${ip}`);
      }
      const ipResults = await ipPipeline.exec();
      ipResults.forEach((res: any, idx: number) => {
        if (res && Object.keys(res).length > 0) {
          const ip = recentIps[idx];
          // If this IP isn't represented by an existing device, add it as a legacy visitor
          const alreadyCovered = Array.from(visitorsMap.values()).some((v) => v.ip === ip);
          if (!alreadyCovered) {
            visitorsMap.set(`legacy_${ip}`, {
              deviceId: `legacy_${ip}`,
              ip: ip,
              previousIps: ip,
              ...res,
            });
          }
        }
      });
    }

    const visitors = Array.from(visitorsMap.values());

    return NextResponse.json({
      connected: true,
      totalUniqueDevices: Math.max(totalUniqueDevices, visitors.length),
      totalUniqueVisitors: totalUniqueIps,
      totalVisits,
      totalExtractions,
      totalTtsPlays,
      totalActiveDevices,
      countryUniqueVisitors: countryUnique || {},
      countryTotalVisits: countryTotal || {},
      visitors,
    });
  } catch (error: any) {
    console.error("Error in /api/admin/stats:", error);
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
