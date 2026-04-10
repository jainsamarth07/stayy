/**
 * @module useMediaQuery
 * @description React hook that subscribes to a CSS media query and returns a boolean.
 * SSR-safe: returns false during server render, syncs on first client paint.
 */
import { useCallback, useSyncExternalStore } from "react";

/**
 * Tracks a CSS media query and returns whether it currently matches.
 * Example: const isMobile = useMediaQuery("(max-width: 768px)");
 */
export function useMediaQuery(query: string): boolean {
  const subscribe = useCallback(
    (callback: () => void) => {
      const mql = window.matchMedia(query);
      mql.addEventListener("change", callback);
      return () => mql.removeEventListener("change", callback);
    },
    [query]
  );

  const getSnapshot = () => window.matchMedia(query).matches;
  const getServerSnapshot = () => false;

  return useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);
}
