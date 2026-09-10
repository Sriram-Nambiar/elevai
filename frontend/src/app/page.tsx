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
  Cpu
} from "lucide-react";

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
  quantity: number;
  unit_cost_inr: number;
  extended_cost_inr: number;
  status: "PASS" | "FAIL";
}

interface EvaluationResponse {
  is_compliant: boolean;
  overall_status: "APPROVED" | "REJECTED";
  violations: string[];
  warnings: string[];
  bill_of_materials: BomItem[];
  total_estimated_cost_inr: number;
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
  car_operating_panel: "Car Operating Panel (EN 81-70)",
  ceiling_lighting: "Ceiling Canopy & Lighting",
};

const CATEGORY_TAGS: Record<string, { label: string; color: string }> = {
  wall_panel: { label: "Surfaces", color: "border-blue-500/30 bg-blue-500/10 text-blue-400" },
  flooring: { label: "Sill Safety", color: "border-amber-500/30 bg-amber-500/10 text-amber-400" },
  car_operating_panel: { label: "Accessibility", color: "border-emerald-500/30 bg-emerald-500/10 text-emerald-400" },
  ceiling_lighting: { label: "Illumination", color: "border-purple-500/30 bg-purple-500/10 text-purple-400" },
};

const API_BASE = "http://127.0.0.1:8000";

export default function ElevaiDashboard() {
  const [catalog, setCatalog] = useState<CatalogItem[]>([]);
  const [selectedSkus, setSelectedSkus] = useState<Record<string, string>>({});
  const [evaluation, setEvaluation] = useState<EvaluationResponse | null>(null);

  const [loading, setLoading] = useState<boolean>(true);
  const [evaluating, setEvaluating] = useState<boolean>(false);
  const [rendering, setRendering] = useState<boolean>(false);
  const [uploading, setUploading] = useState<boolean>(false);
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

        // Run evaluation and initial render in parallel
        await runEvaluation(initialSelections);
        await triggerRender("scene_01_passenger", initialSelections);
      } catch (err: any) {
        setError(err.message || "Failed to initialize Elevai Studio");
      } finally {
        setLoading(false);
      }
    }

    initDashboard();
  }, [runEvaluation, triggerRender]);

  // Handle SKU toggle
  const handleSelectSku = (category: string, skuId: string) => {
    const updated = { ...selectedSkus, [category]: skuId };
    setSelectedSkus(updated);
    runEvaluation(updated);
    triggerRender(activeScene, updated);
  };

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
      setRawImageUrl(`${data.image_url}?t=${Date.now()}`);

      if (data.cabin_dimensions_mm) {
        setCabinDims(data.cabin_dimensions_mm);
      }
      if (data.max_allowable_flooring_thickness_mm) {
        setMaxFlooringThickness(data.max_allowable_flooring_thickness_mm);
      }

      // Re-evaluate and generate inpainting render for new photo
      await runEvaluation(selectedSkus);
      await triggerRender(data.scene_id, selectedSkus);
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
                Spatial Compliance Auditing (EN 81-70) & Generative Cabin Modernization
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

              return (
                <div
                  key={catKey}
                  className="rounded-xl border border-zinc-800/80 bg-zinc-900/40 p-4 transition"
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
                          className={`group relative flex flex-col justify-between rounded-xl border p-3.5 text-left transition cursor-pointer ${
                            isSelected
                              ? "border-amber-500/80 bg-amber-500/10 shadow-md shadow-amber-500/10 ring-1 ring-amber-500/30"
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
          <div className="flex items-center space-x-2">
            <Boxes className="h-4 w-4 text-zinc-400" />
            <h2 className="text-xs font-semibold tracking-wider uppercase text-zinc-300">
              Compliance & BOM
            </h2>
          </div>

          {evaluation && (
            <div className="space-y-4">
              {/* Primary Visual Compliance Badge */}
              <div
                className={`rounded-xl border p-4 transition shadow-lg ${
                  evaluation.is_compliant
                    ? "border-emerald-500/40 bg-gradient-to-b from-emerald-500/15 to-emerald-950/30 text-emerald-300 shadow-emerald-500/5"
                    : "border-red-500/40 bg-gradient-to-b from-red-500/15 to-red-950/30 text-red-300 shadow-red-500/5"
                }`}
              >
                <div className="flex items-center space-x-3 mb-2.5">
                  {evaluation.is_compliant ? (
                    <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 shrink-0">
                      <CheckCircle2 className="h-5 w-5" />
                    </div>
                  ) : (
                    <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-red-500/20 text-red-400 border border-red-500/40 shrink-0">
                      <ShieldAlert className="h-5 w-5" />
                    </div>
                  )}
                  <div>
                    <div className="text-[11px] uppercase tracking-wider text-zinc-400 font-medium">
                      Audit Status
                    </div>
                    <div className="text-sm font-bold tracking-wide font-mono">
                      {evaluation.overall_status === "APPROVED"
                        ? "APPROVED (EN 81-70 PASS)"
                        : "REJECTED (CLEARANCE BREACH)"}
                    </div>
                  </div>
                </div>

                <div className="border-t border-zinc-800/60 pt-2.5 mt-2 flex justify-between items-end">
                  <div>
                    <div className="text-[10px] uppercase text-zinc-400 font-medium">Project Total</div>
                    <div className="text-xl font-black text-zinc-100 font-mono tracking-tight">
                      ₹{evaluation.total_estimated_cost_inr.toLocaleString("en-IN")}
                    </div>
                  </div>
                  <div className="text-[10px] text-zinc-400 font-mono">
                    {evaluation.bill_of_materials.length} Items Total
                  </div>
                </div>
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
                          ₹{item.extended_cost_inr.toLocaleString("en-IN")}
                        </span>
                      </div>
                      <div className="text-zinc-300 text-[11px] line-clamp-1 mb-1 font-medium">
                        {item.name}
                      </div>
                      <div className="flex justify-between items-center text-[10px] text-zinc-400 font-mono">
                        <span>{item.quantity} Qty @ ₹{item.unit_cost_inr.toLocaleString("en-IN")}</span>
                        <span className={`px-1.5 py-0.2 rounded text-[9px] font-bold ${
                          item.status === "PASS"
                            ? "text-emerald-400 bg-emerald-500/10 border border-emerald-500/20"
                            : "text-red-400 bg-red-500/10 border border-red-500/20"
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
                    ₹{evaluation.total_estimated_cost_inr.toLocaleString("en-IN")}
                  </span>
                </div>
              </div>
            </div>
          )}
        </section>
      </main>
    </div>
  );
}