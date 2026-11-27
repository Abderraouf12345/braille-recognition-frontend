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

    // --- Step 1: Get total count of registered devices ---
    const totalDevices = (await redis.zcard("devices_by_last_seen")) || 0;

    // --- Step 2: Determine which ID slice to fetch ---
    // If filter or search is active, we scan all registered devices in-memory
    // Otherwise, fast-path slice for the exact page requested
    const needsBroadScan = search.length > 0 || filter !== "all";
    const zStart = needsBroadScan ? 0 : (page - 1) * pageSize;
    const zEnd   = needsBroadScan ? -1 : zStart + pageSize - 1;

    const [pageDeviceIds, activeActionDevsList] = await Promise.all([
      redis.zrange<string[]>("devices_by_last_seen", zStart, zEnd, { rev: true }),
      redis.smembers<string[]>("active_action_devices"),
    ]);

    const activeSet = new Set<string>(activeActionDevsList || []);

    // --- Step 3: Fetch full records for device IDs ---
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

    let visitors = Array.from(visitorsMap.values());

    // Helper to determine if a visitor is human
    const isRecordHuman = (v: any) => {
      if (
        activeSet.has(v.deviceId) ||
        Number(v.extractions) > 0 ||
        Number(v.tts_plays) > 0 ||
        Number(v.copy_count) > 0 ||
        Number(v.downloads) > 0
      ) {
        return true;
      }
      return classifyVisitor(v).isHuman;
    };

    // --- Step 4: Apply filter ---
    if (filter === "humans") {
      visitors = visitors.filter((v) => isRecordHuman(v));
    } else if (filter === "bots") {
      visitors = visitors.filter((v) => !isRecordHuman(v));
    }

    // --- Step 5: Apply search ---
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

    // --- Step 6: Paginate the result ---
    const filteredTotal = needsBroadScan ? visitors.length : totalDevices;
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
