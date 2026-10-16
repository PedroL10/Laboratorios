"""Monta a apresentacao HTML do LAB02 (slides autocontidos, com os graficos
embutidos em base64), seguindo o mesmo design usado em
LAB01/apresentacao/apresentacao_lab01.html.

Uso:
    python scripts/build_presentation.py

Le os PNGs de resultados/graficos/, embute cada um como data URI e escreve
apresentacao/apresentacao_lab02.html. Rode de novo sempre que os graficos
forem atualizados (ex.: apos os trials de P3).
"""

from __future__ import annotations

import base64
from pathlib import Path

LAB_ROOT = Path(__file__).resolve().parent.parent
GRAFICOS_DIR = LAB_ROOT / "resultados" / "graficos"
OUTPUT = LAB_ROOT / "apresentacao" / "apresentacao_lab02.html"


def img_data_uri(filename: str) -> str:
    data = (GRAFICOS_DIR / filename).read_bytes()
    return "data:image/png;base64," + base64.b64encode(data).decode("ascii")


CSS = """
:root {
  --paper: #F1F4F2; --paper-raised: #FFFFFF; --ink: #16232C; --ink-soft: #4A5A62;
  --line: #D7DEDB; --signal: #2E5266; --signal-soft: #E4EBEC;
  --confirm: #3F8A32; --confirm-soft: #E7F3E1;
  --warn: #B5651D; --warn-soft: #F5E6D8;
  --shadow: 0 1px 2px rgba(22,35,44,0.06), 0 8px 24px rgba(22,35,44,0.06);
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --paper: #101A20; --paper-raised: #17232A; --ink: #E8EEEC; --ink-soft: #9FB0B6;
    --line: #26343B; --signal: #8FB6C8; --signal-soft: #1C2C33;
    --confirm: #6CC24A; --confirm-soft: #1B2A18; --warn: #E0A45C; --warn-soft: #2E2417;
    --shadow: 0 1px 2px rgba(0,0,0,0.3), 0 8px 24px rgba(0,0,0,0.35);
  }
}
:root[data-theme="dark"] {
  --paper: #101A20; --paper-raised: #17232A; --ink: #E8EEEC; --ink-soft: #9FB0B6;
  --line: #26343B; --signal: #8FB6C8; --signal-soft: #1C2C33;
  --confirm: #6CC24A; --confirm-soft: #1B2A18; --warn: #E0A45C; --warn-soft: #2E2417;
  --shadow: 0 1px 2px rgba(0,0,0,0.3), 0 8px 24px rgba(0,0,0,0.35);
}
* { box-sizing: border-box; }
html, body {
  margin: 0; padding: 0; background: var(--paper); color: var(--ink);
  font-family: "IBM Plex Sans", system-ui, sans-serif; height: 100%; overflow: hidden;
}
.mono { font-family: "IBM Plex Mono", ui-monospace, monospace; }
#deck { position: relative; width: 100vw; height: 100vh; }
.progress { position: fixed; top: 0; left: 0; height: 3px; background: var(--signal); width: 0%; transition: width 300ms ease; z-index: 40; }
.slide { position: absolute; inset: 0; display: none; flex-direction: column; padding: clamp(24px, 4vw, 60px) clamp(32px, 6vw, 92px); opacity: 0; overflow-y: auto; }
.slide.active { display: flex; opacity: 1; }
.eyebrow { font-family: "IBM Plex Mono", monospace; font-size: 12.5px; letter-spacing: 0.11em; text-transform: uppercase; color: var(--signal); margin: 0 0 10px 0; }
h1 { font-size: clamp(28px, 3.8vw, 48px); line-height: 1.08; font-weight: 700; margin: 0 0 16px 0; text-wrap: balance; max-width: 24ch; }
h2 { font-size: clamp(22px, 2.6vw, 32px); font-weight: 600; margin: 0 0 8px 0; text-wrap: balance; }
p.lede { font-size: clamp(15px, 1.3vw, 18px); line-height: 1.55; color: var(--ink-soft); max-width: 72ch; margin: 0 0 6px 0; }
p.body-text { font-size: 14.5px; line-height: 1.6; color: var(--ink); max-width: 78ch; margin: 0 0 10px 0; }
p.body-text.soft { color: var(--ink-soft); }
p.body-text strong { color: var(--signal); font-weight: 600; }
.rule { height: 1px; background: var(--line); border: 0; margin: 16px 0; width: 100%; }
.title-slide { justify-content: center; }
.title-meta { margin-top: 24px; display: flex; gap: 26px; flex-wrap: wrap; font-family: "IBM Plex Mono", monospace; font-size: 13.5px; color: var(--ink-soft); }
.title-meta strong { color: var(--ink); font-weight: 500; }
.rq-grid { display: grid; grid-template-columns: repeat(1, 1fr); gap: 10px; margin-top: 18px; max-width: 900px; }
.rq-item { display: flex; gap: 12px; align-items: baseline; font-size: 15.5px; line-height: 1.4; }
.rq-tag { font-family: "IBM Plex Mono", monospace; font-size: 12.5px; color: var(--signal); font-weight: 600; flex-shrink: 0; width: 4.4ch; }
.rq-item .desc { color: var(--ink-soft); font-size: 13.5px; display: block; }
.method-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 14px 36px; margin-top: 16px; max-width: 1180px; }
.method-card { background: var(--paper-raised); border: 1px solid var(--line); border-radius: 4px; padding: 15px 18px; box-shadow: var(--shadow); }
.method-card .k { font-family: "IBM Plex Mono", monospace; font-size: 11.5px; color: var(--signal); text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 5px; display: block; }
.method-card p { margin: 0; font-size: 14px; line-height: 1.5; color: var(--ink); }
.rq-body { flex: 1; display: flex; flex-direction: column; min-height: 0; }
.rq-columns { flex: 1; display: grid; grid-template-columns: 1fr 1fr; gap: 30px; margin-top: 10px; min-height: 0; }
.rq-col { display: flex; flex-direction: column; min-height: 0; }
.rq-col .chart-wrap { flex: 1 1 auto; min-height: 0; max-height: 40vh; display: flex; align-items: center; justify-content: center; background: var(--paper-raised); border: 1px solid var(--line); border-radius: 4px; box-shadow: var(--shadow); padding: 8px; }
.rq-col img { max-width: 100%; max-height: 100%; object-fit: contain; }
.rq-question { font-size: 14px; font-weight: 600; margin: 10px 0 4px 0; }
.stat-row { display: flex; align-items: baseline; gap: 10px; margin: 2px 0 5px 0; }
.stat-num { font-family: "IBM Plex Mono", monospace; font-size: clamp(20px, 2vw, 26px); font-weight: 600; color: var(--signal); }
.stat-label { font-size: 12.5px; color: var(--ink-soft); }
.finding { font-size: 13px; line-height: 1.5; color: var(--ink-soft); margin: 0; }
.single-rq { flex: 1; display: flex; flex-direction: column; min-height: 0; margin-top: 8px; align-items: center; }
.single-rq .chart-wrap { flex: 1; width: 100%; max-width: 1100px; min-height: 0; display: flex; align-items: center; justify-content: center; background: var(--paper-raised); border: 1px solid var(--line); border-radius: 4px; box-shadow: var(--shadow); padding: 10px; }
.single-rq img { max-width: 100%; max-height: 100%; object-fit: contain; }
.compare-cards { display: flex; gap: 18px; justify-content: center; margin-top: 14px; flex-wrap: wrap; }
.compare-card { background: var(--paper-raised); border: 1px solid var(--line); border-left: 3px solid var(--signal); border-radius: 4px; padding: 14px 18px; box-shadow: var(--shadow); min-width: 200px; }
.compare-card.sem { border-left-color: var(--ink-soft); }
.compare-card .ck { font-family: "IBM Plex Mono", monospace; font-size: 11.5px; text-transform: uppercase; letter-spacing: 0.06em; color: var(--ink-soft); margin-bottom: 7px; display:block; }
.compare-card .stat-num { font-size: 22px; }
.stat-table { width: 100%; border-collapse: collapse; margin-top: 14px; }
.stat-table th, .stat-table td { text-align: left; padding: 8px 12px; border-bottom: 1px solid var(--line); font-size: 13px; }
.stat-table th { font-family: "IBM Plex Mono", monospace; font-size: 10.5px; text-transform: uppercase; letter-spacing: 0.06em; color: var(--ink-soft); font-weight: 500; }
.stat-table td.num { font-family: "IBM Plex Mono", monospace; font-variant-numeric: tabular-nums; }
.stat-table td.pval { font-family: "IBM Plex Mono", monospace; color: var(--ink-soft); font-weight: 600; font-variant-numeric: tabular-nums; }
.caveat-box { margin-top: 16px; background: var(--warn-soft); border-left: 3px solid var(--warn); border-radius: 4px; padding: 14px 18px; }
.caveat-box .k { font-family: "IBM Plex Mono", monospace; font-size: 11.5px; color: var(--warn); text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 6px; display: block; }
.caveat-box p { margin: 0; font-size: 13.5px; line-height: 1.5; color: var(--ink); }
.conclusion-list { display: flex; flex-direction: column; gap: 9px; margin-top: 12px; max-width: 78ch; padding-left: 0; list-style: none; }
.conclusion-list li { font-size: 14.5px; line-height: 1.5; padding-left: 20px; position: relative; }
.conclusion-list li::before { content: "\\2014"; position: absolute; left: 0; color: var(--signal); }
.closing-slide { justify-content: center; align-items: flex-start; }
footer.chrome { position: fixed; left: 0; right: 0; bottom: 0; height: 42px; display: flex; align-items: center; justify-content: space-between; padding: 0 clamp(20px, 4vw, 56px); font-family: "IBM Plex Mono", monospace; font-size: 12px; color: var(--ink-soft); z-index: 40; pointer-events: none; background: linear-gradient(to top, var(--paper) 60%, transparent); }
footer.chrome .count { pointer-events: auto; }
.nav-btns { display: flex; gap: 8px; pointer-events: auto; }
.nav-btns button { font-family: "IBM Plex Mono", monospace; font-size: 13px; background: var(--paper-raised); border: 1px solid var(--line); color: var(--ink); border-radius: 3px; padding: 5px 12px; cursor: pointer; }
.nav-btns button:hover { border-color: var(--signal); color: var(--signal); }
.nav-btns button:focus-visible, .notes-toggle:focus-visible { outline: 2px solid var(--signal); outline-offset: 2px; }
.notes-toggle { position: fixed; right: clamp(20px, 4vw, 56px); top: 14px; font-family: "IBM Plex Mono", monospace; font-size: 12px; background: var(--paper-raised); border: 1px solid var(--line); color: var(--ink-soft); border-radius: 3px; padding: 5px 10px; cursor: pointer; z-index: 50; }
.notes-toggle:hover { color: var(--signal); border-color: var(--signal); }
.notes-panel { position: fixed; left: 0; right: 0; bottom: 42px; max-height: 32vh; overflow-y: auto; background: var(--paper-raised); border-top: 1px solid var(--line); padding: 14px clamp(20px, 4vw, 56px); display: none; z-index: 45; box-shadow: 0 -8px 24px rgba(0,0,0,0.1); }
.notes-panel.show { display: block; }
.notes-panel .budget { font-family: "IBM Plex Mono", monospace; font-size: 11.5px; color: var(--confirm); margin-bottom: 6px; }
.notes-panel p { margin: 0; font-size: 13.5px; line-height: 1.6; color: var(--ink); max-width: 92ch; }
@media (prefers-reduced-motion: reduce) { .slide { transition: none; } .progress { transition: none; } }
"""

SCRIPT = """
const slides = document.querySelectorAll('.slide');
const total = slides.length;
let idx = 0;
const progress = document.getElementById('progress');
const count = document.getElementById('count');
const notesPanel = document.getElementById('notesPanel');
const notesToggle = document.getElementById('notesToggle');
let notesOn = false;
function pad(n) { return String(n).padStart(2, '0'); }
function render() {
  slides.forEach((s, i) => s.classList.toggle('active', i === idx));
  progress.style.width = ((idx + 1) / total * 100) + '%';
  count.textContent = pad(idx + 1) + ' / ' + pad(total);
  if (notesOn) renderNotes();
}
function renderNotes() {
  const s = slides[idx];
  const budget = s.dataset.budget || '';
  const note = s.dataset.note || '(sem nota para este slide)';
  notesPanel.innerHTML = '<div class="budget">TEMPO SUGERIDO: ' + budget + '</div><p>' + note + '</p>';
}
function next() { idx = Math.min(idx + 1, total - 1); render(); }
function prev() { idx = Math.max(idx - 1, 0); render(); }
document.getElementById('nextBtn').addEventListener('click', next);
document.getElementById('prevBtn').addEventListener('click', prev);
notesToggle.addEventListener('click', () => {
  notesOn = !notesOn;
  notesPanel.classList.toggle('show', notesOn);
  notesToggle.setAttribute('aria-pressed', String(notesOn));
  if (notesOn) renderNotes();
});
window.addEventListener('keydown', (e) => {
  if (e.key === 'ArrowRight' || e.key === ' ' || e.key === 'PageDown') { e.preventDefault(); next(); }
  else if (e.key === 'ArrowLeft' || e.key === 'PageUp') { e.preventDefault(); prev(); }
  else if (e.key.toLowerCase() === 'n') { notesToggle.click(); }
});
render();
"""


def slide(inner: str, *, classes: str = "", budget: str = "", note: str = "") -> str:
    cls = ("slide " + classes).strip()
    note = note.replace('"', "&quot;")
    return f'<section class="{cls}" data-budget="{budget}" data-note="{note}">\n{inner}\n</section>\n'


def build_slides() -> str:
    parts = []

    parts.append(slide(
        classes="title-slide active",
        budget="~15s",
        note="Boa tarde. Vamos apresentar o Lab02: um experimento controlado comparando o uso de assistente de IA "
             "generativa contra codificacao manual, resolvendo os mesmos katas sob tempo limitado, com desenho "
             "crossover within-subject.",
        inner="""
    <p class="eyebrow">Laboratorio de Experimentacao de Software &mdash; Lab02</p>
    <h1>Assistentes de IA vs. codificacao manual: um experimento controlado</h1>
    <p class="lede">O que muda quando um assistente de IA entra na resolucao de katas de programacao, sob tempo limitado e protocolo controlado.</p>
    <div class="title-meta">
      <span><strong>Grupo</strong> Pedro Luis &middot; Enrico Bessa &middot; Pericles Pires</span>
      <span><strong>Desenho</strong> crossover within-subject &middot; 4 katas</span>
      <span><strong>Repositorio</strong> github.com/PedroL10/Lab01Exp</span>
    </div>
"""))

    parts.append(slide(
        budget="~40s",
        note="Ferramentas de IA generativa como Copilot, ChatGPT, Claude e Gemini viraram onipresentes no "
             "desenvolvimento, mas a maior parte do que se ouve sobre produtividade e qualidade e relato anedotico. "
             "Formulamos tres questoes de pesquisa: RQ1 tempo, RQ2 defeitos, RQ3 estrutura do codigo produzido.",
        inner="""
    <p class="eyebrow">Contexto</p>
    <h2>Pouca evidencia controlada sobre o real impacto da IA generativa</h2>
    <p class="body-text soft">Ferramentas de IA generativa tornaram-se onipresentes no desenvolvimento de software, mas
    ainda ha pouca evidencia controlada e reproduzivel sobre seu efeito em produtividade e qualidade. Este experimento
    compara, para os mesmos participantes e os mesmos katas, o tratamento com IA habilitada contra o tratamento manual.</p>
    <div class="rq-grid">
      <div class="rq-item"><span class="rq-tag mono">RQ1</span><span>IA reduz o tempo de resolucao?<span class="desc">time-to-green, em segundos</span></span></div>
      <div class="rq-item"><span class="rq-tag mono">RQ2</span><span>IA reduz a quantidade de defeitos?<span class="desc">testes de aceitacao passando/falhando</span></span></div>
      <div class="rq-item"><span class="rq-tag mono">RQ3</span><span>IA altera a estrutura do codigo?<span class="desc">LOC, complexidade ciclomatica, duplicacao</span></span></div>
    </div>
"""))

    parts.append(slide(
        budget="~40s",
        note="Desenho crossover within-subject: cada participante resolve os quatro katas, dois com IA e dois sem, "
             "em ordem contrabalanceada, para que cada pessoa sirva como seu proprio controle. Time-box fixo de 35 "
             "minutos por trial, encerrado ao passar todos os testes ou ao estourar o tempo (trial censurado).",
        inner="""
    <p class="eyebrow">Desenho do experimento</p>
    <h2>Crossover within-subject, contrabalanceado</h2>
    <p class="body-text soft">Cada participante resolve os quatro katas: dois no tratamento IA e dois no tratamento MANUAL,
    em ordem contrabalanceada, controlando a variacao individual de habilidade. Time-box fixo de 35 minutos (2100s) por
    trial &mdash; ao estourar sem sucesso, o trial e registrado como censurado, nao descartado.</p>
    <table class="stat-table">
      <thead><tr><th>Participante</th><th>K1</th><th>K2</th><th>K3</th><th>K4</th></tr></thead>
      <tbody>
        <tr><td>P1 &mdash; Pedro</td><td class="num">IA</td><td class="num">IA</td><td class="num">MANUAL</td><td class="num">MANUAL</td></tr>
        <tr><td>P2 &mdash; Enrico</td><td class="num">MANUAL</td><td class="num">MANUAL</td><td class="num">IA</td><td class="num">IA</td></tr>
        <tr><td>P3 &mdash; Pericles</td><td class="num">IA</td><td class="num">MANUAL</td><td class="num">IA</td><td class="num">MANUAL</td></tr>
      </tbody>
    </table>
    <p class="finding" style="margin-top:10px;">Planejados 12 trials (6 IA / 6 MANUAL). Nesta apresentacao, 8 trials
    concluidos ate o momento &mdash; ver aviso de dados parciais no slide de discussao.</p>
"""))

    parts.append(slide(
        budget="~35s",
        note="Os quatro katas sao autorais, para reduzir o risco de a IA reproduzir uma solucao ja memorizada de "
             "exercicios muito conhecidos. K1 e K2 sao faceis, K3 e K4 sao medios, todos com dez ou onze testes de "
             "aceitacao automatizados.",
        inner="""
    <p class="eyebrow">Objetos experimentais</p>
    <h2>Quatro katas autorais, dificuldade comparavel</h2>
    <div class="method-grid">
      <div class="method-card"><span class="k">K1 &middot; Facil &middot; 10 testes</span><p><strong>Resumo de leituras.</strong> Dada uma lista de leituras de sensor e um limite minimo, retorna contagem, media e maximo. Usa listas, media e arredondamento.</p></div>
      <div class="method-card"><span class="k">K2 &middot; Facil &middot; 11 testes</span><p><strong>Validador de etiquetas.</strong> Valida se tags no estilo [nome]...[/nome] estao corretamente aninhadas. Usa strings e uma pilha.</p></div>
      <div class="method-card"><span class="k">K3 &middot; Medio &middot; 10 testes</span><p><strong>Janela de entregas.</strong> Agrupa entregas por zona e calcula o numero maximo de janelas simultaneas necessarias. Usa ordenacao e intervalos.</p></div>
      <div class="method-card"><span class="k">K4 &middot; Medio &middot; 10 testes</span><p><strong>Pontuacao de campeonato.</strong> Gera a classificacao de um campeonato a partir dos resultados das partidas, com desempates em cascata. Usa dicionarios e ordenacao composta.</p></div>
    </div>
"""))

    parts.append(slide(
        budget="~35s",
        note="Ambiente controlado: Python 3, pytest para os testes de aceitacao, Radon para LOC e complexidade, "
             "JSCPD para duplicacao. Cada trial registra tempo, resultado dos testes e, para o tratamento IA, o "
             "assistente usado e o numero de interacoes.",
        inner="""
    <p class="eyebrow">Preparacao</p>
    <h2>Ambiente controlado e dados registrados por trial</h2>
    <div class="method-grid">
      <div class="method-card"><span class="k">Ferramentas</span><p>Python 3.11/3.12, pytest 8.4.2 (testes de aceitacao), Radon 6.0.1 (LOC e complexidade ciclomatica), JSCPD 5.2.0 (duplicacao de codigo).</p></div>
      <div class="method-card"><span class="k">Assistentes de IA usados</span><p>ChatGPT e Claude Sonnet 5, conforme o participante &mdash; registrados por trial junto com a quantidade de interacoes.</p></div>
      <div class="method-card"><span class="k">Scripts proprios</span><p><code>run_trial.py</code> cronometra o trial e roda o pytest sob demanda; <code>collect_static_metrics.py</code> roda Radon e JSCPD sobre a solucao final.</p></div>
      <div class="method-card"><span class="k">Registro por trial</span><p>Participante, kata, tratamento, ordem, inicio/fim, time-to-green, testes passando/falhando, LOC, complexidade, duplicacao.</p></div>
    </div>
"""))

    parts.append(slide(
        budget="~45s",
        note="Aqui estao os oito trials concluidos ate agora. Reparem nos dois trials do Enrico em IA com tempo "
             "muito baixo -- quatro e quarenta e oito segundos -- porque ele preparou a solucao numa consulta ao "
             "assistente antes de iniciar o cronometro oficialmente. Vale mencionar isso com transparencia.",
        inner="""
    <p class="eyebrow">Dados coletados</p>
    <h2>Os oito trials concluidos ate o momento</h2>
    <table class="stat-table">
      <thead><tr><th>Participante</th><th>Kata</th><th>Tratamento</th><th>Tempo (s)</th><th>Testes</th><th>LOC</th><th>Complex. media</th></tr></thead>
      <tbody>
        <tr><td>P2</td><td>K3</td><td class="num">IA</td><td class="num">4</td><td class="num">10/10</td><td class="num">25</td><td class="num">8,0</td></tr>
        <tr><td>P2</td><td>K1</td><td class="num">MANUAL</td><td class="num">360</td><td class="num">10/10</td><td class="num">12</td><td class="num">5,0</td></tr>
        <tr><td>P2</td><td>K4</td><td class="num">IA</td><td class="num">48</td><td class="num">10/10</td><td class="num">46</td><td class="num">7,0</td></tr>
        <tr><td>P2</td><td>K2</td><td class="num">MANUAL</td><td class="num">4</td><td class="num">11/11</td><td class="num">41</td><td class="num">14,0</td></tr>
        <tr><td>P1</td><td>K1</td><td class="num">IA</td><td class="num">345</td><td class="num">10/10</td><td class="num">21</td><td class="num">5,0</td></tr>
        <tr><td>P1</td><td>K3</td><td class="num">MANUAL</td><td class="num">950</td><td class="num">10/10</td><td class="num">38</td><td class="num">10,0</td></tr>
        <tr><td>P1</td><td>K2</td><td class="num">IA</td><td class="num">337</td><td class="num">11/11</td><td class="num">51</td><td class="num">17,0</td></tr>
        <tr><td>P1</td><td>K4</td><td class="num">MANUAL</td><td class="num">1158</td><td class="num">10/10</td><td class="num">75</td><td class="num">14,0</td></tr>
      </tbody>
    </table>
"""))

    parts.append(slide(
        budget="~55s",
        note="RQ1: o boxplot mostra mediana e IQR, nao media, porque o N e pequeno. Mediana de 192 segundos com IA "
             "contra 655 segundos no manual. O grafico pareado por kata mostra a mesma comparacao usada no teste de "
             "Wilcoxon: K3 e K4, os katas medios, sobem bastante de IA para manual; K1 e K2 quase nao mudam. Com "
             "apenas quatro pares o Wilcoxon deu p igual a 0,375, entao a diferenca visual nao e estatisticamente "
             "confirmada ainda.",
        inner="""
    <p class="eyebrow">Resultados</p>
    <h2>RQ1 &mdash; Tempo ate passar nos testes</h2>
    <div class="rq-body"><div class="rq-columns">
      <div class="rq-col">
        <div class="chart-wrap"><img src="{img:rq1_tempo.png}" alt="Boxplot do tempo por tratamento" /></div>
        <p class="rq-question">Distribuicao do tempo por tratamento</p>
        <div class="stat-row"><span class="stat-num mono">192,5s</span><span class="stat-label">mediana IA (IQR 302s)</span></div>
        <div class="stat-row"><span class="stat-num mono">655s</span><span class="stat-label">mediana MANUAL (IQR 731s)</span></div>
        <p class="finding">Boxplot com mediana/IQR (nao media) e pontos individuais, dado o N pequeno.</p>
      </div>
      <div class="rq-col">
        <div class="chart-wrap"><img src="{img:rq1_tempo_pareado_por_kata.png}" alt="Grafico pareado do tempo por kata" /></div>
        <p class="rq-question">Mesmo kata, IA vs. MANUAL</p>
        <div class="stat-row"><span class="stat-num mono">p = 0,375</span><span class="stat-label">Wilcoxon pareado, n=4 katas</span></div>
        <p class="finding">K3 e K4 (katas medios) sobem bastante no manual; K1 e K2 (faceis) quase nao mudam &mdash; nao significativo com N=4.</p>
      </div>
    </div></div>
"""))

    parts.append(slide(
        budget="~35s",
        note="RQ2: nos oito trials ate agora, cem por cento de sucesso nos dois tratamentos, nenhum trial censurado "
             "e nenhum teste falhando ao final do tempo. Isso nao significa que IA e manual sao iguais em defeitos "
             "-- significa que essa amostra ainda nao teve nenhuma falha para comparar.",
        inner="""
    <p class="eyebrow">Resultados</p>
    <h2>RQ2 &mdash; Defeitos ao final do time-box</h2>
    <div class="single-rq">
      <div class="chart-wrap"><img src="{img:rq2_taxa_sucesso.png}" alt="Boxplot da taxa de sucesso por tratamento" /></div>
      <div class="compare-cards">
        <div class="compare-card"><span class="ck">IA</span><span class="stat-num mono">100%</span></div>
        <div class="compare-card sem"><span class="ck">MANUAL</span><span class="stat-num mono">100%</span></div>
        <div class="compare-card"><span class="ck">Wilcoxon</span><span class="stat-num mono">p = 1,0</span></div>
      </div>
    </div>
    <p class="finding" style="margin-top:10px;">Todos os 8 trials passaram em 100% dos testes, sem censura. Sem
    variacao na amostra, o teste nao encontra diferenca &mdash; nao e evidencia de que os tratamentos sejam iguais.</p>
"""))

    parts.append(slide(
        budget="~45s",
        note="RQ3, primeira metade: LOC sem diferenca clara entre tratamentos. Complexidade normalizada por LOC, "
             "para nao confundir 'mais codigo' com 'mais complexo': mediana um pouco menor com IA. Ha um outlier "
             "sinalizado, o kata 2 do Pedro em IA, com complexidade 17 -- a logica de pilha e validacao gerou mais "
             "ramificacoes que o esperado.",
        inner="""
    <p class="eyebrow">Resultados</p>
    <h2>RQ3 &mdash; LOC e complexidade ciclomatica</h2>
    <div class="rq-body"><div class="rq-columns">
      <div class="rq-col">
        <div class="chart-wrap"><img src="{img:rq3_loc.png}" alt="Boxplot de LOC por tratamento" /></div>
        <p class="rq-question">Linhas de codigo (LOC)</p>
        <div class="stat-row"><span class="stat-num mono">p = 0,625</span><span class="stat-label">Wilcoxon pareado, n=4</span></div>
        <p class="finding">Mediana IA=35,5 vs. MANUAL=39,5 &mdash; sem diferenca clara.</p>
      </div>
      <div class="rq-col">
        <div class="chart-wrap"><img src="{img:rq3_complexidade_por_loc.png}" alt="Boxplot de complexidade por LOC" /></div>
        <p class="rq-question">Complexidade normalizada por LOC</p>
        <div class="stat-row"><span class="stat-num mono">p = 0,625</span><span class="stat-label">Wilcoxon pareado, n=4</span></div>
        <p class="finding">Mediana IA=0,279 vs. MANUAL=0,302. Outlier sinalizado: P1/K2/IA, complexidade media 17.</p>
      </div>
    </div></div>
"""))

    parts.append(slide(
        budget="~35s",
        note="RQ3, segunda metade: duplicacao de codigo zerada nos dois tratamentos, em todos os oito trials -- "
             "esperado, dado que sao solucoes curtas e independentes. O grafico pareado por kata mostra a mesma "
             "comparacao usada no Wilcoxon.",
        inner="""
    <p class="eyebrow">Resultados</p>
    <h2>RQ3 &mdash; Duplicacao de codigo</h2>
    <div class="rq-body"><div class="rq-columns">
      <div class="rq-col">
        <div class="chart-wrap"><img src="{img:rq3_duplicacao.png}" alt="Boxplot de duplicacao por tratamento" /></div>
        <p class="rq-question">% de linhas duplicadas</p>
        <div class="stat-row"><span class="stat-num mono">p = 1,0</span><span class="stat-label">Wilcoxon pareado, n=4</span></div>
        <p class="finding">0% de duplicacao em todos os 8 trials, nos dois tratamentos.</p>
      </div>
      <div class="rq-col">
        <div class="chart-wrap"><img src="{img:rq3_complexidade_pareada_por_kata.png}" alt="Grafico pareado de complexidade por LOC por kata" /></div>
        <p class="rq-question">Complexidade/LOC pareada por kata</p>
        <p class="finding">Mesma logica de pareamento do teste de Wilcoxon, aplicada a RQ3.</p>
      </div>
    </div></div>
"""))

    parts.append(slide(
        budget="~25s",
        note="Visao consolidada das seis metricas num unico dashboard, gerado automaticamente pelo script "
             "build_dashboard.py a partir dos CSVs de dados_trials e metricas_estaticas.",
        inner="""
    <p class="eyebrow">Dashboard</p>
    <h2>Visao consolidada IA vs. MANUAL</h2>
    <div class="single-rq">
      <div class="chart-wrap"><img src="{img:dashboard_consolidado.png}" alt="Dashboard consolidado com as seis metricas" /></div>
    </div>
"""))

    parts.append(slide(
        budget="~40s",
        note="Resumo: nenhuma das tres RQs teve diferenca estatisticamente significativa, todos os p-valores acima "
             "de 0,05. Mas o dado mais importante deste slide e o aviso: esta apresentacao usa 8 dos 12 trials "
             "planejados, os outros 4 ainda estao em execucao. Decidimos seguir em frente com o que temos, "
             "documentando isso com transparencia.",
        inner="""
    <p class="eyebrow">Discussao</p>
    <h2>Nenhuma diferenca estatisticamente significativa &mdash; ainda</h2>
    <table class="stat-table">
      <thead><tr><th>RQ</th><th>Metrica</th><th>Mediana IA</th><th>Mediana MANUAL</th><th>p-valor (Wilcoxon, n=4)</th></tr></thead>
      <tbody>
        <tr><td>RQ1</td><td>Tempo (time-to-green)</td><td class="num">192,5s</td><td class="num">655s</td><td class="pval">0,375</td></tr>
        <tr><td>RQ2</td><td>Taxa de sucesso</td><td class="num">100%</td><td class="num">100%</td><td class="pval">1,000</td></tr>
        <tr><td>RQ3</td><td>LOC</td><td class="num">35,5</td><td class="num">39,5</td><td class="pval">0,625</td></tr>
        <tr><td>RQ3</td><td>Complexidade/LOC</td><td class="num">0,279</td><td class="num">0,302</td><td class="pval">0,625</td></tr>
        <tr><td>RQ3</td><td>Duplicacao</td><td class="num">0%</td><td class="num">0%</td><td class="pval">1,000</td></tr>
      </tbody>
    </table>
    <div class="caveat-box">
      <span class="k">Dados parciais</span>
      <p>Esta analise usa 8 dos 12 trials planejados (4 trials ainda em execucao). Com N=4 pares, o teste de
      Wilcoxon ja tem pouco poder estatistico mesmo completo &mdash; as tendencias descritivas (IA mais rapido,
      especialmente em katas medios) nao devem ser lidas como confirmadas.</p>
    </div>
"""))

    parts.append(slide(
        budget="~35s",
        note="Limitacoes e ameacas a validade: amostra pequena, dados parciais, e um detalhe metodologico "
             "importante -- alguns trials em IA do Enrico tiveram tempo muito baixo porque a solucao foi obtida "
             "numa consulta ao assistente antes do cronometro comecar, o que pode nao refletir o uso real da IA "
             "durante a resolucao.",
        inner="""
    <p class="eyebrow">Limitacoes</p>
    <h2>O que ainda pode mudar essa leitura</h2>
    <ul class="conclusion-list">
      <li>Dataset parcial: 8 de 12 trials planejados &mdash; os numeros mudam quando os 4 trials restantes forem concluidos.</li>
      <li>N pequeno mesmo com o desenho completo (4 katas para pareamento) &mdash; poder estatistico limitado por desenho, nao so por atraso.</li>
      <li>Dois trials em IA tiveram tempo muito curto porque a solucao foi obtida antes do cronometro iniciar &mdash; pode nao refletir o uso real da IA durante a resolucao.</li>
      <li>Ameacas ja mapeadas no desenho: efeito de aprendizado entre katas, familiaridade previa com a IA, e vazamento de solucao entre participantes.</li>
    </ul>
"""))

    parts.append(slide(
        classes="closing-slide",
        budget="~10s",
        note="Obrigado. Ficamos a disposicao para perguntas.",
        inner="""
    <p class="eyebrow">Obrigado</p>
    <h1>Perguntas?</h1>
    <div class="title-meta">
      <span><strong>Repositorio</strong> github.com/PedroL10/Lab01Exp</span>
      <span><strong>Grupo</strong> Pedro Luis &middot; Enrico Bessa &middot; Pericles Pires</span>
    </div>
"""))

    return "".join(parts)


def main() -> None:
    images = [
        "rq1_tempo.png",
        "rq1_tempo_pareado_por_kata.png",
        "rq2_taxa_sucesso.png",
        "rq3_loc.png",
        "rq3_complexidade_por_loc.png",
        "rq3_duplicacao.png",
        "rq3_complexidade_pareada_por_kata.png",
        "dashboard_consolidado.png",
    ]
    data_uris = {name: img_data_uri(name) for name in images}

    slides_html = build_slides()
    for name, uri in data_uris.items():
        slides_html = slides_html.replace("{img:" + name + "}", uri)

    total_slides = slides_html.count('<section class="slide')

    html = f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8" />
<title>LAB02 &mdash; IA vs. codificacao manual</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap">
<style>{CSS}</style>
</head>
<body>

<div class="progress" id="progress"></div>
<button class="notes-toggle" id="notesToggle" aria-pressed="false">notas [N]</button>

<div id="deck">
{slides_html}</div>

<div class="notes-panel" id="notesPanel"></div>

<footer class="chrome">
  <span class="count mono" id="count">01 / {total_slides:02d}</span>
  <div class="nav-btns">
    <button id="prevBtn" aria-label="Slide anterior">&larr;</button>
    <button id="nextBtn" aria-label="Proximo slide">&rarr;</button>
  </div>
</footer>

<script>{SCRIPT}</script>
</body>
</html>
"""

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(html, encoding="utf-8")
    print(f"Apresentacao gerada em {OUTPUT} ({len(html) / 1024:.0f} KB, {total_slides} slides)")


if __name__ == "__main__":
    main()
