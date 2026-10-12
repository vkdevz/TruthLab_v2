import React, { useState, useMemo } from 'react';
import type { EvidenceGraph, GraphNode, VeracityLabel } from '../types/verification';

interface EvidenceGraphViewProps {
  graph: EvidenceGraph;
  overallVerdict?: VeracityLabel | null;
  onSelectCitation?: (sourceName: string) => void;
}

interface NodePosition {
  node: GraphNode;
  x: number;
  y: number;
  isClaim: boolean;
}

export const EvidenceGraphView: React.FC<EvidenceGraphViewProps> = ({
  graph,
  overallVerdict,
  onSelectCitation,
}) => {
  const [hoveredNodeId, setHoveredNodeId] = useState<string | null>(null);

  const width = 860;
  const height = 440;
  const centerX = width / 2;
  const centerY = height / 2;

  // Compute node coordinates using a radial layout
  const { nodePositions, edgeList } = useMemo(() => {
    if (!graph || !graph.nodes || graph.nodes.length === 0) {
      return { nodePositions: new Map<string, NodePosition>(), edgeList: [] };
    }

    const claimNodes = graph.nodes.filter((n) => n.type === 'claim');
    const evidenceNodes = graph.nodes.filter((n) => n.type !== 'claim');
    const positions = new Map<string, NodePosition>();

    // Position claim nodes at the center
    if (claimNodes.length === 1) {
      positions.set(claimNodes[0].id, {
        node: claimNodes[0],
        x: centerX,
        y: centerY,
        isClaim: true,
      });
    } else {
      const claimStepY = height / (claimNodes.length + 1);
      claimNodes.forEach((c, idx) => {
        positions.set(c.id, {
          node: c,
          x: centerX + (idx % 2 === 0 ? -40 : 40),
          y: claimStepY * (idx + 1),
          isClaim: true,
        });
      });
    }

    // Position evidence nodes in an ellipse around the center
    const totalEvidence = evidenceNodes.length;
    if (totalEvidence > 0) {
      const radiusX = Math.min(350, width * 0.40);
      const radiusY = Math.min(160, height * 0.38);

      evidenceNodes.forEach((ev, idx) => {
        const angle = (2 * Math.PI * idx) / totalEvidence - Math.PI / 2;
        const x = centerX + radiusX * Math.cos(angle);
        const y = centerY + radiusY * Math.sin(angle);
        positions.set(ev.id, {
          node: ev,
          x,
          y,
          isClaim: false,
        });
      });
    }

    return { nodePositions: positions, edgeList: graph.edges || [] };
  }, [graph, centerX, centerY, width, height]);

  if (!graph || !graph.nodes || graph.nodes.length === 0) {
    return (
      <div
        style={{
          background: 'rgba(10, 13, 20, 0.6)',
          border: '1px dashed var(--border-subtle)',
          borderRadius: '12px',
          padding: '40px 20px',
          textAlign: 'center',
          color: 'var(--text-dim)',
        }}
      >
        <span style={{ fontSize: '2rem', display: 'block', marginBottom: '8px' }}>🕸️</span>
        <div style={{ fontWeight: 600, color: 'var(--text-muted)' }}>
          No Evidence Graph Generated
        </div>
        <p style={{ fontSize: '0.85rem', marginTop: '4px' }}>
          Graph will populate when check-worthy propositions and corresponding evidence citations are retrieved.
        </p>
      </div>
    );
  }

  const getRelationColor = (relation: string) => {
    switch (relation?.toUpperCase()) {
      case 'SUPPORTS':
        return '#10b981'; // Green
      case 'REFUTES':
        return '#ef4444'; // Red
      case 'NEUTRAL':
      default:
        return '#94a3b8'; // Slate
    }
  };

  const getVerdictBorderColor = (verdict?: string | null) => {
    switch (verdict?.toUpperCase()) {
      case 'SUPPORTED':
        return '#10b981';
      case 'CONTRADICTED':
        return '#ef4444';
      case 'MISLEADING':
        return '#f59e0b';
      case 'OUTDATED':
        return '#8b5cf6';
      default:
        return '#64748b';
    }
  };

  return (
    <div
      style={{
        background: 'rgba(10, 14, 23, 0.75)',
        border: '1px solid var(--border-subtle)',
        borderRadius: '12px',
        padding: '20px',
        overflow: 'hidden',
        position: 'relative',
      }}
    >
      {/* Header and Legend */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '12px',
          marginBottom: '16px',
          borderBottom: '1px solid rgba(255, 255, 255, 0.06)',
          paddingBottom: '12px',
        }}
      >
        <div>
          <h4
            style={{
              fontSize: '0.95rem',
              fontWeight: 700,
              color: 'var(--accent-cyan)',
              margin: 0,
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
            }}
          >
            <span>🕸️</span> Directed Evidence Reasoning Graph
          </h4>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
            Topological citation relationships with directional stance vectors
          </span>
        </div>

        {/* Legend */}
        <div style={{ display: 'flex', gap: '14px', alignItems: 'center', fontSize: '0.75rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span
              style={{ width: '10px', height: '10px', borderRadius: '2px', background: '#10b981' }}
            ></span>
            <span style={{ color: 'var(--text-muted)' }}>Supports</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span
              style={{ width: '10px', height: '10px', borderRadius: '2px', background: '#ef4444' }}
            ></span>
            <span style={{ color: 'var(--text-muted)' }}>Refutes</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span
              style={{ width: '10px', height: '10px', borderRadius: '2px', background: '#94a3b8' }}
            ></span>
            <span style={{ color: 'var(--text-muted)' }}>Neutral</span>
          </div>
        </div>
      </div>

      {/* SVG Canvas */}
      <div style={{ width: '100%', overflowX: 'auto', WebkitOverflowScrolling: 'touch' }}>
        <svg
          viewBox={`0 0 ${width} ${height}`}
          style={{ width: '100%', minWidth: '580px', maxHeight: '420px', display: 'block' }}
        >
          <defs>
            {/* Arrowhead Markers */}
            <marker
              id="arrow-supports"
              viewBox="0 0 10 10"
              refX="18"
              refY="5"
              markerWidth="6"
              markerHeight="6"
              orient="auto-start-reverse"
            >
              <path d="M 0 1 L 10 5 L 0 9 z" fill="#10b981" />
            </marker>
            <marker
              id="arrow-refutes"
              viewBox="0 0 10 10"
              refX="18"
              refY="5"
              markerWidth="6"
              markerHeight="6"
              orient="auto-start-reverse"
            >
              <path d="M 0 1 L 10 5 L 0 9 z" fill="#ef4444" />
            </marker>
            <marker
              id="arrow-neutral"
              viewBox="0 0 10 10"
              refX="18"
              refY="5"
              markerWidth="6"
              markerHeight="6"
              orient="auto-start-reverse"
            >
              <path d="M 0 1 L 10 5 L 0 9 z" fill="#94a3b8" />
            </marker>

            {/* Radial Gradient Glow for Center Node */}
            <radialGradient id="claimGlow" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="rgba(56, 189, 248, 0.25)" />
              <stop offset="100%" stopColor="rgba(56, 189, 248, 0)" />
            </radialGradient>
          </defs>

          {/* Central Glow Effect */}
          <circle cx={centerX} cy={centerY} r="180" fill="url(#claimGlow)" />

          {/* Render Directed Edges */}
          {edgeList.map((edge, idx) => {
            const sourcePos = nodePositions.get(edge.source);
            const targetPos = nodePositions.get(edge.target);
            if (!sourcePos || !targetPos) return null;

            const isHighlighted =
              hoveredNodeId === edge.source || hoveredNodeId === edge.target;
            const strokeColor = getRelationColor(edge.relation);
            const markerType =
              edge.relation === 'SUPPORTS'
                ? 'url(#arrow-supports)'
                : edge.relation === 'REFUTES'
                ? 'url(#arrow-refutes)'
                : 'url(#arrow-neutral)';

            // Midpoint for curved path
            const midX = (sourcePos.x + targetPos.x) / 2;
            const midY = (sourcePos.y + targetPos.y) / 2 - 15;

            return (
              <g key={`edge-${idx}`}>
                <path
                  d={`M ${sourcePos.x} ${sourcePos.y} Q ${midX} ${midY} ${targetPos.x} ${targetPos.y}`}
                  fill="none"
                  stroke={strokeColor}
                  strokeWidth={isHighlighted ? 3 : 1.8}
                  strokeOpacity={isHighlighted ? 0.95 : 0.65}
                  markerEnd={markerType}
                  strokeDasharray={edge.relation === 'NEUTRAL' ? '4 3' : 'none'}
                  style={{ transition: 'all 0.2s ease' }}
                />
                {/* Weight badge near curve midpoint */}
                <rect
                  x={midX - 16}
                  y={midY - 9}
                  width="32"
                  height="16"
                  rx="4"
                  fill="rgba(15, 23, 42, 0.85)"
                  stroke={strokeColor}
                  strokeWidth="0.8"
                />
                <text
                  x={midX}
                  y={midY + 3}
                  textAnchor="middle"
                  fill={strokeColor}
                  fontSize="9"
                  fontFamily="monospace"
                  fontWeight="bold"
                >
                  {(edge.weight ?? 0.85).toFixed(2)}
                </text>
              </g>
            );
          })}

          {/* Render Nodes */}
          {Array.from(nodePositions.values()).map((pos) => {
            const isHovered = hoveredNodeId === pos.node.id;
            const isClaim = pos.isClaim;

            if (isClaim) {
              const borderColor = getVerdictBorderColor(pos.node.status || overallVerdict);
              const nodeWidth = 200;
              const nodeHeight = 56;

              return (
                <g
                  key={pos.node.id}
                  transform={`translate(${pos.x - nodeWidth / 2}, ${pos.y - nodeHeight / 2})`}
                  onMouseEnter={() => setHoveredNodeId(pos.node.id)}
                  onMouseLeave={() => setHoveredNodeId(null)}
                  style={{ cursor: 'pointer' }}
                >
                  <rect
                    width={nodeWidth}
                    height={nodeHeight}
                    rx="12"
                    fill="rgba(15, 23, 42, 0.92)"
                    stroke={borderColor}
                    strokeWidth={isHovered ? 3 : 2}
                    filter="drop-shadow(0 4px 12px rgba(0, 0, 0, 0.6))"
                    style={{ transition: 'all 0.2s ease' }}
                  />
                  <text
                    x={nodeWidth / 2}
                    y="18"
                    textAnchor="middle"
                    fill="var(--accent-cyan)"
                    fontSize="10"
                    fontWeight="bold"
                    letterSpacing="0.05em"
                  >
                    TARGET PROPOSITION
                  </text>
                  <text
                    x={nodeWidth / 2}
                    y="36"
                    textAnchor="middle"
                    fill="#fff"
                    fontSize="11"
                    fontWeight="600"
                  >
                    {pos.node.label.length > 28
                      ? `${pos.node.label.slice(0, 26)}...`
                      : pos.node.label}
                  </text>
                  {pos.node.status && (
                    <text
                      x={nodeWidth / 2}
                      y="49"
                      textAnchor="middle"
                      fill={borderColor}
                      fontSize="9"
                      fontWeight="bold"
                    >
                      [{pos.node.status}]
                    </text>
                  )}
                </g>
              );
            }

            // Evidence Node (Orbiting)
            const nodeWidth = 140;
            const nodeHeight = 44;
            const stanceColor = getRelationColor(pos.node.status || 'NEUTRAL');

            return (
              <g
                key={pos.node.id}
                transform={`translate(${pos.x - nodeWidth / 2}, ${pos.y - nodeHeight / 2})`}
                onMouseEnter={() => setHoveredNodeId(pos.node.id)}
                onMouseLeave={() => setHoveredNodeId(null)}
                onClick={() => onSelectCitation && onSelectCitation(pos.node.label)}
                style={{ cursor: 'pointer' }}
              >
                <rect
                  width={nodeWidth}
                  height={nodeHeight}
                  rx="8"
                  fill="rgba(24, 30, 48, 0.88)"
                  stroke={isHovered ? stanceColor : 'rgba(255, 255, 255, 0.15)'}
                  strokeWidth={isHovered ? 2 : 1}
                  style={{ transition: 'all 0.2s ease' }}
                />
                <circle cx="16" cy={nodeHeight / 2} r="5" fill={stanceColor} />
                <text
                  x="28"
                  y="20"
                  fill="#fff"
                  fontSize="11"
                  fontWeight="600"
                >
                  {pos.node.label.length > 15
                    ? `${pos.node.label.slice(0, 14)}...`
                    : pos.node.label}
                </text>
                <text
                  x="28"
                  y="34"
                  fill={stanceColor}
                  fontSize="9"
                  fontWeight="bold"
                >
                  {pos.node.status || 'EVIDENCE'}
                </text>
              </g>
            );
          })}
        </svg>
      </div>

      {/* Footer Info Strip */}
      <div
        style={{
          marginTop: '12px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          fontSize: '0.75rem',
          color: 'var(--text-dim)',
          borderTop: '1px solid rgba(255, 255, 255, 0.04)',
          paddingTop: '8px',
        }}
      >
        <span>
          Showing {edgeList.length} relation edge(s) across {nodePositions.size} topological entity nodes.
        </span>
        <span>Click an evidence node to inspect matching citation.</span>
      </div>
    </div>
  );
};
export default EvidenceGraphView;
