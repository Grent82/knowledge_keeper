import type { ReactNode } from "react";
import { useFormStatus } from "react-dom";

type SubmitButtonProps = {
  children: ReactNode;
  pendingLabel?: string;
};

export function SubmitButton({ children, pendingLabel = "Saving..." }: SubmitButtonProps) {
  const { pending } = useFormStatus();

  return (
    <button disabled={pending} type="submit">
      {pending ? pendingLabel : children}
    </button>
  );
}
