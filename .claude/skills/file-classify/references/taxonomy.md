# File-Org Taxonomy

The contract for `files.category` and `units.kind`. Keep in sync with the
tables at the top of `scripts/classify.py`.

## Unit kinds (atomic directories — moved whole, never deduped internally)

| kind            | markers                                                        |
|-----------------|----------------------------------------------------------------|
| `vm`            | `.vmx`, `.vbox`, `.vmcx`, or disk images `.vmdk .vdi .qcow2 .vhd .vhdx` in the dir |
| `code_project`  | `.git` dir, or `package.json` / `pyproject.toml` / `*.sln` / `Cargo.toml` / `go.mod` |
| `app_install`   | `unins*.exe` / `uninstall.exe`, or ≥3 `.exe` with ≥5 `.dll` in the dir |
| `photo_library` | `DCIM` directory, or Lightroom `.lrcat` / Photos `.photoslibrary` |
| `game`          | `steam_appid.txt`, `UnityCrashHandler*.exe`, `.pak`+`.exe` cluster |

Nested markers resolve to the **shallowest** qualifying directory; units never
nest inside other units.

## File categories (loose files)

| category     | typical extensions / signals                                        |
|--------------|---------------------------------------------------------------------|
| `video`      | mp4 mkv avi mov wmv flv webm m4v mpg mpeg ts vob 3gp                |
| `image`      | jpg jpeg png gif bmp tiff webp heic raw cr2 nef arw dng svg ico psd |
| `audio`      | mp3 flac wav aac ogg m4a wma opus aiff mid                          |
| `document`   | pdf doc docx xls xlsx ppt pptx odt ods txt rtf md csv epub mobi     |
| `installer`  | msi exe (top-level/Downloads-style loose ones) apk deb rpm pkg appimage msix |
| `disc_image` | iso img bin cue nrg dmg                                             |
| `vm_image`   | vmdk vdi qcow2 vhd vhdx ova ovf (loose, outside a `vm` unit)        |
| `archive`    | zip rar 7z tar gz bz2 xz tgz cab                                    |
| `backup`     | bak old bkp bkf tib gho — or any file whose *name* matches backup heuristics |
| `code`       | py js ts java c cpp h cs go rs rb php sh ps1 bat html css json yaml sql ipynb |
| `font`       | ttf otf woff woff2                                                  |
| `database`   | db sqlite mdb accdb                                                 |
| `system`     | dll sys drv tmp log ini cfg dat lnk thumbs.db .ds_store             |
| `other`      | anything unmatched                                                  |

## Name heuristics (override extension mapping)

A file is re-categorized `backup` when its lowercase name:
- contains `backup`, `bckp`, or ends in `.bak`, `.old`, `.orig`
- starts with `copy of ` / `kopie von `
- matches `* (1).*` … `* (9).*` or `*-copy.*`

These are *hints* — dedupe (stage 4) is what actually proves duplication.
