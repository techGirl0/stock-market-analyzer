import { Suspense } from "react";
import { LoadingState } from "@/components/feedback/LoadingState";
import { BriefView } from "./BriefView";

interface BriefPageProps {
  params: Promise<{ symbol: string }>;
}

export default async function BriefPage({ params }: BriefPageProps) {
  const { symbol } = await params;
  // BriefView reads ?fixture= from the URL, which needs a Suspense boundary.
  return (
    <Suspense fallback={<LoadingState label="Loading…" />}>
      <BriefView symbol={decodeURIComponent(symbol).toUpperCase()} />
    </Suspense>
  );
}
