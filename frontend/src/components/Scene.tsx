"use client";

import { SylvaHero } from "@designcodeio/threeui";
import "@designcodeio/threeui/style.css";

const sylvaProps = {
  variant: "living-green",
  headingFont: "lexend",
  bodyFont: "lexend",
  headingWeight: "300",
  bodyWeight: "300",
  primaryColor: "#ffffff",
  headingSize: 63,
  bodySize: 16.5,
  headingLetterSpacing: -0.006,
};

export function Scene() {
  return (
    <div className="shader-frame">
      <SylvaHero {...(sylvaProps as any)} />
    </div>
  );
}

export default Scene;
