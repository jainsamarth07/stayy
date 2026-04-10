/**
 * @module useInfiniteScroll
 * @description React hook that triggers a callback when a sentinel element scrolls into view.
 */
import { useEffect, useRef, useCallback } from "react";

/**
 * Calls `onLoadMore` when the sentinel element becomes visible in the viewport.
 * Attach the returned `ref` to a bottom-of-list sentinel element.
 */
export function useInfiniteScroll(
  onLoadMore: () => void,
  { enabled = true, rootMargin = "200px" } = {}
) {
  const sentinelRef = useRef<HTMLDivElement | null>(null);

  const stableCallback = useCallback(onLoadMore, [onLoadMore]);

  useEffect(() => {
    if (!enabled || !sentinelRef.current) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) stableCallback();
      },
      { rootMargin }
    );

    observer.observe(sentinelRef.current);
    return () => observer.disconnect();
  }, [enabled, rootMargin, stableCallback]);

  return sentinelRef;
}
