import { useState } from "react";

import { SubmitButton } from "./SubmitButton";

type ExternalSourceFormProps = {
  error: string;
  onSubmit: (
    provider: string,
    sourceUrl: string,
    externalId: string,
    sourceTitle: string,
    authorName: string,
    itemTitle: string,
    mediaType: string,
    description: string,
  ) => Promise<void>;
};

export function ExternalSourceForm({ error, onSubmit }: ExternalSourceFormProps) {
  const [mediaType, setMediaType] = useState("audio");
  const [resetKey, setResetKey] = useState(0);

  return (
    <article className="card">
      <h2>Add External Source</h2>
      <p className="muted">Create a media item from YouTube, podcast, direct links or other sources.</p>
      <form
        key={resetKey}
        className="stack-form"
        action={async (formData) => {
          const provider = String(formData.get("provider") ?? "direct_link");
          const sourceUrl = String(formData.get("sourceUrl") ?? "").trim();
          const externalId = String(formData.get("externalId") ?? "").trim();
          const sourceTitle = String(formData.get("sourceTitle") ?? "").trim();
          const authorName = String(formData.get("authorName") ?? "").trim();
          const itemTitle = String(formData.get("itemTitle") ?? "").trim();
          const nextMediaType = String(formData.get("mediaType") ?? mediaType);
          const description = String(formData.get("description") ?? "").trim();

          if (!sourceUrl || !itemTitle) {
            return;
          }

          await onSubmit(
            provider,
            sourceUrl,
            externalId,
            sourceTitle,
            authorName,
            itemTitle,
            nextMediaType,
            description,
          );
          setMediaType("audio");
          setResetKey((currentKey) => currentKey + 1);
        }}
      >
        <label className="field">
          <span>Provider</span>
          <select name="provider" defaultValue="direct_link">
            <option value="direct_link">Direct link</option>
            <option value="youtube">YouTube</option>
            <option value="podcast">Podcast</option>
            <option value="other">Other</option>
          </select>
        </label>
        <label className="field">
          <span>Source URL</span>
          <input name="sourceUrl" required type="url" />
        </label>
        <label className="field">
          <span>External ID</span>
          <input name="externalId" placeholder="YouTube video ID" type="text" />
        </label>
        <label className="field">
          <span>Source title</span>
          <input name="sourceTitle" type="text" />
        </label>
        <label className="field">
          <span>Author name</span>
          <input name="authorName" type="text" />
        </label>
        <label className="field">
          <span>Media item title</span>
          <input name="itemTitle" required type="text" />
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
        <SubmitButton pendingLabel="Creating...">Create external media</SubmitButton>
      </form>
    </article>
  );
}
