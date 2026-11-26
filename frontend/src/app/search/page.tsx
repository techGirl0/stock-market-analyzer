import { Suspense } from "react";
import { LoadingState } from "@/components/feedback/LoadingState";
import { SearchView } from "./SearchView";

// SearchView reads the ?q= query from the URL, which Next.js requires
// to be wrapped in a Suspense boundary.
export default function SearchPage() {
  return (
    <Suspense fallback={<LoadingState label="Loading search…" />}>
      <SearchView />
    </Suspense>
  );
}
