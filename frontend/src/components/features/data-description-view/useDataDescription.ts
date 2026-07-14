import { useState, useCallback } from "react";

export function useDataDescription() {
  const [generatingColumn, setGeneratingColumn] = useState<string | null>(null);
  const [generatingAll, setGeneratingAll] = useState(false);

  const updateDescription = useCallback((column: string, value: string) => {
  }, []);

  const generateOne = useCallback(
    async (columnName: string, type: string) => {
    },
    []
  );

  const generateAll = useCallback(async () => {
  }, []);

  return {
    datasetId: null,
    setDatasetId: () => {},
    descriptions: {} as Record<string, string>,
    generatingColumn,
    generatingAll,
    dataset: null as any,
    filledCount: 0,
    updateDescription,
    generateOne,
    generateAll,
  };
}
