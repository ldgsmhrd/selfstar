import { useCallback, useEffect, useState } from 'react';
import { getHealth } from '../api/client.js';

export function useHealth(auto = true) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const h = await getHealth();
      setData(h);
    } catch (e) {
      setError(e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (auto) refresh();
  }, [auto, refresh]);

  return { data, loading, error, refresh };
}
