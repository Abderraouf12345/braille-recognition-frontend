import { NextResponse } from "next/server";
import { getRedis } from "@/lib/redis";

export async function POST(request: Request) {
  try {
    const redis = getRedis();
    if (!redis) {
      // Redis not yet configured in environment variables, respond safely
      return NextResponse.json({ status: "skipped", reason: "Redis not configured" });
    }

    // Extract Client IP
    const forwarded = request.headers.get("x-forwarded-for");
    const realIp = request.headers.get("x-real-ip");
    const clientIp = forwarded ? forwarded.split(",")[0].trim() : realIp || "127.0.0.1";

    // Extract Geolocation Headers from Vercel Edge
    const country = request.headers.get("x-vercel-ip-country") || "Unknown";
    let city = request.headers.get("x-vercel-ip-city") || "Unknown";
    try {
      city = decodeURIComponent(city);
    } catch {
      // Keep as-is if decoding fails
    }
    const region = request.headers.get("x-vercel-ip-country-region") || "";
    const userAgent = request.headers.get("user-agent") || "Unknown";

    const now = new Date().toISOString();
    const timestamp = Date.now();

    // Check if this IP is already in our permanent unique visitors set
    const isNew = await redis.sadd("all_unique_ips", clientIp);
    await redis.incr("total_page_visits");

    const visitorKey = `visitor:${clientIp}`;
    const existing = await redis.hgetall<Record<string, string>>(visitorKey);

    if (!existing || Object.keys(existing).length === 0) {
      // First time visitor
      await redis.hset(visitorKey, {
        ip: clientIp,
        country,
        city,
        region,
        firstSeen: now,
        lastSeen: now,
        visits: "1",
        userAgent: userAgent.slice(0, 200), // sanitize length
      });

      // Track unique visitor per country
      await redis.hincrby("country_unique_visitors", country, 1);
    } else {
      // Returning visitor
      const currentVisits = parseInt(existing.visits || "1", 10);
      const updateData: Record<string, string | number> = {
        lastSeen: now,
        visits: currentVisits + 1,
      };

      // If location was previously Unknown and now available, update it
      if (existing.country === "Unknown" && country !== "Unknown") {
        updateData.country = country;
        updateData.city = city;
        updateData.region = region;
        await redis.hincrby("country_unique_visitors", country, 1);
      }

      await redis.hset(visitorKey, updateData);
    }

    // Always update total country visits counter
    await redis.hincrby("country_total_visits", country, 1);

    // Update sorted set for fast chronological lookup of recent visitors
    await redis.zadd("visitors_by_last_seen", { score: timestamp, member: clientIp });

    return NextResponse.json({
      status: "ok",
      isNew: isNew === 1,
      ip: clientIp,
      country,
      city,
    });
  } catch (error: any) {
    console.error("Error in /api/track:", error);
    return NextResponse.json({ status: "error", message: error.message }, { status: 500 });
  }
}
