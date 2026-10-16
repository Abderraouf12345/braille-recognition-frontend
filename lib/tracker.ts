import { getRedis } from "@/lib/redis";

/**
 * Parses cookies from header string
 */
function parseCookie(cookieHeader: string | null, key: string): string | null {
  if (!cookieHeader) return null;
  const match = cookieHeader.match(new RegExp("(^|;\\s*)" + key + "=([^;]+)"));
  return match && match[2] ? decodeURIComponent(match[2]) : null;
}

/**
 * Records visitor Device ID, IP address, and Vercel edge geolocation permanently in Upstash Redis.
 * Called on page load and on image recognition/processing requests.
 */
export async function recordVisitor(headers: Headers, deviceIdOverride?: string | null) {
  try {
    const redis = getRedis();
    if (!redis) return;

    // 1. Extract real client IP
    const forwarded = headers.get("x-forwarded-for");
    const realIp = headers.get("x-real-ip");
    const clientIp = forwarded ? forwarded.split(",")[0].trim() : realIp || "127.0.0.1";

    // 2. Extract Permanent Device ID (Header > Body Override > Cookie > IP Fallback)
    const cookieHeader = headers.get("cookie");
    const cookieDeviceId = parseCookie(cookieHeader, "braille_device_id");
    const headerDeviceId = headers.get("x-device-id");
    const deviceId =
      deviceIdOverride ||
      headerDeviceId ||
      cookieDeviceId ||
      `legacy_${clientIp}`;

    // 3. Extract Vercel Edge Geolocation headers
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

    // 4. Update sets: Permanent Devices & Permanent Network IPs
    const isNewDevice = await redis.sadd("all_unique_devices", deviceId);
    await redis.sadd("all_unique_ips", clientIp);
    await redis.incr("total_page_visits");

    // 5. Manage Device Profile in Redis
    const deviceKey = `device:${deviceId}`;
    const legacyKey = `visitor:${clientIp}`;

    let existing = await redis.hgetall<Record<string, string>>(deviceKey);

    // If no device key yet, check legacy visitor key for migration
    if (!existing || Object.keys(existing).length === 0) {
      const legacy = await redis.hgetall<Record<string, string>>(legacyKey);
      if (legacy && Object.keys(legacy).length > 0) {
        existing = legacy;
      }
    }

    if (!existing || Object.keys(existing).length === 0) {
      // Brand new physical device / user
      await redis.hset(deviceKey, {
        deviceId,
        ip: clientIp,
        previousIps: clientIp,
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
      // Returning device! (Even if their IP changed due to router reboot or 4G)
      const currentVisits = parseInt(existing.visits || "1", 10);
      const prevIpsList = (existing.previousIps || existing.ip || clientIp)
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean);

      if (!prevIpsList.includes(clientIp)) {
        prevIpsList.push(clientIp);
      }

      const updateData: Record<string, string | number> = {
        deviceId,
        ip: clientIp, // latest active IP
        previousIps: prevIpsList.join(", "),
        lastSeen: now,
        visits: currentVisits + 1,
      };

      // If location was previously Unknown and now available, update it
      if ((!existing.country || existing.country === "Unknown") && country !== "Unknown") {
        updateData.country = country;
        updateData.city = city;
        updateData.region = region;
        await redis.hincrby("country_unique_visitors", country, 1);
      }

      await redis.hset(deviceKey, updateData);
    }

    // Always maintain legacy key so existing dashboard lookups remain intact
    await redis.hset(legacyKey, {
      ip: clientIp,
      country,
      city,
      region,
      lastSeen: now,
      visits: existing?.visits ? parseInt(existing.visits, 10) + 1 : 1,
      userAgent: userAgent.slice(0, 200),
    });

    // Update sorted sets
    await redis.zadd("devices_by_last_seen", { score: timestamp, member: deviceId });
    await redis.zadd("visitors_by_last_seen", { score: timestamp, member: clientIp });
    await redis.hincrby("country_total_visits", country, 1);

    return {
      deviceId,
      clientIp,
      country,
      city,
      isNewDevice: isNewDevice === 1,
    };
  } catch (error) {
    console.error("[Tracker Error]:", error);
  }
}
