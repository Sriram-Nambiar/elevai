export interface CatalogItem {
  sku_id: string;
  name: string;
  category: string;
  unit_cost_inr: number;
  weight_kg?: number;
  fire_rating?: string;
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

export interface SceneProfile {
  id: string;
  name: string;
  type: string;
  archetype: "Passenger Lift" | "Hospital / Stretcher Lift" | "Panoramic / Boutique Lift";
  subtitle: string;
  dimensions_mm: { width: number; depth: number; height: number };
  max_floor_mm: number;
  door_width_mm: number;
  recommended_standard: string;
  fire_rating: string;
  capacity_persons: number;
  rated_load_kg: number;
  existing_image: string;
  modernized_image: string;
}

export const SCENE_PROFILES: SceneProfile[] = [
  {
    id: "scene_01_passenger",
    name: "Scene 01",
    type: "Standard Passenger Lift",
    archetype: "Passenger Lift",
    subtitle: "Commercial Class-A Office",
    dimensions_mm: { width: 1200, depth: 1400, height: 2350 },
    max_floor_mm: 12,
    door_width_mm: 800,
    recommended_standard: "EN 81-70 / ASME A17.1",
    fire_rating: "Class A1 (EN 13501-1 Non-combustible)",
    capacity_persons: 8,
    rated_load_kg: 630,
    existing_image: "/static/scenes/scene_01_passenger/cabin_view.jpg",
    modernized_image: "/assets/studio/cabin_modernized.jpg"
  },
  {
    id: "scene_02_hospital",
    name: "Scene 02",
    type: "Hospital Stretcher & Bed Lift",
    archetype: "Hospital / Stretcher Lift",
    subtitle: "Regional Medical Center",
    dimensions_mm: { width: 1400, depth: 2400, height: 2400 },
    max_floor_mm: 10,
    door_width_mm: 1100,
    recommended_standard: "EN 81-70 Section 5.3 (Type 3 Bed Lift)",
    fire_rating: "Class A1 (EN 13501-1 Non-combustible)",
    capacity_persons: 21,
    rated_load_kg: 1600,
    existing_image: "/assets/studio/viewport_scene.jpg",
    modernized_image: "/assets/studio/cabin_clean_surface.jpg"
  },
  {
    id: "scene_03_panoramic",
    name: "Scene 03",
    type: "Boutique Hotel Panoramic Lift",
    archetype: "Panoramic / Boutique Lift",
    subtitle: "Heritage Luxury Hotel",
    dimensions_mm: { width: 1600, depth: 1500, height: 2500 },
    max_floor_mm: 15,
    door_width_mm: 900,
    recommended_standard: "ASME A17.1 & IS 14665 Premium",
    fire_rating: "Class A1 / A2-s1,d0 Compliant",
    capacity_persons: 13,
    rated_load_kg: 1000,
    existing_image: "/static/scenes/scene_01_passenger/cabin_view.jpg",
    modernized_image: "/assets/studio/cabin_pure.jpg"
  }
];

export interface RegionalCode {
  id: string;
  name: string;
  short_code: string;
  jurisdiction: string;
  min_width_mm: number;
  min_depth_mm: number;
  min_door_width_mm: number;
  max_sill_threshold_mm: number;
  cop_min_height_mm: number;
  cop_max_height_mm: number;
  braille_mandatory: boolean;
  handrail_mandatory: boolean;
  description: string;
}

export const REGIONAL_STANDARDS: Record<string, RegionalCode> = {
  "EN_81_70": {
    id: "EN_81_70",
    name: "EN 81-70:2018",
    short_code: "EN 81-70",
    jurisdiction: "Europe & Global",
    min_width_mm: 1100,
    min_depth_mm: 1400,
    min_door_width_mm: 800,
    max_sill_threshold_mm: 12.0,
    cop_min_height_mm: 900,
    cop_max_height_mm: 1200,
    braille_mandatory: true,
    handrail_mandatory: true,
    description: "Accessibility to passenger lifts for persons including persons with disability"
  },
  "ASME_A17_1": {
    id: "ASME_A17_1",
    name: "ASME A17.1 / CSA B44",
    short_code: "ASME A17.1",
    jurisdiction: "North America (US & Canada)",
    min_width_mm: 1219, // 48 inches
    min_depth_mm: 1372, // 54 inches
    min_door_width_mm: 914, // 36 inches
    max_sill_threshold_mm: 12.7, // 0.5 inches
    cop_min_height_mm: 890,
    cop_max_height_mm: 1220,
    braille_mandatory: true,
    handrail_mandatory: false,
    description: "Safety Code for Elevators and Escalators (ADA / ICC A117.1 accessible car)"
  },
  "IS_14665": {
    id: "IS_14665",
    name: "IS 14665 / NBC 2016",
    short_code: "IS 14665",
    jurisdiction: "Bureau of Indian Standards",
    min_width_mm: 1100,
    min_depth_mm: 1300,
    min_door_width_mm: 800,
    max_sill_threshold_mm: 12.0,
    cop_min_height_mm: 900,
    cop_max_height_mm: 1200,
    braille_mandatory: true,
    handrail_mandatory: true,
    description: "Electric Traction Lifts code with National Building Code accessibility rules"
  }
};

export interface CVTelemetry {
  detector_model: string;
  depth_model: string;
  mean_iou: number;
  detections: { category: string; confidence: number; label: string }[];
  depth_disparity_range: string;
  photogrammetric_rms_mm: number;
  models: {
    zero_shot_detector: {
      name: string;
      type: string;
      mIoU: number;
      mean_precision: number;
      mean_recall: number;
      inference_latency_ms: number;
    };
    monocular_depth: {
      name: string;
      type: string;
      relative_disparity_error: string;
      edge_preservation_score: number;
      inference_latency_ms: number;
    };
    pose_calibration: {
      name: string;
      type: string;
      reprojection_rms_mm: number;
      inlier_ratio: string;
      solve_latency_ms: number;
    };
    procedural_inpainter: {
      name: string;
      type: string;
      psnr_db: number;
      ssim: number;
      blend_latency_ms: number;
    };
  };
  realtime_pipeline_total_ms: number;
  calibration_accuracy_tolerance_mm: number;
  structural_weight_safety_limit_kg: number;
}

export const DEFAULT_CV_TELEMETRY: CVTelemetry = {
  detector_model: "google/owlv2-base-patch16-ensemble",
  depth_model: "depth-anything/Depth-Anything-V2-Small-hf",
  mean_iou: 0.884,
  detections: [
    { category: "wall_panel", confidence: 0.964, label: "Back & Side Walls" },
    { category: "flooring", confidence: 0.981, label: "Sill & Cabin Floor" },
    { category: "car_operating_panel", confidence: 0.947, label: "Column Operating Panel" },
    { category: "ceiling_lighting", confidence: 0.923, label: "Ceiling Cove Troffer" },
    { category: "doors", confidence: 0.952, label: "Entrance Center-Opening" }
  ],
  depth_disparity_range: "0.14 - 3.82 m (relative normalized)",
  photogrammetric_rms_mm: 1.8,
  models: {
    zero_shot_detector: {
      name: "OWLv2 (google/owlv2-base-patch16-ensemble)",
      type: "Vision Transformer Zero-Shot Object Detection",
      mIoU: 0.884,
      mean_precision: 0.912,
      mean_recall: 0.941,
      inference_latency_ms: 142
    },
    monocular_depth: {
      name: "Depth Anything V2 Small",
      type: "Foundation Monocular Metric & Relative Depth",
      relative_disparity_error: "2.8%",
      edge_preservation_score: 0.946,
      inference_latency_ms: 48
    },
    pose_calibration: {
      name: "EPnP + RANSAC Solver",
      type: "Metric Photogrammetric Pose Estimation",
      reprojection_rms_mm: 1.8,
      inlier_ratio: "94.2%",
      solve_latency_ms: 12
    },
    procedural_inpainter: {
      name: "Texture-Aware Latent Synthesizer & Seamless Poisson Blender",
      type: "Surface Inpainting & Architectural Replacement",
      psnr_db: 36.4,
      ssim: 0.972,
      blend_latency_ms: 22
    }
  },
  realtime_pipeline_total_ms: 224,
  calibration_accuracy_tolerance_mm: 1.8,
  structural_weight_safety_limit_kg: 150.0
};


export const FALLBACK_CATALOG: CatalogItem[] = [
  {
    sku_id: "COP-COL-TFT",
    category: "car_operating_panel",
    name: "Full-Height Column COP with 7-Inch TFT & Micro-Motion Braille",
    dimensions_mm: { height: 1950, width: 260, depth: 35 },
    mounting_constraints: { min_floor_clearance_mm: 150, max_cutout_width_mm: 280, interactive_reach_max_mm: 1200 },
    visual_attributes: { material: "stainless_steel_304", finish: "hairline_satin" },
    unit_cost_inr: 54000,
    weight_kg: 14.5,
    fire_rating: "Class A1 (Non-Combustible)"
  },
  {
    sku_id: "COP-MOD-SLM",
    category: "car_operating_panel",
    name: "Surface-Mount Slim Retrofit COP (Cutout-Free)",
    dimensions_mm: { height: 1100, width: 220, depth: 22 },
    mounting_constraints: { min_floor_clearance_mm: 900, max_cutout_width_mm: 0, interactive_reach_max_mm: 1200 },
    visual_attributes: { material: "anodized_aluminum", finish: "matte_silver" },
    unit_cost_inr: 36000,
    weight_kg: 8.2,
    fire_rating: "Class A1 (Non-Combustible)"
  },
  {
    sku_id: "COP-ACC-HOR",
    category: "car_operating_panel",
    name: "Horizontal Barrier-Free Disability Auxiliary COP (EN 81-70)",
    dimensions_mm: { height: 280, width: 850, depth: 25 },
    mounting_constraints: { min_floor_clearance_mm: 900, max_cutout_width_mm: 150, interactive_reach_max_mm: 1100 },
    visual_attributes: { material: "stainless_steel_316", finish: "bead_blasted" },
    unit_cost_inr: 28000,
    weight_kg: 9.0,
    fire_rating: "Class A1 (Non-Combustible)"
  },
  {
    sku_id: "WALL-SS-HAIRLINE",
    category: "wall_panel",
    name: "304 Hairline Brushed Stainless Steel Architectural Panel",
    dimensions_mm: { height: 2100, width: 600, depth: 15 },
    visual_attributes: { material: "stainless_steel_304", finish: "hairline_brushed" },
    unit_cost_inr: 16500,
    weight_kg: 18.4,
    fire_rating: "Class A1 (EN 13501-1)"
  },
  {
    sku_id: "WALL-BRZ-BRUSHED",
    category: "wall_panel",
    name: "Architectural Brushed Bronze Satin Stainless Cladding",
    dimensions_mm: { height: 2100, width: 600, depth: 15 },
    visual_attributes: { material: "bronze_coated_steel", finish: "brushed_bronze_satin" },
    unit_cost_inr: 21500,
    weight_kg: 19.2,
    fire_rating: "Class A1 (EN 13501-1)"
  },
  {
    sku_id: "WALL-SS-BLACKPVD",
    category: "wall_panel",
    name: "Black Titanium PVD Mirror-Accent Stainless Steel Panel",
    dimensions_mm: { height: 2100, width: 600, depth: 15 },
    visual_attributes: { material: "pvd_coated_steel", finish: "black_mirror_satin" },
    unit_cost_inr: 24000,
    weight_kg: 18.8,
    fire_rating: "Class A1 (EN 13501-1)"
  },
  {
    sku_id: "WALL-LAM-OAK",
    category: "wall_panel",
    name: "Class-A Fire-Rated Architectural Natural Oak Veneer",
    dimensions_mm: { height: 2100, width: 500, depth: 18 },
    visual_attributes: { material: "fire_rated_laminate", finish: "natural_matte_timber" },
    unit_cost_inr: 13500,
    weight_kg: 12.0,
    fire_rating: "Class A2-s1,d0 (Flame Retardant)"
  },
  {
    sku_id: "WALL-LAM-WALNUT",
    category: "wall_panel",
    name: "Fluted Dark American Walnut Architectural Panel",
    dimensions_mm: { height: 2100, width: 500, depth: 20 },
    visual_attributes: { material: "engineered_timber", finish: "satin_polyurethane" },
    unit_cost_inr: 19000,
    weight_kg: 14.5,
    fire_rating: "Class B-s1,d0 (Treated Timber)"
  },
  {
    sku_id: "WALL-GLS-WHITE",
    category: "wall_panel",
    name: "Toughened Back-Painted Pure White Safety Glass Panel",
    dimensions_mm: { height: 2100, width: 450, depth: 12 },
    visual_attributes: { material: "tempered_glass", finish: "gloss_lacquered" },
    unit_cost_inr: 17500,
    weight_kg: 24.0,
    fire_rating: "Class A1 (Tempered Glass)"
  },
  {
    sku_id: "CEIL-LED-PERIM",
    category: "ceiling_lighting",
    name: "Perimeter Indirect LED Cove Suspended Canopy",
    dimensions_mm: { height: 75, width: 1350, depth: 1550 },
    visual_attributes: { material: "stainless_steel_and_acrylic", finish: "hairline_with_4000k_cove" },
    unit_cost_inr: 27000,
    weight_kg: 16.0,
    fire_rating: "Class A1 (Diffuser UL94-V0)"
  },
  {
    sku_id: "CEIL-GRD-ACRYLIC",
    category: "ceiling_lighting",
    name: "Full-Luminous Monolithic Acrylic Diffuser Ceiling",
    dimensions_mm: { height: 50, width: 1350, depth: 1550 },
    visual_attributes: { material: "optical_acrylic", finish: "milky_diffused_5000k" },
    unit_cost_inr: 23000,
    weight_kg: 13.5,
    fire_rating: "Class B-s2,d0 (Optical Grade)"
  },
  {
    sku_id: "CEIL-SPT-CANOPY",
    category: "ceiling_lighting",
    name: "Four-Spot Downlight Canopy with Brushed Titanium Border",
    dimensions_mm: { height: 60, width: 1350, depth: 1550 },
    visual_attributes: { material: "brushed_titanium_aluminum", finish: "satin_black" },
    unit_cost_inr: 21500,
    weight_kg: 15.0,
    fire_rating: "Class A1 (Metallic Troffer)"
  },
  {
    sku_id: "FLR-RUB-COIN",
    category: "flooring",
    name: "Commercial Heavy-Duty Coin-Pattern Non-Slip Rubber Flooring",
    dimensions_mm: { height: 4, width: 1400, depth: 1600, thickness_mm: 4 },
    visual_attributes: { material: "synthetic_elastomer_rubber", finish: "matte_raised_stud" },
    unit_cost_inr: 11000,
    weight_kg: 9.8,
    fire_rating: "Class Bfl-s1 (Flame Retardant)"
  },
  {
    sku_id: "FLR-GRAN-NERO",
    category: "flooring",
    name: "Nero Marquina Engineered Granite Precision Floor Tile",
    dimensions_mm: { height: 10, width: 1400, depth: 1600, thickness_mm: 10 },
    visual_attributes: { material: "engineered_granite", finish: "honed_anti_slip" },
    unit_cost_inr: 28500,
    weight_kg: 46.0,
    fire_rating: "Class A1fl (Non-Combustible Stone)"
  },
  {
    sku_id: "FLR-STN-GRANITE",
    category: "flooring",
    name: "Honed Absolute Black Engineered Granite Thin-Slab",
    dimensions_mm: { height: 10, width: 1400, depth: 1600, thickness_mm: 10 },
    visual_attributes: { material: "engineered_granite", finish: "honed_anti_slip" },
    unit_cost_inr: 26000,
    weight_kg: 44.5,
    fire_rating: "Class A1fl (Non-Combustible Stone)"
  },
  {
    sku_id: "DOR-SKN-SS304",
    category: "doors",
    name: "Flush Architectural Hairline Door Cladding Skins (Set of 2)",
    dimensions_mm: { height: 2100, width: 450, depth: 2 },
    visual_attributes: { material: "stainless_steel_304", finish: "hairline_grain" },
    unit_cost_inr: 22000,
    weight_kg: 16.0,
    fire_rating: "Class A1 (EN 81-58 Fire Tested)"
  },
  {
    sku_id: "DOR-SKN-LINEN",
    category: "doors",
    name: "Scratch-Resistant Linen-Textured Rigidized Metal Door Skins",
    dimensions_mm: { height: 2100, width: 450, depth: 2 },
    visual_attributes: { material: "textured_rigidized_steel", finish: "micro_linen_embossed" },
    unit_cost_inr: 26500,
    weight_kg: 17.5,
    fire_rating: "Class A1 (EN 81-58 Fire Tested)"
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

