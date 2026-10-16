"use client";

import { useEffect } from "react";

export function VisitorTracker() {
  useEffect(() => {
    // Only track once per page session to avoid unnecessary spam
    const sessionKey = "braille_tracked_session";
    const alreadyTracked = sessionStorage.getItem(sessionKey);

    if (!alreadyTracked) {
      fetch("/api/track", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        keepalive: true,
      })
        .then((res) => {
          if (res.ok) {
            sessionStorage.setItem(sessionKey, "true");
          }
        })
        .catch((err) => {
          console.debug("Tracking ping skipped:", err);
        });
    }
  }, []);

  return null;
}
