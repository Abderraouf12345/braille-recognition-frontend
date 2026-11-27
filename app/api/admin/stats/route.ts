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
    const zStart = (page - 1) * pageSize;
    const zEnd   = zStart + pageSize - 1;

    // --- Step 1: Get total counts for KPIs + both sorted set sizes ---
    const [
      totalUniqueDevicesRaw,
      totalUniqueIpsRaw,
      totalVisitsRaw,
      totalExtractionsRaw,
      totalTtsPlaysRaw,
      activeActionDevicesRaw,
      countryUnique,
      countryTotal,
      deviceSetCount,   // zcard of devices_by_last_seen
      legacySetCount,   // zcard of visitors_by_last_seen
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
      redis.zcard("visitors_by_last_seen"),
    ]);

    const totalUniqueDevices = Number(totalUniqueDevicesRaw) || 0;
    const totalUniqueIps     = Number(totalUniqueIpsRaw)     || 0;
    const totalVisits        = Number(totalVisitsRaw)        || 0;
    const totalExtractions   = Number(totalExtractionsRaw)   || 0;
    const totalTtsPlays      = Number(totalTtsPlaysRaw)      || 0;
    const totalActiveDevices = Number(activeActionDevicesRaw)|| 0;

    // --- Step 2: Determine unified total ---
    // We use the LARGER of: Redis all_unique_devices scard vs devices sorted-set size.
    // Legacy-only users (IP-only, no device fingerprint) live in visitors_by_last_seen
    // but may already overlap with device records. We use all_unique_devices as the
    // authoritative total since it's kept in sync by the tracker for every user type.
    const totalVisitorCount = Math.max(
      totalUniqueDevices,
      Number(deviceSetCount) || 0,
    );
    const totalPages = Math.max(1, Math.ceil(totalVisitorCount / pageSize));

    // --- Step 3: Fetch the page slice of device records ---
    const visitorsMap = new Map<string, any>();

    const [pageDeviceIds, allLegacyIps] = await Promise.all([
      redis.zrange<string[]>("devices_by_last_seen", zStart, zEnd, { rev: true }),
      // Always load ALL legacy IPs so we can deduplicate properly and paginate them too
      Number(legacySetCount) > 0
        ? redis.zrange<string[]>("visitors_by_last_seen", 0, Number(legacySetCount) - 1, { rev: true })
        : Promise.resolve([] as string[]),
    ]);

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

    // --- Step 4: Collect legacy IP-only users (not covered by any device record) ---
    // Build a set of IPs already covered by device records so deduplication is O(1)
    const coveredIps = new Set<string>(
      Array.from(visitorsMap.values()).map((v) => v.ip).filter(Boolean)
    );

    // Find all legacy-only IPs (across the entire set, not just page 1)
    const legacyOnlyIps = (allLegacyIps || []).filter((ip) => !coveredIps.has(ip));

    // Paginate legacy users: they form a secondary list appended after device users.
    // The device records fill positions 0..(deviceSetCount-1) across all pages,
    // then legacy-only records extend those pages.
    // Simple approach: fetch ALL legacy records upfront (they're typically few),
    // then append only the ones belonging to this page's slot.
    const devicePageCount = pageDeviceIds?.length ?? 0;
    const remainingSlots  = pageSize - devicePageCount; // slots left on this page after devices

    // Determine which legacy-only IPs fall on this page.
    // Legacy users are ordered after all device-pages, so their global index starts
    // at deviceSetCount. We compute which ones belong to this page's window.
    const legacyGlobalStart = (page - 1) * pageSize;             // global start of this page
    const deviceSetSize     = Number(deviceSetCount) || 0;
    // Index into legacyOnlyIps array for this page
    const legacyLocalStart  = Math.max(0, legacyGlobalStart - deviceSetSize);
    const legacyLocalEnd    = legacyLocalStart + remainingSlots;
    const legacyIpsForPage  = legacyOnlyIps.slice(legacyLocalStart, legacyLocalEnd);

    if (legacyIpsForPage.length > 0) {
      const ipPipeline = redis.pipeline();
      for (const ip of legacyIpsForPage) {
        ipPipeline.hgetall(`visitor:${ip}`);
      }
      const ipResults = await ipPipeline.exec();
      ipResults.forEach((res: any, idx: number) => {
        if (res && Object.keys(res).length > 0) {
          const ip = legacyIpsForPage[idx];
          visitorsMap.set(`legacy_${ip}`, {
            deviceId: `legacy_${ip}`,
            ip,
            previousIps: ip,
            ...res,
          });
        }
      });
    }

    const visitors = Array.from(visitorsMap.values());

    // The real total includes both device-fingerprinted users AND legacy-IP-only users.
    // legacyOnlyIps.length gives the number of users NOT already covered by a device record.
    const realTotal = Math.max(
      totalUniqueDevices,
      Number(deviceSetCount) + legacyOnlyIps.length,
    );
    const realTotalPages = Math.max(1, Math.ceil(realTotal / pageSize));

    return NextResponse.json({
      connected: true,
      totalUniqueDevices: Math.max(totalUniqueDevices, realTotal),
      totalUniqueVisitors: totalUniqueIps,
      totalVisits,
      totalExtractions,
      totalTtsPlays,
      totalActiveDevices,
      // Pagination metadata
      totalVisitorCount: realTotal,
      totalPages: realTotalPages,
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
