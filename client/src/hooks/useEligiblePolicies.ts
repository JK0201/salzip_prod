import { useEffect, useState } from 'react';
import { fetchEligiblePolicies, type EligiblePolicy, type UserCriteria } from '@/api/policiesEligible';
import { useSessionStore } from '@/store/useSessionStore';

export function useEligiblePolicies() {
  const [data, setData] = useState<EligiblePolicy[] | null>(null);
  const [criteria, setCriteria] = useState<UserCriteria | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const [needsLogin, setNeedsLogin] = useState(false);
  const token = useSessionStore((s) => s.token);

  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    fetchEligiblePolicies()
      .then((res) => {
        if (cancelled) return;
        setData(res.policies);
        setCriteria(res.criteria);
      })
      .catch((e) => {
        if (cancelled) return;
        const status = (e as { response?: { status?: number } })?.response?.status;
        if (status === 401) setNeedsLogin(true);
        else setError(e as Error);
      });
    return () => {
      cancelled = true;
    };
  }, [token]);

  return {
    data,
    criteria,
    error,
    needsLogin,
    isLoading: data === null && error === null && !needsLogin,
  };
}
