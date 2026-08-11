import { NextRequest, NextResponse } from "next/server";

const API_URL = process.env.NEXT_PUBLIC_API_URL!;

export async function POST(req: NextRequest) {
  const body = await req.json();

  const res = await fetch(`${API_URL}/index`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ repo_name: body.repo }),
  });

  const data = await res.json();
  if (!res.ok) return NextResponse.json(data, { status: res.status });

 return NextResponse.json({
  filesIndexed: data.file_count ?? 0,
  chunksCreated: data.chunk_count ?? 0,
});
}