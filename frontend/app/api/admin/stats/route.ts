import { NextResponse } from "next/server";
import { getRedis } from "@/lib/redis";
import { classifyVisitor } from "@/lib/browserDetect";

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
        humanCount: 0,
        botCount: 0,
        countryUniqueVisitors: {},
        countryTotalVisits: {},
      });
    }

    // 1. Fetch global counters and all registered device IDs
    const [
      totalUniqueIpsRaw,
      totalVisitsRaw,
      totalExtractionsRaw,
      totalTtsPlaysRaw,
      allDevIds,
      activeActionDevsList,
    ] = await Promise.all([
      redis.scard("all_unique_ips"),
      redis.get<string | number>("total_page_visits"),
      redis.get<string | number>("total_extractions"),
      redis.get<string | number>("total_tts_plays"),
      // Get all registered physical devices sorted by lastSeen descending
      redis.zrange<string[]>("devices_by_last_seen", 0, -1, { rev: true }),
      // Get devices that performed real user actions
      redis.smembers<string[]>("active_action_devices"),
    ]);

    const devIds = allDevIds || [];
    const totalUniqueDevices = devIds.length;
    const totalUniqueIps = Number(totalUniqueIpsRaw) || 0;
    const totalVisits = Number(totalVisitsRaw) || 0;
    const totalExtractions = Number(totalExtractionsRaw) || 0;
    const totalTtsPlays = Number(totalTtsPlaysRaw) || 0;
    const activeSet = new Set<string>(activeActionDevsList || []);

    // 2. Fetch full profiles for all registered devices
    const countryUniqueVisitors: Record<string, number> = {};
    const countryTotalVisits: Record<string, number> = {};
    let humanCount = 0;
    let botCount = 0;

    if (devIds.length > 0) {
      const pipeline = redis.pipeline();
      for (const id of devIds) {
        pipeline.hgetall(`device:${id}`);
      }
      const devResults = await pipeline.exec();

      devResults.forEach((res: any, idx: number) => {
        const devId = devIds[idx];
        const data = res || {};

        // Action check: if device performed extractions, TTS, copy, or is in activeSet, it is guaranteed Human
        const hasActions =
          activeSet.has(devId) ||
          Number(data.extractions) > 0 ||
          Number(data.tts_plays) > 0 ||
          Number(data.copy_count) > 0 ||
          Number(data.downloads) > 0;

        let isHuman = false;
        if (hasActions) {
          isHuman = true;
        } else {
          const cls = classifyVisitor({
            deviceId: devId,
            ip: data.ip,
            userAgent: data.userAgent,
            browser: data.browser,
            os: data.os,
          });
          isHuman = cls.isHuman;
        }

        if (isHuman) {
          humanCount++;
        } else {
          botCount++;
        }

        // Country distribution across the registered devices
        const country = data.country && data.country !== "Unknown" ? data.country : "Unknown";
        countryUniqueVisitors[country] = (countryUniqueVisitors[country] || 0) + 1;
        countryTotalVisits[country] =
          (countryTotalVisits[country] || 0) + (Number(data.visits) || 1);
      });
    }

    return NextResponse.json({
      connected: true,
      totalUniqueDevices,
      totalUniqueVisitors: totalUniqueIps,
      totalVisits,
      totalExtractions,
      totalTtsPlays,
      totalActiveDevices: activeSet.size,
      totalVisitorCount: totalUniqueDevices,
      humanCount,
      botCount,
      countryUniqueVisitors,
      countryTotalVisits,
    });
  } catch (error: any) {
    console.error("Error in /api/admin/stats:", error);
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
