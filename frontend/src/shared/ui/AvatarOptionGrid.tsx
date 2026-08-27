import type { ReactNode } from "react";

type AvatarOptionGridProps = {
  children: ReactNode;
};

export function AvatarOptionGrid({ children }: AvatarOptionGridProps) {
  return (
    <div className="grid grid-cols-4 gap-2 sm:grid-cols-5">{children}</div>
  );
}
