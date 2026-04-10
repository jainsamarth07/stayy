/** Unit tests for the {@link useAsync} hook. */
import { describe, it, expect, vi } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useAsync } from "@/hooks/use-async";

describe("useAsync", () => {
  it("starts in idle state", () => {
    const fn = vi.fn().mockResolvedValue("data");
    const { result } = renderHook(() => useAsync(fn));
    
    expect(result.current.status).toBe("idle");
    expect(result.current.data).toBeNull();
    expect(result.current.error).toBeNull();
    expect(result.current.isLoading).toBe(false);
  });

  it("transitions to loading then success", async () => {
    const fn = vi.fn().mockResolvedValue("result");
    const { result } = renderHook(() => useAsync(fn));

    await act(async () => {
      await result.current.run();
    });

    expect(result.current.status).toBe("success");
    expect(result.current.data).toBe("result");
    expect(result.current.isLoading).toBe(false);
  });

  it("transitions to error on failure", async () => {
    const fn = vi.fn().mockRejectedValue(new Error("fail"));
    const { result } = renderHook(() => useAsync(fn));

    await act(async () => {
      try {
        await result.current.run();
      } catch {
        // expected
      }
    });

    expect(result.current.status).toBe("error");
    expect(result.current.error).toBe("fail");
    expect(result.current.data).toBeNull();
  });

  it("resets state", async () => {
    const fn = vi.fn().mockResolvedValue("data");
    const { result } = renderHook(() => useAsync(fn));

    await act(async () => {
      await result.current.run();
    });
    expect(result.current.data).toBe("data");

    act(() => {
      result.current.reset();
    });

    expect(result.current.status).toBe("idle");
    expect(result.current.data).toBeNull();
  });
});
