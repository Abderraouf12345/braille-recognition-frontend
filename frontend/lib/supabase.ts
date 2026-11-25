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
  userFolder: string;
  baseFileName: string;
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

    // Clean user device directory name: e.g. "users/dev_32ffade6-2a8f-4afd-81f2-9a583c2d7b62"
    const userFolder = meta.deviceId
      ? `users/${meta.deviceId.replace(/[^a-zA-Z0-9_-]/g, "_")}`
      : "users/anonymous";

    const baseFileName = `${timestamp}_${randomId}`;
    const imagePath = `${userFolder}/scans/${baseFileName}.${fileExt}`;
    const metaPath = `${userFolder}/metadata/${baseFileName}.json`;

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

    // 2. Upload initial metadata JSON
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
        braille: meta.brailleResult ? meta.brailleResult.split("\n") : [],
        translation: meta.translationResult ? meta.translationResult.split("\n") : [],
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

    return { userFolder, baseFileName, metaPath, payload };
  } catch (err) {
    console.warn("[Supabase] Non-blocking scan save error:", err);
    return null;
  }
}

/**
 * Updates the JSON metadata file and creates human-readable text files
 * (result.txt, braille.txt, translation.txt) in the user's folder.
 */
export async function updateScanResultsInSupabase(
  session: ScanSession,
  braille: string,
  translation: string
) {
  try {
    const cleanBraille = braille || "";
    const cleanTranslation = translation || "";

    // 1. In JSON, format as line-by-line arrays so \n renders cleanly
    session.payload.results = {
      braille: cleanBraille.split("\n"),
      translation: cleanTranslation.split("\n"),
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

    // 2. Also save clean readable .txt files directly alongside in results/
    // Explicitly set UTF-8 charset in contentType header so browsers & Supabase serve it with proper encoding
    const combinedText = `=== BRAILLE OUTPUT ===\n${cleanBraille}\n\n=== TRANSLATION (${session.payload.language || "text"}) ===\n${cleanTranslation}\n`;

    const txtPath = `${session.userFolder}/results/${session.baseFileName}.txt`;
    const txtBlob = new Blob([new Uint8Array([0xef, 0xbb, 0xbf]), combinedText], {
      type: "text/plain;charset=utf-8",
    });

    await supabase.storage
      .from("braille-uploads")
      .upload(txtPath, txtBlob, {
        cacheControl: "3600",
        upsert: true,
        contentType: "text/plain; charset=utf-8",
      });
  } catch (err) {
    console.warn("[Supabase] Non-blocking metadata update error:", err);
  }
}
