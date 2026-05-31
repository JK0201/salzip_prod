import { useEffect, useState } from 'react';
import { fetchLifestyleTags, type LifestyleTag } from '@/api/lifestyleTags';

export function useLifestyleTags() {
  const [data, setData] = useState<LifestyleTag[] | null>(null);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchLifestyleTags()
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
