#!/usr/bin/env python3
"""Render the file-org catalog as a self-contained HTML dashboard."""
import argparse
import html
import json
import os
import sqlite3
import time
from collections import defaultdict

CAT_COLORS = {
    "video": "#5B8DEF", "image": "#43B97F", "audio": "#9B6BDF",
    "document": "#E8A33D", "installer": "#D96C6C", "disc_image": "#C05C9E",
    "vm_image": "#4FB3BF", "vm": "#4FB3BF", "archive": "#8A8F98",
    "backup": "#B0413E", "code": "#3FA37A", "code_project": "#3FA37A",
    "app_install": "#7A6FF0", "game": "#E06AA3", "photo_library": "#43B97F",
    "font": "#A9A34C", "database": "#5C7CB0", "system": "#6B7280",
    "other": "#9CA3AF",
}


def gb(b):
    return (b or 0) / 1e9


def fmt_size(b):
    b = b or 0
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if b < 1000 or unit == "TB":
            return f"{b:.1f} {unit}" if unit != "B" else f"{b:.0f} B"
        b /= 1000


def has_column(con, table, col):
    return col in {r[1] for r in con.execute(f"PRAGMA table_info({table})")}


def has_table(con, name):
    return con.execute("SELECT 1 FROM sqlite_master WHERE name=?",
                       (name,)).fetchone() is not None


def top_dirs(con, n):
    """Aggregate sizes at depth<=2 directories per root."""
    agg = defaultdict(int)
    for root, path, size, depth in con.execute(
            "SELECT root, path, size, depth FROM files"):
        parts = path.split(os.sep)
        cut = len(parts) - depth  # index where the root portion ends
        key = os.sep.join(parts[:min(len(parts) - 1, cut + 2)])
        agg[(root, key)] += size
    rows = sorted(agg.items(), key=lambda kv: -kv[1])[:n]
    return [{"root": r, "dir": d, "size": s} for (r, d), s in rows]


def build(con, args):
    parts = []
    add = parts.append
    now = time.strftime("%Y-%m-%d %H:%M")
    total_n, total_b = con.execute(
        "SELECT COUNT(*), COALESCE(SUM(size),0) FROM files").fetchone()
    drives = con.execute(
        "SELECT root, COUNT(*), SUM(size) FROM files GROUP BY root"
        " ORDER BY SUM(size) DESC").fetchall()

    has_cat = has_column(con, "files", "category")
    has_hash = has_column(con, "files", "full_hash")
    has_units = has_table(con, "units")

    dup_bytes = 0
    dup_groups = []
    if has_hash:
        dup_groups = con.execute(
            "SELECT full_hash, size, COUNT(*) AS n, MIN(path)"
            " FROM files WHERE full_hash IS NOT NULL AND unit_id IS NULL"
            " GROUP BY full_hash, size HAVING n > 1"
            " ORDER BY size*(n-1) DESC").fetchall()
        dup_bytes = sum(s * (n - 1) for _, s, n, _ in dup_groups)

    # ---- summary tiles
    tiles = [("Total files", f"{total_n:,}"), ("Total size", fmt_size(total_b))]
    for root, n, b in drives:
        tiles.append((html.escape(root), fmt_size(b)))
    if has_units:
        (nu,) = con.execute("SELECT COUNT(*) FROM units").fetchone()
        tiles.append(("Units (VMs, repos, apps)", f"{nu:,}"))
    if dup_bytes:
        tiles.append(("Duplicate waste", fmt_size(dup_bytes)))
    add('<section class="tiles">')
    for label, val in tiles:
        add(f'<div class="tile"><div class="v">{val}</div>'
            f'<div class="l">{label}</div></div>')
    add('</section>')

    # ---- category bars
    if has_cat:
        cats = con.execute(
            "SELECT COALESCE(category,'unclassified'), COUNT(*), SUM(size)"
            " FROM files GROUP BY category ORDER BY SUM(size) DESC").fetchall()
        maxb = max((b or 0) for _, _, b in cats) or 1
        add('<section><h2>By category</h2><div class="bars">')
        for cat, n, b in cats:
            c = CAT_COLORS.get(cat, "#9CA3AF")
            pct = 100.0 * (b or 0) / maxb
            add(f'<div class="bar-row"><div class="bar-label">{html.escape(cat)}</div>'
                f'<div class="bar-track"><div class="bar-fill" '
                f'style="width:{pct:.1f}%;background:{c}"></div></div>'
                f'<div class="bar-val">{fmt_size(b)} · {n:,} files</div></div>')
        add('</div></section>')

    # ---- treemap
    dirs = top_dirs(con, args.top_dirs)
    if dirs:
        add('<section><h2>Where the space is (top folders)</h2>'
            '<div id="treemap"></div>'
            f'<script>const TREE={json.dumps(dirs)};</script></section>')

    # ---- units table
    if has_units:
        units = con.execute(
            "SELECT kind, path, file_count, total_bytes FROM units"
            " ORDER BY total_bytes DESC LIMIT 60").fetchall()
        if units:
            add('<section><h2>Detected units</h2>'
                '<div class="scroll"><table><tr><th>Kind</th><th>Size</th>'
                '<th>Files</th><th>Path</th></tr>')
            for kind, path, n, b in units:
                add(f'<tr><td><span class="chip" style="background:'
                    f'{CAT_COLORS.get(kind, "#9CA3AF")}"></span>'
                    f'{html.escape(kind)}</td>'
                    f'<td data-s="{b or 0}">{fmt_size(b)}</td>'
                    f'<td data-s="{n or 0}">{(n or 0):,}</td>'
                    f'<td class="path">{html.escape(path)}</td></tr>')
            add('</table></div></section>')

    # ---- largest files
    largest = con.execute(
        "SELECT path, size" + (", category" if has_cat else ", NULL") +
        " FROM files ORDER BY size DESC LIMIT ?", (args.top_files,)).fetchall()
    add('<section><h2>Largest files</h2><div class="scroll"><table>'
        '<tr><th>Size</th><th>Category</th><th>Path</th></tr>')
    for path, size, cat in largest:
        add(f'<tr><td data-s="{size}">{fmt_size(size)}</td>'
            f'<td>{html.escape(cat or "-")}</td>'
            f'<td class="path">{html.escape(path)}</td></tr>')
    add('</table></div></section>')

    # ---- duplicates
    if dup_groups:
        add(f'<section><h2>Top duplicate groups '
            f'({fmt_size(dup_bytes)} reclaimable)</h2>'
            '<div class="scroll"><table><tr><th>Wasted</th><th>Copies</th>'
            '<th>Each</th><th>Example path</th></tr>')
        for _, size, n, p in dup_groups[:40]:
            add(f'<tr><td data-s="{size * (n - 1)}">'
                f'{fmt_size(size * (n - 1))}</td><td data-s="{n}">{n}</td>'
                f'<td data-s="{size}">{fmt_size(size)}</td>'
                f'<td class="path">{html.escape(p)}</td></tr>')
        add('</table></div></section>')

    body = "\n".join(parts)
    return TEMPLATE.replace("__BODY__", body).replace("__DATE__", now)


TEMPLATE = """<title>Storage Report</title>
<style>
:root{--bg:#fff;--fg:#1a1d21;--muted:#6b7280;--card:#f4f5f7;--line:#e5e7eb}
@media(prefers-color-scheme:dark){:root{--bg:#111418;--fg:#e7e9ec;
 --muted:#9aa1ab;--card:#1b2027;--line:#2a313b}}
:root[data-theme=dark]{--bg:#111418;--fg:#e7e9ec;--muted:#9aa1ab;
 --card:#1b2027;--line:#2a313b}
:root[data-theme=light]{--bg:#fff;--fg:#1a1d21;--muted:#6b7280;
 --card:#f4f5f7;--line:#e5e7eb}
body{background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,sans-serif;
 margin:0;padding:24px;max-width:1100px;margin-inline:auto}
h1{font-size:22px}h2{font-size:16px;margin:28px 0 10px}
.sub{color:var(--muted);font-size:13px}
.tiles{display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));
 gap:10px;margin-top:16px}
.tile{background:var(--card);border-radius:10px;padding:12px 14px}
.tile .v{font-size:20px;font-weight:650}.tile .l{color:var(--muted);
 font-size:12px;margin-top:2px}
.bars{display:flex;flex-direction:column;gap:6px}
.bar-row{display:grid;grid-template-columns:130px 1fr 200px;gap:10px;
 align-items:center}
.bar-label{font-size:13px;text-align:right;color:var(--muted)}
.bar-track{background:var(--card);border-radius:5px;height:18px}
.bar-fill{height:100%;border-radius:5px;min-width:2px}
.bar-val{font-size:12px;color:var(--muted)}
.scroll{overflow-x:auto}
table{border-collapse:collapse;width:100%;font-size:13px}
th{text-align:left;color:var(--muted);font-weight:600}
td,th{padding:5px 10px;border-bottom:1px solid var(--line);
 white-space:nowrap}
td.path{font-family:ui-monospace,monospace;font-size:12px;max-width:560px;
 overflow:hidden;text-overflow:ellipsis}
.chip{display:inline-block;width:9px;height:9px;border-radius:3px;
 margin-right:6px}
.flt{display:block;margin:0 0 8px;padding:6px 10px;font:13px system-ui;
 color:var(--fg);background:var(--card);border:1px solid var(--line);
 border-radius:7px;width:min(320px,100%)}
#treemap{position:relative;width:100%;height:420px;background:var(--card);
 border-radius:10px;overflow:hidden}
.tm{position:absolute;overflow:hidden;border:1px solid var(--bg);
 border-radius:3px;padding:4px 6px;font-size:11px;color:#fff;
 box-sizing:border-box;cursor:default}
.tm small{opacity:.85}
</style>
<h1>Storage Report</h1>
<div class="sub">Generated __DATE__ by file-org pipeline</div>
__BODY__
<script>
(function(){
 const el=document.getElementById('treemap');
 if(!el||typeof TREE==='undefined')return;
 const items=TREE.map(t=>({...t}));const total=items.reduce((a,b)=>a+b.size,0);
 const W=el.clientWidth,H=420;const hues=[212,152,268,32,0,312,186,96,340,50];
 // simple slice-and-dice alternating treemap (good enough, zero deps)
 function layout(items,x,y,w,h,horiz){
  if(!items.length)return;
  const sum=items.reduce((a,b)=>a+b.size,0)||1;
  if(items.length===1){place(items[0],x,y,w,h);return}
  let acc=0,i=0;const half=sum/2;
  while(i<items.length-1&&acc+items[i].size<half){acc+=items[i].size;i++}
  const a=items.slice(0,i+1),b=items.slice(i+1);
  const fa=a.reduce((s,t)=>s+t.size,0)/sum;
  if(horiz){layout(a,x,y,w*fa,h,!horiz);layout(b,x+w*fa,y,w*(1-fa),h,!horiz)}
  else{layout(a,x,y,w,h*fa,!horiz);layout(b,x,y+h*fa,w,h*(1-fa),!horiz)}
 }
 let ci=0;
 function place(t,x,y,w,h){
  const d=document.createElement('div');d.className='tm';
  const hue=hues[ci++%hues.length];
  d.style.cssText+=`left:${x}px;top:${y}px;width:${w}px;height:${h}px;`+
   `background:hsl(${hue} 45% 45%)`;
  const name=t.dir.split(/[\\\\/]/).filter(Boolean).slice(-2).join('/');
  const gbv=(t.size/1e9).toFixed(1);
  if(w>70&&h>30)d.innerHTML=`<b>${name}</b><br><small>${gbv} GB</small>`;
  d.title=`${t.dir}\\n${gbv} GB (${(100*t.size/total).toFixed(1)}%)`;
  el.appendChild(d);
 }
 layout(items.sort((a,b)=>b.size-a.size),0,0,W,H,W>H);
})();
// sortable table headers (numeric via data-s, else text)
document.querySelectorAll('table').forEach(tb=>{
 const head=tb.rows[0];if(!head)return;
 [...head.cells].forEach((th,ci)=>{
  th.title='click to sort';th.style.cursor='pointer';
  th.addEventListener('click',()=>{
   const dir=th.dataset.dir=th.dataset.dir==='d'?'a':'d';
   const rows=[...tb.rows].slice(1);
   rows.sort((r1,r2)=>{
    const c1=r1.cells[ci],c2=r2.cells[ci];
    const a=c1.dataset.s!==undefined?+c1.dataset.s:c1.textContent.trim(),
          b=c2.dataset.s!==undefined?+c2.dataset.s:c2.textContent.trim();
    const cmp=(typeof a==='number'&&typeof b==='number')?a-b
      :String(a).localeCompare(String(b));
    return dir==='d'?-cmp:cmp});
   rows.forEach(r=>tb.appendChild(r))});});});
// live text filter above every table
document.querySelectorAll('.scroll').forEach(w=>{
 const t=w.querySelector('table');if(!t)return;
 const inp=document.createElement('input');
 inp.placeholder='filter rows…';inp.className='flt';
 w.parentNode.insertBefore(inp,w);
 inp.addEventListener('input',()=>{
  const q=inp.value.toLowerCase();
  [...t.rows].slice(1).forEach(r=>{
   r.style.display=r.textContent.toLowerCase().includes(q)?'':'none'});});});
</script>
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--db", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--top-dirs", type=int, default=30)
    ap.add_argument("--top-files", type=int, default=50)
    args = ap.parse_args()
    con = sqlite3.connect(args.db)
    html_doc = build(con, args)
    with open(args.out, "w") as f:
        f.write(html_doc)
    print(f"Report written: {args.out}")
    con.close()


if __name__ == "__main__":
    main()
