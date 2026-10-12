import React, { useState, useMemo, useEffect } from 'react';
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
  const [isMobileViewport, setIsMobileViewport] = useState<boolean>(
    typeof window !== 'undefined' ? window.innerWidth < 768 : false
  );
  const [layoutMode, setLayoutMode] = useState<'RADIAL' | 'TREE'>(
    typeof window !== 'undefined' && window.innerWidth < 768 ? 'TREE' : 'RADIAL'
  );

  useEffect(() => {
    const handleResize = () => {
      const mobile = window.innerWidth < 768;
      setIsMobileViewport(mobile);
      setLayoutMode(mobile ? 'TREE' : 'RADIAL');
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const width = 840;
  const height = 400;
  const centerX = width / 2;
  const centerY = height / 2;

  const { nodePositions, edgeList, claimNodes, evidenceNodes } = useMemo(() => {
    if (!graph || !graph.nodes || graph.nodes.length === 0) {
      return {
        nodePositions: new Map<string, NodePosition>(),
        edgeList: [],
        claimNodes: [] as GraphNode[],
        evidenceNodes: [] as GraphNode[],
      };
    }

    const cNodes = graph.nodes.filter((n) => n.type === 'claim');
    const eNodes = graph.nodes.filter((n) => n.type !== 'claim');
    const positions = new Map<string, NodePosition>();

    if (cNodes.length === 1) {
      positions.set(cNodes[0].id, {
        node: cNodes[0],
        x: centerX,
        y: centerY,
        isClaim: true,
      });
    } else {
      const claimStepY = height / (cNodes.length + 1);
      cNodes.forEach((c, idx) => {
        positions.set(c.id, {
          node: c,
          x: centerX + (idx % 2 === 0 ? -40 : 40),
          y: claimStepY * (idx + 1),
          isClaim: true,
        });
      });
    }

    const totalEvidence = eNodes.length;
    if (totalEvidence > 0) {
      const radiusX = Math.min(330, width * 0.39);
      const radiusY = Math.min(145, height * 0.36);

      eNodes.forEach((ev, idx) => {
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

    return {
      nodePositions: positions,
      edgeList: graph.edges || [],
      claimNodes: cNodes,
      evidenceNodes: eNodes,
    };
  }, [graph, centerX, centerY, width, height]);

  if (!graph || !graph.nodes || graph.nodes.length === 0) {
    return (
      <div
        style={{
          background: 'var(--bg-input)',
          border: '1px dashed var(--border-subtle)',
          borderRadius: 'var(--radius-md)',
          padding: '32px 16px',
          textAlign: 'center',
          color: 'var(--text-muted)',
          fontSize: '0.82rem',
        }}
      >
        <div style={{ fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '4px' }}>
          No Topological Graph Available
        </div>
        <p>Graph populates when check-worthy propositions and evidence citations are linked.</p>
      </div>
    );
  }

  const getRelationColor = (relation: string) => {
    switch (relation?.toUpperCase()) {
      case 'SUPPORTS':
        return '#22c55e';
      case 'REFUTES':
        return '#ef4444';
      case 'NEUTRAL':
      default:
        return '#71717a';
    }
  };

  const getVerdictBorderColor = (verdict?: string | null) => {
    switch (verdict?.toUpperCase()) {
      case 'SUPPORTED':
        return '#22c55e';
      case 'CONTRADICTED':
        return '#ef4444';
      case 'MISLEADING':
      case 'OUTDATED':
        return '#eab308';
      default:
        return '#71717a';
    }
  };

  return (
    <div style={{ position: 'relative' }}>
      {/* Header & Layout Switcher */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '10px',
          marginBottom: '14px',
          paddingBottom: '10px',
          borderBottom: '1px solid var(--border-subtle)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
          <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-primary)' }}>
            Evidence Topology
          </span>
          {/* Legend */}
          <div style={{ display: 'flex', gap: '12px', alignItems: 'center', fontSize: '0.72rem', fontFamily: 'var(--font-mono)' }}>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: '5px', color: 'var(--text-muted)' }}>
              <span style={{ width: '7px', height: '7px', borderRadius: '50%', background: '#22c55e' }} />
              Supports
            </span>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: '5px', color: 'var(--text-muted)' }}>
              <span style={{ width: '7px', height: '7px', borderRadius: '50%', background: '#ef4444' }} />
              Refutes
            </span>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: '5px', color: 'var(--text-muted)' }}>
              <span style={{ width: '7px', height: '7px', borderRadius: '50%', background: '#71717a' }} />
              Neutral
            </span>
          </div>
        </div>

        {/* Toggle between Tree (Mobile Optimal) and Radial (Desktop Optimal) */}
        <div style={{ display: 'inline-flex', background: 'var(--bg-subtle)', padding: '2px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
          <button
            type="button"
            onClick={() => setLayoutMode('TREE')}
            style={{
              background: layoutMode === 'TREE' ? 'var(--bg-card)' : 'transparent',
              color: layoutMode === 'TREE' ? 'var(--text-primary)' : 'var(--text-muted)',
              border: 'none',
              padding: '3px 8px',
              borderRadius: '4px',
              fontSize: '0.7rem',
              fontFamily: 'var(--font-mono)',
              cursor: 'pointer',
            }}
          >
            Tree {isMobileViewport ? '(Mobile)' : ''}
          </button>
          <button
            type="button"
            onClick={() => setLayoutMode('RADIAL')}
            style={{
              background: layoutMode === 'RADIAL' ? 'var(--bg-card)' : 'transparent',
              color: layoutMode === 'RADIAL' ? 'var(--text-primary)' : 'var(--text-muted)',
              border: 'none',
              padding: '3px 8px',
              borderRadius: '4px',
              fontSize: '0.7rem',
              fontFamily: 'var(--font-mono)',
              cursor: 'pointer',
            }}
          >
            Radial SVG
          </button>
        </div>
      </div>

      {/* MODE 1: Dedicated Mobile-First Vertical Topological Tree */}
      {layoutMode === 'TREE' ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', padding: '4px 0' }}>
          {/* Root Claim Node */}
          {claimNodes.map((cNode) => {
            const borderColor = getVerdictBorderColor(cNode.status || overallVerdict);
            return (
              <div
                key={cNode.id}
                style={{
                  background: 'var(--bg-card)',
                  border: `1px solid ${borderColor}`,
                  borderLeft: `4px solid ${borderColor}`,
                  borderRadius: 'var(--radius-sm)',
                  padding: '12px 14px',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.68rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                    Target Proposition
                  </span>
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.7rem', fontWeight: 600, color: borderColor }}>
                    {cNode.status || overallVerdict}
                  </span>
                </div>
                <div style={{ fontSize: '0.84rem', fontWeight: 500, color: 'var(--text-primary)', lineHeight: 1.4 }}>
                  {cNode.label}
                </div>
              </div>
            );
          })}

          {/* Connected Evidence Nodes along Vertical Spine */}
          <div style={{ paddingLeft: '14px', borderLeft: '1px dashed var(--border-hover)', marginLeft: '12px', display: 'flex', flexDirection: 'column', gap: '8px', paddingTop: '4px' }}>
            {evidenceNodes.map((evNode) => {
              const matchingEdge = edgeList.find((e) => e.source === evNode.id || e.target === evNode.id);
              const relation = matchingEdge?.relation || evNode.status || 'NEUTRAL';
              const weight = matchingEdge?.weight ?? 0.85;
              const relColor = getRelationColor(relation);

              return (
                <div
                  key={evNode.id}
                  onClick={() => onSelectCitation && onSelectCitation(evNode.label)}
                  style={{
                    background: 'var(--bg-card)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: 'var(--radius-sm)',
                    padding: '10px 12px',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    gap: '10px',
                    cursor: onSelectCitation ? 'pointer' : 'default',
                    position: 'relative',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', minWidth: 0 }}>
                    <span style={{ width: '7px', height: '7px', borderRadius: '50%', background: relColor, flexShrink: 0 }} />
                    <span style={{ fontSize: '0.8rem', fontWeight: 500, color: 'var(--text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {evNode.label}
                    </span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexShrink: 0, fontFamily: 'var(--font-mono)', fontSize: '0.7rem' }}>
                    <span style={{ color: relColor, fontWeight: 600 }}>{relation}</span>
                    <span style={{ color: 'var(--text-faint)' }}>({weight.toFixed(2)})</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      ) : (
        /* MODE 2: Desktop Radial SVG Canvas */
        <div style={{ width: '100%', overflowX: 'auto', WebkitOverflowScrolling: 'touch' }}>
          <svg
            viewBox={`0 0 ${width} ${height}`}
            style={{ width: '100%', minWidth: '560px', maxHeight: '390px', display: 'block' }}
          >
            <defs>
              <marker id="arrow-supports" viewBox="0 0 10 10" refX="18" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                <path d="M 0 1 L 10 5 L 0 9 z" fill="#22c55e" />
              </marker>
              <marker id="arrow-refutes" viewBox="0 0 10 10" refX="18" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                <path d="M 0 1 L 10 5 L 0 9 z" fill="#ef4444" />
              </marker>
              <marker id="arrow-neutral" viewBox="0 0 10 10" refX="18" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                <path d="M 0 1 L 10 5 L 0 9 z" fill="#71717a" />
              </marker>
            </defs>

            {/* Render Directed Edges */}
            {edgeList.map((edge, idx) => {
              const sourcePos = nodePositions.get(edge.source);
              const targetPos = nodePositions.get(edge.target);
              if (!sourcePos || !targetPos) return null;

              const isHighlighted = hoveredNodeId === edge.source || hoveredNodeId === edge.target;
              const strokeColor = getRelationColor(edge.relation);
              const markerType =
                edge.relation === 'SUPPORTS'
                  ? 'url(#arrow-supports)'
                  : edge.relation === 'REFUTES'
                  ? 'url(#arrow-refutes)'
                  : 'url(#arrow-neutral)';

              const midX = (sourcePos.x + targetPos.x) / 2;
              const midY = (sourcePos.y + targetPos.y) / 2 - 14;

              return (
                <g key={`edge-${idx}`}>
                  <path
                    d={`M ${sourcePos.x} ${sourcePos.y} Q ${midX} ${midY} ${targetPos.x} ${targetPos.y}`}
                    fill="none"
                    stroke={strokeColor}
                    strokeWidth={isHighlighted ? 2.5 : 1.5}
                    strokeOpacity={isHighlighted ? 0.95 : 0.6}
                    markerEnd={markerType}
                    strokeDasharray={edge.relation === 'NEUTRAL' ? '4 3' : 'none'}
                  />
                  <rect
                    x={midX - 16}
                    y={midY - 8}
                    width="32"
                    height="15"
                    rx="3"
                    fill="#111114"
                    stroke={strokeColor}
                    strokeWidth="0.8"
                  />
                  <text
                    x={midX}
                    y={midY + 2}
                    textAnchor="middle"
                    fill={strokeColor}
                    fontSize="8.5"
                    fontFamily="monospace"
                    fontWeight="600"
                  >
                    {(edge.weight ?? 0.85).toFixed(2)}
                  </text>
                </g>
              );
            })}

            {/* Render Nodes */}
            {Array.from(nodePositions.values()).map((pos) => {
              const isHovered = hoveredNodeId === pos.node.id;
              if (pos.isClaim) {
                const borderColor = getVerdictBorderColor(pos.node.status || overallVerdict);
                const nodeWidth = 200;
                const nodeHeight = 54;

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
                      rx="8"
                      fill="#111114"
                      stroke={borderColor}
                      strokeWidth={isHovered ? 2.5 : 1.5}
                    />
                    <text
                      x={nodeWidth / 2}
                      y="17"
                      textAnchor="middle"
                      fill="#a1a1aa"
                      fontSize="9"
                      fontFamily="monospace"
                      letterSpacing="0.05em"
                    >
                      PROPOSITION
                    </text>
                    <text
                      x={nodeWidth / 2}
                      y="33"
                      textAnchor="middle"
                      fill="#fafafa"
                      fontSize="10.5"
                      fontWeight="600"
                    >
                      {pos.node.label.length > 26 ? `${pos.node.label.slice(0, 24)}...` : pos.node.label}
                    </text>
                    {pos.node.status && (
                      <text
                        x={nodeWidth / 2}
                        y="46"
                        textAnchor="middle"
                        fill={borderColor}
                        fontSize="8.5"
                        fontFamily="monospace"
                        fontWeight="600"
                      >
                        {pos.node.status}
                      </text>
                    )}
                  </g>
                );
              }

              const nodeWidth = 140;
              const nodeHeight = 42;
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
                    rx="6"
                    fill="#16161a"
                    stroke={isHovered ? stanceColor : '#27272a'}
                    strokeWidth={isHovered ? 1.8 : 1}
                  />
                  <circle cx="14" cy={nodeHeight / 2} r="4" fill={stanceColor} />
                  <text x="25" y="19" fill="#fafafa" fontSize="10.5" fontWeight="500">
                    {pos.node.label.length > 15 ? `${pos.node.label.slice(0, 14)}...` : pos.node.label}
                  </text>
                  <text x="25" y="32" fill={stanceColor} fontSize="8.5" fontFamily="monospace" fontWeight="600">
                    {pos.node.status || 'SOURCE'}
                  </text>
                </g>
              );
            })}
          </svg>
        </div>
      )}
    </div>
  );
};

export default EvidenceGraphView;
