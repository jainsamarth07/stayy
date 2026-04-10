/**
 * @module Pagination
 * @description Page navigation component with ellipsis for large page ranges,
 * plus a `PageLoading` helper for full-screen loading states.
 */
import { Spinner } from "./index";

interface PaginationProps {
  page: number;
  totalPages: number;
  onPageChange: (page: number) => void;
}

/**
 * Renders a pagination bar with Previous/Next buttons and page number buttons.
 * Automatically inserts ellipsis when the total page count is large.
 *
 * @param props - Pagination state.
 * @param props.page - The currently active page (1-based).
 * @param props.totalPages - Total number of pages.
 * @param props.onPageChange - Callback with the selected page number.
 * @returns The pagination `<nav>` element.
 */
export function Pagination({ page, totalPages, onPageChange }: PaginationProps) {
  const pages = Array.from({ length: totalPages }, (_, i) => i + 1);
  const visible = pages.filter(
    (p) => p === 1 || p === totalPages || Math.abs(p - page) <= 1
  );

  const withEllipsis: (number | "...")[] = [];
  visible.forEach((p, i) => {
    if (i > 0 && p - visible[i - 1] > 1) withEllipsis.push("...");
    withEllipsis.push(p);
  });

  return (
    <nav className="flex items-center justify-center gap-1 mt-8">
      <button
        onClick={() => onPageChange(page - 1)}
        disabled={page <= 1}
        className="px-3 py-2 text-sm rounded-lg hover:bg-gray-100 disabled:opacity-40 disabled:cursor-not-allowed"
      >
        Previous
      </button>
      {withEllipsis.map((item, i) =>
        item === "..." ? (
          <span key={`e-${i}`} className="px-2 text-gray-400">
            …
          </span>
        ) : (
          <button
            key={item}
            onClick={() => onPageChange(item as number)}
            className={`px-3 py-1.5 text-sm rounded-lg ${
              item === page
                ? "bg-rose-600 text-white"
                : "hover:bg-gray-100 text-gray-700"
            }`}
          >
            {item}
          </button>
        )
      )}
      <button
        onClick={() => onPageChange(page + 1)}
        disabled={page >= totalPages}
        className="px-3 py-2 text-sm rounded-lg hover:bg-gray-100 disabled:opacity-40 disabled:cursor-not-allowed"
      >
        Next
      </button>
    </nav>
  );
}

/* ---------- PageLoading ---------- */
/**
 * A centred full-height loading spinner for page-level loading states.
 *
 * @returns The spinner wrapped in a flex container.
 */
export function PageLoading() {
  return (
    <div className="flex items-center justify-center min-h-[50vh]">
      <Spinner size="lg" />
    </div>
  );
}
