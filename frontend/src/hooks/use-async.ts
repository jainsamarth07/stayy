/**
 * @module useAsync
 * @description React hook that wraps an async function with loading/success/error state tracking.
 */
import { useState, useCallback } from "react";

/** Possible states of an async operation. */
type Status = "idle" | "loading" | "success" | "error";

/** Internal state shape for the `useAsync` hook. */
interface AsyncState<T> {
  data: T | null;
  status: Status;
  error: string | null;
}

/**
 * Wraps an async function and tracks loading / success / error states.
 * Usage: const { run, data, status, error } = useAsync(fetchProperties);
 */
export function useAsync<T, A extends unknown[] = []>(
  asyncFn: (...args: A) => Promise<T>
) {
  const [state, setState] = useState<AsyncState<T>>({
    data: null,
    status: "idle",
    error: null,
  });

  const run = useCallback(
    async (...args: A) => {
      setState({ data: null, status: "loading", error: null });
      try {
        const data = await asyncFn(...args);
        setState({ data, status: "success", error: null });
        return data;
      } catch (err: unknown) {
        const message = err instanceof Error ? err.message : "An error occurred";
        setState({ data: null, status: "error", error: message });
        throw err;
      }
    },
    [asyncFn]
  );

  const reset = useCallback(() => {
    setState({ data: null, status: "idle", error: null });
  }, []);

  return { ...state, run, reset, isLoading: state.status === "loading" };
}
