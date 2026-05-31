import { useEffect, useState } from 'react';
import { fetchPoliciesPreview, type PolicyPreviewResponse } from '@/api/policies';

const DEBOUNCE_MS = 500;

export function usePoliciesPreview(depositWan: number, monthlyRentWan: number) {
  const [data, setData] = useState<PolicyPreviewResponse | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setIsLoading(true);
    const timer = setTimeout(() => {
      fetchPoliciesPreview({
        deposit_max_wan: depositWan,
        monthly_rent_max_wan: monthlyRentWan,
      })
        .then((res) => {
          if (cancelled) return;
          setData(res);
          setError(null);
        })
        .catch((e) => {
          if (cancelled) return;
          setError(e as Error);
        })
        .finally(() => {
          if (!cancelled) setIsLoading(false);
        });
    }, DEBOUNCE_MS);

    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [depositWan, monthlyRentWan]);

  return { data, error, isLoading };
}
