type TagManagerProps = {
  error: string;
  onSubmit: (name: string) => Promise<void>;
};

export function TagManager({ error, onSubmit }: TagManagerProps) {
  return (
    <article className="card">
      <h2>Manage Tags</h2>
      <p className="muted">Create reusable labels that cut across categories and topics.</p>
      <form
        className="stack-form"
        action={async (formData) => {
          const name = String(formData.get("name") ?? "").trim();
          if (!name) {
            return;
          }

          await onSubmit(name);
        }}
      >
        <label className="field">
          <span>Name</span>
          <input name="name" required type="text" />
        </label>
        {error ? <p className="error-text">{error}</p> : null}
        <button type="submit">Create tag</button>
      </form>
    </article>
  );
}
