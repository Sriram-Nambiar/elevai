"use client";

import React, { useEffect, useState, useRef, useCallback } from "react";
import {
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Boxes,
  ShieldCheck,
  ShieldAlert,
  Layers,
  RefreshCw,
  Eye,
  UploadCloud,
  FileImage,
  Loader2,
  Sparkles,
  Camera,
  Check,
  Wrench,
  IndianRupee,
  Cpu,
  FileText,
  Download
} from "lucide-react";
import SegmentOverlay, { Segment } from "../components/SegmentOverlay";

interface CatalogItem {
  sku_id: string;
  name: string;
  category: string;
  unit_cost_inr: number;
  dimensions_mm?: Record<string, number>;
  mounting_constraints?: Record<string, any>;
  visual_attributes?: {
    material?: string;
    finish?: string;
    prompt_keywords?: string[];
  };
}

interface BomItem {
  sku_id: string;
  name: string;
  category: string;
  quantity: number | null;
  unit_cost_inr: number | null;
  extended_cost_inr: number | null;
  status: "PASS" | "FAIL" | "REVIEW";
  fit_reasons: string[];
  missing_information: string[];
}

interface EvaluationResponse {
  is_compliant: boolean;
  overall_status: "GEOMETRY_CHECKS_PASSED" | "REJECTED" | "REVIEW_REQUIRED";
  violations: string[];
  warnings: string[];
  missing_information: string[];
  bill_of_materials: BomItem[];
  total_estimated_cost_inr: number | null;
}

const CATEGORY_ORDER = [
  "wall_panel",
  "flooring",
  "car_operating_panel",
  "ceiling_lighting"
];

const CATEGORY_LABELS: Record<string, string> = {
  wall_panel: "Wall Cladding Panels",
  flooring: "Cabin Flooring & Sill",
  car_operating_panel: "Car Operating Panel",
  ceiling_lighting: "Ceiling Canopy & Lighting",
};

const CATEGORY_TAGS: Record<string, { label: string; color: string }> = {
  wall_panel: { label: "Surfaces", color: "border-blue-500/30 bg-blue-500/10 text-blue-400" },
  flooring: { label: "Sill Safety", color: "border-amber-500/30 bg-amber-500/10 text-amber-400" },
  car_operating_panel: { label: "Accessibility", color: "border-emerald-500/30 bg-emerald-500/10 text-emerald-400" },
  ceiling_lighting: { label: "Illumination", color: "border-purple-500/30 bg-purple-500/10 text-purple-400" },
};

const LAYER_CHIPS: { key: string; label: string; color: string }[] = [
  { key: "wall_panel", label: "Walls", color: "#3b82f6" },
  { key: "flooring", label: "Floor", color: "#f59e0b" },
  { key: "ceiling_lighting", label: "Ceiling", color: "#a855f7" },
  { key: "car_operating_panel", label: "COP", color: "#10b981" },
];

const API_BASE = (process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000").replace(/\/$/, "");

export default function ElevaiDashboard() {
  const [catalog, setCatalog] = useState<CatalogItem[]>([]);
  const [selectedSkus, setSelectedSkus] = useState<Record<string, string>>({});
  const [evaluation, setEvaluation] = useState<EvaluationResponse | null>(null);

  const [loading, setLoading] = useState<boolean>(true);
  const [evaluating, setEvaluating] = useState<boolean>(false);
  const [rendering, setRendering] = useState<boolean>(false);
  const [uploading, setUploading] = useState<boolean>(false);
  const [exportingPdf, setExportingPdf] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Viewport & Scene state
  const [activeScene, setActiveScene] = useState<string>("scene_01_passenger");
  const [viewMode, setViewMode] = useState<"existing" | "modernized">("modernized");
  const [rawImageUrl, setRawImageUrl] = useState<string>(
    `${API_BASE}/static/scenes/scene_01_passenger/cabin_view.jpg`
  );
  const [previewImageUrl, setPreviewImageUrl] = useState<string>(
    `${API_BASE}/static/scenes/scene_01_passenger/after_preview.jpg`
  );
  const [cabinDims, setCabinDims] = useState({ width: 1200, depth: 1400, height: 2350 });
  const [maxFlooringThickness, setMaxFlooringThickness] = useState<number>(12);
  const [isDragging, setIsDragging] = useState<boolean>(false);

  const fileInputRef = useRef<HTMLInputElement | null>(null);

  // Category visibility and segmentation state
  const [visibleLayers, setVisibleLayers] = useState<Record<string, boolean>>({
    wall_panel: true,
    flooring: true,
    car_operating_panel: true,
    ceiling_lighting: true,
  });
  const [hoveredSegment, setHoveredSegment] = useState<string | null>(null);
  const [hoveredCategory, setHoveredCategory] = useState<string | null>(null);
  const [segments, setSegments] = useState<Segment[]>([]);

  // Cross-component hover mapping
  const hoveredSegmentCategory = hoveredSegment
    ? segments.find((s) => s.id === hoveredSegment)?.category || null
    : null;
  const activeHoverCategory = hoveredCategory || hoveredSegmentCategory;

  // Fetch normalized segment overlays
  const fetchSegmentation = useCallback(async (sceneId: string = activeScene) => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/segment`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ scene_id: sceneId }),
      });
      if (!res.ok) return;
      const data = await res.json();
      setSegments(data.segments || []);
    } catch (err) {
      console.error("Segmentation error:", err);
    }
  }, [activeScene]);

  // Trigger procedural inpainting preview
  const triggerRender = useCallback(async (sceneId: string, skus: Record<string, string>) => {
    const skuList = Object.values(skus).filter(Boolean);
    if (skuList.length === 0) return;

    try {
      setRendering(true);
      const res = await fetch(`${API_BASE}/api/v1/preview/render`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          scene_id: sceneId,
          selected_skus: skuList
        }),
      });

      if (!res.ok) {
        console.warn("Inpainter render request failed with status:", res.status);
        return;
      }

      const data = await res.json();
      // Bust browser cache to display fresh composite
      const freshUrl = `${API_BASE}/static/scenes/${sceneId}/after_preview.jpg?t=${Date.now()}`;
      setPreviewImageUrl(freshUrl);
    } catch (err: any) {
      console.error("Preview rendering failed:", err);
    } finally {
      setRendering(false);
    }
  }, []);

  // Run deterministic rules engine
  const runEvaluation = useCallback(async (skus: Record<string, string>) => {
    const activeList = Object.values(skus).filter(Boolean);
    if (activeList.length === 0) return;

    try {
      setEvaluating(true);
      setError(null);
      const res = await fetch(`${API_BASE}/api/v1/rules/evaluate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          selected_skus: activeList,
          site_measurements: {
            scene_id: activeScene,
            cabin_dimensions_mm: cabinDims,
            max_allowable_flooring_thickness_mm: maxFlooringThickness,
            existing_cop: {
              mounting_height_from_floor_mm: 1000
            }
          }
        }),
      });

      if (!res.ok) throw new Error(`Rules engine error: ${res.statusText}`);
      const data = await res.json();
      setEvaluation(data);
    } catch (err: any) {
      setError(err.message || "Rule evaluation failed");
    } finally {
      setEvaluating(false);
    }
  }, [activeScene, cabinDims, maxFlooringThickness]);

  // Initial load
  useEffect(() => {
    async function initDashboard() {
      try {
        setLoading(true);
        const res = await fetch(`${API_BASE}/api/v1/catalog`);
        if (!res.ok) throw new Error(`Catalog connection failed: ${res.statusText}`);
        const data = await res.json();
        const items: CatalogItem[] = data.catalog_items || [];
        setCatalog(items);

        // Populate default SKUs
        const initialSelections: Record<string, string> = {
          wall_panel: "WALL-SS-HAIRLINE",
          flooring: "FLR-RUB-COIN",
          car_operating_panel: "COP-COL-TFT",
          ceiling_lighting: "CEIL-LED-PERIM"
        };

        // Validate that keys exist in catalog
        CATEGORY_ORDER.forEach((cat) => {
          if (!initialSelections[cat]) {
            const found = items.find((i) => i.category === cat);
            if (found) initialSelections[cat] = found.sku_id;
          }
        });

        setSelectedSkus(initialSelections);

        // Run evaluation, initial render, and fetch segmentation in parallel
        await runEvaluation(initialSelections);
        await triggerRender("scene_01_passenger", initialSelections);
        await fetchSegmentation("scene_01_passenger");
      } catch (err: any) {
        setError(err.message || "Failed to initialize Elevai Studio");
      } finally {
        setLoading(false);
      }
    }

    initDashboard();
  }, [runEvaluation, triggerRender, fetchSegmentation]);

  // Handle SKU toggle
  const handleSelectSku = (category: string, skuId: string) => {
    const updated = { ...selectedSkus, [category]: skuId };
    setSelectedSkus(updated);
    runEvaluation(updated);
    triggerRender(activeScene, updated);
  };

  // Export PDF Quotation & Engineering Spec Sheet
  async function handleDownloadQuote() {
    const activeList = Object.values(selectedSkus).filter(Boolean);
    if (activeList.length === 0) return;

    try {
      setExportingPdf(true);
      setError(null);

      const res = await fetch("http://127.0.0.1:8000/api/v1/quote/export", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          selected_skus: activeList,
          cabin_dimensions_mm: cabinDims,
          max_allowable_flooring_thickness_mm: maxFlooringThickness,
        }),
      });

      if (!res.ok) {
        throw new Error(`Failed to generate PDF quotation: ${res.statusText}`);
      }

      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "elevai_modernization_quote.pdf";
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err: any) {
      setError(err.message || "PDF quote export failed");
    } finally {
      setExportingPdf(false);
    }
  }

  const handleExportPdf = handleDownloadQuote;

  // Upload handler for cabin photo dropzone
  async function handleFileUpload(file: File) {
    if (!file.type.startsWith("image/")) {
      setError("Please drop a valid image file (JPEG or PNG).");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    try {
      setUploading(true);
      setError(null);

      const res = await fetch(`${API_BASE}/api/v1/scene/upload`, {
        method: "POST",
        body: formData,
      });

      if (!res.ok) throw new Error("Failed to process cabin image on server");
      const data = await res.json();

      setActiveScene(data.scene_id);
      const uploadedImageUrl = data.image_url.startsWith("http")
        ? data.image_url
        : `${API_BASE}${data.image_url}`;
      setRawImageUrl(`${uploadedImageUrl}?t=${Date.now()}`);

      if (data.cabin_dimensions_mm) {
        setCabinDims(data.cabin_dimensions_mm);
      }
      if (data.max_allowable_flooring_thickness_mm) {
        setMaxFlooringThickness(data.max_allowable_flooring_thickness_mm);
      }

      // Re-evaluate, generate inpainting render, and fetch segmentation for new photo
      await runEvaluation(selectedSkus);
      await triggerRender(data.scene_id, selectedSkus);
      await fetchSegmentation(data.scene_id);
      setViewMode("modernized");
    } catch (err: any) {
      setError(err.message || "Cabin upload failed");
    } finally {
      setUploading(false);
    }
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileUpload(e.dataTransfer.files[0]);
    }
  };

  const groupedCatalog = catalog.reduce<Record<string, CatalogItem[]>>((acc, item) => {
    acc[item.category] = acc[item.category] || [];
    acc[item.category].push(item);
    return acc;
  }, {});

  if (loading) {
    return (
      <div className="flex h-screen flex-col items-center justify-center bg-zinc-950 text-zinc-300">
        <div className="flex items-center space-x-3 mb-3">
          <Cpu className="h-6 w-6 animate-pulse text-amber-400" />
          <span className="font-semibold text-base tracking-wider uppercase">Elevai Studio</span>
        </div>
        <div className="flex items-center text-xs text-zinc-400">
          <Loader2 className="mr-2 h-4 w-4 animate-spin text-amber-500" />
          Loading geometric scene model & hardware catalog...
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 font-sans selection:bg-amber-500/30 selection:text-amber-200">
      {/* Top Application Bar */}
      <header className="border-b border-zinc-800/80 bg-zinc-900/70 px-6 py-3.5 backdrop-blur sticky top-0 z-30">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-amber-500 to-amber-600 font-bold text-zinc-950 shadow-md shadow-amber-500/20">
              E
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h1 className="text-sm font-semibold tracking-wider uppercase text-zinc-100">Elevai Studio</h1>
                <span className="rounded bg-amber-500/10 px-1.5 py-0.5 text-[10px] font-mono font-medium text-amber-400 border border-amber-500/30">
                  v1.0
                </span>
              </div>
              <p className="text-[11px] text-zinc-400">
                Dimension Fit Checks & Cabin Modernization Previews
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-3 text-xs">
            <div className="hidden sm:flex items-center space-x-2 rounded-lg border border-zinc-800 bg-zinc-900/60 px-3 py-1.5 font-mono text-[11px] text-zinc-300">
              <span className="text-zinc-500">CABIN:</span>
              <span className="text-amber-400 font-semibold">{cabinDims.width}</span>
              <span className="text-zinc-500">×</span>
              <span className="text-amber-400 font-semibold">{cabinDims.depth}</span>
              <span className="text-zinc-500">×</span>
              <span className="text-amber-400 font-semibold">{cabinDims.height}</span>
              <span className="text-zinc-500">mm</span>
            </div>

            <div className="flex items-center space-x-1.5 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1 text-emerald-400 text-[11px] font-medium">
              <ShieldCheck className="h-3.5 w-3.5" />
              <span>Rules Engine Live</span>
            </div>
          </div>
        </div>
      </header>

      {/* Main 3-Column Engineering Layout */}
      <main className="grid grid-cols-1 gap-6 p-6 xl:grid-cols-12 max-w-[1720px] mx-auto">
        
        {/* =================================================================== */}
        {/* LEFT COLUMN: Spatial Viewport & Before/After Inpainting Switcher    */}
        {/* =================================================================== */}
        <section className="space-y-4 xl:col-span-4 flex flex-col">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Eye className="h-4 w-4 text-zinc-400" />
              <h2 className="text-xs font-semibold tracking-wider uppercase text-zinc-300">
                Spatial Viewport
              </h2>
            </div>

            {/* Before / After Switcher Tabs */}
            <div className="flex items-center rounded-lg border border-zinc-800 bg-zinc-900/80 p-0.5 text-[11px]">
              <button
                onClick={() => setViewMode("existing")}
                className={`flex items-center space-x-1.5 rounded-md px-2.5 py-1 font-medium transition ${
                  viewMode === "existing"
                    ? "bg-zinc-800 text-zinc-100 shadow-sm"
                    : "text-zinc-400 hover:text-zinc-200"
                }`}
              >
                <Camera className="h-3 w-3" />
                <span>Existing</span>
              </button>
              <button
                onClick={() => setViewMode("modernized")}
                className={`flex items-center space-x-1.5 rounded-md px-2.5 py-1 font-medium transition ${
                  viewMode === "modernized"
                    ? "bg-amber-500/20 text-amber-300 border border-amber-500/30 shadow-sm"
                    : "text-zinc-400 hover:text-zinc-200"
                }`}
              >
                <Sparkles className="h-3 w-3 text-amber-400" />
                <span>Modernized</span>
              </button>
            </div>
          </div>

          {/* Layer Control Bar */}
          <div className="flex flex-wrap items-center justify-between gap-1.5 rounded-lg border border-zinc-800/80 bg-zinc-900/50 px-2.5 py-1.5">
            <div className="flex items-center space-x-1.5">
              <Layers className="h-3.5 w-3.5 text-zinc-400" />
              <span className="text-[10px] font-mono uppercase tracking-wider text-zinc-400">
                Layer Masks:
              </span>
            </div>
            <div className="flex flex-wrap items-center gap-1.5">
              {LAYER_CHIPS.map((chip) => {
                const isVisible = visibleLayers[chip.key] ?? true;
                const isCategoryActive = activeHoverCategory === chip.key;
                return (
                  <button
                    key={chip.key}
                    type="button"
                    onClick={() =>
                      setVisibleLayers((prev) => ({ ...prev, [chip.key]: !prev[chip.key] }))
                    }
                    onMouseEnter={() => setHoveredCategory(chip.key)}
                    onMouseLeave={() => setHoveredCategory(null)}
                    className={`rounded px-2.5 py-0.5 text-[10px] font-medium border transition-all cursor-pointer flex items-center space-x-1.5 ${
                      isVisible
                        ? isCategoryActive
                          ? "bg-zinc-700 border-zinc-500 text-zinc-100 ring-1 ring-zinc-400"
                          : "bg-zinc-800 border-zinc-650 text-zinc-200 shadow-xs hover:bg-zinc-750"
                        : "bg-zinc-950/60 border-zinc-800/60 text-zinc-500 line-through opacity-70"
                    }`}
                    title={`Toggle ${chip.label} mask visibility`}
                  >
                    <span
                      className="h-1.5 w-1.5 rounded-full"
                      style={{ backgroundColor: isVisible ? chip.color : "#52525b" }}
                    />
                    <span>{chip.label}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Hidden File Input */}
          <input
            type="file"
            ref={fileInputRef}
            className="hidden"
            accept="image/jpeg,image/png,image/webp"
            onChange={(e) => {
              if (e.target.files && e.target.files[0]) {
                handleFileUpload(e.target.files[0]);
              }
            }}
          />

          {/* Viewport Display Box */}
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            className={`relative flex-1 overflow-hidden rounded-xl border transition p-2.5 ${
              isDragging
                ? "border-amber-500 bg-amber-500/10 ring-2 ring-amber-500/20"
                : "border-zinc-800/90 bg-zinc-900/40"
            }`}
          >
            <div className="relative aspect-[3/4] w-full overflow-hidden rounded-lg bg-zinc-950 flex items-center justify-center border border-zinc-800/80 shadow-inner">
              {uploading ? (
                <div className="flex flex-col items-center justify-center space-y-2.5 text-zinc-400 p-6 text-center">
                  <Loader2 className="h-8 w-8 animate-spin text-amber-400" />
                  <span className="text-xs font-medium">Ingesting cabin scan & calibrating depth...</span>
                </div>
              ) : (
                <>
                  <img
                    src={viewMode === "modernized" ? previewImageUrl : rawImageUrl}
                    alt={viewMode === "modernized" ? "Modernized Inpainted Preview" : "Raw Cabin Scan"}
                    className="h-full w-full object-cover transition-opacity duration-300"
                  />

                  {/* Interactive SVG Segmentation Overlays when in Existing inspection view */}
                  {viewMode === "existing" && (
                    <SegmentOverlay
                      segments={segments}
                      visibleCategories={visibleLayers}
                      hoveredSegment={hoveredSegment}
                      hoveredCategory={hoveredCategory}
                      onHoverSegment={setHoveredSegment}
                    />
                  )}

                  {/* Hovered segment indicator tooltip */}
                  {viewMode === "existing" && (hoveredSegment || activeHoverCategory) && (
                    <div className="absolute bottom-12 left-1/2 -translate-x-1/2 pointer-events-none z-20">
                      {(() => {
                        const activeSeg = segments.find(
                          (s) => s.id === hoveredSegment || s.category === activeHoverCategory
                        );
                        if (!activeSeg) return null;
                        return (
                          <div className="flex items-center space-x-2 rounded-md bg-zinc-950/90 px-3 py-1 text-xs border border-zinc-700 shadow-xl backdrop-blur-md">
                            <span
                              className="h-2.5 w-2.5 rounded-full"
                              style={{ backgroundColor: activeSeg.color }}
                            />
                            <span className="font-semibold text-zinc-100">{activeSeg.label}</span>
                            <span className="font-mono text-[10px] text-zinc-400">
                              ({(activeSeg.confidence * 100).toFixed(0)}% conf)
                            </span>
                          </div>
                        );
                      })()}
                    </div>
                  )}

                  {/* Rendering Spinner Overlay */}
                  {rendering && (
                    <div className="absolute inset-0 bg-black/60 backdrop-blur-xs flex flex-col items-center justify-center space-y-2">
                      <Loader2 className="h-7 w-7 animate-spin text-amber-400" />
                      <span className="text-[11px] font-mono text-zinc-300">
                        Synthesizing perspective textures...
                      </span>
                    </div>
                  )}

                  {/* Status Indicator Tag */}
                  <div className="absolute top-2.5 left-2.5">
                    <span className={`flex items-center space-x-1.5 rounded-md px-2 py-0.5 text-[10px] font-mono font-medium backdrop-blur-md border ${
                      viewMode === "modernized"
                        ? "bg-amber-950/70 border-amber-500/40 text-amber-300"
                        : "bg-zinc-900/80 border-zinc-700/60 text-zinc-300"
                    }`}>
                      {viewMode === "modernized" ? (
                        <>
                          <Sparkles className="h-2.5 w-2.5 text-amber-400" />
                          <span>AI Modernized Preview</span>
                        </>
                      ) : (
                        <>
                          <Camera className="h-2.5 w-2.5 text-zinc-400" />
                          <span>Existing Site Scan</span>
                        </>
                      )}
                    </span>
                  </div>

                  {/* Spatial Measurement Overlays */}
                  <div className="absolute inset-0 p-2.5 pointer-events-none flex flex-col justify-between">
                    <div className="flex justify-between items-start mt-7">
                      <span className="rounded bg-black/75 px-2 py-0.5 text-[10px] font-mono text-purple-300 border border-purple-500/30 backdrop-blur-xs">
                        Ceiling: {cabinDims.width}×{cabinDims.depth}mm
                      </span>
                      <span className="rounded bg-black/75 px-2 py-0.5 text-[10px] font-mono text-emerald-300 border border-emerald-500/30 backdrop-blur-xs">
                        EN 81-70 Reach ≤1200mm
                      </span>
                    </div>
                    <div className="flex justify-between items-end">
                      <span className="rounded bg-black/75 px-2 py-0.5 text-[10px] font-mono text-blue-300 border border-blue-500/30 backdrop-blur-xs">
                        Wall H: {cabinDims.height}mm
                      </span>
                      <span className="rounded bg-black/75 px-2 py-0.5 text-[10px] font-mono text-amber-300 border border-amber-500/30 backdrop-blur-xs">
                        Sill Allowance ≤{maxFlooringThickness}mm
                      </span>
                    </div>
                  </div>
                </>
              )}
            </div>

            {/* Ingestion Dropzone Action */}
            <div
              onClick={() => fileInputRef.current?.click()}
              className="mt-2.5 flex items-center justify-center space-x-2 py-2 cursor-pointer border border-dashed border-zinc-800 rounded-lg hover:border-amber-500/50 hover:bg-zinc-900/60 bg-zinc-900/30 transition group"
            >
              <UploadCloud className="h-3.5 w-3.5 text-zinc-400 group-hover:text-amber-400 transition" />
              <span className="text-[11px] text-zinc-400 group-hover:text-zinc-200 transition">
                Drop new cabin photograph here or click to browse
              </span>
            </div>

            {/* Dimension Breakdown Metrics */}
            <div className="mt-2.5 grid grid-cols-3 gap-2 text-center text-xs">
              <div className="rounded-lg bg-zinc-900/80 p-2 border border-zinc-800/80">
                <div className="text-[10px] uppercase text-zinc-500 font-mono">Width</div>
                <div className="font-semibold text-zinc-200 font-mono">{cabinDims.width} mm</div>
              </div>
              <div className="rounded-lg bg-zinc-900/80 p-2 border border-zinc-800/80">
                <div className="text-[10px] uppercase text-zinc-500 font-mono">Depth</div>
                <div className="font-semibold text-zinc-200 font-mono">{cabinDims.depth} mm</div>
              </div>
              <div className="rounded-lg bg-zinc-900/80 p-2 border border-zinc-800/80">
                <div className="text-[10px] uppercase text-zinc-500 font-mono">Height</div>
                <div className="font-semibold text-zinc-200 font-mono">{cabinDims.height} mm</div>
              </div>
            </div>
          </div>
        </section>

        {/* =================================================================== */}
        {/* CENTER COLUMN: Hardware Package Configurator                       */}
        {/* =================================================================== */}
        <section className="space-y-4 xl:col-span-5">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Layers className="h-4 w-4 text-zinc-400" />
              <h2 className="text-xs font-semibold tracking-wider uppercase text-zinc-300">
                Hardware Configurator
              </h2>
            </div>

            <button
              onClick={() => {
                runEvaluation(selectedSkus);
                triggerRender(activeScene, selectedSkus);
              }}
              disabled={evaluating || rendering}
              className="inline-flex items-center space-x-1.5 rounded-lg border border-zinc-800 bg-zinc-900/80 hover:bg-zinc-800 px-2.5 py-1 text-[11px] font-medium text-zinc-200 transition"
            >
              <RefreshCw className={`h-3 w-3 text-amber-400 ${evaluating || rendering ? "animate-spin" : ""}`} />
              <span>Revalidate & Render</span>
            </button>
          </div>

          {error && (
            <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-3.5 text-xs text-red-300 flex items-start space-x-2">
              <AlertTriangle className="h-4 w-4 text-red-400 shrink-0 mt-0.5" />
              <div>{error}</div>
            </div>
          )}

          {/* Categorized SKU Cards */}
          <div className="space-y-4">
            {CATEGORY_ORDER.map((catKey) => {
              const items = groupedCatalog[catKey] || [];
              const categoryInfo = CATEGORY_TAGS[catKey] || { label: catKey, color: "border-zinc-700 bg-zinc-800 text-zinc-300" };
              const isCategoryHovered = activeHoverCategory === catKey;

              return (
                <div
                  key={catKey}
                  onMouseEnter={() => setHoveredCategory(catKey)}
                  onMouseLeave={() => setHoveredCategory(null)}
                  className={`rounded-xl border transition-all duration-200 p-4 ${
                    isCategoryHovered
                      ? "border-amber-500/70 bg-zinc-900/80 shadow-lg shadow-amber-500/10 ring-1 ring-amber-500/40"
                      : "border-zinc-800/80 bg-zinc-900/40"
                  }`}
                >
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center space-x-2">
                      <h3 className="text-xs font-semibold uppercase tracking-wider text-zinc-300">
                        {CATEGORY_LABELS[catKey]}
                      </h3>
                      <span className={`text-[10px] px-2 py-0.5 rounded-full border font-mono ${categoryInfo.color}`}>
                        {categoryInfo.label}
                      </span>
                    </div>
                    <span className="text-[11px] text-zinc-500 font-mono">
                      {items.length} SKUs
                    </span>
                  </div>

                  <div className="grid grid-cols-1 gap-2.5 sm:grid-cols-2">
                    {items.map((item) => {
                      const isSelected = selectedSkus[catKey] === item.sku_id;
                      const dims = item.dimensions_mm || {};
                      const thickness = dims.thickness_mm || dims.height;

                      return (
                        <button
                          key={item.sku_id}
                          onClick={() => handleSelectSku(catKey, item.sku_id)}
                          onMouseEnter={() => setHoveredCategory(catKey)}
                          onMouseLeave={() => setHoveredCategory(null)}
                          className={`group relative flex flex-col justify-between rounded-xl border p-3.5 text-left transition-all duration-200 cursor-pointer ${
                            isSelected
                              ? isCategoryHovered
                                ? "border-amber-400 bg-amber-500/20 shadow-lg shadow-amber-500/20 ring-2 ring-amber-400/80 scale-[1.01]"
                                : "border-amber-500/80 bg-amber-500/10 shadow-md shadow-amber-500/10 ring-1 ring-amber-500/30"
                              : isCategoryHovered
                              ? "border-zinc-700 bg-zinc-850/80 ring-1 ring-zinc-600/50"
                              : "border-zinc-800 bg-zinc-900/50 hover:border-zinc-700 hover:bg-zinc-900"
                          }`}
                        >
                          <div>
                            <div className="flex items-center justify-between text-[10px] font-mono text-zinc-400 mb-1">
                              <span className="font-semibold text-zinc-300">{item.sku_id}</span>
                              {isSelected ? (
                                <span className="flex items-center text-amber-400 font-medium">
                                  <Check className="h-3 w-3 mr-0.5" /> Active
                                </span>
                              ) : (
                                <span className="text-zinc-600 group-hover:text-zinc-400">Select</span>
                              )}
                            </div>

                            <div className="text-xs font-medium text-zinc-100 leading-snug line-clamp-2 mb-2">
                              {item.name}
                            </div>

                            {/* Technical Specs Tags */}
                            <div className="flex flex-wrap gap-1 text-[10px] font-mono text-zinc-400 mb-2">
                              {catKey === "flooring" && thickness && (
                                <span className="rounded bg-zinc-800/80 px-1.5 py-0.5 border border-zinc-700/60">
                                  Thk: {thickness}mm
                                </span>
                              )}
                              {catKey === "car_operating_panel" && (
                                <span className="rounded bg-zinc-800/80 px-1.5 py-0.5 border border-zinc-700/60">
                                  Reach: ≤1200mm
                                </span>
                              )}
                              {catKey === "ceiling_lighting" && (
                                <span className="rounded bg-zinc-800/80 px-1.5 py-0.5 border border-zinc-700/60">
                                  Trim: ≤200mm
                                </span>
                              )}
                              {item.visual_attributes?.finish && (
                                <span className="rounded bg-zinc-800/80 px-1.5 py-0.5 border border-zinc-700/60 capitalize">
                                  {item.visual_attributes.finish.replace(/_/g, " ")}
                                </span>
                              )}
                            </div>
                          </div>

                          <div className="pt-2 border-t border-zinc-800/60 flex items-center justify-between">
                            <span className="text-[10px] uppercase text-zinc-500">Unit Price</span>
                            <span className="text-xs font-bold font-mono text-zinc-200">
                              ₹{item.unit_cost_inr.toLocaleString("en-IN")}
                            </span>
                          </div>
                        </button>
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </div>
        </section>

        {/* =================================================================== */}
        {/* RIGHT COLUMN: Compliance Audit Badge, Violations & Itemized BOM    */}
        {/* =================================================================== */}
        <section className="space-y-4 xl:col-span-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Boxes className="h-4 w-4 text-zinc-400" />
              <h2 className="text-xs font-semibold tracking-wider uppercase text-zinc-300">
                Compliance & BOM
              </h2>
            </div>
            <button
              onClick={handleExportPdf}
              disabled={exportingPdf}
              className="inline-flex items-center space-x-1 text-[11px] font-medium text-amber-400 hover:text-amber-300 transition cursor-pointer disabled:opacity-50"
            >
              <Download className="h-3 w-3" />
              <span>PDF Export</span>
            </button>
          </div>

          {evaluation && (
            <div className="space-y-4">
              {/* Primary Visual Compliance Badge */}
              <div
                className={`rounded-xl border p-4 transition shadow-lg ${
                  evaluation.is_compliant
                    ? "border-emerald-500/40 bg-gradient-to-b from-emerald-500/15 to-emerald-950/30 text-emerald-300 shadow-emerald-500/5"
                    : evaluation.overall_status === "REJECTED"
                      ? "border-red-500/40 bg-gradient-to-b from-red-500/15 to-red-950/30 text-red-300 shadow-red-500/5"
                      : "border-amber-500/40 bg-gradient-to-b from-amber-500/15 to-amber-950/30 text-amber-200 shadow-amber-500/5"
                }`}
              >
                <div className="flex items-center space-x-3 mb-2.5">
                  {evaluation.is_compliant ? (
                    <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 shrink-0">
                      <CheckCircle2 className="h-5 w-5" />
                    </div>
                  ) : evaluation.overall_status === "REJECTED" ? (
                    <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-red-500/20 text-red-400 border border-red-500/40 shrink-0">
                      <ShieldAlert className="h-5 w-5" />
                    </div>
                  ) : (
                    <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-amber-500/20 text-amber-300 border border-amber-500/40 shrink-0">
                      <AlertTriangle className="h-5 w-5" />
                    </div>
                  )}
                  <div>
                    <div className="text-[11px] uppercase tracking-wider text-zinc-400 font-medium">
                      Audit Status
                    </div>
                    <div className="text-sm font-bold tracking-wide font-mono">
                      {evaluation.overall_status === "GEOMETRY_CHECKS_PASSED"
                        ? "DIMENSIONAL SCREEN PASSED"
                        : evaluation.overall_status === "REJECTED"
                          ? "FIT CHECK FAILED"
                          : "MORE INFORMATION NEEDED"}
                    </div>
                  </div>
                </div>

                <div className="border-t border-zinc-800/60 pt-2.5 mt-2 flex justify-between items-end">
                  <div>
                    <div className="text-[10px] uppercase text-zinc-400 font-medium">Project Total</div>
                    <div className="text-xl font-black text-zinc-100 font-mono tracking-tight">
                      {evaluation.total_estimated_cost_inr === null
                        ? "Pending measurements"
                        : `₹${evaluation.total_estimated_cost_inr.toLocaleString("en-IN")}`}
                    </div>
                  </div>
                  <div className="text-[10px] text-zinc-400 font-mono">
                    {evaluation.bill_of_materials.length} Items Total
                  </div>
                </div>

                {/* Styled CTA button right below the total project estimate */}
                <button
                  onClick={handleDownloadQuote}
                  disabled={exportingPdf}
                  className="w-full mt-3 flex items-center justify-center space-x-2 rounded-lg border border-amber-500/50 bg-amber-500/20 hover:bg-amber-500/30 px-3.5 py-2.5 text-xs font-semibold text-amber-200 transition shadow-sm cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed group"
                >
                  {exportingPdf ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin text-amber-400" />
                      <span>Compiling Engineering Spec Sheet...</span>
                    </>
                  ) : (
                    <>
                      <FileText className="h-4 w-4 text-amber-400 group-hover:scale-105 transition-transform" />
                      <span>Download Engineering Spec Sheet (PDF)</span>
                      <Download className="h-3.5 w-3.5 ml-1 text-amber-400/80" />
                    </>
                  )}
                </button>
              </div>

              {/* Explanatory Fatal Violations List */}
              {evaluation.violations.length > 0 && (
                <div className="rounded-xl border border-red-500/30 bg-red-950/20 p-3.5">
                  <div className="mb-2 flex items-center text-[11px] font-semibold uppercase tracking-wider text-red-400">
                    <XCircle className="mr-1.5 h-3.5 w-3.5" /> Fatal Violations ({evaluation.violations.length})
                  </div>
                  <ul className="space-y-2 text-[11px] text-red-300 leading-relaxed">
                    {evaluation.violations.map((v, i) => (
                      <li key={i} className="flex items-start bg-red-500/10 p-2 rounded-lg border border-red-500/20">
                        <span className="mr-2 text-red-400 font-bold shrink-0">✕</span>
                        <span>{v}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {evaluation.missing_information.length > 0 && (
                <div className="rounded-xl border border-amber-500/30 bg-amber-950/20 p-3.5">
                  <div className="mb-2 flex items-center text-[11px] font-semibold uppercase tracking-wider text-amber-300">
                    <AlertTriangle className="mr-1.5 h-3.5 w-3.5" /> Needed before a fit decision
                  </div>
                  <ul className="space-y-1.5 text-[11px] text-amber-200/90">
                    {evaluation.missing_information.map((missing, i) => (
                      <li key={`${missing}-${i}`}>• {missing}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Explanatory Site Adjustment Warnings List */}
              {evaluation.warnings.length > 0 && (
                <div className="rounded-xl border border-amber-500/30 bg-amber-950/20 p-3.5">
                  <div className="mb-2 flex items-center text-[11px] font-semibold uppercase tracking-wider text-amber-400">
                    <AlertTriangle className="mr-1.5 h-3.5 w-3.5" /> Site Adjustments ({evaluation.warnings.length})
                  </div>
                  <ul className="space-y-2 text-[11px] text-amber-300/90 leading-relaxed">
                    {evaluation.warnings.map((w, i) => (
                      <li key={i} className="flex items-start bg-amber-500/10 p-2 rounded-lg border border-amber-500/20">
                        <Wrench className="mr-2 h-3.5 w-3.5 text-amber-400 shrink-0 mt-0.5" />
                        <span>{w}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Itemized Bill of Materials (BOM) */}
              <div className="overflow-hidden rounded-xl border border-zinc-800 bg-zinc-900/40">
                <div className="border-b border-zinc-800 px-3.5 py-2.5 flex justify-between items-center bg-zinc-900/70">
                  <span className="text-[11px] font-semibold uppercase tracking-wider text-zinc-400">
                    Itemized Bill of Materials
                  </span>
                  <span className="text-[10px] font-mono text-zinc-500">
                    Tax / Duties Excl.
                  </span>
                </div>

                <div className="divide-y divide-zinc-800/60 max-h-[360px] overflow-y-auto">
                  {evaluation.bill_of_materials.map((item) => (
                    <div key={item.sku_id} className="p-3 text-xs hover:bg-zinc-900/70 transition">
                      <div className="flex justify-between items-start mb-1">
                        <span className="font-mono text-[10px] font-semibold text-amber-400">
                          {item.sku_id}
                        </span>
                        <span className="font-semibold font-mono text-zinc-100">
                          {item.extended_cost_inr === null
                            ? "Pending fit"
                            : `₹${item.extended_cost_inr.toLocaleString("en-IN")}`}
                        </span>
                      </div>
                      <div className="text-zinc-300 text-[11px] line-clamp-1 mb-1 font-medium">
                        {item.name}
                      </div>
                      <div className="flex justify-between items-center text-[10px] text-zinc-400 font-mono">
                          <span>
                            {item.quantity ?? "—"} Qty @ {item.unit_cost_inr === null
                              ? "price unavailable"
                              : `₹${item.unit_cost_inr.toLocaleString("en-IN")}`}
                          </span>
                          <span className={`px-1.5 py-0.2 rounded text-[9px] font-bold ${
                            item.status === "PASS"
                              ? "text-emerald-400 bg-emerald-500/10 border border-emerald-500/20"
                              : item.status === "FAIL"
                                ? "text-red-400 bg-red-500/10 border border-red-500/20"
                                : "text-amber-300 bg-amber-500/10 border border-amber-500/20"
                          }`}>
                          {item.status}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>

                <div className="border-t border-zinc-800 p-3 bg-zinc-900/80 flex justify-between items-center">
                  <span className="text-xs font-semibold text-zinc-300 uppercase">Estimated Total</span>
                  <span className="text-sm font-bold font-mono text-amber-400">
                    {evaluation.total_estimated_cost_inr === null
                      ? "Pending measurements"
                      : `₹${evaluation.total_estimated_cost_inr.toLocaleString("en-IN")}`}
                  </span>
                </div>
              </div>

              {/* Direct PDF Quotation & Engineering Spec Sheet Download Trigger */}
              <button
                onClick={handleDownloadQuote}
                disabled={exportingPdf}
                className="w-full flex items-center justify-center space-x-2 rounded-xl border border-amber-500/40 bg-gradient-to-r from-amber-500/20 to-amber-600/20 hover:from-amber-500/30 hover:to-amber-600/30 px-4 py-3 text-xs font-semibold text-amber-300 transition shadow-lg shadow-amber-500/5 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed group"
              >
                {exportingPdf ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin text-amber-400" />
                    <span>Compiling Engineering Spec Sheet...</span>
                  </>
                ) : (
                  <>
                    <FileText className="h-4 w-4 text-amber-400 group-hover:scale-110 transition-transform" />
                    <span>Download Engineering Spec Sheet (PDF)</span>
                    <Download className="h-3.5 w-3.5 ml-1 text-amber-400/80" />
                  </>
                )}
              </button>
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
