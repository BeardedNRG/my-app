# Default Target Layout

A starting point to adapt with the user. The principle: **top level answers
"what kind of thing is this?", second level answers "which one?"** — never
more than 3 levels deep before content's own structure takes over.

```
<Drive A - biggest/fastest>
├── Media/
│   ├── Photos/          # consolidated; keep year/event substructure
│   │   └── Libraries/   # Lightroom/Photos libraries (units, moved whole)
│   ├── Video/
│   └── Audio/
├── Documents/
└── Projects/            # code_project units, moved whole

<Drive B - bulk storage>
├── VMs/                 # vm units, moved whole
│   └── loose-images/    # stray vmdk/vhdx/ova not inside a VM folder
├── Software/
│   ├── Installers/      # setup exes, msi, apk...
│   └── ISOs/            # disc images
└── Archive/
    ├── old-backups/     # everything the backup category caught
    └── ...              # cold storage, zips, "deal with later"

<Drive C - untouched or backups-of-A>
```

## Rules of thumb

- **Leave installed apps and games where they are** (`app_install`, `game`
  → `null`). Moving them breaks registry paths, shortcuts, and launchers.
- **Backups are quarantine-adjacent**: park them in `Archive/old-backups`
  rather than deleting; after dedupe has proven what's redundant, the user
  can decide.
- **Don't flatten.** Moving 80,000 photos into one folder is worse than the
  mess you started with. The planner keeps the source's parent-folder
  context by default.
- **One category, one home.** The whole point is that the user can answer
  "where are my ISOs?" without searching.
- If a drive is to be **emptied entirely** (e.g. to sell or repurpose it),
  say so up front — the plan then routes everything off it instead of
  organizing in place.
