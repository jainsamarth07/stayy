interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description?: string;
  action?: React.ReactNode;
}

export default function EmptyState({ icon, title, description, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] px-4 text-center">
      {icon && <div className="mb-6 text-neutral-300">{icon}</div>}
      <h3 className="text-xl font-semibold mb-2">{title}</h3>
      {description && (
        <p className="text-sm text-neutral-500 max-w-md mb-8 leading-relaxed">{description}</p>
      )}
      {action}
    </div>
  );
}
