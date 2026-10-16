import { getRedis } from "@/lib/redis";

/**
 * Records visitor IP and Vercel edge geolocation permanently in Upstash Redis.
 * Called on page load and on image recognition/processing requests.
 */
export async function recordVisitor(headers: Headers) {
  try {
    const redis = getRedis();
    if (!redis) return;

    // Extract real client IP
    const forwarded = headers.get("x-forwarded-for");
    const realIp = headers.get("x-real-ip");
    const clientIp = forwarded ? forwarded.split(",")[0].trim() : realIp || "127.0.0.1";

    // Extract Vercel Edge Geolocation headers
    const country = headers.get("x-vercel-ip-country") || "Unknown";
    let city = headers.get("x-vercel-ip-city") || "Unknown";
    try {
      city = decodeURIComponent(city);
    } catch {
      // Keep as-is if decoding fails
    }
    const region = headers.get("x-vercel-ip-country-region") || "";
    const userAgent = headers.get("user-agent") || "Unknown";

    const now = new Date().toISOString();
    const timestamp = Date.now();

    // 1. Add to permanent all-time unique IPs set
    const isNew = await redis.sadd("all_unique_ips", clientIp);
    await redis.incr("total_page_visits");

    // 2. Update visitor profile
    const visitorKey = `visitor:${clientIp}`;
    const existing = await redis.hgetall<Record<string, string>>(visitorKey);

    if (!existing || Object.keys(existing).length === 0) {
      // First-time visitor
      await redis.hset(visitorKey, {
        ip: clientIp,
        country,
        city,
        region,
        firstSeen: now,
        lastSeen: now,
        visits: "1",
        userAgent: userAgent.slice(0, 200),
      });

      await redis.hincrby("country_unique_visitors", country, 1);
    } else {
      // Returning visitor
      const currentVisits = parseInt(existing.visits || "1", 10);
      const updateData: Record<string, string | number> = {
        lastSeen: now,
        visits: currentVisits + 1,
      };

      if ((!existing.country || existing.country === "Unknown") && country !== "Unknown") {
        updateData.country = country;
        updateData.city = city;
        updateData.region = region;
        await redis.hincrby("country_unique_visitors", country, 1);
      }

      await redis.hset(visitorKey, updateData);
    }

    await redis.hincrby("country_total_visits", country, 1);
    await redis.zadd("visitors_by_last_seen", { score: timestamp, member: clientIp });

    return { clientIp, country, city, isNew: isNew === 1 };
  } catch (error) {
    console.error("[Tracker Error]:", error);
  }
}
