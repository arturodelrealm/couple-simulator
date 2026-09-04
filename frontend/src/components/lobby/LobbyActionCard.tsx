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
      className="group flex h-full flex-col rounded-3xl border-2 border-slate-200 bg-white p-6 shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:border-sky-300 hover:bg-sky-50 hover:shadow-md focus:outline-none focus:ring-2 focus:ring-sky-300"
    >
      <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-sky-100 text-sky-700 transition-colors group-hover:bg-sky-200">
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
