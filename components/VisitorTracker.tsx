"use client";

import { useEffect } from "react";

export function VisitorTracker() {
  useEffect(() => {
    // Send a silent visit ping on page load
    fetch("/api/track", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      keepalive: true,
    }).catch(() => {});
  }, []);

  return null;
}
