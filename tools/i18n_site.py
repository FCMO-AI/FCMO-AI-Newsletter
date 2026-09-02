#!/usr/bin/env python3
"""Validate and apply the public FCMO AI Newsletter localization layer.

The script reads only the already-public static publication tree. It never translates
copy, contacts a model, or calls a translation provider. Curated locale content must
already exist in data/translations.json; missing content is a hard build failure.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REQUIRED_LOCALES = ("es-419", "zh-Hans")
REQUIRED_FIELDS = ("title", "summary", "why_it_matters")
PUBLIC_ID = re.compile(r"^FCMO-[0-9A-F]{12}$")

CSS = r'''
<style id="fcmo-i18n-system">
.fcmo-language{margin-left:auto;display:inline-flex;align-items:center;gap:8px;min-height:34px;padding:3px 5px 3px 9px;border:1px solid rgba(255,255,255,.11);border-radius:10px;background:rgba(255,255,255,.035);font:750 9px/1 var(--ui,Arial,sans-serif);letter-spacing:.08em;color:#9faabc}
.fcmo-language label{white-space:nowrap;text-transform:uppercase}.fcmo-language select{appearance:auto;min-height:26px;max-width:170px;border:0;border-left:1px solid rgba(255,255,255,.1);padding:0 6px;background:#0b0e15;color:#e7ecf5;font:700 10px/1.2 var(--ui,Arial,sans-serif);outline:none}.fcmo-language option,.fcmo-language optgroup{background:#0b0e15;color:#e7ecf5}.fcmo-curated-note{font-size:8px;color:#78e7ff;white-space:nowrap}
:lang(zh-Hans){--ui:"Noto Sans CJK SC","Noto Sans SC","PingFang SC","Microsoft YaHei",ui-sans-serif,system-ui,sans-serif;--display:"Noto Sans CJK SC","Noto Sans SC","PingFang SC","Microsoft YaHei",ui-sans-serif,system-ui,sans-serif}
@media(max-width:760px){.fcmo-language{order:20;width:100%;justify-content:flex-end;margin-left:0}.fcmo-language label{margin-right:auto}.fcmo-curated-note{display:none}}
</style>
'''

JS = r'''
<script id="fcmo-i18n-runtime">
(()=>{
"use strict";
const ROOT="/FCMO-AI-Newsletter/";
const SUPPORTED=["en","es-419","zh-Hans"];
const STORAGE="fcmo-newsletter-language";
const UI={
  "Continuous evidence-first intelligence on the AI frontier":{
    "es-419":"Inteligencia continua y basada en evidencia sobre la frontera de la IA",
    "zh-Hans":"持续、证据优先的人工智能前沿情报"
  },
  "Front Page":{"es-419":"Portada","zh-Hans":"首页"},
  "Archive":{"es-419":"Archivo","zh-Hans":"存档"},
  "Search":{"es-419":"Buscar","zh-Hans":"搜索"},
  "Topics":{"es-419":"Temas","zh-Hans":"主题"},
  "Organizations":{"es-419":"Organizaciones","zh-Hans":"机构"},
  "Corrections":{"es-419":"Correcciones","zh-Hans":"更正"},
  "Feeds":{"es-419":"Fuentes","zh-Hans":"订阅源"},
  "About / Evidence":{"es-419":"Acerca de / Evidencia","zh-Hans":"关于 / 证据"},
  "Top verified research":{"es-419":"Investigación verificada destacada","zh-Hans":"重点已验证研究"},
  "Latest archive date":{"es-419":"Última fecha del archivo","zh-Hans":"最新存档日期"},
  "Search & filter all research":{"es-419":"Buscar y filtrar toda la investigación","zh-Hans":"搜索并筛选全部研究"},
  "Major verified research":{"es-419":"Investigación verificada de alto impacto","zh-Hans":"重大已验证研究"},
  "High-impact signals":{"es-419":"Señales de alto impacto","zh-Hans":"高影响信号"},
  "Recently verified / updated":{"es-419":"Verificado / actualizado recientemente","zh-Hans":"近期验证 / 更新"},
  "all research →":{"es-419":"toda la investigación →","zh-Hans":"全部研究 →"},
  "Why it matters:":{"es-419":"Por qué importa:","zh-Hans":"为什么重要："},
  "Why it matters":{"es-419":"Por qué importa","zh-Hans":"为什么重要"},
  "Evidence":{"es-419":"Evidencia","zh-Hans":"证据"},
  "Confidence":{"es-419":"Confianza","zh-Hans":"置信度"},
  "Importance":{"es-419":"Importancia","zh-Hans":"重要性"},
  "Status":{"es-419":"Estado","zh-Hans":"状态"},
  "Technical detail":{"es-419":"Detalle técnico","zh-Hans":"技术细节"},
  "Mechanism":{"es-419":"Mecanismo","zh-Hans":"机制"},
  "Demonstrated result":{"es-419":"Resultado demostrado","zh-Hans":"已证实结果"},
  "Claimed result":{"es-419":"Resultado declarado","zh-Hans":"声称结果"},
  "Strongest baseline":{"es-419":"Línea base más sólida","zh-Hans":"最强基线"},
  "Regime":{"es-419":"Régimen","zh-Hans":"适用条件"},
  "Implementation status":{"es-419":"Estado de implementación","zh-Hans":"实现状态"},
  "Compute / cost":{"es-419":"Cómputo / costo","zh-Hans":"计算 / 成本"},
  "Novelty":{"es-419":"Novedad","zh-Hans":"新颖性"},
  "Reproducibility":{"es-419":"Reproducibilidad","zh-Hans":"可复现性"},
  "Claims":{"es-419":"Afirmaciones","zh-Hans":"论断"},
  "Limitations":{"es-419":"Limitaciones","zh-Hans":"局限"},
  "Contradictory evidence":{"es-419":"Evidencia contradictoria","zh-Hans":"相反证据"},
  "Research implications":{"es-419":"Implicaciones para investigación","zh-Hans":"研究启示"},
  "Engineering implications":{"es-419":"Implicaciones de ingeniería","zh-Hans":"工程启示"},
  "Policy implications":{"es-419":"Implicaciones de política pública","zh-Hans":"政策启示"},
  "Sources":{"es-419":"Fuentes","zh-Hans":"来源"},
  "Relationships":{"es-419":"Relaciones","zh-Hans":"关联"},
  "Evidence gaps":{"es-419":"Vacíos de evidencia","zh-Hans":"证据缺口"},
  "Search all research":{"es-419":"Buscar en toda la investigación","zh-Hans":"搜索全部研究"},
  "Loading index…":{"es-419":"Cargando índice…","zh-Hans":"正在加载索引…"},
  "Any evidence":{"es-419":"Cualquier evidencia","zh-Hans":"任意证据"},
  "Any desk":{"es-419":"Cualquier sección","zh-Hans":"任意栏目"},
  "Sort: importance":{"es-419":"Ordenar: importancia","zh-Hans":"排序：重要性"},
  "Sort: recent":{"es-419":"Ordenar: reciente","zh-Hans":"排序：最近"},
  "Sort: evidence":{"es-419":"Ordenar: evidencia","zh-Hans":"排序：证据"},
  "Feeds & data":{"es-419":"Fuentes y datos","zh-Hans":"订阅源与数据"},
  "About":{"es-419":"Acerca de","zh-Hans":"关于"},
  "Privacy":{"es-419":"Privacidad","zh-Hans":"隐私"},
  "License":{"es-419":"Licencia","zh-Hans":"许可"},
  "Disclaimer":{"es-419":"Aviso legal","zh-Hans":"免责声明"},
  "Canonical source":{"es-419":"Fuente canónica","zh-Hans":"规范来源"},
  "Curated translations":{"es-419":"Traducciones curadas","zh-Hans":"精选翻译"},
  "Language":{"es-419":"Idioma","zh-Hans":"语言"},
  "curated":{"es-419":"curada","zh-Hans":"精选"}
};
function mapLocale(value, browser=false){
  if(!value)return null;
  const raw=String(value), lower=raw.toLowerCase();
  if(lower==="en"||lower.startsWith("en-"))return "en";
  if(lower==="es"||lower.startsWith("es-"))return "es-419";
  if(lower==="zh"||lower.startsWith("zh-")){
    if(/(?:^|-)hant(?:-|$)|(?:^|-)(tw|hk|mo)(?:-|$)/.test(lower))return browser?null:"en";
    return "zh-Hans";
  }
  return null;
}
function resolveLocale(){
  const explicit=new URL(location.href).searchParams.get("lang");
  if(explicit!==null)return mapLocale(explicit,false)||"en";
  try{const saved=localStorage.getItem(STORAGE);if(SUPPORTED.includes(saved))return saved;}catch(_){ }
  for(const candidate of (navigator.languages||[navigator.language])){
    const mapped=mapLocale(candidate,true);if(mapped)return mapped;
  }
  return "en";
}
const locale=resolveLocale();
document.documentElement.lang=locale;
function replaceNodeText(node, source, target){
  const value=node.nodeValue||"";
  const trimmed=value.trim();
  if(trimmed===source){
    const lead=value.match(/^\s*/)?.[0]||"", tail=value.match(/\s*$/)?.[0]||"";
    node.nodeValue=lead+target+tail; return true;
  }
  if(source.length>36 && value.includes(source)){node.nodeValue=value.replace(source,target);return true;}
  return false;
}
function applyMap(map, root=document){
  const walker=document.createTreeWalker(root,NodeFilter.SHOW_TEXT,{acceptNode(n){
    const p=n.parentElement;if(!p||p.closest("script,style,noscript"))return NodeFilter.FILTER_REJECT;
    return NodeFilter.FILTER_ACCEPT;
  }});
  const nodes=[];while(walker.nextNode())nodes.push(walker.currentNode);
  for(const node of nodes){
    const exact=(node.nodeValue||"").trim();
    if(map.has(exact)){replaceNodeText(node,exact,map.get(exact));continue;}
    for(const [source,target] of map){if(source.length>36 && (node.nodeValue||"").includes(source)){replaceNodeText(node,source,target);break;}}
  }
}
function makePicker(){
  const nav=document.querySelector(".nav");if(!nav||document.getElementById("fcmo-language-select"))return;
  const box=document.createElement("div");box.className="fcmo-language";
  box.innerHTML='<label for="fcmo-language-select">Language</label><span class="fcmo-curated-note">curated</span><select id="fcmo-language-select" aria-label="Language"><optgroup label="Canonical source"><option value="en">English</option></optgroup><optgroup label="Curated translations"><option value="es-419">Español</option><option value="zh-Hans">简体中文</option></optgroup></select>';
  nav.appendChild(box);const select=box.querySelector("select");select.value=locale;
  select.addEventListener("change",()=>{const next=select.value;try{localStorage.setItem(STORAGE,next);}catch(_){ }const u=new URL(location.href);u.searchParams.set("lang",next);location.href=u.toString();});
}
function preserveLocaleLinks(){
  if(locale==="en")return;
  for(const a of document.querySelectorAll("a[href]")){
    const raw=a.getAttribute("href");if(!raw||raw.startsWith("#")||raw.startsWith("mailto:")||raw.startsWith("http://")||raw.startsWith("https://"))continue;
    try{const u=new URL(raw,location.href);if(u.origin===location.origin&&u.pathname.startsWith(ROOT)){u.searchParams.set("lang",locale);a.setAttribute("href",u.pathname+u.search+u.hash);}}catch(_){ }
  }
}
function buildMap(catalog, rows){
  const map=new Map();
  if(locale!=="en"){
    for(const [source,variants] of Object.entries(UI)){if(variants[locale])map.set(source,variants[locale]);}
    for(const row of rows){
      const translated=catalog.developments?.[row.id]?.[locale];if(!translated)continue;
      for(const field of catalog.required_fields||["title","summary","why_it_matters"]){if(row[field]&&translated[field])map.set(row[field],translated[field]);}
    }
  }
  return map;
}
function localizePicker(map){
  const box=document.querySelector(".fcmo-language");if(!box)return;
  const label=box.querySelector("label"),note=box.querySelector(".fcmo-curated-note"),groups=box.querySelectorAll("optgroup");
  if(locale!=="en"){
    if(label)label.textContent=UI.Language[locale];if(note)note.textContent=UI.curated[locale];
    if(groups[0])groups[0].label=UI["Canonical source"][locale];if(groups[1])groups[1].label=UI["Curated translations"][locale];
  }
}
makePicker();
Promise.all([
  fetch(ROOT+"data/translations.json",{cache:"no-cache"}).then(r=>{if(!r.ok)throw new Error("translation catalogue unavailable");return r.json();}),
  fetch(ROOT+"data/search.json",{cache:"no-cache"}).then(r=>{if(!r.ok)throw new Error("canonical search index unavailable");return r.json();})
]).then(([catalog,rows])=>{
  const map=buildMap(catalog,rows);applyMap(map);localizePicker(map);preserveLocaleLinks();
  let queued=false;const observer=new MutationObserver(()=>{if(queued)return;queued=true;queueMicrotask(()=>{queued=false;applyMap(map);preserveLocaleLinks();});});
  observer.observe(document.body,{childList:true,subtree:true});
  window.__FCMO_I18N__=Object.freeze({locale,supported:[...SUPPORTED],canonical:"en",curated:["es-419","zh-Hans"],humanReviewed:false});
}).catch(err=>{console.error("FCMO curated localization unavailable:",err);window.__FCMO_I18N__=Object.freeze({locale:"en",supported:[...SUPPORTED],error:String(err)});});
})();
</script>
'''


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise SystemExit(f"invalid JSON {path}: {exc}") from exc


def validate(root: Path) -> tuple[dict, list[dict]]:
    catalog_path = root / "data" / "translations.json"
    search_path = root / "data" / "search.json"
    dev_path = root / "data" / "developments.jsonl"
    if not catalog_path.is_file():
        raise SystemExit("missing curated translation catalogue: data/translations.json")
    if not search_path.is_file() or not dev_path.is_file():
        raise SystemExit("canonical public data missing for i18n validation")

    catalog = load_json(catalog_path)
    search_rows = load_json(search_path)
    if catalog.get("canonical_locale") != "en":
        raise SystemExit("translation catalogue must declare English as canonical_locale")
    if catalog.get("native_locales") != ["en", "es-419", "zh-Hans"]:
        raise SystemExit("native_locales must be exactly en, es-419, zh-Hans")
    if catalog.get("required_fields") != list(REQUIRED_FIELDS):
        raise SystemExit(f"required_fields must be exactly {list(REQUIRED_FIELDS)}")

    canonical = {row.get("id"): row for row in search_rows if PUBLIC_ID.fullmatch(str(row.get("id", "")))}
    public_ids: list[str] = []
    for n, line in enumerate(dev_path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        row = json.loads(line)
        item_id = str(row.get("id", ""))
        if not PUBLIC_ID.fullmatch(item_id):
            raise SystemExit(f"developments.jsonl:{n}: invalid public id for i18n")
        public_ids.append(item_id)

    errors: list[str] = []
    translations = catalog.get("developments") or {}
    if set(translations) != set(public_ids):
        missing = sorted(set(public_ids) - set(translations))
        extra = sorted(set(translations) - set(public_ids))
        if missing: errors.append(f"missing development translations: {missing}")
        if extra: errors.append(f"orphan development translations: {extra}")

    for item_id in public_ids:
        if item_id not in canonical:
            errors.append(f"{item_id}: missing from canonical search index")
            continue
        entry = translations.get(item_id) or {}
        for locale in REQUIRED_LOCALES:
            translated = entry.get(locale) or {}
            for field in REQUIRED_FIELDS:
                value = translated.get(field)
                if not isinstance(value, str) or not value.strip():
                    errors.append(f"{item_id}/{locale}: missing {field}")
                    continue
                source = canonical[item_id].get(field)
                if not isinstance(source, str) or not source.strip():
                    errors.append(f"{item_id}: canonical search index missing {field}")
                elif value.strip() == source.strip():
                    errors.append(f"{item_id}/{locale}: {field} is unchanged canonical English")
        extra_locales = set(entry) - set(REQUIRED_LOCALES)
        if extra_locales:
            errors.append(f"{item_id}: unsupported native locales {sorted(extra_locales)}")

    blob = catalog_path.read_text(encoding="utf-8").lower()
    forbidden = ("translate.googleapis.com", "translate.google.com", "api.deepl.com", "api.cognitive.microsofttranslator.com")
    for endpoint in forbidden:
        if endpoint in blob:
            errors.append(f"runtime translation provider forbidden in catalogue: {endpoint}")
    if errors:
        print("Curated localization validation FAILED:")
        for error in errors:
            print("-", error)
        raise SystemExit(1)
    return catalog, search_rows


def inject(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    if 'id="fcmo-i18n-runtime"' in text:
        return False
    if "</head>" not in text or "</body>" not in text:
        raise SystemExit(f"cannot inject localization runtime into malformed HTML: {path}")
    text = text.replace("</head>", CSS + "</head>", 1)
    text = text.replace("</body>", JS + "</body>", 1)
    path.write_text(text, encoding="utf-8")
    return True


def main() -> None:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else "site").resolve()
    if not root.is_dir():
        raise SystemExit(f"site tree not found: {root}")
    validate(root)
    changed = 0
    for path in sorted(root.rglob("*.html")):
        changed += int(inject(path))
    print(f"FCMO curated localization OK: injected {changed} HTML pages; native locales en/es-419/zh-Hans")


if __name__ == "__main__":
    main()
