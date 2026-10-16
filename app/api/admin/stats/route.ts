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
        totalUniqueVisitors: 0,
        totalVisits: 0,
        countryUniqueVisitors: {},
        countryTotalVisits: {},
        visitors: [],
      });
    }

    // Retrieve aggregate statistics
    const [totalUniqueVisitors, totalVisitsRaw, countryUnique, countryTotal, recentIps] =
      await Promise.all([
        redis.scard("all_unique_ips"),
        redis.get<string | number>("total_page_visits"),
        redis.hgetall<Record<string, number | string>>("country_unique_visitors"),
        redis.hgetall<Record<string, number | string>>("country_total_visits"),
        redis.zrange<string[]>("visitors_by_last_seen", 0, 99, { rev: true }),
      ]);

    const totalVisits = Number(totalVisitsRaw) || 0;

    // Fetch details for the latest 100 unique visitor IPs
    let visitors: Array<Record<string, any>> = [];
    if (recentIps && recentIps.length > 0) {
      const pipeline = redis.pipeline();
      for (const ip of recentIps) {
        pipeline.hgetall(`visitor:${ip}`);
      }
      const results = await pipeline.exec();
      visitors = results
        .map((res: any, idx: number) => {
          if (!res) {
            return { ip: recentIps[idx] };
          }
          return res;
        })
        .filter(Boolean);
    }

    return NextResponse.json({
      connected: true,
      totalUniqueVisitors,
      totalVisits,
      countryUniqueVisitors: countryUnique || {},
      countryTotalVisits: countryTotal || {},
      visitors,
    });
  } catch (error: any) {
    console.error("Error in /api/admin/stats:", error);
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
