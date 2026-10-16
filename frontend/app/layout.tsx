import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { Analytics } from "@vercel/analytics/react";
import { VisitorTracker } from "@/components/VisitorTracker";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Braille Recognition — AI-Powered Braille Translator",
  description:
    "Upload a Braille image and get instant translation to Arabic, French, English, Russian, Chinese and more. Powered by deep learning.",
  openGraph: {
    title: "Braille Recognition — AI Translator",
    description:
      "AI-powered Braille recognition and multi-language translation. Upload an image, set the light angle, and translate instantly.",
    url: "https://braille-recognition.com",
    siteName: "Braille Recognition",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "Braille Recognition — AI Translator",
    description: "AI-powered Braille recognition and multi-language translation.",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">
        <VisitorTracker />
        {children}
        <Analytics />
      </body>
    </html>
  );
}
