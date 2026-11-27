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
        totalVisitorCount: 0,
        totalPages: 0,
        currentPage: 1,
        pageSize: 50,
        countryUniqueVisitors: {},
        countryTotalVisits: {},
        visitors: [],
      });
    }

    // --- Pagination params ---
    const page     = Math.max(1, parseInt(searchParams.get("page")     || "1",  10));
    const pageSize = Math.max(1, Math.min(250, parseInt(searchParams.get("pageSize") || "50", 10)));
    // zrange offset: 0-based index into the sorted set
    const zStart = (page - 1) * pageSize;
    const zEnd   = zStart + pageSize - 1;

    // --- Aggregate KPI stats (always full counts, independent of page) ---
    const [
      totalUniqueDevicesRaw,
      totalUniqueIpsRaw,
      totalVisitsRaw,
      totalExtractionsRaw,
      totalTtsPlaysRaw,
      activeActionDevicesRaw,
      countryUnique,
      countryTotal,
      totalDeviceSetCount,  // zcard = exact count of items in sorted set
      pageDeviceIds,        // only the IDs for this page
      recentIps,            // legacy IP visitors (kept for backwards compat)
    ] = await Promise.all([
      redis.scard("all_unique_devices"),
      redis.scard("all_unique_ips"),
      redis.get<string | number>("total_page_visits"),
      redis.get<string | number>("total_extractions"),
      redis.get<string | number>("total_tts_plays"),
      redis.scard("active_action_devices"),
      redis.hgetall<Record<string, number | string>>("country_unique_visitors"),
      redis.hgetall<Record<string, number | string>>("country_total_visits"),
      redis.zcard("devices_by_last_seen"),
      // Fetch only the slice for this page
      redis.zrange<string[]>("devices_by_last_seen", zStart, zEnd, { rev: true }),
      // Legacy IPs: only fetch on page 1 so they appear first; cap at pageSize
      page === 1
        ? redis.zrange<string[]>("visitors_by_last_seen", 0, pageSize - 1, { rev: true })
        : Promise.resolve([] as string[]),
    ]);

    const totalUniqueDevices  = Number(totalUniqueDevicesRaw)  || 0;
    const totalUniqueIps      = Number(totalUniqueIpsRaw)      || 0;
    const totalVisits         = Number(totalVisitsRaw)         || 0;
    const totalExtractions    = Number(totalExtractionsRaw)    || 0;
    const totalTtsPlays       = Number(totalTtsPlaysRaw)       || 0;
    const totalActiveDevices  = Number(activeActionDevicesRaw) || 0;
    // Total visitor count for pagination: use the sorted set cardinality
    const totalVisitorCount   = Number(totalDeviceSetCount)    || totalUniqueDevices;
    const totalPages          = Math.max(1, Math.ceil(totalVisitorCount / pageSize));

    // --- Fetch device records for this page only ---
    const visitorsMap = new Map<string, any>();

    if (pageDeviceIds && pageDeviceIds.length > 0) {
      const devPipeline = redis.pipeline();
      for (const devId of pageDeviceIds) {
        devPipeline.hgetall(`device:${devId}`);
      }
      const devResults = await devPipeline.exec();
      devResults.forEach((res: any, idx: number) => {
        if (res && Object.keys(res).length > 0) {
          visitorsMap.set(pageDeviceIds[idx], res);
        }
      });
    }

    // Legacy IP records (page 1 only)
    if (recentIps && recentIps.length > 0) {
      const ipPipeline = redis.pipeline();
      for (const ip of recentIps) {
        ipPipeline.hgetall(`visitor:${ip}`);
      }
      const ipResults = await ipPipeline.exec();
      ipResults.forEach((res: any, idx: number) => {
        if (res && Object.keys(res).length > 0) {
          const ip = recentIps[idx];
          const alreadyCovered = Array.from(visitorsMap.values()).some((v) => v.ip === ip);
          if (!alreadyCovered) {
            visitorsMap.set(`legacy_${ip}`, {
              deviceId: `legacy_${ip}`,
              ip,
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
      totalUniqueDevices: Math.max(totalUniqueDevices, totalVisitorCount),
      totalUniqueVisitors: totalUniqueIps,
      totalVisits,
      totalExtractions,
      totalTtsPlays,
      totalActiveDevices,
      // Pagination metadata
      totalVisitorCount,
      totalPages,
      currentPage: page,
      pageSize,
      countryUniqueVisitors: countryUnique || {},
      countryTotalVisits: countryTotal || {},
      visitors,
    });
  } catch (error: any) {
    console.error("Error in /api/admin/stats:", error);
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
