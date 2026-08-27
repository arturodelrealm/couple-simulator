type LoadingStateProps = {
  message: string;
};

export function LoadingState({ message }: LoadingStateProps) {
  return (
    <div className="flex items-center justify-center py-12 text-slate-600">
      <p>{message}</p>
    </div>
  );
}
