import { AppShell } from "./AppShell";
import { AppScreen } from "../features/app-shell/AppScreen";

export function App() {
  return (
    <AppShell>
      <AppScreen />
    </AppShell>
  );
}
