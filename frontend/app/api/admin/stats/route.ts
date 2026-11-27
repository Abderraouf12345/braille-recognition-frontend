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
      humanDevicesCountRaw,
      botDevicesCountRaw,
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
      redis.scard("all_human_devices"),
      redis.scard("all_bot_devices"),
    ]);

    const totalUniqueDevices = Number(totalUniqueDevicesRaw) || 0;
    const totalUniqueIps     = Number(totalUniqueIpsRaw)     || 0;
    const totalVisits        = Number(totalVisitsRaw)        || 0;
    const totalExtractions   = Number(totalExtractionsRaw)   || 0;
    const totalTtsPlays      = Number(totalTtsPlaysRaw)      || 0;
    const totalActiveDevices = Number(activeActionDevicesRaw)|| 0;
    const numLegacy          = Number(legacySetCount)        || 0;

    let humanCount = Number(humanDevicesCountRaw) || 0;
    let botCount   = Number(botDevicesCountRaw)   || 0;

    // Backfill / populate sets if they haven't been created yet or are empty
    if (humanCount === 0 && botCount === 0 && totalUniqueDevices > 0) {
      const allDevIds = await redis.smembers<string[]>("all_unique_devices");
      if (allDevIds && allDevIds.length > 0) {
        const pipeline = redis.pipeline();
        for (const devId of allDevIds) {
          pipeline.hgetall(`device:${devId}`);
        }
        const devResults = await pipeline.exec();
        const humanDevs: string[] = [];
        const botDevs: string[] = [];

        devResults.forEach((res: any, idx: number) => {
          const devId = allDevIds[idx];
          const cls = classifyVisitor({
            deviceId: devId,
            ip: res?.ip,
            userAgent: res?.userAgent,
            browser: res?.browser,
            os: res?.os,
          });
          if (cls.isHuman) {
            humanDevs.push(devId);
          } else {
            botDevs.push(devId);
          }
        });

        const savePipeline = redis.pipeline();
        for (const dev of humanDevs) {
          savePipeline.sadd("all_human_devices", dev);
        }
        for (const dev of botDevs) {
          savePipeline.sadd("all_bot_devices", dev);
        }
        await savePipeline.exec();

        humanCount = humanDevs.length;
        botCount = botDevs.length;
      }
    }

    // Legacy IP-only visitors without JS execution are automated HTTP scanners / bots
    const totalBotCount = botCount + numLegacy;

    // Best estimate of total visitor count across both sorted sets
    const totalVisitorCount = Math.max(
      totalUniqueDevices,
      (Number(deviceSetCount) || 0) + numLegacy,
      humanCount + totalBotCount
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
      humanCount,
      botCount: totalBotCount,
      countryUniqueVisitors: countryUnique || {},
      countryTotalVisits:    countryTotal  || {},
    });
  } catch (error: any) {
    console.error("Error in /api/admin/stats:", error);
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
