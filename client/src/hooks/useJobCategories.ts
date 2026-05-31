import { useEffect, useState } from 'react';
import { fetchJobCategories, type JobCategory } from '@/api/jobCategories';

export function useJobCategories() {
  const [data, setData] = useState<JobCategory[] | null>(null);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchJobCategories()
      .then((res) => {
        if (!cancelled) setData(res);
      })
      .catch((e) => {
        if (!cancelled) setError(e as Error);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return { data, error, isLoading: data === null && error === null };
}
