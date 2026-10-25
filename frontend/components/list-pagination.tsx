import { ArrowDown } from "lucide-react";

interface ListPaginationProps {
  count: number;
  hasMore: boolean;
  loading: boolean;
  onLoadMore: () => void;
}

export function ListPagination({
  count,
  hasMore,
  loading,
  onLoadMore,
}: ListPaginationProps) {
  if (!hasMore) return null;

  return (
    <div className="workspace-pagination">
      <span className="muted-copy">Showing {count} records</span>
      <button
        className="button button-outline"
        disabled={loading}
        onClick={onLoadMore}
        type="button"
      >
        {loading ? "Loading…" : "Load more"} <ArrowDown size={16} />
      </button>
    </div>
  );
}
