import { getRedis } from "@/lib/redis";
import { detectBrowser, detectOS } from "@/lib/browserDetect";

/**
 * Parses cookies from header string
 */
function parseCookie(cookieHeader: string | null, key: string): string | null {
  if (!cookieHeader) return null;
  const match = cookieHeader.match(new RegExp("(^|;\\s*)" + key + "=([^;]+)"));
  return match && match[2] ? decodeURIComponent(match[2]) : null;
}

/**
 * Extracts client IP address from headers
 */
export function extractClientIp(headers: Headers): string {
  const forwarded = headers.get("x-forwarded-for");
  const realIp = headers.get("x-real-ip");
  return forwarded ? forwarded.split(",")[0].trim() : realIp || "127.0.0.1";
}

/**
 * Extracts device ID from headers or cookies with IP fallback
 */
export function extractDeviceId(headers: Headers, deviceIdOverride?: string | null): string {
  const clientIp = extractClientIp(headers);
  const cookieHeader = headers.get("cookie");
  const cookieDeviceId = parseCookie(cookieHeader, "braille_device_id");
  const headerDeviceId = headers.get("x-device-id");
  return (
    deviceIdOverride ||
    headerDeviceId ||
    cookieDeviceId ||
    `legacy_${clientIp}`
  );
}

/**
 * Records visitor Device ID, IP address, and Vercel edge geolocation permanently in Upstash Redis.
 * Called on page load and on image recognition/processing requests.
 */
export async function recordVisitor(headers: Headers, deviceIdOverride?: string | null) {
  try {
    const redis = getRedis();
    if (!redis) return;

    // 1. Extract real client IP and Device ID
    const clientIp = extractClientIp(headers);
    const deviceId = extractDeviceId(headers, deviceIdOverride);

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
    const browser = detectBrowser(userAgent);
    const os = detectOS(userAgent);

    const now = new Date().toISOString();
    const timestamp = Date.now();

    // 4. Update sets: Permanent Devices & Permanent Network IPs
    const isNewDevice = await redis.sadd("all_unique_devices", deviceId);
    await redis.sadd("all_unique_ips", clientIp);
    await redis.incr("total_page_visits");

    // 5. Manage Device Profile in Redis (Each device ID is strictly isolated)
    const deviceKey = `device:${deviceId}`;

    const existing = await redis.hgetall<Record<string, string>>(deviceKey);

    if (!existing || Object.keys(existing).length === 0) {
      // Brand new physical device / user / browser sandbox
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
        browser,
        os,
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
        firstSeen: existing.firstSeen || now,
        lastSeen: now,
        visits: currentVisits + 1,
      };

      // Backfill browser and OS if missing or previously Unknown
      if ((!existing.browser || existing.browser === "Unknown") && browser !== "Unknown") {
        updateData.browser = browser;
      }
      if ((!existing.os || existing.os === "Unknown") && os !== "Unknown") {
        updateData.os = os;
      }
      if (!existing.userAgent || existing.userAgent === "Unknown") {
        updateData.userAgent = userAgent.slice(0, 200);
      }

      // If location was previously Unknown and now available, update it
      if ((!existing.country || existing.country === "Unknown") && country !== "Unknown") {
        updateData.country = country;
        updateData.city = city;
        updateData.region = region;
        await redis.hincrby("country_unique_visitors", country, 1);
      }

      await redis.hset(deviceKey, updateData);
    }

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

export type UserActionType = "extraction" | "tts_play" | "copy_text" | "download_results";

/**
 * Records a specific high-value user action (e.g. Braille extraction, TTS audio play).
 */
export async function recordUserAction(
  headers: Headers,
  action: UserActionType,
  deviceIdOverride?: string | null
) {
  try {
    const redis = getRedis();
    if (!redis) return;

    const deviceId = extractDeviceId(headers, deviceIdOverride);
    const deviceKey = `device:${deviceId}`;
    const now = new Date().toISOString();
    const timestamp = Date.now();

    const humanLabels: Record<UserActionType, string> = {
      extraction: "Extract Braille",
      tts_play: "Listen to Audio",
      copy_text: "Copy Result",
      download_results: "Download File",
    };

    const actionLabel = humanLabels[action] || action;

    const pipeline = redis.pipeline();

    // 1. Increment global metrics
    if (action === "extraction") {
      pipeline.incr("total_extractions");
    } else if (action === "tts_play") {
      pipeline.incr("total_tts_plays");
    }

    // 2. Mark this device as active in action devices set
    pipeline.sadd("active_action_devices", deviceId);

    // 3. Increment per-device action counters (snake_case matches admin dashboard reading)
    if (action === "extraction") {
      pipeline.hincrby(deviceKey, "extractions", 1);
    } else if (action === "tts_play") {
      pipeline.hincrby(deviceKey, "tts_plays", 1);
    } else if (action === "copy_text") {
      pipeline.hincrby(deviceKey, "copy_count", 1);
    } else if (action === "download_results") {
      pipeline.hincrby(deviceKey, "downloads", 1);
    }

    pipeline.hset(deviceKey, {
      lastAction: actionLabel,
      lastActionTime: now,
      lastSeen: now,
    });
    pipeline.zadd("devices_by_last_seen", { score: timestamp, member: deviceId });

    await pipeline.exec();
  } catch (error) {
    console.error("[RecordUserAction Error]:", error);
  }
}

