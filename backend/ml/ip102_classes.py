"""IP102 Agricultural Pest Dataset Class Definitions & Taxonomy Mappings.

Contains all 102 benchmark pest classes (Xiaoping Wu et al., CVPR 2019) mapped
to biological orders, common names, visual signature characteristics, and management protocols.
"""

from typing import Dict, Any, List

# 0-indexed mapping matching folder names in datasets/pests/classification (0 to 101)
IP102_CLASSES: Dict[int, Dict[str, Any]] = {
    0: {"name": "Rice Leaf Roller", "family": "caterpillar_borer", "order": "Lepidoptera", "color": "#ef4444"},
    1: {"name": "Rice Leaf Caterpillar", "family": "caterpillar_borer", "order": "Lepidoptera", "color": "#ef4444"},
    2: {"name": "Paddy Stem Maggot", "family": "fly_midge", "order": "Diptera", "color": "#64748b"},
    3: {"name": "Asiatic Rice Borer", "family": "caterpillar_borer", "order": "Lepidoptera", "color": "#ef4444"},
    4: {"name": "Yellow Rice Borer", "family": "caterpillar_borer", "order": "Lepidoptera", "color": "#ef4444"},
    5: {"name": "Rice Gall Midge", "family": "fly_midge", "order": "Diptera", "color": "#64748b"},
    6: {"name": "Rice Stemfly", "family": "fly_midge", "order": "Diptera", "color": "#64748b"},
    7: {"name": "Brown Plant Hopper", "family": "hopper", "order": "Hemiptera", "color": "#10b981"},
    8: {"name": "White Backed Plant Hopper", "family": "hopper", "order": "Hemiptera", "color": "#10b981"},
    9: {"name": "Small Brown Plant Hopper", "family": "hopper", "order": "Hemiptera", "color": "#10b981"},
    10: {"name": "Rice Water Weevil", "family": "beetle_weevil", "order": "Coleoptera", "color": "#f97316"},
    11: {"name": "Rice Leafhopper", "family": "hopper", "order": "Hemiptera", "color": "#10b981"},
    12: {"name": "Grain Spreader Thrips", "family": "thrips", "order": "Thysanoptera", "color": "#8b5cf6"},
    13: {"name": "Rice Shell Pest", "family": "beetle_weevil", "order": "Coleoptera", "color": "#f97316"},
    14: {"name": "White Grub", "family": "beetle_weevil", "order": "Coleoptera", "color": "#f97316"},
    15: {"name": "Mole Cricket", "family": "orthoptera", "order": "Orthoptera", "color": "#78350f"},
    16: {"name": "Wireworm", "family": "beetle_weevil", "order": "Coleoptera", "color": "#f97316"},
    17: {"name": "White Margined Moth", "family": "caterpillar_borer", "order": "Lepidoptera", "color": "#ef4444"},
    18: {"name": "Black Cutworm", "family": "caterpillar_borer", "order": "Lepidoptera", "color": "#ef4444"},
    19: {"name": "Large Cutworm", "family": "caterpillar_borer", "order": "Lepidoptera", "color": "#ef4444"},
    20: {"name": "Yellow Cutworm", "family": "caterpillar_borer", "order": "Lepidoptera", "color": "#ef4444"},
    21: {"name": "Red Spider Mite (Tetranychus urticae)", "family": "spider_mite", "order": "Acari", "color": "#f59e0b"},
    22: {"name": "Corn Borer (Ostrinia nubilalis)", "family": "caterpillar_borer", "order": "Lepidoptera", "color": "#ef4444"},
    23: {"name": "Armyworm (Spodoptera)", "family": "caterpillar_borer", "order": "Lepidoptera", "color": "#ef4444"},
    24: {"name": "Aphids (Aphis / Myzus / Macrosiphum)", "family": "aphids", "order": "Hemiptera", "color": "#ec4899"},
    25: {"name": "Potosia brevitarsis (Flower Chafer Beetle)", "family": "beetle_weevil", "order": "Coleoptera", "color": "#f97316"},
    26: {"name": "Peach Borer", "family": "caterpillar_borer", "order": "Lepidoptera", "color": "#ef4444"},
    27: {"name": "English Grain Aphid (Sitobion avenae)", "family": "aphids", "order": "Hemiptera", "color": "#ec4899"},
    28: {"name": "Greenbug Aphid (Schizaphis graminum)", "family": "aphids", "order": "Hemiptera", "color": "#ec4899"},
    29: {"name": "Bird Cherry-Oat Aphid", "family": "aphids", "order": "Hemiptera", "color": "#ec4899"},
    30: {"name": "Wheat Blossom Midge", "family": "fly_midge", "order": "Diptera", "color": "#64748b"},
    31: {"name": "Penthaleus major (Blue Oat Mite)", "family": "spider_mite", "order": "Acari", "color": "#f59e0b"},
    32: {"name": "Longlegged Spider Mite", "family": "spider_mite", "order": "Acari", "color": "#f59e0b"},
    33: {"name": "Wheat Phloeothrips", "family": "thrips", "order": "Thysanoptera", "color": "#8b5cf6"},
    34: {"name": "Wheat Sawfly", "family": "caterpillar_borer", "order": "Hymenoptera", "color": "#ef4444"},
    35: {"name": "Cerodonta denticornis (Grass Sheath Miner)", "family": "leaf_miner", "order": "Diptera", "color": "#14b8a6"},
    36: {"name": "Beet Fly", "family": "fly_midge", "order": "Diptera", "color": "#64748b"},
    37: {"name": "Flea Beetle (Phyllotreta)", "family": "beetle_weevil", "order": "Coleoptera", "color": "#f97316"},
    38: {"name": "Cabbage Armyworm (Mamestra brassicae)", "family": "caterpillar_borer", "order": "Lepidoptera", "color": "#ef4444"},
    39: {"name": "Beet Armyworm (Spodoptera exigua)", "family": "caterpillar_borer", "order": "Lepidoptera", "color": "#ef4444"},
    40: {"name": "Beet Spot Fly", "family": "fly_midge", "order": "Diptera", "color": "#64748b"},
    41: {"name": "Meadow Moth", "family": "caterpillar_borer", "order": "Lepidoptera", "color": "#ef4444"},
    42: {"name": "Beet Weevil", "family": "beetle_weevil", "order": "Coleoptera", "color": "#f97316"},
    43: {"name": "Serica orientalis (Chafers Beetle)", "family": "beetle_weevil", "order": "Coleoptera", "color": "#f97316"},
    44: {"name": "Alfalfa Weevil (Hypera postica)", "family": "beetle_weevil", "order": "Coleoptera", "color": "#f97316"},
    45: {"name": "Flax Budworm", "family": "caterpillar_borer", "order": "Lepidoptera", "color": "#ef4444"},
    46: {"name": "Alfalfa Plant Bug", "family": "hopper", "order": "Hemiptera", "color": "#10b981"},
    47: {"name": "Tarnished Plant Bug (Lygus lineolaris)", "family": "hopper", "order": "Hemiptera", "color": "#10b981"},
    48: {"name": "Locustoidea (Grasshopper)", "family": "orthoptera", "order": "Orthoptera", "color": "#78350f"},
    49: {"name": "Lytta polita (Blister Beetle)", "family": "beetle_weevil", "order": "Coleoptera", "color": "#f97316"},
    50: {"name": "Legume Blister Beetle", "family": "beetle_weevil", "order": "Coleoptera", "color": "#f97316"},
    51: {"name": "Blister Beetle", "family": "beetle_weevil", "order": "Coleoptera", "color": "#f97316"},
    52: {"name": "Spotted Alfalfa Aphid (Therioaphis maculata)", "family": "aphids", "order": "Hemiptera", "color": "#ec4899"},
    53: {"name": "Odontothrips loti", "family": "thrips", "order": "Thysanoptera", "color": "#8b5cf6"},
    54: {"name": "Thrips (Frankliniella / Thrips tabaci)", "family": "thrips", "order": "Thysanoptera", "color": "#8b5cf6"},
    55: {"name": "Alfalfa Seed Chalcid", "family": "fly_midge", "order": "Hymenoptera", "color": "#64748b"},
    56: {"name": "Pieris canidia (Indian Cabbage White)", "family": "caterpillar_borer", "order": "Lepidoptera", "color": "#ef4444"},
    57: {"name": "Apolygus lucorum (Green Plant Bug)", "family": "hopper", "order": "Hemiptera", "color": "#10b981"},
    58: {"name": "Limacodidae (Slug Caterpillar)", "family": "caterpillar_borer", "order": "Lepidoptera", "color": "#ef4444"},
    59: {"name": "Viteus vitifoliae (Grape Phylloxera)", "family": "aphids", "order": "Hemiptera", "color": "#ec4899"},
    60: {"name": "Colomerus vitis (Grape Erineum Mite)", "family": "spider_mite", "order": "Acari", "color": "#f59e0b"},
    61: {"name": "Brevipalpus lewisi (Citrus Flat Mite)", "family": "spider_mite", "order": "Acari", "color": "#f59e0b"},
    62: {"name": "Oides decempunctata (Grape Leaf Beetle)", "family": "beetle_weevil", "order": "Coleoptera", "color": "#f97316"},
    63: {"name": "Polyphagotarsonemus latus (Broad Mite)", "family": "spider_mite", "order": "Acari", "color": "#f59e0b"},
    64: {"name": "Pseudococcus comstocki (Mealybug)", "family": "mealybug", "order": "Hemiptera", "color": "#a855f7"},
    65: {"name": "Paranthrene regalis (Clearwing Moth)", "family": "caterpillar_borer", "order": "Lepidoptera", "color": "#ef4444"},
    66: {"name": "Ampelophaga (Grapevine Sphinx Moth)", "family": "caterpillar_borer", "order": "Lepidoptera", "color": "#ef4444"},
    67: {"name": "Lycorma delicatula (Spotted Lanternfly)", "family": "hopper", "order": "Hemiptera", "color": "#10b981"},
    68: {"name": "Xylotrechus (Tiger Longicorn Beetle)", "family": "beetle_weevil", "order": "Coleoptera", "color": "#f97316"},
    69: {"name": "Cicadella viridis (Green Leafhopper)", "family": "hopper", "order": "Hemiptera", "color": "#10b981"},
    70: {"name": "Miridae (Plant Bug)", "family": "hopper", "order": "Hemiptera", "color": "#10b981"},
    71: {"name": "Trialeurodes vaporariorum (Greenhouse Whitefly)", "family": "whitefly", "order": "Hemiptera", "color": "#0ea5e9"},
    72: {"name": "Erythroneura apicalis (Grape Leafhopper)", "family": "hopper", "order": "Hemiptera", "color": "#10b981"},
    73: {"name": "Papilio xuthus (Citrus Swallowtail Caterpillar)", "family": "caterpillar_borer", "order": "Lepidoptera", "color": "#ef4444"},
    74: {"name": "Panonychus citri (Citrus Red Mite)", "family": "spider_mite", "order": "Acari", "color": "#f59e0b"},
    75: {"name": "Phyllocoptes oleivorus (Citrus Rust Mite)", "family": "spider_mite", "order": "Acari", "color": "#f59e0b"},
    76: {"name": "Icerya purchasi (Cottony Cushion Scale)", "family": "mealybug", "order": "Hemiptera", "color": "#a855f7"},
    77: {"name": "Unaspis yanonensis (Arrowhead Scale)", "family": "scale", "order": "Hemiptera", "color": "#71717a"},
    78: {"name": "Ceroplastes rubens (Red Wax Scale)", "family": "scale", "order": "Hemiptera", "color": "#71717a"},
    79: {"name": "Chrysomphalus aonidum (Florida Red Scale)", "family": "scale", "order": "Hemiptera", "color": "#71717a"},
    80: {"name": "Parlatoria ziziphi (Black Scale)", "family": "scale", "order": "Hemiptera", "color": "#71717a"},
    81: {"name": "Nipaecoccus vastator (Spherical Mealybug)", "family": "mealybug", "order": "Hemiptera", "color": "#a855f7"},
    82: {"name": "Aleurocanthus spiniferus (Orange Spiny Whitefly)", "family": "whitefly", "order": "Hemiptera", "color": "#0ea5e9"},
    83: {"name": "Bactrocera minax (Chinese Citrus Fly)", "family": "fruit_fly", "order": "Diptera", "color": "#eab308"},
    84: {"name": "Bactrocera dorsalis (Oriental Fruit Fly)", "family": "fruit_fly", "order": "Diptera", "color": "#eab308"},
    85: {"name": "Bactrocera tsuneonis (Japanese Orange Fly)", "family": "fruit_fly", "order": "Diptera", "color": "#eab308"},
    86: {"name": "Prodenia litura (Tobacco Cutworm / Armyworm)", "family": "caterpillar_borer", "order": "Lepidoptera", "color": "#ef4444"},
    87: {"name": "Adristyrannus", "family": "beetle_weevil", "order": "Coleoptera", "color": "#f97316"},
    88: {"name": "Phyllocnistis citrella (Citrus Leafminer)", "family": "leaf_miner", "order": "Diptera", "color": "#14b8a6"},
    89: {"name": "Toxoptera citricida (Brown Citrus Aphid)", "family": "aphids", "order": "Hemiptera", "color": "#ec4899"},
    90: {"name": "Toxoptera aurantii (Black Citrus Aphid)", "family": "aphids", "order": "Hemiptera", "color": "#ec4899"},
    91: {"name": "Aphis citricola (Spirea Aphid)", "family": "aphids", "order": "Hemiptera", "color": "#ec4899"},
    92: {"name": "Scirtothrips dorsalis (Chilli Thrips)", "family": "thrips", "order": "Thysanoptera", "color": "#8b5cf6"},
    93: {"name": "Dasineura sp (Gall Midge)", "family": "fly_midge", "order": "Diptera", "color": "#64748b"},
    94: {"name": "Lawana imitata (Flatid Planthopper)", "family": "hopper", "order": "Hemiptera", "color": "#10b981"},
    95: {"name": "Salurnis marginella (Planthopper)", "family": "hopper", "order": "Hemiptera", "color": "#10b981"},
    96: {"name": "Deporaus marginatus (Mango Leaf-Cutting Weevil)", "family": "beetle_weevil", "order": "Coleoptera", "color": "#f97316"},
    97: {"name": "Chlumetia transversa (Mango Shoot Borer)", "family": "caterpillar_borer", "order": "Lepidoptera", "color": "#ef4444"},
    98: {"name": "Mango Flat Beak Leafhopper", "family": "hopper", "order": "Hemiptera", "color": "#10b981"},
    99: {"name": "Rhytidodera bowringii (Mango Longhorn Beetle)", "family": "beetle_weevil", "order": "Coleoptera", "color": "#f97316"},
    100: {"name": "Sternochetus frigidus (Mango Weevil)", "family": "beetle_weevil", "order": "Coleoptera", "color": "#f97316"},
    101: {"name": "Cicadellidae (Leafhopper / Sharpshooter)", "family": "hopper", "order": "Hemiptera", "color": "#10b981"},
}

# Family Metadata & Color Schemes for Multi-Pest YOLO Bounding Boxes
PEST_FAMILY_CONFIG: Dict[str, Dict[str, Any]] = {
    "caterpillar_borer": {
        "display_name": "Caterpillar / Borer (Lepidoptera Larva)",
        "color": (239, 68, 68),  # Red #ef4444
        "hex": "#ef4444",
        "organic_remedy": "Spray Bacillus thuringiensis (Bt kurstaki @ 2g/L) or Neem Seed Kernel Extract (5%). Handpick larvae.",
        "damage_pattern": "Chewing damage, irregular foliage holes, defoliation, and fecal frass pellets."
    },
    "aphids": {
        "display_name": "Aphids (Greenfly / Blackfly / Potato Aphid)",
        "color": (236, 72, 153),  # Pink #ec4899
        "hex": "#ec4899",
        "organic_remedy": "Cold-pressed Neem Oil (5ml/L) emulsified with mild soap spray, or spray 2% potassium salts of fatty acids.",
        "damage_pattern": "Colonial sap extraction along tender veins, leaf curling, sticky honeydew, and sooty mold."
    },
    "whitefly": {
        "display_name": "Silverleaf / Greenhouse Whiteflies (Aleyrodidae)",
        "color": (14, 165, 233),  # Sky Blue #0ea5e9
        "hex": "#0ea5e9",
        "organic_remedy": "Install yellow sticky card traps at plant canopy level. Spray insecticidal soap or Beauveria bassiana.",
        "damage_pattern": "Translucent sap-sucking nymphs under leaf surface; adults fluttering when disturbed."
    },
    "spider_mite": {
        "display_name": "Red Spider Mite / Two-Spotted Spider Mite (Acari)",
        "color": (245, 158, 11),  # Amber #f59e0b
        "hex": "#f59e0b",
        "organic_remedy": "Spray Wettable Sulfur (2g/L) or Neem oil. Increase ambient foliage humidity; rinse undersides of leaves.",
        "damage_pattern": "Dense yellow/bronze micro-stippling, fine silken webbing on leaf undersides, and leaf desiccation."
    },
    "mealybug": {
        "display_name": "Mealybugs (Cottony Pseudococcidae)",
        "color": (168, 85, 247),  # Purple #a855f7
        "hex": "#a855f7",
        "organic_remedy": "Spot dab clusters with 70% isopropyl alcohol on cotton swab, followed by systemic Neem / Horticultural oil spray.",
        "damage_pattern": "White cottony waxy clusters in leaf axils and petiole joints, stunting plant growth."
    },
    "leaf_miner": {
        "display_name": "Leaf Miner Larvae (Agromyzidae)",
        "color": (20, 184, 166),  # Teal #14b8a6
        "hex": "#14b8a6",
        "organic_remedy": "Hand-crush active larvae inside leaf mines. Spray Neem oil (Azadirachtin 0.03%) to deter adult egg deposition.",
        "damage_pattern": "Irregular winding, serpentine translucent-white tunnels carved inside leaf mesophyll."
    },
    "beetle_weevil": {
        "display_name": "Beetle / Weevil (Coleoptera)",
        "color": (249, 115, 22),  # Orange #f97316
        "hex": "#f97316",
        "organic_remedy": "Diatomaceous earth dusting around stem base. Install pheromone traps or spray Pyrethrum-based botanical extract.",
        "damage_pattern": "Shot-hole feeding punctures on foliage, notched leaf margins, and root girdling."
    },
    "thrips": {
        "display_name": "Thrips (Thysanoptera)",
        "color": (139, 92, 246),  # Violet #8b5cf6
        "hex": "#8b5cf6",
        "organic_remedy": "Install blue sticky card traps. Spray Spinosad (organic bacterial ferment) or insecticidal soap.",
        "damage_pattern": "Silvery leaf sheen with tiny dark frass specks, leaf curling, and flower bud distortion."
    },
    "hopper": {
        "display_name": "Leafhopper / Planthopper (Cicadellidae)",
        "color": (16, 185, 129),  # Emerald #10b981
        "hex": "#10b981",
        "organic_remedy": "Yellow sticky traps and spray 3% Neem oil. Encourage beneficial predators (ladybugs, lacewings).",
        "damage_pattern": "Hopperburn (yellowing and browning leaf margins from toxic saliva), wedge-shaped nymphs jumping sideways."
    },
    "fruit_fly": {
        "display_name": "Fruit Fly (Tephritidae)",
        "color": (234, 179, 8),  # Yellow #eab308
        "hex": "#eab308",
        "organic_remedy": "Hang Methyl Eugenol / Cue-lure pheromone traps. Bag developing container fruits with fine mesh.",
        "damage_pattern": "Oviposition puncture sting marks on container fruits, followed by premature fruit drop and internal rot."
    },
    "scale": {
        "display_name": "Scale Insects (Coccidae / Diaspididae)",
        "color": (113, 113, 122),  # Zinc #71717a
        "hex": "#71717a",
        "organic_remedy": "Prune heavily encrusted twigs. Spray Horticultural dormant oil or wash stems with soft soapy water.",
        "damage_pattern": "Immobile waxy or armored bumps clustered along stems and woody twigs, draining sap."
    },
    "orthoptera": {
        "display_name": "Grasshopper / Mole Cricket (Orthoptera)",
        "color": (120, 53, 15),  # Brown #78350f
        "hex": "#78350f",
        "organic_remedy": "Erect bird perches near terrace garden. Use fine exclusion netting over vegetable containers.",
        "damage_pattern": "Large ragged bites missing from leaves, chewed stem bases, and chewed root crowns."
    },
    "fly_midge": {
        "display_name": "Gall Midge / Stem Fly (Diptera)",
        "color": (100, 116, 139),  # Slate #64748b
        "hex": "#64748b",
        "organic_remedy": "Remove and incinerate onion-shoot galls. Spray 5% NSKE at early vegetative flush.",
        "damage_pattern": "Abnormal tubular gall formation (silver shoots / onion shoot galls), terminal bud suppression."
    }
}
