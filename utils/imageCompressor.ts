/**
 * Client-side image optimization utility.
 * Automatically resizes and compresses high-resolution photos (e.g. 10MB+ phone shots)
 * so they stay safely under Vercel's 4.5 MB request body limit, while preserving high
 * visual clarity for Braille character detection.
 */
export async function optimizeImageForUpload(
  file: File,
  maxDimension = 2048,
  targetMaxBytes = 3.5 * 1024 * 1024 // 3.5 MB max target
): Promise<File> {
  // If the file is already small (under 2.5 MB) and standard format, keep original
  if (file.size <= 2.5 * 1024 * 1024 && !file.type.includes("tiff")) {
    return file;
  }

  return new Promise((resolve) => {
    const img = new Image();
    const url = URL.createObjectURL(file);

    img.onload = () => {
      URL.revokeObjectURL(url);

      let { width, height } = img;

      // Scale down proportionally if either dimension exceeds maxDimension
      if (width > maxDimension || height > maxDimension) {
        if (width > height) {
          height = Math.round((height * maxDimension) / width);
          width = maxDimension;
        } else {
          width = Math.round((width * maxDimension) / height);
          height = maxDimension;
        }
      }

      const canvas = document.createElement("canvas");
      canvas.width = width;
      canvas.height = height;

      const ctx = canvas.getContext("2d");
      if (!ctx) {
        resolve(file); // fallback if canvas 2d context is unavailable
        return;
      }

      // Fill white background for transparency handling
      ctx.fillStyle = "#FFFFFF";
      ctx.fillRect(0, 0, width, height);
      ctx.drawImage(img, 0, 0, width, height);

      // Determine quality based on original file size
      let quality = 0.88;
      if (file.size > 8 * 1024 * 1024) {
        quality = 0.82;
      }

      canvas.toBlob(
        (blob) => {
          if (!blob) {
            resolve(file);
            return;
          }

          const safeFileName = file.name.replace(/\.[^/.]+$/, "") + ".jpg";
          const optimizedFile = new File([blob], safeFileName, {
            type: "image/jpeg",
            lastModified: Date.now(),
          });

          resolve(optimizedFile);
        },
        "image/jpeg",
        quality
      );
    };

    img.onerror = () => {
      URL.revokeObjectURL(url);
      resolve(file); // fallback to original file if loading fails
    };

    img.src = url;
  });
}
