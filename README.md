# D&D / Classic Fantasy Token Collection

This project contains compact, double-sided, two-colour tabletop tokens organised by creature category.

Each category uses the same structure:

- `source/` — original black-and-white PNG artwork;
- `svg/` — traced vector artwork;
- `3mf/` — ready-to-print category plate;
- `previews/` — labelled visual overview;
- `manifest.json` — token names and roles;
- `README.md` — category contents and printing notes.

Each `3mf/` directory contains two project variants:

- `*-tokens.3mf` — original PrusaSlicer 2.9 project;
- `*-tokens-prusaslicer-3.0.3mf` — native PrusaSlicer 3.0 project using the new JSON project schema.

## Categories

- `goblins` — 4 tokens, approved
- `kobolds` — 4 tokens, approved
- `orcs` — 4 tokens, approved
- `hobgoblins` — 4 tokens, approved
- `gnolls` — 4 tokens, approved
- `bandits` — 4 tokens, approved
- `cultists` — 4 tokens, approved
- `undead` — 9 tokens, approved
- `animals` — 9 tokens, approved
- `elves` — 4 tokens, approved
- `wizards` — 4 tokens, approved
- `guards` — 4 tokens, approved
- `dwarves` — 4 tokens, approved
- `ogres` — 4 tokens, approved
- `trolls` — 4 tokens, ready for review
- `bugbears` — 4 tokens, ready for review
- `lizardfolk` — 4 tokens, ready for review
- `giants` — 4 tokens, ready for review
- `monstrosities` — 4 tokens, ready for review
- `oozes` — 4 tokens, ready for review
- `constructs` — 4 tokens, ready for review
- `fey` — 4 tokens, ready for review
- `fiends` — 4 tokens, ready for review
- `dragons` — 4 tokens, ready for review
- `drow` — 4 tokens, ready for review
- `duergar` — 4 tokens, ready for review
- `troglodytes` — 4 tokens, ready for review
- `bullywugs` — 4 tokens, ready for review
- `kuo-toa` — 4 tokens, ready for review
- `sahuagin` — 4 tokens, ready for review
- `myconids` — 4 tokens, ready for review
- `yuan-ti` — 4 tokens, ready for review
- `aberrations` — 4 tokens, ready for review
- `minor-elementals` — 4 tokens, ready for review
- `plant-creatures` — 4 tokens, ready for review
- `swarms-vermin` — 4 tokens, ready for review
- `monstrosities-ii` — 4 tokens, ready for review
- `monstrosities-iii` — 4 tokens, ready for review
- `fey-ii` — 4 tokens, ready for review
- `fiends-ii` — 4 tokens, ready for review
- `undead-ii` — 4 tokens, ready for review
- `lycanthropes` — 4 tokens, ready for review
- `beasts-ii` — 4 tokens, ready for review
- `aquatic-beasts` — 4 tokens, ready for review
- `dragonkin` — 4 tokens, ready for review
- `liches` — 4 tokens, ready for review
- `beholders` — 4 tokens, ready for review
- `mind-flayers` — 4 tokens, ready for review
- `greater-elementals` — 4 tokens, ready for review
- `chromatic-dragons` — 5 tokens, ready for review
- `metallic-dragons` — 5 tokens, ready for review
- `fighters` — 4 class/NPC tokens, ready for review
- `clerics` — 4 class/NPC tokens, ready for review
- `adventurer-wizards` — 4 class/NPC tokens, ready for review
- `rogues` — 4 class/NPC tokens, ready for review
- `rangers` — 4 class/NPC tokens, ready for review
- `paladins` — 4 class/NPC tokens, ready for review
- `barbarians` — 4 class/NPC tokens, ready for review
- `bards` — 4 class/NPC tokens, ready for review
- `druids` — 4 class/NPC tokens, ready for review
- `monks` — 4 class/NPC tokens, ready for review
- `sorcerers` — 4 class/NPC tokens, ready for review
- `warlocks` — 4 class/NPC tokens, ready for review
- `containers-loot` — 4 object tokens, ready for review
- `doors-passages` — 4 object tokens, ready for review
- `dungeon-features` — 4 object tokens, ready for review
- `camp-supplies` — 4 object tokens, ready for review
- `magic-objectives` — 4 object tokens, ready for review
- `cover-obstacles` — 4 object tokens, ready for review
- `floor-traps` — 4 trap tokens, ready for review
- `mechanical-traps` — 4 trap tokens, ready for review
- `magical-traps` — 4 trap tokens, ready for review
- `environmental-hazards` — 4 hazard tokens, ready for review
- `initiative-markers` — 20 numbered utility tokens, ready for review
- `conditions-body-mind` — 6 condition tokens, ready for review
- `conditions-senses-magic` — 6 condition tokens, ready for review
- `slavic-creatures` — 19 previously generated tokens

## Shared print specification

- 25 mm diameter;
- 1.0 mm total thickness;
- 0.4 mm colour inlay on each face;
- 0.2 mm central core;
- matching artwork on both faces, mirrored on the bottom;
- flush surfaces with no raised relief;
- base assigned to extruder 2;
- artwork and outer ring assigned to extruder 1;
- recommended layer height: 0.20 mm.

The original 3MF files have been checked with PrusaSlicer 2.9.6. All 3.0 variants have
been checked with PrusaSlicer 3.0.0-alpha11, including object count, manifold geometry,
25 × 25 × 1 mm dimensions, two volumes per token, and E4/E1 assignments.
