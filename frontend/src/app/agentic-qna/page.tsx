import { AgenticQnaView } from "@/components/features/agentic-qna-view";
import { Suspense } from "react";

export default function AgenticQnaPage() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <AgenticQnaView />
    </Suspense>
  );
}


