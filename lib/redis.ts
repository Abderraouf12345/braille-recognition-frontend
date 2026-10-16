import { Redis } from "@upstash/redis";

/**
 * Returns an Upstash Redis client instance if environment variables are configured.
 * Returns null if UPSTASH_REDIS_REST_URL or UPSTASH_REDIS_REST_TOKEN are missing,
 * preventing any crashes when running in environments without Redis configured.
 */
export function getRedis(): Redis | null {
  const url = process.env.UPSTASH_REDIS_REST_URL;
  const token = process.env.UPSTASH_REDIS_REST_TOKEN;

  if (!url || !token) {
    return null;
  }

  return new Redis({
    url,
    token,
  });
}
