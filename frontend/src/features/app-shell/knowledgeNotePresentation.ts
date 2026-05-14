export const KIND_LABELS: Record<string, string> = {
  insight: "Erkenntnis",
  action: "Aktion",
  reflection: "Reflexion",
  question: "Frage",
  general: "Allgemein",
};

export function formatKnowledgeNoteTitle(title: string): string {
  return title.replace(/^\[Stub\]\s*/i, "").trim();
}

export function formatKnowledgeNoteKind(kind: string): string {
  return KIND_LABELS[kind] ?? KIND_LABELS.general;
}
