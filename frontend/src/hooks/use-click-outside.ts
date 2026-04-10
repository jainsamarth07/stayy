/**
 * @module useClickOutside
 * @description React hook for detecting clicks outside a referenced element.
 */
import { useEffect } from "react";

/**
 * Detect clicks outside a referenced element.
 * Useful for closing dropdowns, modals, and popovers.
 */
export function useClickOutside(
  ref: React.RefObject<HTMLElement | null>,
  handler: () => void
) {
  useEffect(() => {
    const listener = (e: MouseEvent | TouchEvent) => {
      if (!ref.current || ref.current.contains(e.target as Node)) return;
      handler();
    };

    document.addEventListener("mousedown", listener);
    document.addEventListener("touchstart", listener);
    return () => {
      document.removeEventListener("mousedown", listener);
      document.removeEventListener("touchstart", listener);
    };
  }, [ref, handler]);
}
