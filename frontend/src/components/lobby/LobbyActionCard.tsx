import type { ReactNode } from "react";
import { Link } from "react-router-dom";

export type LobbyActionCardProps = {
  to: string;
  title: string;
  description: string;
  icon: ReactNode;
};

export function LobbyActionCard({
  to,
  title,
  description,
  icon,
}: LobbyActionCardProps) {
  return (
    <Link
      to={to}
      className="group flex h-full flex-col rounded-3xl border-2 border-purple-100 bg-white p-6 shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:border-purple-300 hover:bg-purple-50 hover:shadow-md focus:outline-none focus:ring-2 focus:ring-purple-300"
    >
      <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-purple-100 text-purple-700 transition-colors group-hover:bg-purple-200">
        {icon}
      </div>
      <h2 className="font-display text-xl font-extrabold text-slate-800">
        {title}
      </h2>
      <p className="mt-2 text-sm leading-relaxed text-slate-600">
        {description}
      </p>
    </Link>
  );
}
