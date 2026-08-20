import { renderHook, waitFor, act } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { useAsync } from "../useAsync";

describe("useAsync", () => {
  it("starts in loading state", () => {
    const { result } = renderHook(() =>
      useAsync(() => new Promise(() => {}), [])
    );
    expect(result.current.loading).toBe(true);
    expect(result.current.data).toBeNull();
    expect(result.current.error).toBeNull();
  });

  it("resolves with data on success", async () => {
    const { result } = renderHook(() =>
      useAsync(async () => "hello", [])
    );

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.data).toBe("hello");
    expect(result.current.error).toBeNull();
  });

  it("captures error on failure", async () => {
    const { result } = renderHook(() =>
      useAsync(async () => { throw new Error("boom"); }, [])
    );

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.data).toBeNull();
    expect(result.current.error).toBe("boom");
  });

  it("captures non-Error exceptions as strings", async () => {
    const { result } = renderHook(() =>
      useAsync(async () => { throw "string error"; }, [])
    );

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.error).toBe("string error");
  });

  it("reload re-fetches data", async () => {
    let counter = 0;
    const { result } = renderHook(() =>
      useAsync(async () => ++counter, [])
    );

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.data).toBe(1);

    await act(async () => {
      await result.current.reload();
    });

    expect(result.current.data).toBe(2);
  });

  it("re-fetches when deps change", async () => {
    let lastId = 0;
    const fetcher = (id: number) =>
      async () => { lastId = id; return `item-${id}`; };

    const { result, rerender } = renderHook(
      ({ id }) => useAsync(fetcher(id), [id]),
      { initialProps: { id: 1 } }
    );

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.data).toBe("item-1");

    rerender({ id: 2 });

    await waitFor(() => expect(result.current.data).toBe("item-2"));
  });
});
