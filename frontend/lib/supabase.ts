import { createClient } from "@supabase/supabase-js";

const SUPABASE_URL =
  process.env.NEXT_PUBLIC_SUPABASE_URL ||
  "https://dihqttparfhiodwppsco.supabase.co";

const SUPABASE_KEY =
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ||
  "sb_publishable_7NV7M1N--rG1oDeHwo8Ojw_xLQ9NuV7";

export const supabase = createClient(SUPABASE_URL, SUPABASE_KEY);

export interface ScanUploadMetadata {
  deviceId?: string;
  language: string;
  lightAngle: number;
  corners: { x: number; y: number }[];
  brailleResult?: string;
  translationResult?: string;
}

/**
 * Uploads an anonymous user scan (image + JSON metadata) to Supabase Storage
 * for dataset collection. Fails silently/non-blockingly so user experience is never interrupted.
 */
export async function saveUserScanToSupabase(
  file: File,
  meta: ScanUploadMetadata
): Promise<string | null> {
  try {
    const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
    const randomId = Math.random().toString(36).substring(2, 8);
    const sanitizedName = file.name.replace(/[^a-zA-Z0-9.-]/g, "_");
    const fileExt = file.name.split(".").pop() || "jpg";

    const baseFileName = `${timestamp}_${randomId}`;
    const imagePath = `scans/${baseFileName}.${fileExt}`;
    const metaPath = `metadata/${baseFileName}.json`;

    // 1. Upload original image to 'braille-uploads' bucket
    const { error: uploadError } = await supabase.storage
      .from("braille-uploads")
      .upload(imagePath, file, {
        cacheControl: "3600",
        upsert: false,
        contentType: file.type || "image/jpeg",
      });

    if (uploadError) {
      console.warn("[Supabase] Image upload notice:", uploadError.message);
      return null;
    }

    // 2. Upload corresponding scan metadata JSON
    const metadataPayload = {
      imagePath,
      fileName: file.name,
      fileSize: file.size,
      uploadedAt: new Date().toISOString(),
      deviceId: meta.deviceId || "unknown",
      language: meta.language,
      lightAngle: meta.lightAngle,
      corners: meta.corners,
      results: {
        braille: meta.brailleResult || "",
        translation: meta.translationResult || "",
      },
    };

    const metaBlob = new Blob([JSON.stringify(metadataPayload, null, 2)], {
      type: "application/json",
    });

    await supabase.storage
      .from("braille-uploads")
      .upload(metaPath, metaBlob, {
        cacheControl: "3600",
        upsert: false,
        contentType: "application/json",
      });

    return imagePath;
  } catch (err) {
    console.warn("[Supabase] Non-blocking scan save error:", err);
    return null;
  }
}
