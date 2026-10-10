export interface CatalogItem {
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

export interface Recommendation {
  profile: string;
  label: string;
  selected_skus: string[];
  estimated_cost_inr: number;
  reasons: string[];
  review_required: boolean;
}

export const FALLBACK_CATALOG: CatalogItem[] = [
  {
    sku_id: "COP-COL-TFT",
    category: "car_operating_panel",
    name: "Full-Height Column COP with 7-Inch TFT & Micro-Motion Braille",
    dimensions_mm: { height: 1950, width: 260, depth: 35 },
    mounting_constraints: { min_floor_clearance_mm: 150, max_cutout_width_mm: 280, interactive_reach_max_mm: 1200 },
    visual_attributes: { material: "stainless_steel_304", finish: "hairline_satin" },
    unit_cost_inr: 54000
  },
  {
    sku_id: "COP-MOD-SLM",
    category: "car_operating_panel",
    name: "Surface-Mount Slim Retrofit COP (Cutout-Free)",
    dimensions_mm: { height: 1100, width: 220, depth: 22 },
    mounting_constraints: { min_floor_clearance_mm: 900, max_cutout_width_mm: 0, interactive_reach_max_mm: 1200 },
    visual_attributes: { material: "anodized_aluminum", finish: "matte_silver" },
    unit_cost_inr: 36000
  },
  {
    sku_id: "COP-ACC-HOR",
    category: "car_operating_panel",
    name: "Horizontal Barrier-Free Disability Auxiliary COP (EN 81-70)",
    dimensions_mm: { height: 280, width: 850, depth: 25 },
    mounting_constraints: { min_floor_clearance_mm: 900, max_cutout_width_mm: 150, interactive_reach_max_mm: 1100 },
    visual_attributes: { material: "stainless_steel_316", finish: "bead_blasted" },
    unit_cost_inr: 28000
  },
  {
    sku_id: "WALL-SS-HAIRLINE",
    category: "wall_panel",
    name: "304 Hairline Brushed Stainless Steel Architectural Panel",
    dimensions_mm: { height: 2100, width: 600, depth: 15 },
    visual_attributes: { material: "stainless_steel_304", finish: "hairline_brushed" },
    unit_cost_inr: 16500
  },
  {
    sku_id: "WALL-BRZ-BRUSHED",
    category: "wall_panel",
    name: "Architectural Brushed Bronze Satin Stainless Cladding",
    dimensions_mm: { height: 2100, width: 600, depth: 15 },
    visual_attributes: { material: "bronze_coated_steel", finish: "brushed_bronze_satin" },
    unit_cost_inr: 21500
  },
  {
    sku_id: "WALL-SS-BLACKPVD",
    category: "wall_panel",
    name: "Black Titanium PVD Mirror-Accent Stainless Steel Panel",
    dimensions_mm: { height: 2100, width: 600, depth: 15 },
    visual_attributes: { material: "pvd_coated_steel", finish: "black_mirror_satin" },
    unit_cost_inr: 24000
  },
  {
    sku_id: "WALL-LAM-OAK",
    category: "wall_panel",
    name: "Class-A Fire-Rated Architectural Natural Oak Veneer",
    dimensions_mm: { height: 2100, width: 500, depth: 18 },
    visual_attributes: { material: "fire_rated_laminate", finish: "natural_matte_timber" },
    unit_cost_inr: 13500
  },
  {
    sku_id: "WALL-LAM-WALNUT",
    category: "wall_panel",
    name: "Fluted Dark American Walnut Architectural Panel",
    dimensions_mm: { height: 2100, width: 500, depth: 20 },
    visual_attributes: { material: "engineered_timber", finish: "satin_polyurethane" },
    unit_cost_inr: 19000
  },
  {
    sku_id: "WALL-GLS-WHITE",
    category: "wall_panel",
    name: "Toughened Back-Painted Pure White Safety Glass Panel",
    dimensions_mm: { height: 2100, width: 450, depth: 12 },
    visual_attributes: { material: "tempered_glass", finish: "gloss_lacquered" },
    unit_cost_inr: 17500
  },
  {
    sku_id: "CEIL-LED-PERIM",
    category: "ceiling_lighting",
    name: "Perimeter Indirect LED Cove Suspended Canopy",
    dimensions_mm: { height: 75, width: 1350, depth: 1550 },
    visual_attributes: { material: "stainless_steel_and_acrylic", finish: "hairline_with_4000k_cove" },
    unit_cost_inr: 27000
  },
  {
    sku_id: "CEIL-GRD-ACRYLIC",
    category: "ceiling_lighting",
    name: "Full-Luminous Monolithic Acrylic Diffuser Ceiling",
    dimensions_mm: { height: 50, width: 1350, depth: 1550 },
    visual_attributes: { material: "optical_acrylic", finish: "milky_diffused_5000k" },
    unit_cost_inr: 23000
  },
  {
    sku_id: "CEIL-SPT-CANOPY",
    category: "ceiling_lighting",
    name: "Four-Spot Downlight Canopy with Brushed Titanium Border",
    dimensions_mm: { height: 60, width: 1350, depth: 1550 },
    visual_attributes: { material: "brushed_titanium_aluminum", finish: "satin_black" },
    unit_cost_inr: 21500
  },
  {
    sku_id: "FLR-RUB-COIN",
    category: "flooring",
    name: "Commercial Heavy-Duty Coin-Pattern Non-Slip Rubber Flooring",
    dimensions_mm: { height: 4, width: 1400, depth: 1600, thickness_mm: 4 },
    visual_attributes: { material: "synthetic_elastomer_rubber", finish: "matte_raised_stud" },
    unit_cost_inr: 11000
  },
  {
    sku_id: "FLR-GRAN-NERO",
    category: "flooring",
    name: "Nero Marquina Engineered Granite Precision Floor Tile",
    dimensions_mm: { height: 10, width: 1400, depth: 1600, thickness_mm: 10 },
    visual_attributes: { material: "engineered_granite", finish: "honed_anti_slip" },
    unit_cost_inr: 28500
  },
  {
    sku_id: "FLR-STN-GRANITE",
    category: "flooring",
    name: "Honed Absolute Black Engineered Granite Thin-Slab",
    dimensions_mm: { height: 10, width: 1400, depth: 1600, thickness_mm: 10 },
    visual_attributes: { material: "engineered_granite", finish: "honed_anti_slip" },
    unit_cost_inr: 26000
  },
  {
    sku_id: "DOR-SKN-SS304",
    category: "doors",
    name: "Flush Architectural Hairline Door Cladding Skins (Set of 2)",
    dimensions_mm: { height: 2100, width: 450, depth: 2 },
    visual_attributes: { material: "stainless_steel_304", finish: "hairline_grain" },
    unit_cost_inr: 22000
  },
  {
    sku_id: "DOR-SKN-LINEN",
    category: "doors",
    name: "Scratch-Resistant Linen-Textured Rigidized Metal Door Skins",
    dimensions_mm: { height: 2100, width: 450, depth: 2 },
    visual_attributes: { material: "textured_rigidized_steel", finish: "micro_linen_embossed" },
    unit_cost_inr: 26500
  }
];

export const DEFAULT_SELECTED_SKUS: Record<string, string> = {
  wall_panel: "WALL-SS-HAIRLINE",
  flooring: "FLR-RUB-COIN",
  car_operating_panel: "COP-COL-TFT",
  ceiling_lighting: "CEIL-LED-PERIM",
  doors: "DOR-SKN-SS304"
};

export const DEFAULT_RECOMMENDATIONS: Recommendation[] = [
  {
    profile: "executive_prestige",
    label: "Executive Prestige (Architectural Bronze & Granite)",
    selected_skus: ["WALL-BRZ-BRUSHED", "FLR-GRAN-NERO", "COP-COL-TFT", "CEIL-LED-PERIM", "DOR-SKN-SS304"],
    estimated_cost_inr: 131000,
    reasons: ["Warm architectural bronze finishes", "Heavy-duty Nero Marquina stone floor", "High-contrast TFT call display"],
    review_required: false
  },
  {
    profile: "high_traffic_commercial",
    label: "High-Traffic Commercial (Brushed 304 & Coin Rubber)",
    selected_skus: ["WALL-SS-HAIRLINE", "FLR-RUB-COIN", "COP-MOD-SLM", "CEIL-GRD-ACRYLIC", "DOR-SKN-LINEN"],
    estimated_cost_inr: 109500,
    reasons: ["Anti-scratch linen metal door skin", "Slip-resistant coin rubber floor", "High-durability hairline cladding"],
    review_required: false
  },
  {
    profile: "hospitality_warm_timber",
    label: "Hospitality Warm (Natural Oak Veneer & Indirect Cove)",
    selected_skus: ["WALL-LAM-OAK", "FLR-STN-GRANITE", "COP-ACC-HOR", "CEIL-SPT-CANOPY", "DOR-SKN-SS304"],
    estimated_cost_inr: 101000,
    reasons: ["Natural Class-A fire rated timber veneer", "EN 81-70 horizontal disability auxiliary panel", "Warm ambient canopy lighting"],
    review_required: false
  }
];
