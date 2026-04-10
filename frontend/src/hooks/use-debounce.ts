/**
 * @module useDebounce
 * @description React hook that debounces a rapidly-changing value.
 */
import { useEffect, useState } from "react";

/**
 * Debounce a value by a given delay (ms).
 * Useful for search inputs to avoid firing API calls on every keystroke.
 */
export function useDebounce<T>(value: T, delay = 400): T {
  const [debounced, setDebounced] = useState(value);

  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);

  return debounced;
}
