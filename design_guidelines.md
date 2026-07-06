{
  "product": {
    "name": "NRG Agent OS — Phase 0 Source Lock Console",
    "phase_scope": "PHASE 0 ONLY (Source Intake + Classification + Contradiction Preservation + Artifact Generation + WAIT)",
    "brand_attributes": [
      "forensic",
      "disciplined",
      "mission-control",
      "operator-first",
      "high-signal / low-noise",
      "non-cinematic (explicitly NOT JARVIS)",
      "ADHD-friendly (clear, direct, structured)"
    ],
    "north_star_actions": [
      "Run ingestion pipeline",
      "Inspect sources + authority tiers",
      "Review preserved contradictions",
      "Review Phase 0 artifacts",
      "Operator Accept → freeze into WAIT mode"
    ]
  },

  "visual_personality": {
    "style_fusion": [
      "Swiss/International Typographic Style (grid discipline, hierarchy)",
      "Mission-control console (status codification, dense tables)",
      "Modern enterprise dark mode (soft blacks, layered surfaces)",
      "Subtle industrial texture (grain/noise overlays)"
    ],
    "do_not": [
      "No neon cyberpunk",
      "No cinematic HUD glow overload",
      "No purple gradients",
      "No flashy animated backgrounds",
      "No centered reading layouts"
    ],
    "density_strategy": {
      "default": "dense",
      "escape_hatches": [
        "Collapsible sections",
        "Resizable panels",
        "Drawer for details",
        "Sticky table header + column visibility"
      ]
    }
  },

  "typography": {
    "font_pairing": {
      "heading": {
        "family": "Space Grotesk",
        "fallback": "ui-sans-serif, system-ui",
        "notes": "Geometric but serious; reads like modern ops tooling."
      },
      "body": {
        "family": "IBM Plex Sans",
        "fallback": "ui-sans-serif, system-ui",
        "notes": "Neutral, highly legible for dense tables and long metadata."
      },
      "mono": {
        "family": "IBM Plex Mono",
        "fallback": "ui-monospace, SFMono-Regular",
        "notes": "Use for sha256, filenames, ranks, IDs, code-like claims."
      }
    },
    "google_fonts_import": {
      "instructions": "Add to /app/frontend/src/index.css (top) or in public/index.html <link> tags.",
      "css": "@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500;600&family=Space+Grotesk:wght@500;600;700&display=swap');"
    },
    "text_size_hierarchy": {
      "h1": "text-4xl sm:text-5xl lg:text-6xl",
      "h2": "text-base md:text-lg",
      "body": "text-sm md:text-base",
      "small": "text-xs"
    },
    "usage_rules": [
      "Headings: Space Grotesk 600–700",
      "Body/UI: IBM Plex Sans 400–600",
      "Monospace: IBM Plex Mono for hashes, filenames, IDs",
      "Avoid ALL CAPS paragraphs; allow ALL CAPS only for short status chips (e.g., WAIT, LOCKED)."
    ]
  },

  "color_system": {
    "mode": "dark-first (disciplined)",
    "tokens_css_variables": {
      "instructions": "Replace the default shadcn tokens in /app/frontend/src/index.css :root and .dark with these. Keep HSL format for shadcn compatibility.",
      "notes": "Soft-black base, teal/cyan as controlled accent (not neon). Authority tiers get distinct but muted hues.",
      "css": ":root {\n  --background: 210 20% 98%;\n  --foreground: 222 47% 11%;\n  --card: 0 0% 100%;\n  --card-foreground: 222 47% 11%;\n  --popover: 0 0% 100%;\n  --popover-foreground: 222 47% 11%;\n  --primary: 222 47% 11%;\n  --primary-foreground: 210 40% 98%;\n  --secondary: 210 40% 96%;\n  --secondary-foreground: 222 47% 11%;\n  --muted: 210 40% 96%;\n  --muted-foreground: 215 16% 47%;\n  --accent: 188 55% 40%;\n  --accent-foreground: 210 40% 98%;\n  --destructive: 0 72% 52%;\n  --destructive-foreground: 210 40% 98%;\n  --border: 214 32% 91%;\n  --input: 214 32% 91%;\n  --ring: 188 55% 40%;\n  --radius: 0.6rem;\n\n  /* semantic */\n  --success: 152 55% 36%;\n  --warning: 38 85% 52%;\n  --info: 199 70% 45%;\n  --danger: 0 72% 52%;\n\n  /* tier hues (muted) */\n  --tier-control: 199 70% 45%;\n  --tier-primary: 152 55% 36%;\n  --tier-process: 38 85% 52%;\n  --tier-concept: 262 25% 55%;\n  --tier-archive: 215 16% 55%;\n  --tier-unlisted: 0 0% 55%;\n}\n\n.dark {\n  --background: 222 22% 8%;\n  --foreground: 210 40% 96%;\n  --card: 222 22% 10%;\n  --card-foreground: 210 40% 96%;\n  --popover: 222 22% 10%;\n  --popover-foreground: 210 40% 96%;\n\n  --primary: 210 40% 96%;\n  --primary-foreground: 222 22% 10%;\n\n  --secondary: 222 18% 14%;\n  --secondary-foreground: 210 40% 96%;\n\n  --muted: 222 18% 14%;\n  --muted-foreground: 215 18% 70%;\n\n  --accent: 188 55% 40%;\n  --accent-foreground: 222 22% 10%;\n\n  --destructive: 0 62% 38%;\n  --destructive-foreground: 210 40% 96%;\n\n  --border: 222 16% 18%;\n  --input: 222 16% 18%;\n  --ring: 188 55% 40%;\n\n  --success: 152 55% 40%;\n  --warning: 38 85% 56%;\n  --info: 199 70% 55%;\n  --danger: 0 72% 58%;\n\n  --tier-control: 199 70% 55%;\n  --tier-primary: 152 55% 40%;\n  --tier-process: 38 85% 56%;\n  --tier-concept: 262 25% 62%;\n  --tier-archive: 215 18% 70%;\n  --tier-unlisted: 0 0% 70%;\n}"
    },
    "surface_steps": {
      "bg": "hsl(var(--background))",
      "surface_1": "hsl(222 22% 10%)",
      "surface_2": "hsl(222 18% 14%)",
      "surface_3": "hsl(222 16% 18%)",
      "hairline": "hsl(222 16% 18%)",
      "notes": "In dark mode, create elevation by stepping surfaces lighter, not by heavy shadows."
    },
    "status_mapping": {
      "scope_lock": {
        "bg": "hsl(0 62% 18%)",
        "border": "hsl(var(--danger))",
        "text": "hsl(210 40% 96%)"
      },
      "wait_mode": {
        "bg": "hsl(222 18% 14%)",
        "border": "hsl(var(--tier-archive))",
        "text": "hsl(210 40% 96%)"
      },
      "pipeline": {
        "extracting": "hsl(var(--info))",
        "analyzing": "hsl(var(--tier-control))",
        "contradictions": "hsl(var(--warning))",
        "artifacts": "hsl(var(--success))",
        "failed": "hsl(var(--danger))"
      }
    },
    "authority_tier_badges": {
      "CONTROL_PACKET": { "hue": "--tier-control", "intent": "highest authority" },
      "PRIMARY_ARCHITECTURE": { "hue": "--tier-primary", "intent": "defines what project is" },
      "PROCESS_RULES": { "hue": "--tier-process", "intent": "how to operate" },
      "CONCEPT_ONLY": { "hue": "--tier-concept", "intent": "inspiration only" },
      "ARCHIVE_REFERENCE": { "hue": "--tier-archive", "intent": "historical context" },
      "UNLISTED": { "hue": "--tier-unlisted", "intent": "unknown/unclassified" }
    }
  },

  "texture_and_gradients": {
    "gradient_policy": {
      "restriction": "Follow GRADIENT RESTRICTION RULE. Gradients only as subtle section background accents; never on dense reading areas.",
      "allowed_usage": [
        "Top header strip behind the global status bar (max ~12vh)",
        "Very subtle sidebar top fade",
        "Empty states illustration backdrop"
      ],
      "approved_gradients": [
        {
          "name": "Ops Teal Mist",
          "css": "radial-gradient(1200px 600px at 20% -10%, rgba(45, 212, 191, 0.14), transparent 55%), radial-gradient(900px 500px at 80% 0%, rgba(56, 189, 248, 0.10), transparent 60%)",
          "notes": "Use only on page shell background; keep content cards solid."
        }
      ]
    },
    "noise_overlay": {
      "css_snippet": "/* Add once to the app shell wrapper */\n.ops-noise::before {\n  content: '';\n  position: fixed;\n  inset: 0;\n  pointer-events: none;\n  background-image: url('https://images.unsplash.com/photo-1650488908294-07186d808e5d?crop=entropy&cs=srgb&fm=jpg&ixlib=rb-4.1.0&q=60');\n  opacity: 0.06;\n  mix-blend-mode: overlay;\n  filter: grayscale(1) contrast(1.1);\n}\n@media (prefers-reduced-motion: reduce) {\n  .ops-noise::before { opacity: 0.04; }\n}",
      "notes": "If image-based noise feels heavy, replace with a tiny inline SVG noise data-uri later. Keep subtle."
    }
  },

  "layout_and_grid": {
    "app_shell": {
      "pattern": "Sidebar + top status header + content",
      "sidebar_width": "w-[280px] (desktop), collapsible to Sheet on mobile",
      "content_max_width": "max-w-[1400px] but NOT centered text; use left-aligned content with generous padding",
      "page_padding": "px-4 sm:px-6 lg:px-8 py-6",
      "grid": "12-col on desktop; 4-col on mobile",
      "reading_flow": "Left aligned; use F-pattern scanning."
    },
    "dashboard_overview": {
      "top_row": "Scope-lock banner (full width) + Source Lock status header",
      "main": "Two-column on lg: left = pipeline + counts; right = contradictions + artifacts status",
      "mobile": "Single column; pipeline first, then counts, then contradictions."
    },
    "tables": {
      "density": "compact",
      "sticky_header": true,
      "row_height": "h-10",
      "monospace_columns": ["filename", "sha256", "priority_rank"],
      "column_visibility": "Provide a column toggle menu (DropdownMenu)"
    }
  },

  "components": {
    "component_path": {
      "shell": [
        "/app/frontend/src/components/ui/sheet.jsx",
        "/app/frontend/src/components/ui/separator.jsx",
        "/app/frontend/src/components/ui/navigation-menu.jsx",
        "/app/frontend/src/components/ui/scroll-area.jsx"
      ],
      "status_and_alerting": [
        "/app/frontend/src/components/ui/alert.jsx",
        "/app/frontend/src/components/ui/badge.jsx",
        "/app/frontend/src/components/ui/progress.jsx",
        "/app/frontend/src/components/ui/tooltip.jsx",
        "/app/frontend/src/components/ui/sonner.jsx"
      ],
      "data_display": [
        "/app/frontend/src/components/ui/table.jsx",
        "/app/frontend/src/components/ui/card.jsx",
        "/app/frontend/src/components/ui/tabs.jsx",
        "/app/frontend/src/components/ui/collapsible.jsx",
        "/app/frontend/src/components/ui/skeleton.jsx"
      ],
      "filters_and_commands": [
        "/app/frontend/src/components/ui/input.jsx",
        "/app/frontend/src/components/ui/select.jsx",
        "/app/frontend/src/components/ui/command.jsx",
        "/app/frontend/src/components/ui/dropdown-menu.jsx",
        "/app/frontend/src/components/ui/checkbox.jsx"
      ],
      "dialogs_drawers": [
        "/app/frontend/src/components/ui/drawer.jsx",
        "/app/frontend/src/components/ui/dialog.jsx",
        "/app/frontend/src/components/ui/alert-dialog.jsx"
      ]
    },
    "custom_components_to_create": [
      {
        "name": "ScopeLockBanner",
        "purpose": "Persistent warning listing forbidden build areas; must be visually unavoidable but not neon.",
        "structure": "Alert variant with icon + compact list chips",
        "testids": ["scope-lock-banner"]
      },
      {
        "name": "SourceLockStatusHeader",
        "purpose": "Shows LOCKED/UNLOCKED, WAIT mode, last run timestamp, bundle count (37), and environment.",
        "testids": ["source-lock-status-header", "wait-mode-indicator"]
      },
      {
        "name": "IngestionRunPanel",
        "purpose": "Run trigger + stepper progress (extract → analyze → contradictions → artifacts) + logs.",
        "testids": ["ingestion-run-trigger-button", "ingestion-progress"]
      },
      {
        "name": "AuthorityTierBadge",
        "purpose": "Consistent tier badge mapping with muted fills + border + dot.",
        "testids": ["authority-tier-badge"]
      },
      {
        "name": "ContradictionCard",
        "purpose": "Compact contradiction summary with preserved status and involved sources.",
        "testids": ["contradiction-card"]
      },
      {
        "name": "MarkdownArtifactViewer",
        "purpose": "Rendered markdown with TOC, code blocks, copy button, download.",
        "testids": ["artifact-viewer", "artifact-download-button"]
      }
    ]
  },

  "component_specs": {
    "buttons": {
      "style": "Professional / Corporate",
      "radius": "rounded-md (10px-ish via --radius 0.6rem)",
      "variants": {
        "primary": {
          "use": "Run ingestion, Operator Accept",
          "classes": "bg-primary text-primary-foreground hover:bg-primary/90 focus-visible:ring-2 focus-visible:ring-ring",
          "micro_interaction": "active:scale-[0.98] transition-colors"
        },
        "secondary": {
          "use": "View details, open drawer",
          "classes": "bg-secondary text-secondary-foreground hover:bg-secondary/80"
        },
        "ghost": {
          "use": "Table row actions",
          "classes": "hover:bg-accent/10 hover:text-foreground"
        },
        "danger": {
          "use": "Reset run (if exists), destructive actions",
          "classes": "bg-destructive text-destructive-foreground hover:bg-destructive/90"
        }
      },
      "rules": [
        "No universal transition: avoid transition-all",
        "Use transition-colors for hover; use active scale only on buttons",
        "All buttons must include data-testid"
      ]
    },
    "badges": {
      "authority_badge_pattern": {
        "structure": "Badge with left dot + label + optional short tag",
        "classes": "inline-flex items-center gap-2 rounded-md border px-2 py-0.5 text-xs font-medium",
        "dot": "h-1.5 w-1.5 rounded-full",
        "examples": {
          "CONTROL_PACKET": "border-[hsl(var(--tier-control))]/30 bg-[hsl(var(--tier-control))]/12 text-[hsl(var(--tier-control))]",
          "PRIMARY_ARCHITECTURE": "border-[hsl(var(--tier-primary))]/30 bg-[hsl(var(--tier-primary))]/12 text-[hsl(var(--tier-primary))]",
          "PROCESS_RULES": "border-[hsl(var(--tier-process))]/30 bg-[hsl(var(--tier-process))]/12 text-[hsl(var(--tier-process))]",
          "CONCEPT_ONLY": "border-[hsl(var(--tier-concept))]/30 bg-[hsl(var(--tier-concept))]/12 text-[hsl(var(--tier-concept))]",
          "ARCHIVE_REFERENCE": "border-[hsl(var(--tier-archive))]/30 bg-[hsl(var(--tier-archive))]/12 text-[hsl(var(--tier-archive))]",
          "UNLISTED": "border-[hsl(var(--tier-unlisted))]/30 bg-[hsl(var(--tier-unlisted))]/12 text-[hsl(var(--tier-unlisted))]"
        }
      },
      "status_badges": {
        "parse_status": {
          "PARSED": "bg-[hsl(var(--success))]/12 text-[hsl(var(--success))] border-[hsl(var(--success))]/30",
          "FAILED": "bg-[hsl(var(--danger))]/12 text-[hsl(var(--danger))] border-[hsl(var(--danger))]/30",
          "PENDING": "bg-[hsl(var(--tier-archive))]/12 text-[hsl(var(--tier-archive))] border-[hsl(var(--tier-archive))]/30"
        },
        "contradiction_status": {
          "PRESERVED": "bg-[hsl(var(--warning))]/12 text-[hsl(var(--warning))] border-[hsl(var(--warning))]/30"
        }
      }
    },
    "tables": {
      "source_index_table": {
        "features": [
          "Search input (filename, tags)",
          "Tier filter (Select)",
          "Parse status filter",
          "Sort by priority rank",
          "Row click opens Drawer with Source Detail",
          "Row actions menu (DropdownMenu): Copy sha256, Open artifact references"
        ],
        "shadcn": "Use /components/ui/table.jsx + custom header controls",
        "ux_notes": [
          "Sticky header",
          "Monospace for sha256",
          "Truncate filename with Tooltip for full",
          "Use zebra rows via bg-muted/30 on even rows"
        ]
      }
    },
    "markdown": {
      "library": {
        "name": "react-markdown + remark-gfm",
        "install": "npm i react-markdown remark-gfm",
        "notes": "Render the 5 artifacts with code block styling and anchor links."
      },
      "code_block_style": {
        "classes": "rounded-md border bg-secondary/40 p-3 font-mono text-xs leading-relaxed overflow-x-auto"
      }
    }
  },

  "motion_and_microinteractions": {
    "library": {
      "name": "framer-motion",
      "install": "npm i framer-motion",
      "usage": [
        "Page transitions: subtle fade + y translate (6px)",
        "Drawer open: slide from right",
        "Progress step highlight: pulse once on step change"
      ],
      "rules": [
        "Respect prefers-reduced-motion",
        "No looping glows",
        "No large parallax backgrounds"
      ]
    },
    "interaction_specs": {
      "table_row_hover": "hover:bg-accent/10 transition-colors",
      "focus_rings": "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background",
      "copy_to_clipboard": "On copy sha256: show sonner toast 'Copied hash'"
    }
  },

  "accessibility": {
    "requirements": [
      "WCAG AA contrast for text and badges",
      "Keyboard navigation for sidebar, tables, drawers",
      "Visible focus states (ring)",
      "Use aria-label for icon-only buttons",
      "Respect prefers-reduced-motion"
    ],
    "adhd_operator_preferences": [
      "Prefer short labels + structured sections",
      "Use consistent placement for primary actions (top-right of panels)",
      "Avoid surprise modals; prefer drawers for detail",
      "Use progressive disclosure (Collapsible) for long text previews"
    ]
  },

  "data_testid_conventions": {
    "rules": [
      "kebab-case",
      "role-based naming (not visual)",
      "Apply to ALL interactive and key informational elements"
    ],
    "examples": [
      "data-testid=\"sidebar-nav-source-index\"",
      "data-testid=\"source-index-search-input\"",
      "data-testid=\"source-row-open-detail\"",
      "data-testid=\"contradictions-filter-select\"",
      "data-testid=\"operator-accept-button\"",
      "data-testid=\"artifact-download-button\"",
      "data-testid=\"scope-lock-banner\""
    ]
  },

  "image_urls": {
    "texture_noise_overlay": [
      {
        "url": "https://images.unsplash.com/photo-1650488908294-07186d808e5d?crop=entropy&cs=srgb&fm=jpg&ixlib=rb-4.1.0&q=60",
        "description": "Subtle dark water/rock texture used as a very low-opacity noise overlay (optional).",
        "category": "background-texture"
      }
    ],
    "optional_reference_photography": [
      {
        "url": "https://images.unsplash.com/photo-1652512456059-92820d862b97?crop=entropy&cs=srgb&fm=jpg&ixlib=rb-4.1.0&q=85",
        "description": "Control-room workstation photo for empty states or onboarding panel (use sparingly, grayscale, low opacity).",
        "category": "empty-state"
      }
    ]
  },

  "instructions_to_main_agent": {
    "global_css_cleanup": [
      "Remove/stop using /app/frontend/src/App.css default CRA styles (App-header centering etc). Prefer Tailwind + tokens in index.css.",
      "Set body font-family to IBM Plex Sans; headings via utility class (font-heading) or Tailwind config if available.",
      "Enable dark mode by default by adding class 'dark' on html/body root (implementation choice)."
    ],
    "page_build_order": [
      "1) AppShell (Sidebar + Top Status Header + ScopeLockBanner)",
      "2) Dashboard Overview (pipeline + counts + recent contradictions + artifacts status)",
      "3) Source Index table + Drawer detail",
      "4) Contradictions Register",
      "5) Priority Order",
      "6) Artifacts viewer",
      "7) Completion Report + Operator Accept → WAIT mode"
    ],
    "forbidden_scope_banner_copy": {
      "title": "SCOPE LOCK: PHASE 0 ONLY",
      "subtitle": "Forbidden build areas (do not implement): Kernel, Memory, Router, Validation, Audit, Workers, Skills, Recovery, UI, Controlled Live Operation.",
      "tone": "Direct, non-negotiable."
    },
    "recommended_icon_set": {
      "library": "lucide-react",
      "notes": "Use minimal line icons (Shield, Lock, FileText, AlertTriangle, ListOrdered, Search, Download)."
    }
  },

  "references": {
    "inspiration_urls": [
      "https://ui.shadcn.com/examples/dashboard",
      "https://dribbble.com/tags/mission-control",
      "https://uxplanet.org/mission-control-software-ux-design-patterns-benchmarking-e8a2d802c1f3",
      "https://shadcnstudio.com/blocks/dashboard-and-application/dashboard-shell"
    ]
  },

  "general_ui_ux_design_guidelines": "<General UI UX Design Guidelines>\n    - You must **not** apply universal transition. Eg: `transition: all`. This results in breaking transforms. Always add transitions for specific interactive elements like button, input excluding transforms\n    - You must **not** center align the app container, ie do not add `.App { text-align: center; }` in the css file. This disrupts the human natural reading flow of text\n   - NEVER: use AI assistant Emoji characters like`🤖🧠💭💡🔮🎯📚🎭🎬🎪🎉🎊🎁🎀🎂🍰🎈🎨🎰💰💵💳🏦💎🪙💸🤑📊📈📉💹🔢🏆🥇 etc for icons. Always use **FontAwesome cdn** or **lucid-react** library already installed in the package.json\n\n **GRADIENT RESTRICTION RULE**\nNEVER use dark/saturated gradient combos (e.g., purple/pink) on any UI element.  Prohibited gradients: blue-500 to purple 600, purple 500 to pink-500, green-500 to blue-500, red to pink etc\nNEVER use dark gradients for logo, testimonial, footer etc\nNEVER let gradients cover more than 20% of the viewport.\nNEVER apply gradients to text-heavy content or reading areas.\nNEVER use gradients on small UI elements (<100px width).\nNEVER stack multiple gradient layers in the same viewport.\n\n**ENFORCEMENT RULE:**\n    • Id gradient area exceeds 20% of viewport OR affects readability, **THEN** use solid colors\n\n**How and where to use:**\n   • Section backgrounds (not content backgrounds)\n   • Hero section header content. Eg: dark to light to dark color\n   • Decorative overlays and accent elements only\n   • Hero section with 2-3 mild color\n   • Gradients creation can be done for any angle say horizontal, vertical or diagonal\n\n- For AI chat, voice application, **do not use purple color. Use color like light green, ocean blue, peach orange etc**\n\n</Font Guidelines>\n\n- Every interaction needs micro-animations - hover states, transitions, parallax effects, and entrance animations. Static = dead. \n   \n- Use 2-3x more spacing than feels comfortable. Cramped designs look cheap.\n\n- Subtle grain textures, noise overlays, custom cursors, selection states, and loading animations: separates good from extraordinary.\n   \n- Before generating UI, infer the visual style from the problem statement (palette, contrast, mood, motion) and immediately instantiate it by setting global design tokens (primary, secondary/accent, background, foreground, ring, state colors), rather than relying on any library defaults. Don't make the background dark as a default step, always understand problem first and define colors accordingly\n    Eg: - if it implies playful/energetic, choose a colorful scheme\n           - if it implies monochrome/minimal, choose a black–white/neutral scheme\n\n**Component Reuse:**\n\t- Prioritize using pre-existing components from src/components/ui when applicable\n\t- Create new components that match the style and conventions of existing components when needed\n\t- Examine existing components to understand the project's component patterns before creating new ones\n\n**IMPORTANT**: Do not use HTML based component like dropdown, calendar, toast etc. You **MUST** always use `/app/frontend/src/components/ui/ ` only as a primary components as these are modern and stylish component\n\n**Best Practices:**\n\t- Use Shadcn/UI as the primary component library for consistency and accessibility\n\t- Import path: ./components/[component-name]\n\n**Export Conventions:**\n\t- Components MUST use named exports (export const ComponentName = ...)\n\t- Pages MUST use default exports (export default function PageName() {...})\n\n**Toasts:**\n  - Use `sonner` for toasts\"\n  - Sonner component are located in `/app/src/components/ui/sonner.tsx`\n\nUse 2–4 color gradients, subtle textures/noise overlays, or CSS-based noise to avoid flat visuals.\n</General UI UX Design Guidelines>"
}
