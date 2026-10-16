/**
 * Detects browser name and OS from a User-Agent string.
 * Returns a clean, human-readable browser name.
 */
export function detectBrowser(ua: string): string {
  if (!ua || ua === "Unknown") return "Unknown";

  // ── Order matters! More specific checks must come first ──

  // Bots & Crawlers
  if (/Googlebot|bingbot|DuckDuckBot|Baiduspider|YandexBot|Slurp|crawler|spider|bot/i.test(ua)) {
    return "Bot / Crawler";
  }

  // Samsung Internet (must be before Chrome check since it also contains Chrome)
  if (/SamsungBrowser/i.test(ua)) {
    const v = ua.match(/SamsungBrowser\/([\d.]+)/);
    return `Samsung Internet${v ? " " + v[1].split(".")[0] : ""}`;
  }

  // Edge (Chromium-based Edge — must be before Chrome)
  if (/Edg\//i.test(ua)) {
    const v = ua.match(/Edg\/([\d.]+)/);
    return `Edge${v ? " " + v[1].split(".")[0] : ""}`;
  }

  // Opera (OPR — must be before Chrome)
  if (/OPR\//i.test(ua)) {
    const v = ua.match(/OPR\/([\d.]+)/);
    return `Opera${v ? " " + v[1].split(".")[0] : ""}`;
  }

  // Brave (identified via its own header since its UA mimics Chrome)
  // Note: Brave sends a sec-ch-ua header but on server we can check
  if (/Brave/i.test(ua)) {
    return "Brave";
  }

  // Chrome / Chromium
  if (/Chrome\/([\d.]+)/.test(ua) && !/Chromium/.test(ua)) {
    const v = ua.match(/Chrome\/([\d.]+)/);
    // Check if it is a WebView (In-App browser)
    if (/wv\)/.test(ua) || /Version\/[\d.]+ Chrome\/[\d.]+ Mobile/.test(ua)) {
      return "In-App WebView (Chrome)";
    }
    return `Chrome${v ? " " + v[1].split(".")[0] : ""}`;
  }

  // Chromium
  if (/Chromium\/([\d.]+)/.test(ua)) {
    const v = ua.match(/Chromium\/([\d.]+)/);
    return `Chromium${v ? " " + v[1].split(".")[0] : ""}`;
  }

  // Firefox
  if (/Firefox\/([\d.]+)/.test(ua)) {
    const v = ua.match(/Firefox\/([\d.]+)/);
    // Firefox Focus on mobile
    if (/Focus/.test(ua)) return "Firefox Focus";
    return `Firefox${v ? " " + v[1].split(".")[0] : ""}`;
  }

  // Safari (must be after Chrome since Chrome UA also includes "Safari")
  if (/Safari\/([\d.]+)/.test(ua) && /Version\/([\d.]+)/.test(ua)) {
    const v = ua.match(/Version\/([\d.]+)/);
    return `Safari${v ? " " + v[1].split(".")[0] : ""}`;
  }

  // Internet Explorer / Edge Legacy
  if (/MSIE |Trident\//.test(ua)) {
    return "Internet Explorer";
  }

  // UC Browser
  if (/UCBrowser/i.test(ua)) {
    return "UC Browser";
  }

  // WhatsApp In-App Browser
  if (/WhatsApp/i.test(ua)) {
    return "WhatsApp Browser";
  }

  // Instagram In-App Browser
  if (/Instagram/i.test(ua)) {
    return "Instagram Browser";
  }

  // Facebook In-App Browser
  if (/FBAN|FBAV/i.test(ua)) {
    return "Facebook Browser";
  }

  return "Other";
}

/**
 * Detects if the User-Agent is from a mobile device.
 */
export function isMobileUA(ua: string): boolean {
  return /mobile|android|iphone|ipad|tablet|phone/i.test(ua);
}

/**
 * Gets the OS name from a User-Agent string.
 */
export function detectOS(ua: string): string {
  if (!ua || ua === "Unknown") return "Unknown";

  if (/Android/i.test(ua)) {
    const v = ua.match(/Android ([\d.]+)/);
    return `Android${v ? " " + v[1].split(".")[0] : ""}`;
  }
  if (/iPhone|iPad|iPod/i.test(ua)) {
    const v = ua.match(/OS ([\d_]+)/);
    return `iOS${v ? " " + v[1].replace(/_/g, ".").split(".")[0] : ""}`;
  }
  if (/Windows NT/i.test(ua)) {
    const versions: Record<string, string> = {
      "10.0": "Windows 10/11",
      "6.3": "Windows 8.1",
      "6.2": "Windows 8",
      "6.1": "Windows 7",
    };
    const v = ua.match(/Windows NT ([\d.]+)/);
    return v ? (versions[v[1]] || `Windows NT ${v[1]}`) : "Windows";
  }
  if (/Mac OS X/i.test(ua)) {
    return "macOS";
  }
  if (/Linux/i.test(ua)) {
    return "Linux";
  }
  if (/CrOS/i.test(ua)) {
    return "ChromeOS";
  }

  return "Unknown OS";
}
