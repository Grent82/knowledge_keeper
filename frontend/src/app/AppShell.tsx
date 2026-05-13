import type { ReactNode } from "react";

type AppShellProps = {
  children: ReactNode;
};

export function AppShell({ children }: AppShellProps) {
  return <main className="app-shell app-shell-wide">{children}</main>;
}
