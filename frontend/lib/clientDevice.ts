/**
 * Client-side helper to retrieve or generate a permanent unique Device ID.
 * Stored in both localStorage (survives clearing cookies) and a 10-year Cookie
 * (automatically sent with fetch requests and API calls).
 */
export function getOrCreateDeviceId(): string {
  if (typeof window === "undefined") {
    return "";
  }

  const STORAGE_KEY = "braille_device_id";
  const COOKIE_NAME = "braille_device_id";

  // 1. Try reading from localStorage
  let deviceId = localStorage.getItem(STORAGE_KEY);

  // 2. Fallback to cookie if localStorage was cleared
  if (!deviceId) {
    const match = document.cookie.match(new RegExp("(^| )" + COOKIE_NAME + "=([^;]+)"));
    if (match && match[2]) {
      deviceId = decodeURIComponent(match[2]);
    }
  }

  // 3. Generate a new permanent UUID if not found
  if (!deviceId) {
    const randomPart =
      typeof crypto !== "undefined" && crypto.randomUUID
        ? crypto.randomUUID()
        : Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
    deviceId = `dev_${randomPart}`;
  }

  // Persist in localStorage
  try {
    localStorage.setItem(STORAGE_KEY, deviceId);
  } catch {}

  // Persist in cookie for 10 years (315,360,000 seconds) so server routes automatically receive it
  try {
    document.cookie = `${COOKIE_NAME}=${encodeURIComponent(
      deviceId
    )}; path=/; max-age=315360000; SameSite=Lax`;
  } catch {}

  return deviceId;
}

/**
 * Sends a non-blocking client-side action beacon (e.g. copying text, downloading results).
 */
export function trackClientAction(
  action: "copy_text" | "download_results" | "tts_play" | "extraction"
) {
  if (typeof window === "undefined") return;
  const deviceId = getOrCreateDeviceId();
  fetch("/api/track", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "x-device-id": deviceId,
    },
    body: JSON.stringify({ deviceId, action }),
    keepalive: true,
  }).catch(() => {});
}

