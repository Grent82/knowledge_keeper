import { useState } from "react";

import { SubmitButton } from "./SubmitButton";

type TagManagerProps = {
  error: string;
  onSubmit: (name: string) => Promise<void>;
};

export function TagManager({ error, onSubmit }: TagManagerProps) {
  const [resetKey, setResetKey] = useState(0);

  return (
    <article className="card">
      <h2>Manage Tags</h2>
      <p className="muted">Create reusable labels that cut across categories and topics.</p>
      <form
        key={resetKey}
        className="stack-form"
        action={async (formData) => {
          const name = String(formData.get("name") ?? "").trim();
          if (!name) {
            return;
          }

          await onSubmit(name);
          setResetKey((currentKey) => currentKey + 1);
        }}
      >
        <label className="field">
          <span>Name</span>
          <input name="name" required type="text" />
        </label>
        {error ? <p className="error-text">{error}</p> : null}
        <SubmitButton pendingLabel="Creating...">Create tag</SubmitButton>
      </form>
    </article>
  );
}
