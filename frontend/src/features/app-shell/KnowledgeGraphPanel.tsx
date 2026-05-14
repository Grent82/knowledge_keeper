import { useMemo } from "react";

import { MarkerType, ReactFlow } from "@xyflow/react";
import type { Edge, Node, NodeMouseHandler } from "@xyflow/react";
import "@xyflow/react/dist/style.css";

import { formatKnowledgeNoteTitle, KIND_LABELS } from "./knowledgeNotePresentation";
import type { KnowledgeNote } from "./types";

type KnowledgeGraphPanelProps = {
  notes: KnowledgeNote[];
  onSelectNote: (note: KnowledgeNote) => void;
};

const GRAPH_CENTER = 300;
const GRAPH_RADIUS = 220;
const LABEL_LIMIT = 28;
const KIND_COLORS: Record<KnowledgeNote["kind"], string> = {
  insight: "#dbeafe",
  action: "#dcfce7",
  reflection: "#fef9c3",
  question: "#fce7f3",
  general: "#f3f4f6",
};

function truncateLabel(label: string): string {
  return label.length > LABEL_LIMIT ? `${label.slice(0, LABEL_LIMIT)}…` : label;
}

function buildNodePosition(index: number, total: number) {
  if (total <= 1) {
    return { x: GRAPH_CENTER, y: GRAPH_CENTER };
  }

  const angle = (2 * Math.PI * index) / total;
  return {
    x: GRAPH_CENTER + GRAPH_RADIUS * Math.cos(angle),
    y: GRAPH_CENTER + GRAPH_RADIUS * Math.sin(angle),
  };
}

export function KnowledgeGraphPanel({ notes, onSelectNote }: KnowledgeGraphPanelProps) {
  const noteById = useMemo(() => new Map(notes.map((note) => [String(note.id), note] as const)), [notes]);

  const nodes = useMemo<Node[]>(
    () =>
      notes.map((note, index) => ({
        id: String(note.id),
        type: "default",
        data: {
          label: truncateLabel(formatKnowledgeNoteTitle(note.title)),
        },
        position: buildNodePosition(index, notes.length),
        style: {
          backgroundColor: KIND_COLORS[note.kind],
          border: "1px solid rgba(23, 32, 42, 0.12)",
          borderRadius: 14,
          color: "#17202a",
          fontSize: 14,
          padding: 12,
          textAlign: "center",
          width: 180,
        },
      })),
    [notes],
  );

  const edges = useMemo<Edge[]>(
    () =>
      notes.flatMap((note) =>
        note.linked_notes
          .filter((targetId) => noteById.has(String(targetId)))
          .map((targetId) => ({
            id: `e-${note.id}-${targetId}`,
            source: String(note.id),
            target: String(targetId),
            markerEnd: { type: MarkerType.ArrowClosed },
          })),
      ),
    [noteById, notes],
  );

  const handleNodeClick = useMemo<NodeMouseHandler<Node>>(
    () =>
      (_, node) => {
        const selectedNote = noteById.get(node.id);
        if (selectedNote) {
          onSelectNote(selectedNote);
        }
      },
    [noteById, onSelectNote],
  );

  if (notes.length === 0) {
    return (
      <article className="card knowledge-graph-panel">
        <h2>Wissensgraph</h2>
        <p className="empty-state">Noch keine Wissensnotizen vorhanden.</p>
      </article>
    );
  }

  return (
    <article className="card knowledge-graph-panel">
      <h2>Wissensgraph</h2>
      <p className="muted">Verbindungen zwischen Wissensnotizen auf einen Blick.</p>
      <div className="knowledge-graph-canvas" style={{ height: "480px" }}>
        <ReactFlow
          edges={edges}
          fitView
          nodes={nodes}
          nodesConnectable={false}
          nodesDraggable={false}
          onNodeClick={handleNodeClick}
        />
      </div>
      <div className="knowledge-graph-legend" aria-label="Legende der Notiztypen">
        {(Object.entries(KIND_LABELS) as Array<[KnowledgeNote["kind"], string]>).map(([kind, label]) => (
          <span className="knowledge-graph-legend-item" key={kind}>
            <span className="knowledge-graph-legend-swatch" style={{ backgroundColor: KIND_COLORS[kind] }} />
            <span>{label}</span>
          </span>
        ))}
      </div>
    </article>
  );
}
