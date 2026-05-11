import { useEffect, useState } from "react";

import { fetchSummaries, fetchTranscriptSegments, fetchTranscripts } from "./api";
import type { MediaItem, Summary, Transcript, TranscriptSegment } from "./types";

type TranscriptPanelProps = { mediaItem: MediaItem };

function formatArtifactStatus(status: string): string {
  switch (status) {
    case "pending":
      return "Pending generation";
    case "processing":
      return "Processing…";
    case "ready":
      return "Ready";
    case "failed":
      return "Generation failed";
    default:
      return status;
  }
}

function formatSegmentTimestamp(value: string | null): string {
  if (!value) {
    return "--:--";
  }

  const totalSeconds = Math.max(0, Number.parseFloat(value));
  if (Number.isNaN(totalSeconds)) {
    return value;
  }

  const minutes = Math.floor(totalSeconds / 60);
  const seconds = Math.floor(totalSeconds % 60);
  return `${minutes}:${seconds.toString().padStart(2, "0")}`;
}

function renderArtifactContent(summary: Summary | Transcript) {
  const content = summary.markdown_content.trim() || summary.content.trim();
  if (!content) {
    return null;
  }

  return <pre className="artifact-content">{content}</pre>;
}

export function TranscriptPanel({ mediaItem }: TranscriptPanelProps) {
  const [transcripts, setTranscripts] = useState<Transcript[]>([]);
  const [summaries, setSummaries] = useState<Summary[]>([]);
  const [segments, setSegments] = useState<TranscriptSegment[]>([]);
  const [selectedTranscriptId, setSelectedTranscriptId] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [segmentLoading, setSegmentLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;

    async function loadArtifacts() {
      setLoading(true);
      setError("");

      try {
        const [nextTranscripts, nextSummaries] = await Promise.all([
          fetchTranscripts(mediaItem.id),
          fetchSummaries(mediaItem.id),
        ]);
        if (cancelled) {
          return;
        }

        setTranscripts(nextTranscripts);
        setSummaries(nextSummaries);
        setSelectedTranscriptId((currentId) => {
          if (currentId && nextTranscripts.some((transcript) => transcript.id === currentId)) {
            return currentId;
          }
          return nextTranscripts[0]?.id ?? null;
        });
      } catch (nextError) {
        if (!cancelled) {
          setError(nextError instanceof Error ? nextError.message : "Artifact loading failed.");
          setTranscripts([]);
          setSummaries([]);
          setSelectedTranscriptId(null);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void loadArtifacts();

    return () => {
      cancelled = true;
    };
  }, [mediaItem.id]);

  useEffect(() => {
    let cancelled = false;

    async function loadSegments() {
      if (!selectedTranscriptId) {
        setSegments([]);
        return;
      }

      setSegmentLoading(true);
      try {
        const nextSegments = await fetchTranscriptSegments(selectedTranscriptId);
        if (!cancelled) {
          setSegments(nextSegments);
        }
      } catch (nextError) {
        if (!cancelled) {
          setError(nextError instanceof Error ? nextError.message : "Segment loading failed.");
          setSegments([]);
        }
      } finally {
        if (!cancelled) {
          setSegmentLoading(false);
        }
      }
    }

    void loadSegments();

    return () => {
      cancelled = true;
    };
  }, [selectedTranscriptId]);

  const selectedTranscript =
    transcripts.find((transcript) => transcript.id === selectedTranscriptId) ?? transcripts[0] ?? null;

  return (
    <article className="card transcript-card">
      <h2>Transcript & Summary</h2>
      <p className="muted">Generated artifacts for {mediaItem.title}.</p>
      {error ? <p className="error-text artifact-error">{error}</p> : null}
      {loading ? <p className="empty-state">Loading generated artifacts…</p> : null}

      <div className="artifact-section">
        <h3>Summaries</h3>
        {summaries.length === 0 && !loading ? (
          <p className="empty-state">No summaries yet.</p>
        ) : (
          <ul className="simple-list compact-list">
            {summaries.map((summary) => {
              const statusLabel = formatArtifactStatus(summary.status);
              return (
                <li key={summary.id}>
                  <div className="artifact-header">
                    <strong>{summary.kind} summary</strong>
                    <span className={`artifact-status artifact-status-${summary.status}`}>{statusLabel}</span>
                  </div>
                  <span className="muted">Provider: {summary.provider}</span>
                  {summary.status === "ready" ? renderArtifactContent(summary) : null}
                  {summary.status === "failed" && summary.error_message ? (
                    <small className="muted">{summary.error_message}</small>
                  ) : null}
                </li>
              );
            })}
          </ul>
        )}
      </div>

      <div className="artifact-section">
        <h3>Transcripts</h3>
        {transcripts.length === 0 && !loading ? (
          <p className="empty-state">No transcripts yet.</p>
        ) : (
          <ul className="simple-list compact-list">
            {transcripts.map((transcript) => {
              const isSelected = transcript.id === selectedTranscript?.id;
              const statusLabel = formatArtifactStatus(transcript.status);
              return (
                <li key={transcript.id} className={isSelected ? "selected-item" : undefined}>
                  <button
                    className="list-button media-list-button"
                    onClick={() => setSelectedTranscriptId(transcript.id)}
                    type="button"
                  >
                    <div className="artifact-header">
                      <strong>
                        {transcript.language_code || "unknown"} · {transcript.provider}
                      </strong>
                      <span className={`artifact-status artifact-status-${transcript.status}`}>
                        {statusLabel}
                      </span>
                    </div>
                  </button>
                  {isSelected && transcript.status === "ready" ? renderArtifactContent(transcript) : null}
                  {isSelected && transcript.status === "processing" ? (
                    <p className="empty-state">Processing… segments will appear here once ready.</p>
                  ) : null}
                  {isSelected && transcript.status === "pending" ? (
                    <p className="empty-state">Pending generation.</p>
                  ) : null}
                  {isSelected && transcript.status === "failed" ? (
                    <>
                      <p className="empty-state">Generation failed.</p>
                      {transcript.error_message ? (
                        <small className="muted">{transcript.error_message}</small>
                      ) : null}
                    </>
                  ) : null}
                  {isSelected && transcript.status === "ready" ? (
                    <div className="artifact-segments">
                      <h4>Segments</h4>
                      {segmentLoading ? (
                        <p className="empty-state">Loading segments…</p>
                      ) : segments.length === 0 ? (
                        <p className="empty-state">No transcript segments yet.</p>
                      ) : (
                        <ul className="simple-list compact-list">
                          {segments.map((segment) => (
                            <li key={segment.id}>
                              <strong>
                                {formatSegmentTimestamp(segment.start_seconds)}–
                                {formatSegmentTimestamp(segment.end_seconds)}
                              </strong>
                              <span>{segment.content}</span>
                            </li>
                          ))}
                        </ul>
                      )}
                    </div>
                  ) : null}
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </article>
  );
}
