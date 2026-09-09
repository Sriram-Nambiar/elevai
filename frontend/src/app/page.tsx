"use client";

import React, { useEffect, useState } from "react";
import { 
  CheckCircle2, 
  AlertTriangle, 
  XCircle, 
  Boxes, 
  ShieldCheck, 
  Layers, 
  RefreshCw 
} from "lucide-react";

interface CatalogItem {
  sku_id: string;
  name: string;
  category: string;
  unit_cost_inr: number;
  dimensions_mm?: Record<string, number>;
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

const CATEGORY_LABELS: Record<string, string> = {
  wall_panel: "Wall Cladding Panels",
  flooring: "Cabin Flooring",
  car_operating_panel: "Car Operating Panel (COP)",
  ceiling_lighting: "Ceiling & Lighting",
};

export default function ElevaiDashboard() {
  const [catalog, setCatalog] = useState<CatalogItem[]>([]);
  const [selectedSkus, setSelectedSkus] = useState<Record<string, string>>({});
  const [evaluation, setEvaluation] = useState<EvaluationResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [evaluating, setEvaluating] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch catalog from FastAPI backend
  useEffect(() => {
    async function loadCatalog() {
      try {
        setLoading(true);
        const res = await fetch("http://127.0.0.1:8000/api/v1/catalog");
        if (!res.ok) throw new Error(`Failed to load catalog: ${res.statusText}`);
        const data = await res.json();
        const items: CatalogItem[] = data.catalog_items || [];
        setCatalog(items);

        // Auto-select first item of each category
        const initialSelections: Record<string, string> = {};
        Object.keys(CATEGORY_LABELS).forEach((cat) => {
          const match = items.find((i) => i.category === cat);
          if (match) initialSelections[cat] = match.sku_id;
        });
        setSelectedSkus(initialSelections);
      } catch (err: any) {
        setError(err.message || "Failed to connect to Elevai API");
      } finally {
        setLoading(false);
      }
    }
    loadCatalog();
  }, []);

  // Trigger Rules Engine Evaluation
  async function runEvaluation(skusToTest?: Record<string, string>) {
    const activeSkus = Object.values(skusToTest || selectedSkus).filter(Boolean);
    if (activeSkus.length === 0) return;

    try {
      setEvaluating(true);
      const res = await fetch("http://127.0.0.1:8000/api/v1/rules/evaluate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ selected_skus: activeSkus }),
      });
      if (!res.ok) throw new Error("Evaluation request failed");
      const result: EvaluationResponse = await res.json();
      setEvaluation(result);
    } catch (err: any) {
      setError(err.message || "Validation failed");
    } finally {
      setEvaluating(false);
    }
  }

  // Handle SKU selection toggle
  const handleSelect = (category: string, skuId: string) => {
    const updated = { ...selectedSkus, [category]: skuId };
    setSelectedSkus(updated);
    runEvaluation(updated);
  };

  const groupedCatalog = catalog.reduce<Record<string, CatalogItem[]>>((acc, item) => {
    acc[item.category] = acc[item.category] || [];
    acc[item.category].push(item);
    return acc;
  }, {});

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center bg-zinc-950 text-zinc-300">
        <RefreshCw className="mr-3 h-5 w-5 animate-spin text-amber-500" />
        Initializing Elevai Platform & Hardware Catalog...
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 font-sans">
      {/* Header Bar */}
      <header className="border-b border-zinc-800 bg-zinc-900/60 px-8 py-4 backdrop-blur">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-400 font-bold text-lg">
              E
            </div>
            <div>
              <h1 className="text-lg font-semibold tracking-wide">Elevai Studio</h1>
              <p className="text-xs text-zinc-400">EN 81-70 Compliance & Modular Fit Engineering</p>
            </div>
          </div>
          <div className="flex items-center space-x-3 text-xs">
            <span className="flex items-center rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1 text-emerald-400">
              <ShieldCheck className="mr-1.5 h-3.5 w-3.5" /> Engine Active
            </span>
            <span className="rounded-md border border-zinc-800 bg-zinc-800 px-3 py-1 text-zinc-400">
              Scene: scene_01_passenger (1200 × 1400 × 2350 mm)
            </span>
          </div>
        </div>
      </header>

      {/* Main Grid Workspace */}
      <main className="grid grid-cols-1 gap-6 p-8 lg:grid-cols-12">
        {/* Left Panel: Hardware Customizer (7 cols) */}
        <section className="space-y-6 lg:col-span-7">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Layers className="h-5 w-5 text-zinc-400" />
              <h2 className="text-sm font-semibold tracking-wider uppercase text-zinc-300">
                Modernization Package
              </h2>
            </div>
            <button
              onClick={() => runEvaluation()}
              disabled={evaluating}
              className="inline-flex items-center rounded-md bg-zinc-800 hover:bg-zinc-700 px-3 py-1.5 text-xs font-medium text-zinc-200 transition"
            >
              <RefreshCw className={`mr-1.5 h-3.5 w-3.5 ${evaluating ? "animate-spin" : ""}`} />
              Re-evaluate Fit
            </button>
          </div>

          {error && (
            <div className="rounded-lg border border-red-500/30 bg-red-500/10 p-4 text-xs text-red-400">
              {error}
            </div>
          )}

          {Object.entries(CATEGORY_LABELS).map(([catKey, label]) => {
            const items = groupedCatalog[catKey] || [];
            return (
              <div key={catKey} className="rounded-xl border border-zinc-800/80 bg-zinc-900/40 p-5">
                <h3 className="text-xs font-semibold uppercase tracking-wider text-zinc-400 mb-3">
                  {label}
                </h3>
                <div className="grid grid-cols-1 gap-2.5 sm:grid-cols-2">
                  {items.map((item) => {
                    const isSelected = selectedSkus[catKey] === item.sku_id;
                    return (
                      <button
                        key={item.sku_id}
                        onClick={() => handleSelect(catKey, item.sku_id)}
                        className={`group relative flex flex-col justify-between rounded-lg border p-3.5 text-left transition ${
                          isSelected
                            ? "border-amber-500/60 bg-amber-500/5 shadow-sm shadow-amber-500/10"
                            : "border-zinc-800 bg-zinc-900/30 hover:border-zinc-700 hover:bg-zinc-900/80"
                        }`}
                      >
                        <div>
                          <div className="flex items-center justify-between text-xs font-mono text-zinc-400 mb-1">
                            <span>{item.sku_id}</span>
                            {isSelected && (
                              <span className="h-1.5 w-1.5 rounded-full bg-amber-400" />
                            )}
                          </div>
                          <div className="text-xs font-medium text-zinc-200 leading-snug line-clamp-2">
                            {item.name}
                          </div>
                        </div>
                        <div className="mt-3 text-xs font-semibold text-zinc-400">
                          ₹{item.unit_cost_inr.toLocaleString("en-IN")}
                        </div>
                      </button>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </section>

        {/* Right Panel: Fit Validation & BOM (5 cols) */}
        <section className="space-y-6 lg:col-span-5">
          <div className="flex items-center space-x-2">
            <Boxes className="h-5 w-5 text-zinc-400" />
            <h2 className="text-sm font-semibold tracking-wider uppercase text-zinc-300">
              Audit & Bill of Materials
            </h2>
          </div>

          {evaluation && (
            <div className="space-y-4">
              {/* Verdict Banner */}
              <div
                className={`flex items-center justify-between rounded-xl border p-4 ${
                  evaluation.is_compliant
                    ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-300"
                    : "border-red-500/30 bg-red-500/10 text-red-300"
                }`}
              >
                <div className="flex items-center space-x-3">
                  {evaluation.is_compliant ? (
                    <CheckCircle2 className="h-6 w-6 text-emerald-400" />
                  ) : (
                    <XCircle className="h-6 w-6 text-red-400" />
                  )}
                  <div>
                    <div className="font-semibold text-sm tracking-wide">
                      {evaluation.overall_status === "APPROVED"
                        ? "Configuration Approved"
                        : "Dimensional Breach Detected"}
                    </div>
                    <div className="text-xs opacity-80">
                      {evaluation.is_compliant
                        ? "Meets EN 81-70 envelope and cabin clearance bounds."
                        : `${evaluation.violations.length} fatal clearance violation(s) identified.`}
                    </div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-xs uppercase tracking-wider text-zinc-400">Total Project</div>
                  <div className="text-base font-bold text-zinc-100">
                    ₹{evaluation.total_estimated_cost_inr.toLocaleString("en-IN")}
                  </div>
                </div>
              </div>

              {/* Violations Block */}
              {evaluation.violations.length > 0 && (
                <div className="rounded-xl border border-red-500/20 bg-zinc-900/40 p-4">
                  <div className="mb-2 flex items-center text-xs font-semibold uppercase tracking-wider text-red-400">
                    <XCircle className="mr-1.5 h-4 w-4" /> Violations ({evaluation.violations.length})
                  </div>
                  <ul className="space-y-1.5 text-xs text-red-300/90">
                    {evaluation.violations.map((v, i) => (
                      <li key={i} className="flex items-start">
                        <span className="mr-2 text-red-500">•</span>
                        <span>{v}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Warnings Block */}
              {evaluation.warnings.length > 0 && (
                <div className="rounded-xl border border-amber-500/20 bg-zinc-900/40 p-4">
                  <div className="mb-2 flex items-center text-xs font-semibold uppercase tracking-wider text-amber-400">
                    <AlertTriangle className="mr-1.5 h-4 w-4" /> Site Adjustments (
                    {evaluation.warnings.length})
                  </div>
                  <ul className="space-y-1.5 text-xs text-amber-300/90">
                    {evaluation.warnings.map((w, i) => (
                      <li key={i} className="flex items-start">
                        <span className="mr-2 text-amber-500">•</span>
                        <span>{w}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Itemized BOM Table */}
              <div className="overflow-hidden rounded-xl border border-zinc-800 bg-zinc-900/40">
                <div className="border-b border-zinc-800 px-4 py-3 text-xs font-semibold uppercase tracking-wider text-zinc-400">
                  Itemized BOM Output
                </div>
                <div className="divide-y divide-zinc-800/60">
                  {evaluation.bill_of_materials.map((item) => (
                    <div key={item.sku_id} className="flex items-center justify-between p-3.5 text-xs">
                      <div className="space-y-0.5">
                        <div className="font-mono text-zinc-400 text-[11px]">{item.sku_id}</div>
                        <div className="font-medium text-zinc-200 line-clamp-1 max-w-[220px]">
                          {item.name}
                        </div>
                        <div className="text-[11px] text-zinc-400">
                          {item.quantity} unit{item.quantity > 1 ? "s" : ""} @ ₹
                          {item.unit_cost_inr.toLocaleString("en-IN")}
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="font-semibold text-zinc-200">
                          ₹{item.extended_cost_inr.toLocaleString("en-IN")}
                        </div>
                        <span
                          className={`inline-block rounded px-1.5 py-0.5 text-[10px] font-semibold ${
                            item.status === "PASS"
                              ? "bg-emerald-500/10 text-emerald-400"
                              : "bg-red-500/10 text-red-400"
                          }`}
                        >
                          {item.status}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </section>
      </main>
    </div>
  );
}