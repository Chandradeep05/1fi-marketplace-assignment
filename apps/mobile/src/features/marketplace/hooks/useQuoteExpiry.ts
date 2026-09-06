import { useEffect, useState } from 'react';

export const useQuoteExpiry = (expiresAt: string | null | undefined): boolean => {
  const [isExpired, setIsExpired] = useState(false);

  useEffect(() => {
    if (!expiresAt) {
      setIsExpired(false);
      return;
    }

    const checkExpiry = () => {
      const expiryMs = new Date(expiresAt).getTime();
      const nowMs = Date.now();
      const diff = expiryMs - nowMs;
      if (diff <= 0) {
        setIsExpired(true);
        return 0;
      }
      setIsExpired(false);
      return diff;
    };

    const diff = checkExpiry();
    if (diff <= 0) return;

    const timer = setTimeout(() => {
      setIsExpired(true);
    }, diff);

    return () => clearTimeout(timer);
  }, [expiresAt]);

  return isExpired;
};
