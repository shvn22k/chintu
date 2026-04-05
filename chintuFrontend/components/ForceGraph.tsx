'use client';

import { useRef, useEffect, useState } from 'react';
import * as d3 from 'd3';
import { GraphNode, GraphLink } from '@/types';

interface ForceGraphProps {
  graph: {
    nodes: GraphNode[];
    links: GraphLink[];
  };
}

interface SimNode extends GraphNode, d3.SimulationNodeDatum {}
interface SimLink extends d3.SimulationLinkDatum<SimNode> {
  strength: number;
  polarity: 1 | -1;
}

const NODE_COLORS: Record<string, string> = {
  seed: '#c87c5a',
  Event: '#5a8fc8',
  Entity: '#5ab87a',
  Topic: '#c8a85a',
};

const LEGEND_ITEMS = [
  { label: 'Seed event', color: '#c87c5a' },
  { label: 'Event', color: '#5a8fc8' },
  { label: 'Entity', color: '#5ab87a' },
  { label: 'Topic', color: '#c8a85a' },
];

/** Spread nodes that have no edges — otherwise D3 stacks them at (0,0) and they look like one dot. */
function layoutDisconnectedNodes(nodes: SimNode[], width: number, height: number): void {
  const cx = width / 2;
  const cy = height / 2;
  const seed = nodes.find((n) => n.is_seed) || nodes[0];
  if (!seed) return;

  seed.x = cx;
  seed.y = cy;

  const others = nodes.filter((n) => n.id !== seed.id);
  if (others.length === 0) return;

  const byHop = d3.group(others, (d) => (d.hop_count != null ? d.hop_count : 1));
  const hops = Array.from(byHop.keys()).sort((a, b) => a - b);
  let ringIndex = 0;
  for (const h of hops) {
    const ring = byHop.get(h)!;
    const baseR = 56 + ringIndex * 58;
    ring.forEach((node, i) => {
      const angle = (2 * Math.PI * i) / Math.max(ring.length, 1) - Math.PI / 2;
      const jitter = (Math.random() - 0.5) * 14;
      node.x = cx + Math.cos(angle) * (baseR + jitter);
      node.y = cy + Math.sin(angle) * (baseR + jitter);
    });
    ringIndex += 1;
  }
}

/** Slight jitter so link-only graphs do not start perfectly stacked. */
function jitterLinkedStart(nodes: SimNode[], width: number, height: number): void {
  const cx = width / 2;
  const cy = height / 2;
  nodes.forEach((n, i) => {
    n.x = cx + (Math.random() - 0.5) * 50 + Math.cos(i * 0.7) * 20;
    n.y = cy + (Math.random() - 0.5) * 50 + Math.sin(i * 0.7) * 20;
  });
}

function visualStrength(d: SimNode): number {
  const c = d.cumulative_strength;
  if (c != null && Number.isFinite(c)) return Math.min(1, Math.max(0.12, c));
  const im = d.impact_score;
  if (im != null && Number.isFinite(im)) return Math.min(1, Math.max(0.12, im));
  return 0.22;
}

export default function ForceGraph({ graph }: ForceGraphProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const wrapperRef = useRef<HTMLDivElement>(null);
  const [tooltip, setTooltip] = useState<{
    px: number;
    py: number;
    node: GraphNode;
  } | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const container = containerRef.current;
    const wrapper = wrapperRef.current;
    if (!canvas || !container || !wrapper || !graph.nodes.length) return;
    const canvasEl: HTMLCanvasElement = canvas;

    const width = container.clientWidth;
    const n = graph.nodes.length;
    const height = Math.min(560, Math.max(360, 140 + Math.sqrt(n) * 42));

    const dpr = window.devicePixelRatio || 1;
    canvasEl.width = width * dpr;
    canvasEl.height = height * dpr;
    canvasEl.style.width = `${width}px`;
    canvasEl.style.height = `${height}px`;

    const ctx = canvasEl.getContext('2d');
    if (!ctx) return;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

    const nodes: SimNode[] = graph.nodes.map((n) => ({ ...n }));
    const links: SimLink[] = graph.links.map((l) => ({
      source: l.source,
      target: l.target,
      strength: l.strength,
      polarity: l.polarity,
    }));

    if (links.length === 0) {
      layoutDisconnectedNodes(nodes, width, height);
    } else {
      jitterLinkedStart(nodes, width, height);
    }

    let transform = d3.zoomIdentity;

    function getRadius(d: SimNode): number {
      if (d.is_seed) return 11;
      const vs = visualStrength(d);
      return 5 + vs * 9;
    }

    function getNodeColor(d: SimNode): string {
      if (d.is_seed) return NODE_COLORS.seed;
      return NODE_COLORS[d.type] || NODE_COLORS.Event;
    }

    function truncate(str: string, max: number): string {
      return str.length > max ? str.slice(0, max) + '…' : str;
    }

    const cx = width / 2;
    const cy = height / 2;
    const simulation = d3.forceSimulation<SimNode>(nodes);
    if (links.length > 0) {
      simulation.force(
        'link',
        d3
          .forceLink<SimNode, SimLink>(links)
          .id((d) => d.id)
          .distance(88)
          .strength(0.55)
      );
    }
    simulation
      .force('charge', d3.forceManyBody().strength(links.length ? -200 : -95))
      .force('center', d3.forceCenter(cx, cy).strength(links.length ? 0.04 : 0.02))
      .force(
        'collide',
        d3
          .forceCollide<SimNode>()
          .radius((d) => getRadius(d) + 10)
          .strength(0.85)
      );

    if (links.length === 0 && nodes.length > 1) {
      simulation.force(
        'radial',
        d3
          .forceRadial(
            (d: SimNode) => (d.is_seed ? 0 : 48 + (d.hop_count != null ? d.hop_count : 1) * 54),
            cx,
            cy
          )
          .strength(0.2)
      );
    }

    let dragged: SimNode | null = null;
    let rafTip = 0;

    function graphPoint(clientX: number, clientY: number): [number, number] {
      const rect = canvasEl.getBoundingClientRect();
      const sx = clientX - rect.left;
      const sy = clientY - rect.top;
      return transform.invert([sx, sy]);
    }

    function nodeAt(gx: number, gy: number): SimNode | null {
      let best: SimNode | null = null;
      let bestD = Infinity;
      for (const node of nodes) {
        if (node.x == null || node.y == null) continue;
        const r = getRadius(node) + 6;
        const dx = node.x - gx;
        const dy = node.y - gy;
        const d2 = dx * dx + dy * dy;
        if (d2 <= r * r && d2 < bestD) {
          bestD = d2;
          best = node;
        }
      }
      return best;
    }

    function draw() {
      if (!ctx) return;
      ctx.save();
      ctx.clearRect(0, 0, width, height);
      ctx.translate(transform.x, transform.y);
      ctx.scale(transform.k, transform.k);

      if (links.length === 0 && nodes.length > 1) {
        ctx.strokeStyle = 'rgba(255,255,255,0.06)';
        ctx.lineWidth = 1 / transform.k;
        const maxHop = d3.max(nodes, (d) => (d.is_seed ? 0 : d.hop_count ?? 1)) ?? 1;
        for (let h = 1; h <= maxHop + 1; h++) {
          const rr = 48 + h * 54;
          ctx.beginPath();
          ctx.arc(cx, cy, rr, 0, Math.PI * 2);
          ctx.stroke();
        }
      }

      for (const link of links) {
        const src = link.source as SimNode;
        const tgt = link.target as SimNode;
        if (src.x == null || src.y == null || tgt.x == null || tgt.y == null) continue;

        const strokeWidth = (0.5 + link.strength * 2.5) / transform.k;

        ctx.beginPath();
        ctx.moveTo(src.x, src.y);
        ctx.lineTo(tgt.x, tgt.y);
        ctx.strokeStyle =
          link.polarity === 1 ? 'rgba(90,143,200,0.35)' : 'rgba(248,81,73,0.5)';
        ctx.lineWidth = strokeWidth;
        if (link.polarity === -1) ctx.setLineDash([4, 3]);
        else ctx.setLineDash([]);
        ctx.stroke();
        ctx.setLineDash([]);

        const angle = Math.atan2(tgt.y - src.y, tgt.x - src.x);
        const r = getRadius(tgt as SimNode);
        const ax = tgt.x - Math.cos(angle) * (r + 4);
        const ay = tgt.y - Math.sin(angle) * (r + 4);
        const arrowLen = 6 / transform.k;
        const arrowAngle = Math.PI / 7;

        ctx.beginPath();
        ctx.moveTo(ax, ay);
        ctx.lineTo(
          ax - arrowLen * Math.cos(angle - arrowAngle),
          ay - arrowLen * Math.sin(angle - arrowAngle)
        );
        ctx.lineTo(
          ax - arrowLen * Math.cos(angle + arrowAngle),
          ay - arrowLen * Math.sin(angle + arrowAngle)
        );
        ctx.closePath();
        ctx.fillStyle =
          link.polarity === 1 ? 'rgba(90,143,200,0.55)' : 'rgba(248,81,73,0.65)';
        ctx.fill();
      }

      for (const node of nodes) {
        if (node.x == null || node.y == null) continue;
        const r = getRadius(node);
        const color = getNodeColor(node);

        if (node.is_seed) {
          ctx.beginPath();
          ctx.arc(node.x, node.y, r + 3, 0, Math.PI * 2);
          ctx.strokeStyle = color;
          ctx.lineWidth = 1.5 / transform.k;
          ctx.stroke();
        }

        ctx.beginPath();
        ctx.arc(node.x, node.y, r, 0, Math.PI * 2);
        ctx.fillStyle = color;
        ctx.fill();

        ctx.font = `${9 / transform.k}px "JetBrains Mono", monospace`;
        ctx.fillStyle = 'rgba(232,230,225,0.75)';
        ctx.textAlign = 'center';
        ctx.fillText(truncate(node.label, 22), node.x, node.y + r + 12 / transform.k);
      }

      ctx.restore();
    }

    const zoom = d3
      .zoom<HTMLDivElement, unknown>()
      .scaleExtent([0.28, 4])
      .filter((event) => event.type === 'wheel')
      .on('zoom', (event) => {
        transform = event.transform;
        draw();
      });

    const sel = d3.select(wrapper);
    sel.call(zoom).on('dblclick.zoom', null);
    sel.on('dblclick', (event: MouseEvent) => {
      event.preventDefault();
      sel.transition().duration(200).call(zoom.transform, d3.zoomIdentity);
    });

    function onPointerMove(e: PointerEvent) {
      if (dragged) {
        const [gx, gy] = graphPoint(e.clientX, e.clientY);
        dragged.fx = gx;
        dragged.fy = gy;
        simulation.alpha(0.25).restart();
        return;
      }
      cancelAnimationFrame(rafTip);
      rafTip = requestAnimationFrame(() => {
        const [gx, gy] = graphPoint(e.clientX, e.clientY);
        const hit = nodeAt(gx, gy);
        if (hit) {
          setTooltip({ px: e.clientX, py: e.clientY, node: hit });
        } else {
          setTooltip(null);
        }
      });
    }

    function onPointerDown(e: PointerEvent) {
      if (e.button !== 0) return;
      const [gx, gy] = graphPoint(e.clientX, e.clientY);
      const hit = nodeAt(gx, gy);
      if (hit) {
        dragged = hit;
        hit.fx = hit.x ?? gx;
        hit.fy = hit.y ?? gy;
        canvasEl.setPointerCapture(e.pointerId);
        simulation.alphaTarget(0.25).restart();
      }
    }

    function endDrag(e?: PointerEvent) {
      if (!dragged) return;
      dragged.fx = null;
      dragged.fy = null;
      dragged = null;
      simulation.alphaTarget(0);
      if (e) {
        try {
          canvasEl.releasePointerCapture(e.pointerId);
        } catch {
          /* ignore */
        }
      }
    }

    function onPointerUp(e: PointerEvent) {
      endDrag(e);
    }

    canvasEl.addEventListener('pointermove', onPointerMove);
    canvasEl.addEventListener('pointerdown', onPointerDown);
    canvasEl.addEventListener('pointerup', onPointerUp);
    canvasEl.addEventListener('pointerleave', () => {
      setTooltip(null);
      endDrag();
    });

    simulation.on('tick', draw);
    simulation.alpha(1).restart();

    return () => {
      simulation.stop();
      sel.on('dblclick', null);
      sel.on('.zoom', null);
      canvasEl.removeEventListener('pointermove', onPointerMove);
      canvasEl.removeEventListener('pointerdown', onPointerDown);
      canvasEl.removeEventListener('pointerup', onPointerUp);
      cancelAnimationFrame(rafTip);
      setTooltip(null);
    };
  }, [graph]);

  const noEdges = graph.links.length === 0 && graph.nodes.length > 0;

  return (
    <div ref={containerRef} className="w-full relative">
      <div ref={wrapperRef} className="w-full cursor-grab active:cursor-grabbing">
        <canvas ref={canvasRef} className="w-full block touch-none" />
      </div>

      {tooltip && (
        <div
          className="fixed z-50 pointer-events-none max-w-[280px] rounded-lg border border-border2 bg-bg2/98 px-3 py-2 shadow-lg backdrop-blur-sm"
          style={{
            left: Math.min(tooltip.px + 12, typeof window !== 'undefined' ? window.innerWidth - 300 : 0),
            top: tooltip.py + 12,
          }}
        >
          <div className="text-[10px] font-jetbrains text-accent truncate">{tooltip.node.id}</div>
          <div className="text-xs font-sora text-text mt-0.5 leading-snug">{tooltip.node.label}</div>
          {tooltip.node.location && (
            <div className="text-[10px] font-jetbrains text-muted mt-1">{tooltip.node.location}</div>
          )}
          {(tooltip.node.hop_count != null || tooltip.node.is_seed) && (
            <div className="text-[10px] font-jetbrains text-muted/80 mt-1">
              {tooltip.node.is_seed ? 'Seed · ' : ''}
              {tooltip.node.hop_count != null ? `hop ${tooltip.node.hop_count}` : ''}
              {tooltip.node.cumulative_strength != null
                ? ` · strength ${tooltip.node.cumulative_strength.toFixed(2)}`
                : ''}
            </div>
          )}
        </div>
      )}

      <div className="flex flex-col gap-1.5 mt-2 px-1">
        <div className="flex flex-wrap items-center gap-4">
          {LEGEND_ITEMS.map((item) => (
            <div key={item.label} className="flex items-center gap-1.5">
              <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: item.color }} />
              <span className="text-[10px] font-jetbrains text-muted">{item.label}</span>
            </div>
          ))}
        </div>
        <p className="text-[10px] font-jetbrains text-muted/70 leading-relaxed">
          {noEdges
            ? 'No INFLUENCES edges in this subgraph — nodes are laid out by hop ring from the seed (same graph data the model described).'
            : 'Wheel to zoom · drag nodes · double-click background area to reset zoom.'}
        </p>
      </div>
    </div>
  );
}
