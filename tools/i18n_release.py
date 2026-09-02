#!/usr/bin/env python3
"""Apply and validate FCMO AI Newsletter curated native-language presentation.

English is the canonical semantic source. Spanish (es-419) and Simplified Chinese
(zh-Hans) are committed, source-controlled translations. This tool never calls a
translation service or a model; it validates the curated catalogue against the
already-verified frozen release, emits a public locale catalogue, and injects a
small deterministic reader runtime into the final HTML tree.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

NATIVE_LOCALES = ["en", "es-419", "zh-Hans"]
CURATED_LOCALES = ["es-419", "zh-Hans"]
REQUIRED_FIELDS = ["title", "summary", "why_it_matters"]
PUBLIC_ID = re.compile(r"^FCMO-[0-9A-F]{12}$")
RUNTIME_MARKER = 'id="fcmo-curated-i18n-runtime"'
STYLE_MARKER = 'id="fcmo-curated-i18n-style"'
PUBLIC_CATALOGUE = Path("data/translations.json")
DERIVATIVE_MANIFEST = Path("localization-manifest.json")
FORBIDDEN_TRANSLATION_HOSTS = (
    "translate.googleapis.com",
    "translate.google.com",
    "api.deepl.com",
    "api.cognitive.microsofttranslator.com",
)

CSS = r'''<style id="fcmo-curated-i18n-style">
.fcmo-language-switch{position:fixed;z-index:9998;right:14px;bottom:14px;display:flex;align-items:center;gap:7px;padding:6px 7px 6px 10px;border:1px solid rgba(18,18,18,.22);border-radius:999px;background:rgba(250,249,246,.96);box-shadow:0 8px 28px rgba(0,0,0,.12);backdrop-filter:blur(12px);font:750 10px/1.1 Arial,system-ui,sans-serif;letter-spacing:.05em;color:#3e3a34}
.fcmo-language-switch label{font-size:9px;text-transform:uppercase;white-space:nowrap}.fcmo-language-switch select{max-width:150px;min-height:29px;border:1px solid rgba(18,18,18,.16);border-radius:999px;background:#fff;color:#111;padding:0 8px;font:750 11px/1.1 Arial,system-ui,sans-serif;outline:none}.fcmo-language-switch .curated{font-size:8px;color:#8d1d17;text-transform:uppercase;white-space:nowrap}
:lang(zh-Hans){font-synthesis:none}.fcmo-language-switch:focus-within{box-shadow:0 0 0 3px rgba(141,29,23,.14),0 8px 28px rgba(0,0,0,.12)}
@media(max-width:620px){.fcmo-language-switch{right:8px;bottom:8px;padding:5px 6px}.fcmo-language-switch label,.fcmo-language-switch .curated{display:none}.fcmo-language-switch select{max-width:124px}}
</style>'''

JS = r'''<script id="fcmo-curated-i18n-runtime">
(()=>{
"use strict";
const ROOT="/FCMO-AI-Newsletter/";
const SUPPORTED=["en","es-419","zh-Hans"];
const STORAGE="fcmo-newsletter-language";
const CATALOGUE=ROOT+"data/translations.json";
function mapLocale(value,browser=false){
  if(!value)return null;
  const lower=String(value).toLowerCase();
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
  for(const candidate of (navigator.languages||[navigator.language])){const mapped=mapLocale(candidate,true);if(mapped)return mapped;}
  return "en";
}
const locale=resolveLocale();
document.documentElement.lang=locale;
function makePicker(){
  if(document.getElementById("fcmo-language-select"))return;
  const box=document.createElement("div");box.className="fcmo-language-switch";
  box.innerHTML='<label for="fcmo-language-select">Language</label><span class="curated">curated</span><select id="fcmo-language-select" aria-label="Language"><optgroup label="Canonical source"><option value="en">English</option></optgroup><optgroup label="Curated translations"><option value="es-419">Español</option><option value="zh-Hans">简体中文</option></optgroup></select>';
  document.body.appendChild(box);
  const select=box.querySelector("select");select.value=locale;
  select.addEventListener("change",()=>{const next=select.value;try{localStorage.setItem(STORAGE,next);}catch(_){ }const u=new URL(location.href);u.searchParams.set("lang",next);location.href=u.toString();});
}
function preserveLocaleLinks(root=document){
  if(locale==="en")return;
  for(const a of root.querySelectorAll?.("a[href]")||[]){
    const raw=a.getAttribute("href");if(!raw||raw.startsWith("#")||raw.startsWith("mailto:")||raw.startsWith("javascript:"))continue;
    try{const u=new URL(raw,location.href);if(u.origin===location.origin&&u.pathname.startsWith(ROOT)){u.searchParams.set("lang",locale);a.setAttribute("href",u.pathname+u.search+u.hash);}}catch(_){ }
  }
}
function replaceText(node,map){
  const value=node.nodeValue||"", exact=value.trim();
  if(map.has(exact)){
    const lead=value.match(/^\s*/)?.[0]||"", tail=value.match(/\s*$/)?.[0]||"";
    node.nodeValue=lead+map.get(exact)+tail;return;
  }
  for(const [source,target] of map){if(source.length>48&&value.includes(source)){node.nodeValue=value.replaceAll(source,target);return;}}
}
function applyMap(map,root=document){
  const walker=document.createTreeWalker(root,NodeFilter.SHOW_TEXT,{acceptNode(n){const p=n.parentElement;if(!p||p.closest("script,style,noscript,code,pre"))return NodeFilter.FILTER_REJECT;return NodeFilter.FILTER_ACCEPT;}});
  const nodes=[];while(walker.nextNode())nodes.push(walker.currentNode);for(const node of nodes)replaceText(node,map);
  for(const el of root.querySelectorAll?.("[placeholder],[aria-label],[title]")||[]){for(const attr of ["placeholder","aria-label","title"]){const v=el.getAttribute(attr);if(v&&map.has(v))el.setAttribute(attr,map.get(v));}}
}
function buildMap(catalogue){
  const map=new Map();if(locale==="en")return map;
  for(const [source,variants] of Object.entries(catalogue.ui||{})){if(variants?.[locale])map.set(source,variants[locale]);}
  for(const entry of Object.values(catalogue.developments||{})){
    const source=entry.source||{}, translated=entry[locale]||{};
    for(const field of catalogue.required_fields||[]){if(source[field]&&translated[field])map.set(source[field],translated[field]);}
  }
  return map;
}
function localizePicker(catalogue){
  const box=document.querySelector(".fcmo-language-switch");if(!box||locale==="en")return;
  const ui=catalogue.ui||{}, t=s=>ui[s]?.[locale]||s;
  const label=box.querySelector("label"), curated=box.querySelector(".curated"), groups=box.querySelectorAll("optgroup");
  if(label)label.textContent=t("Language");if(curated)curated.textContent=t("curated");
  if(groups[0])groups[0].label=t("Canonical source");if(groups[1])groups[1].label=t("Curated translations");
}
makePicker();preserveLocaleLinks();
fetch(CATALOGUE,{cache:"no-cache"}).then(r=>{if(!r.ok)throw new Error("curated translation catalogue unavailable");return r.json();}).then(catalogue=>{
  const map=buildMap(catalogue);applyMap(map);localizePicker(catalogue);preserveLocaleLinks();
  let queued=false;const observer=new MutationObserver(mutations=>{if(queued)return;queued=true;queueMicrotask(()=>{queued=false;for(const m of mutations){for(const node of m.addedNodes){if(node.nodeType===1){applyMap(map,node);preserveLocaleLinks(node);}else if(node.nodeType===3)replaceText(node,map);}}});});
  observer.observe(document.documentElement,{childList:true,subtree:true});
  window.__FCMO_I18N__=Object.freeze({locale,supported:[...SUPPORTED],canonical:"en",curated:["es-419","zh-Hans"],humanReviewed:false});
}).catch(err=>{console.error("FCMO curated localization unavailable:",err);window.__FCMO_I18N__=Object.freeze({locale:"en",error:String(err)});});
})();
</script>'''

# Compact, intentionally high-value interface vocabulary. Story prose is handled by
# the source-controlled per-brief catalogue; these strings localize navigation and
# recurring editorial labels without pretending machine metadata has been translated.
UI = {
    "Language": {"es-419": "Idioma", "zh-Hans": "语言"},
    "curated": {"es-419": "curada", "zh-Hans": "精选"},
    "Canonical source": {"es-419": "Fuente canónica", "zh-Hans": "规范来源"},
    "Curated translations": {"es-419": "Traducciones curadas", "zh-Hans": "精选翻译"},
    "Front page": {"es-419": "Portada", "zh-Hans": "首页"},
    "Front Page": {"es-419": "Portada", "zh-Hans": "首页"},
    "Research": {"es-419": "Investigación", "zh-Hans": "研究"},
    "Desks": {"es-419": "Secciones", "zh-Hans": "栏目"},
    "Editions": {"es-419": "Ediciones", "zh-Hans": "期刊"},
    "Chronology": {"es-419": "Cronología", "zh-Hans": "时间线"},
    "Topics": {"es-419": "Temas", "zh-Hans": "主题"},
    "Organizations": {"es-419": "Organizaciones", "zh-Hans": "机构"},
    "Agent": {"es-419": "Agente", "zh-Hans": "智能体"},
    "Search /": {"es-419": "Buscar /", "zh-Hans": "搜索 /"},
    "Search": {"es-419": "Buscar", "zh-Hans": "搜索"},
    "Archive": {"es-419": "Archivo", "zh-Hans": "存档"},
    "Corrections": {"es-419": "Correcciones", "zh-Hans": "更正"},
    "Feeds": {"es-419": "Fuentes", "zh-Hans": "订阅源"},
    "Feeds & data": {"es-419": "Fuentes y datos", "zh-Hans": "订阅源与数据"},
    "About": {"es-419": "Acerca de", "zh-Hans": "关于"},
    "About / Evidence": {"es-419": "Acerca de / Evidencia", "zh-Hans": "关于 / 证据"},
    "Privacy": {"es-419": "Privacidad", "zh-Hans": "隐私"},
    "License": {"es-419": "Licencia", "zh-Hans": "许可"},
    "Disclaimer": {"es-419": "Aviso legal", "zh-Hans": "免责声明"},
    "Research Intelligence": {"es-419": "Inteligencia de investigación", "zh-Hans": "研究情报"},
    "public briefs": {"es-419": "briefs públicos", "zh-Hans": "公开简报"},
    "open evidence gaps": {"es-419": "vacíos de evidencia abiertos", "zh-Hans": "未闭合证据缺口"},
    "explicit relationships": {"es-419": "relaciones explícitas", "zh-Hans": "显式关联"},
    "Machine-readable corpus →": {"es-419": "Corpus legible por máquina →", "zh-Hans": "机器可读语料 →"},
    "Evidence first.": {"es-419": "La evidencia primero.", "zh-Hans": "证据优先。"},
    "Memory intact.": {"es-419": "Memoria intacta.", "zh-Hans": "记忆完整。"},
    "All research": {"es-419": "Toda la investigación", "zh-Hans": "全部研究"},
    "Agent view": {"es-419": "Vista de agente", "zh-Hans": "智能体视图"},
    "Continuous evidence-first intelligence on the AI frontier": {"es-419": "Inteligencia continua y basada en evidencia sobre la frontera de la IA", "zh-Hans": "持续、证据优先的人工智能前沿情报"},
    "Why it matters": {"es-419": "Por qué importa", "zh-Hans": "为什么重要"},
    "The editorial consequence.": {"es-419": "La consecuencia editorial.", "zh-Hans": "编辑判断。"},
    "Claims ledger": {"es-419": "Registro de afirmaciones", "zh-Hans": "论断记录"},
    "What is actually being asserted.": {"es-419": "Qué se está afirmando realmente.", "zh-Hans": "实际提出了哪些论断。"},
    "Technical dossier": {"es-419": "Dossier técnico", "zh-Hans": "技术档案"},
    "Mechanism and regime.": {"es-419": "Mecanismo y régimen.", "zh-Hans": "机制与适用条件。"},
    "Research implications": {"es-419": "Implicaciones para investigación", "zh-Hans": "研究启示"},
    "Engineering implications": {"es-419": "Implicaciones de ingeniería", "zh-Hans": "工程启示"},
    "Policy implications": {"es-419": "Implicaciones de política pública", "zh-Hans": "政策启示"},
    "Contradictory evidence": {"es-419": "Evidencia contradictoria", "zh-Hans": "相反证据"},
    "Limitations": {"es-419": "Limitaciones", "zh-Hans": "局限"},
    "Open evidence gaps": {"es-419": "Vacíos de evidencia abiertos", "zh-Hans": "未闭合证据缺口"},
    "What would change our mind.": {"es-419": "Qué podría cambiar nuestra evaluación.", "zh-Hans": "什么证据会改变当前判断。"},
    "No explicit open gaps are recorded.": {"es-419": "No hay vacíos abiertos explícitos registrados.", "zh-Hans": "未记录明确的开放证据缺口。"},
    "Impact": {"es-419": "Impacto", "zh-Hans": "影响"},
    "Event": {"es-419": "Evento", "zh-Hans": "事件"},
    "Verified": {"es-419": "Verificado", "zh-Hans": "已验证"},
    "Evidence": {"es-419": "Evidencia", "zh-Hans": "证据"},
    "Confidence": {"es-419": "Confianza", "zh-Hans": "置信度"},
    "Importance": {"es-419": "Importancia", "zh-Hans": "重要性"},
    "Status": {"es-419": "Estado", "zh-Hans": "状态"},
    "Mechanism": {"es-419": "Mecanismo", "zh-Hans": "机制"},
    "Demonstrated result": {"es-419": "Resultado demostrado", "zh-Hans": "已证实结果"},
    "Claimed result": {"es-419": "Resultado declarado", "zh-Hans": "声称结果"},
    "Strongest baseline": {"es-419": "Línea base más sólida", "zh-Hans": "最强基线"},
    "Regime": {"es-419": "Régimen", "zh-Hans": "适用条件"},
    "Implementation status": {"es-419": "Estado de implementación", "zh-Hans": "实现状态"},
    "Compute / cost": {"es-419": "Cómputo / costo", "zh-Hans": "计算 / 成本"},
    "Novelty": {"es-419": "Novedad", "zh-Hans": "新颖性"},
    "Reproducibility": {"es-419": "Reproducibilidad", "zh-Hans": "可复现性"},
    "Sources": {"es-419": "Fuentes", "zh-Hans": "来源"},
    "Interactive deterministic index": {"es-419": "Índice interactivo determinista", "zh-Hans": "确定性交互索引"},
    "Search all research": {"es-419": "Buscar en toda la investigación", "zh-Hans": "搜索全部研究"},
    "All filtering happens in your browser over the generated repository projection. No model is queried.": {"es-419": "Todo el filtrado ocurre en tu navegador sobre la proyección generada del repositorio. No se consulta ningún modelo.", "zh-Hans": "所有筛选都在浏览器中针对生成的仓库投影完成，不会查询任何模型。"},
    "Search title, summary, mechanism, topic, organization…": {"es-419": "Buscar título, resumen, mecanismo, tema, organización…", "zh-Hans": "搜索标题、摘要、机制、主题、机构…"},
    "Loading index…": {"es-419": "Cargando índice…", "zh-Hans": "正在加载索引…"},
    "Sort: importance": {"es-419": "Ordenar: importancia", "zh-Hans": "排序：重要性"},
    "Sort: recent": {"es-419": "Ordenar: reciente", "zh-Hans": "排序：最近"},
    "Sort: evidence": {"es-419": "Ordenar: evidencia", "zh-Hans": "排序：证据"},
}


def canonical_digest(brief: dict) -> str:
    payload = "\0".join(str(brief.get(field, "")).strip() for field in REQUIRED_FIELDS).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def read_json(path: Path) -> dict | list:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise SystemExit(f"invalid JSON {path}: {exc}") from exc


def load_briefs(site: Path) -> dict[str, dict]:
    root = site / "data" / "briefs"
    if not root.is_dir():
        raise SystemExit(f"missing canonical brief directory: {root}")
    briefs: dict[str, dict] = {}
    for path in sorted(root.glob("FCMO-*.json")):
        wrapper = read_json(path)
        if not isinstance(wrapper, dict) or not isinstance(wrapper.get("brief"), dict):
            raise SystemExit(f"invalid public brief wrapper: {path}")
        brief = wrapper["brief"]
        ident = str(brief.get("id", ""))
        if not PUBLIC_ID.fullmatch(ident) or path.stem != ident:
            raise SystemExit(f"brief id/path mismatch: {path}")
        briefs[ident] = brief
    if not briefs:
        raise SystemExit("no canonical public briefs found")
    return briefs


def validate_source_catalogue(source: Path, site: Path) -> tuple[dict, dict[str, dict]]:
    catalogue_path = source / "localization" / "translations.json"
    catalogue = read_json(catalogue_path)
    if not isinstance(catalogue, dict):
        raise SystemExit("translation catalogue must be an object")
    errors: list[str] = []
    if catalogue.get("canonical_locale") != "en": errors.append("canonical_locale must be en")
    if catalogue.get("native_locales") != NATIVE_LOCALES: errors.append(f"native_locales must be exactly {NATIVE_LOCALES}")
    if catalogue.get("required_fields") != REQUIRED_FIELDS: errors.append(f"required_fields must be exactly {REQUIRED_FIELDS}")
    for locale in CURATED_LOCALES:
        meta = (catalogue.get("curation") or {}).get(locale) or {}
        if meta.get("human_reviewed") is not False: errors.append(f"{locale}: human_reviewed must remain false until actual qualified review")
    briefs = load_briefs(site)
    entries = catalogue.get("developments") or {}
    if set(entries) != set(briefs):
        missing = sorted(set(briefs) - set(entries)); extra = sorted(set(entries) - set(briefs))
        if missing: errors.append(f"missing curated story translations: {missing}")
        if extra: errors.append(f"orphan curated story translations: {extra}")
    for ident, brief in briefs.items():
        entry = entries.get(ident) or {}
        digest = canonical_digest(brief)
        if entry.get("source_sha256") != digest:
            errors.append(f"{ident}: canonical English changed; recurate translations and refresh source_sha256")
        for field in REQUIRED_FIELDS:
            source_text = brief.get(field)
            if not isinstance(source_text, str) or not source_text.strip(): errors.append(f"{ident}: canonical {field} missing")
        for locale in CURATED_LOCALES:
            translated = entry.get(locale) or {}
            if not isinstance(translated, dict):
                errors.append(f"{ident}/{locale}: locale entry missing"); continue
            for field in REQUIRED_FIELDS:
                value = translated.get(field)
                if not isinstance(value, str) or not value.strip(): errors.append(f"{ident}/{locale}: missing {field}")
                elif value.strip() == str(brief.get(field, "")).strip(): errors.append(f"{ident}/{locale}: {field} unchanged from canonical English")
    for source_text, variants in UI.items():
        if not source_text.strip(): errors.append("blank UI source string")
        for locale in CURATED_LOCALES:
            if not isinstance((variants or {}).get(locale), str) or not variants[locale].strip(): errors.append(f"UI/{locale}: missing translation for {source_text!r}")
    raw = catalogue_path.read_text(encoding="utf-8").lower()
    for host in FORBIDDEN_TRANSLATION_HOSTS:
        if host in raw: errors.append(f"runtime translation provider forbidden in source catalogue: {host}")
    if errors:
        print("Curated localization source validation FAILED:")
        for error in errors: print("-", error)
        raise SystemExit(1)
    return catalogue, briefs


def public_catalogue(source_catalogue: dict, briefs: dict[str, dict]) -> dict:
    out = {
        "schema": "fcmo-public-curated-i18n-v1",
        "canonical_locale": "en",
        "native_locales": NATIVE_LOCALES,
        "required_fields": REQUIRED_FIELDS,
        "curation": source_catalogue["curation"],
        "ui": UI,
        "developments": {},
    }
    for ident in sorted(briefs):
        src = source_catalogue["developments"][ident]
        brief = briefs[ident]
        out["developments"][ident] = {
            "source_sha256": src["source_sha256"],
            "source": {field: brief[field] for field in REQUIRED_FIELDS},
            "es-419": {field: src["es-419"][field] for field in REQUIRED_FIELDS},
            "zh-Hans": {field: src["zh-Hans"][field] for field in REQUIRED_FIELDS},
        }
    return out


def inject_html(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    if RUNTIME_MARKER in text and STYLE_MARKER in text: return False
    if "</head>" not in text or "</body>" not in text:
        raise SystemExit(f"malformed HTML cannot receive localization runtime: {path}")
    if STYLE_MARKER not in text: text = text.replace("</head>", CSS + "</head>", 1)
    if RUNTIME_MARKER not in text: text = text.replace("</body>", JS + "</body>", 1)
    path.write_text(text, encoding="utf-8")
    return True


def tree_sha256(site: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(p for p in site.rglob("*") if p.is_file() and p.relative_to(site) != DERIVATIVE_MANIFEST):
        rel = path.relative_to(site).as_posix().encode("utf-8")
        data_hash = hashlib.sha256(path.read_bytes()).hexdigest().encode("ascii")
        digest.update(rel + b"\0" + data_hash + b"\n")
    return digest.hexdigest()


def source_catalogue_sha256(source: Path) -> str:
    return hashlib.sha256((source / "localization" / "translations.json").read_bytes()).hexdigest()


def write_manifest(source: Path, site: Path, briefs: dict[str, dict], html_count: int) -> dict:
    release_manifest = read_json(source / "release-overlay" / "final" / "manifest.json")
    manifest = {
        "schema": "fcmo-localized-release-derivative-v1",
        "canonical_release": release_manifest.get("release"),
        "canonical_archive_sha256": release_manifest.get("archive_sha256"),
        "native_locales": NATIVE_LOCALES,
        "canonical_briefs": len(briefs),
        "html_pages": html_count,
        "source_catalogue_sha256": source_catalogue_sha256(source),
        "human_reviewed": False,
        "runtime_translation_provider": None,
        "tree_sha256": tree_sha256(site),
    }
    (site / DERIVATIVE_MANIFEST).write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def apply(source: Path, site: Path) -> None:
    catalogue, briefs = validate_source_catalogue(source, site)
    pub = public_catalogue(catalogue, briefs)
    public_path = site / PUBLIC_CATALOGUE
    public_path.parent.mkdir(parents=True, exist_ok=True)
    public_path.write_text(json.dumps(pub, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    changed = 0
    pages = sorted(site.rglob("*.html"))
    for page in pages: changed += int(inject_html(page))
    manifest = write_manifest(source, site, briefs, len(pages))
    print(f"FCMO curated localization applied: {len(briefs)} briefs, {len(pages)} HTML pages, {changed} newly injected")
    print("localized tree sha256:", manifest["tree_sha256"])


def validate_derivative(source: Path, site: Path) -> None:
    catalogue, briefs = validate_source_catalogue(source, site)
    errors: list[str] = []
    expected_public = public_catalogue(catalogue, briefs)
    public_path = site / PUBLIC_CATALOGUE
    if not public_path.is_file(): errors.append("missing public curated translation catalogue")
    else:
        actual = read_json(public_path)
        if actual != expected_public: errors.append("public translation catalogue differs from deterministic source projection")
    pages = sorted(site.rglob("*.html"))
    for page in pages:
        text = page.read_text(encoding="utf-8")
        rel = page.relative_to(site).as_posix()
        if RUNTIME_MARKER not in text or STYLE_MARKER not in text: errors.append(f"{rel}: curated localization runtime/style missing")
        lower = text.lower()
        for host in FORBIDDEN_TRANSLATION_HOSTS:
            if host in lower: errors.append(f"{rel}: runtime translation endpoint forbidden: {host}")
    manifest_path = site / DERIVATIVE_MANIFEST
    if not manifest_path.is_file(): errors.append("missing localization-manifest.json")
    else:
        manifest = read_json(manifest_path)
        if manifest.get("native_locales") != NATIVE_LOCALES: errors.append("derivative manifest locale contract mismatch")
        if manifest.get("canonical_briefs") != len(briefs): errors.append("derivative manifest brief count mismatch")
        if manifest.get("html_pages") != len(pages): errors.append("derivative manifest HTML count mismatch")
        if manifest.get("source_catalogue_sha256") != source_catalogue_sha256(source): errors.append("source catalogue digest mismatch")
        actual_tree = tree_sha256(site)
        if manifest.get("tree_sha256") != actual_tree: errors.append("localized release tree hash mismatch")
    if errors:
        print("Curated localized derivative validation FAILED:")
        for error in errors: print("-", error)
        raise SystemExit(1)
    print(f"FCMO curated localized derivative OK: {len(briefs)} briefs, {len(pages)} HTML pages, en/es-419/zh-Hans")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("site", type=Path, help="already-assembled and canonically validated public release tree")
    parser.add_argument("--source", type=Path, default=Path("."), help="repository root containing localization/ and release manifest")
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    source = args.source.resolve(); site = args.site.resolve()
    if not source.is_dir() or not site.is_dir(): raise SystemExit("source repository or site directory does not exist")
    if args.validate_only: validate_derivative(source, site)
    else: apply(source, site)

if __name__ == "__main__": main()
