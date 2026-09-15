import { GbrainKnowledgeGraphVisualizer } from "@/components/features/ckg-view";

export default function CkgPage() {
  return (
    <main className="h-[calc(100dvh-72px)] w-full overflow-hidden">
      <GbrainKnowledgeGraphVisualizer />
    </main>
  );
}
