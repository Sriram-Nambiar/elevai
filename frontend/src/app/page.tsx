"use client";

import React, { useState, useEffect } from "react";
import Scene from "@/components/Scene";
import ElevaiDashboard from "@/components/ElevaiStudio";
import { Layers } from "lucide-react";

export { Scene };

export default function Page() {
  const [studioOpen, setStudioOpen] = useState(true);

  useEffect(() => {
    const handleMessage = (event: MessageEvent) => {
      if (event.data?.type === "elevai-open-studio") {
        setStudioOpen(true);
      }
    };
    window.addEventListener("message", handleMessage);
    return () => window.removeEventListener("message", handleMessage);
  }, []);

  return (
    <main className="relative w-screen h-screen overflow-hidden bg-black font-sans select-none">
      <Scene />

      {/* Floating launcher pill to toggle studio anytime */}
      <div className="absolute bottom-6 right-6 z-50">
        <button
          onClick={() => setStudioOpen(!studioOpen)}
          className="flex items-center gap-2.5 px-5 py-2.5 rounded-full border border-[#7CC9A1]/40 bg-[#1F261D]/90 hover:bg-[#33382C] text-[#F3F2E9] text-xs font-semibold backdrop-blur-md shadow-2xl transition-all hover:scale-105 hover:border-[#A7DDB7] cursor-pointer group"
        >
          <div className="w-2 h-2 rounded-full bg-[#7CC9A1] animate-pulse" />
          <Layers className="w-4 h-4 text-[#A7DDB7] group-hover:rotate-6 transition-transform" />
          <span>{studioOpen ? "Hide Modernization Studio" : "Open Modernization Studio"}</span>
        </button>
      </div>

      {/* Modernization Studio Full-Screen Workspace */}
      {studioOpen && (
        <div className="fixed inset-0 z-[600] flex flex-col bg-[#292D23] overflow-y-auto animate-in fade-in duration-200">
          <ElevaiDashboard onClose={() => setStudioOpen(false)} />
        </div>
      )}
    </main>
  );
}
