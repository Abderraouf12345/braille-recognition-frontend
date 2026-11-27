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
      return NextResponse.json({ visitors: [], total: 0, page: 1, pageSize: 50, totalPages: 1 });
    }

    // --- Query params ---
    const page     = Math.max(1,   parseInt(searchParams.get("page")     || "1",   10));
    const pageSize = Math.max(1, Math.min(250, parseInt(searchParams.get("pageSize") || "50", 10)));
    const search   = (searchParams.get("search")   || "").toLowerCase().trim();
    const filter   = (searchParams.get("filter")   || "all") as "all" | "humans" | "bots";

    // --- Step 1: Get total counts for pagination math ---
    const [deviceSetCount, legacySetCount] = await Promise.all([
      redis.zcard("devices_by_last_seen"),
      redis.zcard("visitors_by_last_seen"),
    ]);

    const totalDevices = Number(deviceSetCount) || 0;
    const totalLegacy  = Number(legacySetCount)  || 0;

    // --- Step 2: Determine which ID slice to fetch ---
    // When searching or filtering we need a broader scan; otherwise use exact offset.
    // For search/filter: load up to 2000 candidates and filter in-memory.
    // For plain pagination: load only the page slice (fast path).
    const needsBroadScan = search.length > 0 || filter !== "all";
    const scanLimit = needsBroadScan ? 4999 : pageSize - 1; // 0-based end index for exact page

    // --- Step 3: Fetch device IDs for this window ---
    const zStart = needsBroadScan ? 0 : (page - 1) * pageSize;
    const zEnd   = needsBroadScan ? scanLimit : zStart + pageSize - 1;

    const [pageDeviceIds, allLegacyIps] = await Promise.all([
      redis.zrange<string[]>("devices_by_last_seen", zStart, zEnd, { rev: true }),
      totalLegacy > 0
        ? redis.zrange<string[]>("visitors_by_last_seen", 0, Math.min(scanLimit, totalLegacy - 1), { rev: true })
        : Promise.resolve([] as string[]),
    ]);

    // --- Step 4: Fetch full records for device IDs ---
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

    // --- Step 5: Append legacy IP-only visitors ---
    const coveredIps = new Set<string>(
      Array.from(visitorsMap.values()).map((v) => v.ip).filter(Boolean)
    );
    const legacyOnlyIps = (allLegacyIps || []).filter((ip) => !coveredIps.has(ip));

    if (legacyOnlyIps.length > 0) {
      const ipPipeline = redis.pipeline();
      for (const ip of legacyOnlyIps) {
        ipPipeline.hgetall(`visitor:${ip}`);
      }
      const ipResults = await ipPipeline.exec();
      ipResults.forEach((res: any, idx: number) => {
        if (res && Object.keys(res).length > 0) {
          const ip = legacyOnlyIps[idx];
          visitorsMap.set(`legacy_${ip}`, {
            deviceId:    `legacy_${ip}`,
            ip,
            previousIps: ip,
            ...res,
          });
        }
      });
    }

    let visitors = Array.from(visitorsMap.values());

    // --- Step 6: Apply search & filter in-memory (only on the scanned window) ---
    if (filter === "humans") {
      visitors = visitors.filter((v) => classifyVisitor(v).isHuman);
    } else if (filter === "bots") {
      visitors = visitors.filter((v) => !classifyVisitor(v).isHuman);
    }

    if (search) {
      visitors = visitors.filter((v) => {
        const country = (v.country || "").toLowerCase();
        const city    = (v.city    || "").toLowerCase();
        const ip      = (v.ip      || "").toLowerCase();
        const devId   = (v.deviceId|| "").toLowerCase();
        const prevIps = (v.previousIps || "").toLowerCase();
        const ua      = (v.userAgent   || "").toLowerCase();
        const browser = (v.browser     || "").toLowerCase();
        const os      = (v.os          || "").toLowerCase();
        const cls     = classifyVisitor(v);
        return (
          ip.includes(search)      ||
          devId.includes(search)   ||
          prevIps.includes(search) ||
          country.includes(search) ||
          city.includes(search)    ||
          ua.includes(search)      ||
          browser.includes(search) ||
          os.includes(search)      ||
          cls.label.toLowerCase().includes(search) ||
          cls.reason.toLowerCase().includes(search)
        );
      });
    }

    // --- Step 7: Paginate the filtered result (only needed for broad-scan path) ---
    const filteredTotal = needsBroadScan ? visitors.length : totalDevices + legacyOnlyIps.length;
    const totalPages    = Math.max(1, Math.ceil(filteredTotal / pageSize));

    if (needsBroadScan) {
      const start = (page - 1) * pageSize;
      visitors = visitors.slice(start, start + pageSize);
    }

    return NextResponse.json({
      visitors,
      total:      filteredTotal,
      page,
      pageSize,
      totalPages,
    });
  } catch (error: any) {
    console.error("Error in /api/admin/visitors:", error);
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
