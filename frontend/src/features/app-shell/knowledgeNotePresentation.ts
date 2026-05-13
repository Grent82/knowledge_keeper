export function formatKnowledgeNoteTitle(title: string): string {
  return title.replace(/^\[Stub\]\s*/i, "").trim();
}
