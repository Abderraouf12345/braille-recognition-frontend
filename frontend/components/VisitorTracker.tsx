"use client";

import { useEffect, useRef } from "react";
import { getOrCreateDeviceId } from "@/lib/clientDevice";

export function VisitorTracker() {
  const sessionSecondsRef = useRef(0);

  useEffect(() => {
    // Generate or retrieve permanent device ID
    const deviceId = getOrCreateDeviceId();

    // Capture referrer (filtering out internal self-referrals from our own domain)
    const rawReferrer = typeof document !== "undefined" ? document.referrer : "";
    let referrer = "Direct";
    if (rawReferrer) {
      try {
        const refUrl = new URL(rawReferrer);
        const currentHost = typeof window !== "undefined" ? window.location.hostname.toLowerCase() : "";
        const refHost = refUrl.hostname.toLowerCase();
        const isInternal =
          refHost === currentHost ||
          refHost.endsWith(".braille-recognition.com") ||
          refHost === "braille-recognition.com" ||
          refHost.includes("localhost") ||
          refHost.includes("127.0.0.1") ||
          refHost.endsWith(".vercel.app");

        if (!isInternal) {
          referrer = rawReferrer;
        }
      } catch {
        referrer = "Direct";
      }
    }
    const searchParams = typeof window !== "undefined" ? window.location.search : "";
    const urlParams = new URLSearchParams(searchParams);
    const utmSource = urlParams.get("utm_source") || "";
    const utmMedium = urlParams.get("utm_medium") || "";
    const utmCampaign = urlParams.get("utm_campaign") || "";
    const refParam = urlParams.get("ref") || "";

    const campaign = utmCampaign || refParam || (utmSource ? `${utmSource}/${utmMedium}` : "");

    // 1. Initial Page View Tracking with acquisition data
    fetch("/api/track", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-device-id": deviceId,
      },
      body: JSON.stringify({
        deviceId,
        referrer,
        campaign,
      }),
      keepalive: true,
    }).catch(() => {});

    // 2. Heartbeat Ping every 25 seconds for Live Online status and session duration
    const interval = setInterval(() => {
      sessionSecondsRef.current += 25;
      fetch("/api/track", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "x-device-id": deviceId,
        },
        body: JSON.stringify({
          deviceId,
          heartbeat: true,
          durationSeconds: sessionSecondsRef.current,
        }),
        keepalive: true,
      }).catch(() => {});
    }, 25000);

    return () => clearInterval(interval);
  }, []);

  return null;
}
