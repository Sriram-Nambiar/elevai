"use client";

import React from "react";

export interface Segment {
  id: string;
  label: string;
  category: string;
  color: string;
  polygon: [number, number][];
  confidence: number;
  review_required?: boolean;
  geometry_source?: string;
}

interface SegmentOverlayProps {
  segments: Segment[];
  visibleCategories: Record<string, boolean>;
  hoveredSegment: string | null;
  hoveredCategory?: string | null;
  onHoverSegment: (id: string | null) => void;
}

export default function SegmentOverlay({
  segments,
  visibleCategories,
  hoveredSegment,
  hoveredCategory,
  onHoverSegment,
}: SegmentOverlayProps) {
  return (
    <svg
      className="absolute inset-0 h-full w-full pointer-events-auto"
      viewBox="0 0 100 100"
      preserveAspectRatio="none"
    >
      {segments.map((seg) => {
        if (!visibleCategories[seg.category]) return null;

        const pointsString = seg.polygon
          .map(([x, y]) => `${x * 100},${y * 100}`)
          .join(" ");

        const isHovered =
          hoveredSegment === seg.id ||
          (hoveredCategory !== null && hoveredCategory !== undefined && hoveredCategory === seg.category);

        return (
          <g key={seg.id} className="cursor-pointer transition-all duration-200">
            <polygon
              points={pointsString}
              fill={seg.color}
              fillOpacity={isHovered ? 0.50 : 0.25}
              stroke={seg.color}
              strokeWidth={isHovered ? 1.5 : 0.8}
              strokeDasharray={seg.review_required ? "4,2" : isHovered ? "none" : "2,2"}
              onMouseEnter={() => onHoverSegment(seg.id)}
              onMouseLeave={() => onHoverSegment(null)}
            >
              <title>
                {seg.label} · {Math.round(seg.confidence * 100)}% detector confidence · approximate box; human review required
              </title>
            </polygon>
          </g>
        );
      })}
    </svg>
  );
}
