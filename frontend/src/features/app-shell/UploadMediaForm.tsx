type UploadMediaFormProps = {
  error: string;
  onSubmit: (file: File, title: string, mediaType: string, description: string) => Promise<void>;
};

export function UploadMediaForm({ error, onSubmit }: UploadMediaFormProps) {
  return (
    <article className="card">
      <h2>Upload Playable Media</h2>
      <p className="muted">Create a usable audio or video item from a real file.</p>
      <form
        className="stack-form"
        action={async (formData) => {
          const file = formData.get("file");
          if (!(file instanceof File) || file.size === 0) {
            return;
          }

          await onSubmit(
            file,
            String(formData.get("title") ?? file.name),
            String(formData.get("mediaType") ?? "audio"),
            String(formData.get("description") ?? ""),
          );
        }}
      >
        <label className="field">
          <span>File</span>
          <input accept="audio/*,video/*" name="file" required type="file" />
        </label>
        <label className="field">
          <span>Title</span>
          <input name="title" required type="text" />
        </label>
        <label className="field">
          <span>Type</span>
          <select defaultValue="audio" name="mediaType">
            <option value="audio">Audio</option>
            <option value="video">Video</option>
          </select>
        </label>
        <label className="field">
          <span>Description</span>
          <textarea name="description" rows={3} />
        </label>
        {error ? <p className="error-text">{error}</p> : null}
        <button type="submit">Upload and create</button>
      </form>
    </article>
  );
}
