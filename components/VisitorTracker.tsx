"use client";

import { useEffect } from "react";
import { getOrCreateDeviceId } from "@/lib/clientDevice";

export function VisitorTracker() {
  useEffect(() => {
    // Generate or retrieve permanent device ID
    const deviceId = getOrCreateDeviceId();

    // Send tracking ping with device ID
    fetch("/api/track", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-device-id": deviceId,
      },
      body: JSON.stringify({ deviceId }),
      keepalive: true,
    }).catch(() => {});
  }, []);

  return null;
}
