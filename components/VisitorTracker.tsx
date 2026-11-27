"use client";

import { useEffect, useRef } from "react";
import { getOrCreateDeviceId } from "@/lib/clientDevice";

export function VisitorTracker() {
  const sessionSecondsRef = useRef(0);

  useEffect(() => {
    // Generate or retrieve permanent device ID
    const deviceId = getOrCreateDeviceId();

    // Capture referrer and UTM campaign info
    const referrer = typeof document !== "undefined" ? document.referrer || "Direct" : "Direct";
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
