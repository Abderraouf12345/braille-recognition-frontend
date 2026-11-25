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

export interface ScanSession {
  metaPath: string;
  payload: any;
}

/**
 * Uploads initial scan image + starting metadata to Supabase.
 * Returns a ScanSession object so results can be updated once translation finishes.
 */
export async function saveUserScanToSupabase(
  file: File,
  meta: ScanUploadMetadata
): Promise<ScanSession | null> {
  try {
    const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
    const randomId = Math.random().toString(36).substring(2, 8);
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
    const payload = {
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

    const metaBlob = new Blob([JSON.stringify(payload, null, 2)], {
      type: "application/json",
    });

    await supabase.storage
      .from("braille-uploads")
      .upload(metaPath, metaBlob, {
        cacheControl: "3600",
        upsert: true,
        contentType: "application/json",
      });

    return { metaPath, payload };
  } catch (err) {
    console.warn("[Supabase] Non-blocking scan save error:", err);
    return null;
  }
}

/**
 * Updates the JSON metadata file in Supabase with the final extracted Braille and translation
 */
export async function updateScanResultsInSupabase(
  session: ScanSession,
  braille: string,
  translation: string
) {
  try {
    session.payload.results = {
      braille: braille || session.payload.results?.braille || "",
      translation: translation || session.payload.results?.translation || "",
    };

    const updatedBlob = new Blob([JSON.stringify(session.payload, null, 2)], {
      type: "application/json",
    });

    await supabase.storage
      .from("braille-uploads")
      .upload(session.metaPath, updatedBlob, {
        cacheControl: "3600",
        upsert: true, // Overwrites with final results
        contentType: "application/json",
      });
  } catch (err) {
    console.warn("[Supabase] Non-blocking metadata update error:", err);
  }
}
