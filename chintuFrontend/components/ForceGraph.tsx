'use client';

import { useRef, useEffect } from 'react';
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

export default function ForceGraph({ graph }: ForceGraphProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const container = containerRef.current;
    if (!canvas || !container || !graph.nodes.length) return;

    const width = container.clientWidth;
    const height = 380;
    const dpr = window.devicePixelRatio || 1;

    canvas.width = width * dpr;
    canvas.height = height * dpr;
    canvas.style.width = width + 'px';
    canvas.style.height = height + 'px';

    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    ctx.scale(dpr, dpr);

    const nodes: SimNode[] = graph.nodes.map((n) => ({ ...n }));
    const links: SimLink[] = graph.links.map((l) => ({
      source: l.source,
      target: l.target,
      strength: l.strength,
      polarity: l.polarity,
    }));

    const simulation = d3
      .forceSimulation<SimNode>(nodes)
      .force(
        'link',
        d3.forceLink<SimNode, SimLink>(links)
          .id((d) => d.id)
          .distance(80)
      )
      .force('charge', d3.forceManyBody().strength(-180))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collide', d3.forceCollide<SimNode>().radius((d) => getRadius(d) + 4));

    function getRadius(d: SimNode): number {
      if (d.is_seed) return 10;
      return 6 + (d.impact_score || 0) * 4;
    }

    function getNodeColor(d: SimNode): string {
      if (d.is_seed) return NODE_COLORS.seed;
      return NODE_COLORS[d.type] || NODE_COLORS.Event;
    }

    function truncate(str: string, max: number): string {
      return str.length > max ? str.slice(0, max) + '…' : str;
    }

    function draw() {
      if (!ctx) return;
      ctx.clearRect(0, 0, width, height);

      // Draw edges
      for (const link of links) {
        const src = link.source as SimNode;
        const tgt = link.target as SimNode;
        if (src.x == null || src.y == null || tgt.x == null || tgt.y == null) continue;

        const strokeWidth = 0.5 + link.strength * 2.5;

        ctx.beginPath();
        ctx.moveTo(src.x, src.y);
        ctx.lineTo(tgt.x, tgt.y);
        ctx.strokeStyle =
          link.polarity === 1
            ? 'rgba(90,143,200,0.3)'
            : 'rgba(248,81,73,0.45)';
        ctx.lineWidth = strokeWidth;

        if (link.polarity === -1) {
          ctx.setLineDash([4, 3]);
        } else {
          ctx.setLineDash([]);
        }
        ctx.stroke();
        ctx.setLineDash([]);

        // Arrowhead
        const angle = Math.atan2(tgt.y - src.y, tgt.x - src.x);
        const r = getRadius(tgt as SimNode);
        const ax = tgt.x - Math.cos(angle) * (r + 4);
        const ay = tgt.y - Math.sin(angle) * (r + 4);
        const arrowLen = 6;
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
          link.polarity === 1
            ? 'rgba(90,143,200,0.5)'
            : 'rgba(248,81,73,0.6)';
        ctx.fill();
      }

      // Draw nodes
      for (const node of nodes) {
        if (node.x == null || node.y == null) continue;
        const r = getRadius(node);
        const color = getNodeColor(node);

        // Seed outer ring
        if (node.is_seed) {
          ctx.beginPath();
          ctx.arc(node.x, node.y, r + 3, 0, Math.PI * 2);
          ctx.strokeStyle = color;
          ctx.lineWidth = 1.5;
          ctx.stroke();
        }

        // Node fill
        ctx.beginPath();
        ctx.arc(node.x, node.y, r, 0, Math.PI * 2);
        ctx.fillStyle = color;
        ctx.fill();

        // Label
        ctx.font = '9px "JetBrains Mono", monospace';
        ctx.fillStyle = 'rgba(232,230,225,0.7)';
        ctx.textAlign = 'center';
        ctx.fillText(truncate(node.label, 20), node.x, node.y + r + 12);
      }
    }

    simulation.on('tick', draw);

    return () => {
      simulation.stop();
    };
  }, [graph]);

  return (
    <div ref={containerRef} className="w-full">
      <canvas ref={canvasRef} className="w-full" />
      {/* Legend */}
      <div className="flex items-center gap-4 mt-2 px-1">
        {LEGEND_ITEMS.map((item) => (
          <div key={item.label} className="flex items-center gap-1.5">
            <div
              className="w-2.5 h-2.5 rounded-full"
              style={{ backgroundColor: item.color }}
            />
            <span className="text-[10px] font-jetbrains text-muted">{item.label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
