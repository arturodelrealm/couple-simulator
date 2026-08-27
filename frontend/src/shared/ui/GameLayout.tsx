import type { ReactNode } from "react";

type GameLayoutProps = {
  children: ReactNode;
};

export function GameLayout({ children }: GameLayoutProps) {
  return (
    <div className="min-h-screen bg-slate-50">
      <main className="mx-auto max-w-2xl px-4 py-8">{children}</main>
    </div>
  );
}
