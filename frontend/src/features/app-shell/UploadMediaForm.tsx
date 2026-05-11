import { useState } from "react";

import { SubmitButton } from "./SubmitButton";

type UploadMediaFormProps = {
  error: string;
  onSubmit: (file: File, title: string, mediaType: string, description: string) => Promise<void>;
};

export function UploadMediaForm({ error, onSubmit }: UploadMediaFormProps) {
  const [mediaType, setMediaType] = useState("audio");
  const [resetKey, setResetKey] = useState(0);

  return (
    <article className="card">
      <h2>Upload Playable Media</h2>
      <p className="muted">Create a usable audio or video item from a real file.</p>
      <form
        key={resetKey}
        className="stack-form"
        action={async (formData) => {
          const file = formData.get("file");
          if (!(file instanceof File) || file.size === 0) {
            return;
          }

          await onSubmit(
            file,
            String(formData.get("title") ?? file.name),
            String(formData.get("mediaType") ?? mediaType),
            String(formData.get("description") ?? ""),
          );
          setMediaType("audio");
          setResetKey((currentKey) => currentKey + 1);
        }}
      >
        <label className="field">
          <span>File</span>
          <input
            accept="audio/*,video/*"
            name="file"
            onChange={(event) => {
              const file = event.target.files?.[0];
              if (!file) {
                return;
              }

              if (file.type.startsWith("audio/")) {
                setMediaType("audio");
                return;
              }

              if (file.type.startsWith("video/")) {
                setMediaType("video");
              }
            }}
            required
            type="file"
          />
        </label>
        <label className="field">
          <span>Title</span>
          <input name="title" required type="text" />
        </label>
        <label className="field">
          <span>Type</span>
          <select
            name="mediaType"
            onChange={(event) => {
              setMediaType(event.target.value);
            }}
            value={mediaType}
          >
            <option value="audio">Audio</option>
            <option value="video">Video</option>
          </select>
        </label>
        <label className="field">
          <span>Description</span>
          <textarea name="description" rows={3} />
        </label>
        {error ? <p className="error-text">{error}</p> : null}
        <SubmitButton pendingLabel="Uploading...">Upload and create</SubmitButton>
      </form>
    </article>
  );
}
