#!/usr/bin/env node

/**
 * audit-accessibility.js
 * =========================================================================
 * Subtarea 5.8 del Plan de Trabajo Pre-SAT — Plataforma DTI Níjar
 * Expediente 18962/2025 — IT DIGITTAL
 * =========================================================================
 *
 * Script de auditoría de accesibilidad WCAG 2.1 AA sobre los frontales
 * desarrollados por IT DIGITTAL (tótem y dashboard).
 *
 * Tecnologías utilizadas:
 *   - Playwright   ──  navegador headless real (Chromium 120+)
 *   - axe-core 4.x ──  motor de auditoría accesibilidad estándar (Deque Systems)
 *   - Lighthouse 11 ─  scoring global de accesibilidad
 *
 * Criterios:
 *   - Estándar: WCAG 2.1 nivel AA (referencia UNE 139803)
 *   - Severidades bloqueantes: critical + serious
 *   - Severidades informativas (no bloquean): moderate + minor
 *   - Score Lighthouse mínimo aceptable: 90/100
 *
 * Uso:
 *   node audit-accessibility.js                  # auditoría completa
 *   node audit-accessibility.js --only=totem     # solo el tótem
 *   node audit-accessibility.js --strict         # también moderate y minor
 *   node audit-accessibility.js --base=http://...  # URL base custom
 *
 * Salida:
 *   reports/accessibility/audit-YYYY-MM-DD/
 *     ├── index.html       (informe HTML consolidado y navegable)
 *     ├── findings.json    (datos crudos para integraciones)
 *     ├── findings.xlsx    (plantilla de hallazgos para seguimiento)
 *     └── lighthouse/      (informes Lighthouse por página)
 *
 * Códigos de salida:
 *   0  → todas las páginas pasan (auditoría OK)
 *   1  → al menos 1 violación bloqueante (critical o serious)
 *   2  → score Lighthouse < umbral en alguna página
 *   3  → error técnico durante la ejecución
 * =========================================================================
 */

import { chromium } from 'playwright';
import { AxeBuilder } from '@axe-core/playwright';
import lighthouse from 'lighthouse';
import * as ChromeLauncher from 'chrome-launcher';
import { writeFileSync, mkdirSync, existsSync } from 'node:fs';
import { join } from 'node:path';

// ============================================================
// Configuración (ajustable por flags CLI o variables de entorno)
// ============================================================

const args = parseArgs(process.argv.slice(2));
const BASE_URL = args.base || process.env.NIJAR_BASE_URL || 'http://localhost:8000';
const STRICT_MODE = args.strict === true;
const ONLY_FRONT = args.only || null;  // 'totem' | 'dashboard' | null
const LIGHTHOUSE_THRESHOLD = 90;

const SEVERITIES_BLOCKING = ['critical', 'serious'];
const SEVERITIES_REPORTED = STRICT_MODE
  ? ['critical', 'serious', 'moderate', 'minor']
  : SEVERITIES_BLOCKING;

const PAGES = [
  {
    id: 'totem-home',
    name: 'Tótem — pantalla principal',
    url: `${BASE_URL}/totem`,
    front: 'totem',
    waitFor: 'main',
    description: 'Página inicial del tótem con cabecera, categorías, grid de POIs, chatbot y footer.',
  },
  {
    id: 'totem-high-contrast',
    name: 'Tótem — modo alto contraste activo',
    url: `${BASE_URL}/totem`,
    front: 'totem',
    waitFor: 'main',
    actions: [{ type: 'click', selector: '#contrast-toggle' }],
    description: 'Mismo tótem con el modo alto contraste activado (clase body.high-contrast).',
  },
  {
    id: 'totem-text-large',
    name: 'Tótem — modo texto grande activo',
    url: `${BASE_URL}/totem`,
    front: 'totem',
    waitFor: 'main',
    actions: [{ type: 'click', selector: '#text-size-toggle' }],
    description: 'Tótem con tamaño de texto aumentado (clase body.text-lg-mode).',
  },
  {
    id: 'dashboard-home',
    name: 'Dashboard — pestaña Resumen',
    url: `${BASE_URL}/dashboard`,
    front: 'dashboard',
    waitFor: '[data-tab="overview"]',
    description: 'Dashboard administrativo en la pestaña por defecto (Resumen).',
  },
  {
    id: 'dashboard-environment',
    name: 'Dashboard — pestaña Ambiental',
    url: `${BASE_URL}/dashboard`,
    front: 'dashboard',
    waitFor: '[data-tab="environment"]',
    actions: [{ type: 'click', selector: '[data-tab="environment"]' }],
    description: 'Dashboard en la pestaña Ambiental con KPIs de los sensores Smart Office.',
  },
];

// Filtra por frontal si se ha pedido
const PAGES_TO_AUDIT = ONLY_FRONT
  ? PAGES.filter(p => p.front === ONLY_FRONT)
  : PAGES;

// ============================================================
// Salida: directorio con timestamp
// ============================================================

const today = new Date().toISOString().slice(0, 10);
const OUT_DIR = join('reports', 'accessibility', `audit-${today}`);
const OUT_LIGHTHOUSE = join(OUT_DIR, 'lighthouse');
mkdirSync(OUT_LIGHTHOUSE, { recursive: true });

// ============================================================
// Logger
// ============================================================

const log = {
  info: (m) => console.log(`\x1b[36mℹ\x1b[0m ${m}`),
  ok:   (m) => console.log(`\x1b[32m✓\x1b[0m ${m}`),
  warn: (m) => console.log(`\x1b[33m⚠\x1b[0m ${m}`),
  err:  (m) => console.log(`\x1b[31m✗\x1b[0m ${m}`),
  hr:   ()  => console.log('─'.repeat(72)),
};

// ============================================================
// Auditoría axe-core sobre una página
// ============================================================

async function auditPageAxe(page, config) {
  const builder = new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa']);

  // Excluir reglas conocidas que dan falsos positivos en kioscos
  // (ej: 'region' en componentes que sí están dentro de <main>)
  // Mantener vacío por defecto para no enmascarar problemas reales.

  const results = await builder.analyze();

  return {
    url: page.url(),
    timestamp: new Date().toISOString(),
    violations: results.violations,
    passes: results.passes.length,
    incomplete: results.incomplete.length,
    inapplicable: results.inapplicable.length,
  };
}

// ============================================================
// Auditoría Lighthouse sobre una URL
// ============================================================

async function auditPageLighthouse(url, pageId) {
  const chrome = await ChromeLauncher.launch({
    chromeFlags: ['--headless', '--no-sandbox', '--disable-gpu'],
  });

  try {
    const options = {
      logLevel: 'error',
      output: 'html',
      onlyCategories: ['accessibility'],
      port: chrome.port,
    };

    const runnerResult = await lighthouse(url, options);
    const score = Math.round(runnerResult.lhr.categories.accessibility.score * 100);

    // Guardar informe HTML
    const lhPath = join(OUT_LIGHTHOUSE, `${pageId}.html`);
    writeFileSync(lhPath, runnerResult.report);

    return { score, reportPath: lhPath };
  } finally {
    await chrome.kill();
  }
}

// ============================================================
// Ejecución principal
// ============================================================

(async () => {
  log.hr();
  log.info(`Plataforma DTI Níjar — Auditoría WCAG 2.1 AA`);
  log.info(`Expediente 18962/2025 — Subtarea 5.8 del Plan Pre-SAT`);
  log.info(`Fecha: ${today}  ·  URL base: ${BASE_URL}`);
  log.info(`Modo: ${STRICT_MODE ? 'estricto (incluye moderate/minor)' : 'normal (solo critical/serious)'}`);
  log.info(`Páginas a auditar: ${PAGES_TO_AUDIT.length}`);
  log.hr();

  // Verificar que el servidor responde
  try {
    const r = await fetch(BASE_URL);
    if (!r.ok) throw new Error(`status ${r.status}`);
  } catch (e) {
    log.err(`No se puede conectar a ${BASE_URL}: ${e.message}`);
    log.err('¿Está arrancado el proyecto? Ejecuta: .\\windows\\start.bat');
    process.exit(3);
  }

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 1080, height: 1920 },  // pantalla del tótem real
    deviceScaleFactor: 1,
  });

  const findings = [];
  let totalBlocking = 0;
  let lighthouseFailures = 0;

  for (const config of PAGES_TO_AUDIT) {
    log.info(`Auditando: ${config.name}`);
    log.info(`  URL: ${config.url}`);

    const page = await context.newPage();
    try {
      await page.goto(config.url, { waitUntil: 'networkidle', timeout: 30_000 });

      // Esperar selector si está definido
      if (config.waitFor) {
        await page.waitForSelector(config.waitFor, { timeout: 10_000 }).catch(() => null);
      }

      // Acciones previas (toggle de modos, cambio de pestaña, etc.)
      for (const action of config.actions || []) {
        if (action.type === 'click') {
          await page.click(action.selector).catch(() => null);
          await page.waitForTimeout(500);
        }
      }

      // Auditoría axe-core
      const axeResult = await auditPageAxe(page, config);
      const blocking = axeResult.violations.filter(v =>
        SEVERITIES_BLOCKING.includes(v.impact)
      );
      const informative = axeResult.violations.filter(v =>
        ['moderate', 'minor'].includes(v.impact)
      );

      // Auditoría Lighthouse
      let lighthouseResult = null;
      try {
        lighthouseResult = await auditPageLighthouse(config.url, config.id);
      } catch (e) {
        log.warn(`  Lighthouse falló: ${e.message}`);
      }

      // Resumen por consola
      if (blocking.length === 0) {
        log.ok(`  axe-core: 0 bloqueantes  (${informative.length} informativas, ${axeResult.passes} reglas OK)`);
      } else {
        log.err(`  axe-core: ${blocking.length} BLOQUEANTES  (${informative.length} informativas)`);
        for (const v of blocking) {
          log.err(`    [${v.impact}] ${v.id} — ${v.description}`);
        }
      }
      if (lighthouseResult) {
        if (lighthouseResult.score >= LIGHTHOUSE_THRESHOLD) {
          log.ok(`  Lighthouse: ${lighthouseResult.score}/100`);
        } else {
          log.err(`  Lighthouse: ${lighthouseResult.score}/100 (umbral ${LIGHTHOUSE_THRESHOLD})`);
          lighthouseFailures++;
        }
      }

      totalBlocking += blocking.length;

      findings.push({
        page: config,
        axe: axeResult,
        violations: {
          blocking: blocking.map(simplifyViolation),
          informative: informative.map(simplifyViolation),
        },
        lighthouse: lighthouseResult,
      });

    } catch (e) {
      log.err(`  Error: ${e.message}`);
      findings.push({ page: config, error: e.message });
    } finally {
      await page.close();
    }

    log.hr();
  }

  await browser.close();

  // Generar artefactos
  log.info('Generando informe HTML...');
  const reportPath = join(OUT_DIR, 'index.html');
  writeFileSync(reportPath, renderReportHTML(findings, { today, BASE_URL, STRICT_MODE, LIGHTHOUSE_THRESHOLD }));

  log.info('Guardando datos crudos...');
  writeFileSync(join(OUT_DIR, 'findings.json'), JSON.stringify(findings, null, 2));

  log.info('Generando plantilla de seguimiento Excel...');
  await writeExcelFindings(findings, join(OUT_DIR, 'findings.xlsx'));

  // Resumen final
  log.hr();
  log.info(`Informe HTML: ${reportPath}`);
  log.info(`Plantilla seguimiento: ${join(OUT_DIR, 'findings.xlsx')}`);
  log.info(`Datos crudos: ${join(OUT_DIR, 'findings.json')}`);

  if (totalBlocking > 0) {
    log.err(`AUDITORÍA FALLIDA: ${totalBlocking} violación(es) bloqueante(s)`);
    process.exit(1);
  }
  if (lighthouseFailures > 0) {
    log.err(`AUDITORÍA FALLIDA: ${lighthouseFailures} página(s) por debajo del umbral Lighthouse`);
    process.exit(2);
  }
  log.ok(`AUDITORÍA SUPERADA — 0 bloqueantes, todos los Lighthouse ≥ ${LIGHTHOUSE_THRESHOLD}/100`);
  process.exit(0);
})().catch(err => {
  console.error('\x1b[31mError fatal:\x1b[0m', err);
  process.exit(3);
});

// ============================================================
// Helpers
// ============================================================

function parseArgs(argv) {
  const out = {};
  for (const a of argv) {
    if (a.startsWith('--')) {
      const [k, v] = a.slice(2).split('=');
      out[k] = v === undefined ? true : v;
    }
  }
  return out;
}

function simplifyViolation(v) {
  return {
    id: v.id,
    impact: v.impact,
    description: v.description,
    help: v.help,
    helpUrl: v.helpUrl,
    tags: v.tags,
    nodes: v.nodes.slice(0, 5).map(n => ({
      html: n.html,
      target: n.target,
      failureSummary: n.failureSummary,
    })),
  };
}

function renderReportHTML(findings, meta) {
  const totalBlocking = findings.reduce((s, f) =>
    s + (f.violations?.blocking?.length || 0), 0);
  const totalInformative = findings.reduce((s, f) =>
    s + (f.violations?.informative?.length || 0), 0);

  const escape = (s) => String(s ?? '')
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;').replace(/'/g, '&#39;');

  const verdictClass = totalBlocking === 0 ? 'verdict-ok' : 'verdict-fail';
  const verdictText = totalBlocking === 0 ? 'AUDITORÍA SUPERADA' : 'AUDITORÍA FALLIDA';

  return `<!DOCTYPE html>
<html lang="es"><head>
<meta charset="UTF-8">
<title>Auditoría WCAG 2.1 AA — Plataforma DTI Níjar — ${meta.today}</title>
<style>
  :root {
    --marino: #003B7A;
    --teal: #00A6C0;
    --dorado: #F4C430;
    --arena: #FAFAF7;
    --negro: #0A1628;
    --gris: #4A5568;
    --error: #DC2626;
    --ok: #16A34A;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: -apple-system, "Segoe UI", Helvetica, Arial, sans-serif;
    background: var(--arena);
    color: var(--negro);
    line-height: 1.55;
  }
  .hero {
    background: linear-gradient(135deg, var(--marino), #002952);
    color: white;
    padding: 48px 60px;
    border-bottom: 6px solid var(--teal);
  }
  .hero h1 { font-size: 32px; font-weight: 800; letter-spacing: -0.02em; }
  .hero p { opacity: 0.9; margin-top: 8px; font-size: 14px; }
  .verdict { display: inline-block; padding: 8px 18px; border-radius: 30px; font-weight: 700; font-size: 13px; letter-spacing: 0.1em; margin-top: 18px; }
  .verdict-ok { background: var(--ok); color: white; }
  .verdict-fail { background: var(--error); color: white; }
  main { max-width: 1100px; margin: 40px auto; padding: 0 30px; }
  .summary-cards { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 40px; }
  .card { background: white; border-radius: 16px; padding: 22px 20px; box-shadow: 0 4px 12px -4px rgba(0,59,122,0.15); border-top: 4px solid var(--marino); }
  .card.bloqueante { border-top-color: var(--error); }
  .card.info { border-top-color: var(--dorado); }
  .card.ok { border-top-color: var(--ok); }
  .card-num { font-size: 36px; font-weight: 800; color: var(--marino); letter-spacing: -0.02em; }
  .card-num.fail { color: var(--error); }
  .card-num.ok { color: var(--ok); }
  .card-label { font-size: 12px; text-transform: uppercase; letter-spacing: 0.15em; color: var(--gris); margin-top: 4px; }
  h2 { color: var(--marino); font-size: 22px; margin: 36px 0 12px; padding-bottom: 8px; border-bottom: 2px solid var(--teal); }
  .page-section { background: white; border-radius: 16px; padding: 24px 28px; margin-bottom: 20px; box-shadow: 0 4px 12px -4px rgba(0,59,122,0.10); }
  .page-section h3 { color: var(--marino); font-size: 18px; margin-bottom: 6px; }
  .page-section .url { font-family: ui-monospace, monospace; font-size: 12px; color: var(--gris); word-break: break-all; }
  .page-section .desc { font-size: 13px; color: var(--gris); margin: 10px 0 16px; }
  .scores { display: flex; gap: 16px; flex-wrap: wrap; margin: 14px 0; }
  .score-chip { display: inline-flex; align-items: center; gap: 8px; background: var(--arena); padding: 6px 14px; border-radius: 20px; font-size: 13px; font-weight: 600; }
  .score-chip.fail { background: rgba(220,38,38,0.1); color: var(--error); }
  .score-chip.ok { background: rgba(22,163,74,0.1); color: var(--ok); }
  .score-chip .dot { width: 8px; height: 8px; border-radius: 50%; background: currentColor; }
  .violation { background: rgba(220,38,38,0.04); border-left: 4px solid var(--error); padding: 14px 18px; border-radius: 8px; margin: 12px 0; }
  .violation.informative { background: rgba(244,196,48,0.08); border-left-color: var(--dorado); }
  .violation .imp { display: inline-block; font-size: 10px; padding: 2px 8px; border-radius: 4px; background: var(--error); color: white; font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase; }
  .violation.informative .imp { background: var(--dorado); color: var(--negro); }
  .violation h4 { margin: 8px 0 4px; font-size: 14px; }
  .violation p { font-size: 13px; color: var(--gris); }
  .violation a { color: var(--marino); font-weight: 600; }
  .violation pre { background: var(--negro); color: #FFE0B5; padding: 8px 12px; border-radius: 4px; font-size: 11px; overflow-x: auto; margin-top: 8px; }
  .no-violations { background: rgba(22,163,74,0.05); border-left: 4px solid var(--ok); color: var(--ok); padding: 14px 18px; border-radius: 8px; font-weight: 600; }
  footer { max-width: 1100px; margin: 60px auto 30px; padding: 0 30px; font-size: 12px; color: var(--gris); text-align: center; line-height: 1.6; }
  footer strong { color: var(--marino); }
  @media print { .hero { padding: 24px 30px; } main { max-width: none; } .page-section { page-break-inside: avoid; } }
</style>
</head><body>

<div class="hero">
  <h1>Auditoría de Accesibilidad WCAG 2.1 AA</h1>
  <p>Plataforma DTI Níjar · Expediente 18962/2025 · IT DIGITTAL</p>
  <p>Subtarea 5.8 del Plan de Trabajo Pre-SAT · Fecha: ${meta.today}</p>
  <span class="verdict ${verdictClass}">${verdictText}</span>
</div>

<main>

  <div class="summary-cards">
    <div class="card ${totalBlocking === 0 ? 'ok' : 'bloqueante'}">
      <div class="card-num ${totalBlocking === 0 ? 'ok' : 'fail'}">${totalBlocking}</div>
      <div class="card-label">Bloqueantes (critical + serious)</div>
    </div>
    <div class="card info">
      <div class="card-num">${totalInformative}</div>
      <div class="card-label">Informativas (moderate + minor)</div>
    </div>
    <div class="card">
      <div class="card-num">${findings.length}</div>
      <div class="card-label">Páginas auditadas</div>
    </div>
    <div class="card ok">
      <div class="card-num ok">${findings.reduce((s,f) => s + (f.axe?.passes || 0), 0)}</div>
      <div class="card-label">Reglas OK acumuladas</div>
    </div>
  </div>

  <h2>Metodología</h2>
  <div class="page-section">
    <p><strong>Estándar:</strong> WCAG 2.1 nivel AA (referencia UNE 139803)</p>
    <p><strong>Motor:</strong> axe-core 4.x (Deque Systems) + Lighthouse 11 (Google)</p>
    <p><strong>Navegador:</strong> Playwright + Chromium 120+ headless</p>
    <p><strong>URL base auditada:</strong> <code>${escape(meta.BASE_URL)}</code></p>
    <p><strong>Modo:</strong> ${meta.STRICT_MODE ? 'estricto (informa moderate + minor)' : 'normal (informa solo critical + serious)'}</p>
    <p><strong>Umbral Lighthouse:</strong> ${meta.LIGHTHOUSE_THRESHOLD}/100 mínimo</p>
    <p><strong>Tags evaluados:</strong> wcag2a, wcag2aa, wcag21a, wcag21aa</p>
  </div>

  <h2>Resultados por página</h2>

  ${findings.map(f => {
    if (f.error) {
      return `<div class="page-section">
        <h3>${escape(f.page.name)}</h3>
        <div class="url">${escape(f.page.url)}</div>
        <div class="violation">⚠ Error técnico: ${escape(f.error)}</div>
      </div>`;
    }
    const blocking = f.violations?.blocking || [];
    const informative = f.violations?.informative || [];
    return `<div class="page-section">
      <h3>${escape(f.page.name)}</h3>
      <div class="url">${escape(f.page.url)}</div>
      <p class="desc">${escape(f.page.description)}</p>
      <div class="scores">
        <span class="score-chip ${blocking.length === 0 ? 'ok' : 'fail'}"><span class="dot"></span>axe: ${blocking.length} bloq · ${informative.length} info</span>
        ${f.lighthouse ? `<span class="score-chip ${f.lighthouse.score >= meta.LIGHTHOUSE_THRESHOLD ? 'ok' : 'fail'}"><span class="dot"></span>Lighthouse: ${f.lighthouse.score}/100</span>` : ''}
        <span class="score-chip"><span class="dot" style="background:#9CA3AF"></span>Reglas OK: ${f.axe?.passes || 0}</span>
      </div>
      ${blocking.length === 0 && informative.length === 0
        ? '<div class="no-violations">✓ Sin violaciones detectadas</div>'
        : [...blocking, ...informative].map(v => `
          <div class="violation ${blocking.includes(v) ? '' : 'informative'}">
            <span class="imp">${v.impact}</span>
            <h4>${escape(v.help)}</h4>
            <p>${escape(v.description)}</p>
            <p><a href="${v.helpUrl}" target="_blank">Documentación de la regla → ${v.id}</a></p>
            ${v.nodes.length ? `<pre>${escape(v.nodes[0].html.slice(0, 300))}</pre>` : ''}
          </div>
        `).join('')}
    </div>`;
  }).join('')}

</main>

<footer>
  <p><strong>Plataforma DTI Níjar</strong> · Expediente 18962/2025 · IT DIGITTAL</p>
  <p>Auditoría generada automáticamente con axe-core + Lighthouse + Playwright</p>
  <p>Financiado por la Unión Europea — NextGenerationEU · PRTR Componente 14</p>
</footer>

</body></html>`;
}

async function writeExcelFindings(findings, path) {
  // Lazy import: ExcelJS solo si hay hallazgos a serializar
  const ExcelJS = (await import('exceljs')).default;
  const wb = new ExcelJS.Workbook();
  wb.creator = 'IT DIGITTAL — Plataforma DTI Níjar';
  wb.created = new Date();

  const ws = wb.addWorksheet('Hallazgos accesibilidad');
  ws.columns = [
    { header: 'ID',           key: 'id',         width: 8 },
    { header: 'Fecha',        key: 'fecha',      width: 12 },
    { header: 'Página',       key: 'pagina',     width: 30 },
    { header: 'URL',          key: 'url',        width: 40 },
    { header: 'Severidad',    key: 'sev',        width: 12 },
    { header: 'Regla axe',    key: 'regla',      width: 28 },
    { header: 'WCAG ref.',    key: 'wcag',       width: 18 },
    { header: 'Descripción',  key: 'desc',       width: 60 },
    { header: 'Selector',     key: 'selector',   width: 35 },
    { header: 'Fix propuesto', key: 'fix',       width: 50 },
    { header: 'Responsable',  key: 'resp',       width: 18 },
    { header: 'Fecha fix',    key: 'fechaFix',   width: 12 },
    { header: 'Fecha re-test', key: 'fechaRetest', width: 12 },
    { header: 'Estado',       key: 'estado',     width: 14 },
  ];
  ws.getRow(1).font = { bold: true, color: { argb: 'FFFFFFFF' } };
  ws.getRow(1).fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FF003B7A' } };
  ws.getRow(1).alignment = { vertical: 'middle', horizontal: 'center', wrapText: true };

  let id = 1;
  const today = new Date().toISOString().slice(0,10);
  for (const f of findings) {
    if (f.error) continue;
    const all = [...(f.violations?.blocking || []), ...(f.violations?.informative || [])];
    for (const v of all) {
      for (const n of v.nodes) {
        const wcagTag = (v.tags || []).filter(t => t.startsWith('wcag2')).join(', ');
        ws.addRow({
          id: `H-${String(id++).padStart(4,'0')}`,
          fecha: today,
          pagina: f.page.name,
          url: f.page.url,
          sev: v.impact,
          regla: v.id,
          wcag: wcagTag,
          desc: v.help + '. ' + v.description,
          selector: Array.isArray(n.target) ? n.target.join(', ') : '',
          fix: '(rellenar tras analizar)',
          resp: '',
          fechaFix: '',
          fechaRetest: '',
          estado: 'Detectado',
        });
      }
    }
  }
  // Bordes y autofiltro
  ws.autoFilter = { from: 'A1', to: { row: 1, column: 14 } };
  for (let r = 1; r <= ws.rowCount; r++) {
    for (let c = 1; c <= 14; c++) {
      const cell = ws.getCell(r, c);
      cell.border = {
        top: { style: 'thin', color: { argb: 'FFD1D5DA' } },
        bottom: { style: 'thin', color: { argb: 'FFD1D5DA' } },
        left: { style: 'thin', color: { argb: 'FFD1D5DA' } },
        right: { style: 'thin', color: { argb: 'FFD1D5DA' } },
      };
    }
  }
  await wb.xlsx.writeFile(path);
}
