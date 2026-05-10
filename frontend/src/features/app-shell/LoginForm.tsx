type LoginFormProps = {
  error: string;
  onSubmit: (username: string, password: string) => Promise<void>;
};

export function LoginForm({ error, onSubmit }: LoginFormProps) {
  async function handleSubmit(formData: FormData) {
    const username = String(formData.get("username") ?? "");
    const password = String(formData.get("password") ?? "");
    await onSubmit(username, password);
  }

  return (
    <section className="card auth-card">
      <h2>Login</h2>
      <p className="muted">Sign in with your owner or restricted account.</p>
      <form
        className="stack-form"
        action={async (formData) => {
          await handleSubmit(formData);
        }}
      >
        <label className="field">
          <span>Username</span>
          <input name="username" type="text" required />
        </label>
        <label className="field">
          <span>Password</span>
          <input name="password" type="password" required />
        </label>
        {error ? <p className="error-text">{error}</p> : null}
        <button type="submit">Sign in</button>
      </form>
    </section>
  );
}
