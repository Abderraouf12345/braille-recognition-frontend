import { NextResponse } from "next/server";
import { recordVisitor } from "@/lib/tracker";

export async function POST(request: Request) {
  const result = await recordVisitor(request.headers);
  return NextResponse.json({ status: "ok", data: result });
}

export async function GET(request: Request) {
  const result = await recordVisitor(request.headers);
  return NextResponse.json({ status: "ok", data: result });
}
