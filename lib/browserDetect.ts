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

export type VisitorType = "human" | "cloud_bot" | "scanner" | "crawler";

export interface VisitorClassification {
  type: VisitorType;
  isHuman: boolean;
  label: string;
  badgeClass: string;
  icon: string;
  reason: string;
}

/**
 * Checks if an IP falls into known cloud datacenter / hosting ranges.
 */
function isDatacenterIp(ip: string): { isDc: boolean; provider?: string } {
  if (!ip) return { isDc: false };

  // AWS EC2 IP ranges (common blocks)
  if (
    /^(13\.(5[2-9]|6[0-9]|11[0-9]|12[0-9]|20[0-9]|21[0-9]|22[0-9]|24[0-9]))\./.test(ip) ||
    /^(54\.(1[4-9][0-9]|2[0-4][0-9]))\./.test(ip) ||
    /^(52\.(0|[1-9][0-9]|1[0-9][0-9]|2[0-1][0-9]|22[0-3]))\./.test(ip) ||
    /^(3\.(0|[89]|1[0-9]|2[0-7]))\./.test(ip) ||
    /^(18\.(1[89]|2[0-3][0-9]))\./.test(ip) ||
    /^(34\.(19[2-9]|2[0-4][0-9]|25[0-5]))\./.test(ip) ||
    /^(35\.(15[3-9]|1[6-7][0-9]|18[0-3]))\./.test(ip)
  ) {
    return { isDc: true, provider: "AWS Cloud" };
  }

  // Google Cloud (GCP)
  if (
    /^(34\.(6[4-9]|[7-9][0-9]|1[0-1][0-9]|12[0-7]))\./.test(ip) ||
    /^(35\.(18[4-9]|19[0-9]|2[0-3][0-9]|24[0-7]))\./.test(ip)
  ) {
    return { isDc: true, provider: "Google Cloud" };
  }

  // Microsoft Azure
  if (
    /^(20\.(3[6-9]|[4-9][0-9]|1[0-8][0-9]|19[0-1]))\./.test(ip) ||
    /^(40\.(7[4-9]|[8-9][0-9]|1[0-1][0-9]|12[0-5]))\./.test(ip) ||
    /^(51\.(1[0-4][0-9]|15[0-3]))\./.test(ip)
  ) {
    return { isDc: true, provider: "Microsoft Azure" };
  }

  // DigitalOcean
  if (
    /^(138\.68|142\.93|159\.65|159\.89|167\.99|178\.62|188\.166|206\.189)\./.test(ip)
  ) {
    return { isDc: true, provider: "DigitalOcean" };
  }

  // Known scanner/hosting blocks (e.g. TerraTransit/Packethub 185.197.x.x, Censys, Shodan, etc.)
  if (/^(185\.197\.|198\.235\.|162\.142\.|167\.248\.|74\.120\.)/.test(ip)) {
    return { isDc: true, provider: "Hosting / Scanner Network" };
  }

  return { isDc: false };
}

/**
 * Classifies a visitor record into Human, Cloud Bot, Scanner, or Search Crawler.
 */
export function classifyVisitor(record: {
  deviceId?: string;
  ip?: string;
  userAgent?: string;
  browser?: string;
  os?: string;
}): VisitorClassification {
  const ua = record.userAgent || "";
  const ip = record.ip || "";
  const devId = record.deviceId || "";
  const os = record.os || "";

  // 1. Explicit search engine or SEO crawler in User-Agent
  if (/Googlebot|bingbot|DuckDuckBot|Baiduspider|YandexBot|Slurp/i.test(ua)) {
    return {
      type: "crawler",
      isHuman: false,
      label: "Search Crawler",
      badgeClass: "bg-amber-500/10 text-amber-400 border-amber-500/20",
      icon: "🔍",
      reason: "Verified search engine indexer",
    };
  }

  // 2. Generic bot/spider or script tool (curl, python, postman, headless)
  if (
    /bot|spider|crawler|playwright|puppeteer|selenium|headless|phantomjs|curl|wget|python|postman|go-http|httpclient/i.test(
      ua
    )
  ) {
    return {
      type: "scanner",
      isHuman: false,
      label: "Automated Bot",
      badgeClass: "bg-rose-500/10 text-rose-400 border-rose-500/20",
      icon: "🤖",
      reason: "Automated script or scraper tool detected in User-Agent",
    };
  }

  // 3. No Client JavaScript Execution (Legacy IP fallback / raw HTTP request)
  if (!devId || devId.startsWith("legacy_") || devId.toLowerCase().includes("web visitor")) {
    return {
      type: "scanner",
      isHuman: false,
      label: "HTTP Scanner",
      badgeClass: "bg-orange-500/10 text-orange-400 border-orange-500/20",
      icon: "🕷️",
      reason: "Raw HTTP request without client JavaScript or cookie support",
    };
  }

  // 4. Cloud Datacenter check (AWS, GCP, Azure, etc.)
  const dcInfo = isDatacenterIp(ip);
  if (dcInfo.isDc) {
    return {
      type: "cloud_bot",
      isHuman: false,
      label: `${dcInfo.provider || "Cloud"} Probe`,
      badgeClass: "bg-purple-500/10 text-purple-400 border-purple-500/20",
      icon: "☁️",
      reason: `Automated traffic originating from ${dcInfo.provider || "cloud datacenter"}`,
    };
  }

  // 5. Headless Linux Chrome check (automated worker instance)
  if (/Linux/i.test(os) && /Chrome\/1[4-9][0-9]/i.test(ua)) {
    return {
      type: "cloud_bot",
      isHuman: false,
      label: "Cloud Probe",
      badgeClass: "bg-purple-500/10 text-purple-400 border-purple-500/20",
      icon: "☁️",
      reason: "Automated Linux Chromium worker instance",
    };
  }

  // 6. Authentic human visitor
  return {
    type: "human",
    isHuman: true,
    label: "Real Visitor",
    badgeClass: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
    icon: "👤",
    reason: "Residential/Mobile ISP with interactive browser sandbox",
  };
}
