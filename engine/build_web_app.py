import os
import json
from engine.data_ingestion import MassiveDataCollector


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no" />
  <title>CareerPulse // Motor Estatístico de Carreiras</title>
  <script src="https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js"></script>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;700&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg-base: #07090e;
      --bg-card: rgba(15, 20, 30, 0.78);
      --border-color: rgba(255, 255, 255, 0.08);
      --text-main: #f3f4f6;
      --text-muted: #9ca3af;
      --accent-color: #00f5d4;
      --accent-glow: rgba(0, 245, 212, 0.22);
      --gold-glow: #ffd166;
      --danger-glow: #ef476f;
    }

    * { box-sizing: border-box; margin: 0; padding: 0; -webkit-tap-highlight-color: transparent; }

    body {
      background-color: var(--bg-base);
      background-image:
        radial-gradient(circle at 15% 15%, var(--accent-glow), transparent 38%),
        radial-gradient(circle at 85% 80%, rgba(59, 130, 246, 0.10), transparent 40%);
      color: var(--text-main);
      font-family: 'Inter', -apple-system, sans-serif;
      min-height: 100vh;
      overflow-x: hidden;
      transition: background-image 0.45s ease;
    }

    .container {
      max-width: 1400px;
      margin: 0 auto;
      padding: 20px 24px 40px;
    }

    /* TOP HEADER & PLAYER SELECTOR */
    .topbar {
      display: flex;
      flex-wrap: wrap;
      justify-content: space-between;
      align-items: center;
      gap: 16px;
      padding-bottom: 18px;
      border-bottom: 1px solid var(--border-color);
      margin-bottom: 20px;
    }

    .brand {
      display: flex;
      align-items: center;
      gap: 12px;
    }

    .brand-pulse {
      width: 12px;
      height: 12px;
      border-radius: 50%;
      background: var(--accent-color);
      box-shadow: 0 0 16px var(--accent-color);
      transition: all 0.3s ease;
    }

    .brand h1 {
      font-size: 1.25rem;
      font-weight: 800;
      letter-spacing: -0.03em;
      background: linear-gradient(90deg, #fff, #9ca3af);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }

    .brand span {
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.75rem;
      color: var(--accent-color);
      padding: 2px 8px;
      border-radius: 999px;
      border: 1px solid var(--border-color);
      background: rgba(255,255,255,0.03);
    }

    .controls {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      align-items: center;
    }

    .player-btn {
      background: var(--bg-card);
      color: var(--text-muted);
      border: 1px solid var(--border-color);
      padding: 8px 16px;
      border-radius: 10px;
      font-weight: 600;
      font-size: 0.85rem;
      cursor: pointer;
      transition: all 0.25s ease;
    }

    .player-btn:hover, .player-btn.active {
      color: #fff;
      border-color: var(--accent-color);
      box-shadow: 0 0 18px var(--accent-glow);
      background: rgba(255, 255, 255, 0.06);
    }

    .toggle-btn {
      background: rgba(255,255,255,0.04);
      color: var(--text-main);
      border: 1px dashed rgba(255,255,255,0.2);
      padding: 8px 14px;
      border-radius: 10px;
      font-size: 0.8rem;
      cursor: pointer;
      font-family: 'JetBrains Mono', monospace;
      transition: all 0.2s;
    }

    .toggle-btn.active {
      border-color: #a855f7;
      color: #e9d5ff;
      background: rgba(168, 85, 247, 0.15);
    }

    /* LIVE REACTIVE HUD */
    .hud-grid {
      display: grid;
      grid-template-columns: 1.3fr 2fr 1.1fr;
      gap: 16px;
      margin-bottom: 20px;
    }

    @media (max-width: 1024px) {
      .hud-grid { grid-template-columns: 1fr; }
    }

    .card {
      background: var(--bg-card);
      backdrop-filter: blur(16px);
      border: 1px solid var(--border-color);
      border-radius: 16px;
      padding: 18px 20px;
      position: relative;
      overflow: hidden;
      transition: border-color 0.35s ease, box-shadow 0.35s ease;
    }

    .card.reactive-border {
      border-color: var(--accent-color);
      box-shadow: 0 8px 32px -12px var(--accent-glow);
    }

    .player-title {
      font-size: 1.45rem;
      font-weight: 800;
      margin-bottom: 4px;
    }

    .player-sub {
      font-size: 0.82rem;
      color: var(--text-muted);
      margin-bottom: 14px;
    }

    .phase-badge {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 6px 12px;
      border-radius: 8px;
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.78rem;
      font-weight: 700;
      letter-spacing: 0.04em;
      text-transform: uppercase;
      background: rgba(255,255,255,0.06);
      color: var(--accent-color);
      border: 1px solid var(--accent-color);
      transition: all 0.25s ease;
    }

    .metrics-row {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 12px;
      height: 100%;
      align-items: center;
    }

    @media (max-width: 640px) {
      .metrics-row { grid-template-columns: repeat(2, 1fr); }
    }

    .metric-box {
      background: rgba(255,255,255,0.025);
      border: 1px solid rgba(255,255,255,0.05);
      padding: 12px;
      border-radius: 12px;
    }

    .metric-label {
      font-size: 0.72rem;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.05em;
      margin-bottom: 4px;
    }

    .metric-val {
      font-family: 'JetBrains Mono', monospace;
      font-size: 1.4rem;
      font-weight: 800;
      color: var(--text-main);
    }

    .metric-sub {
      font-size: 0.72rem;
      color: var(--text-muted);
      margin-top: 2px;
    }

    /* MAIN CHART CANVAS */
    .chart-card {
      background: var(--bg-card);
      backdrop-filter: blur(16px);
      border: 1px solid var(--border-color);
      border-radius: 18px;
      padding: 16px;
      position: relative;
    }

    #career-chart {
      width: 100%;
      height: 520px;
      touch-action: pan-y;
    }

    #radar-chart {
      width: 100%;
      height: 170px;
    }

    .event-banner {
      margin-top: 12px;
      padding: 10px 14px;
      border-radius: 10px;
      font-size: 0.85rem;
      font-weight: 600;
      display: flex;
      align-items: center;
      justify-content: space-between;
      background: rgba(255,255,255,0.03);
      border-left: 4px solid var(--accent-color);
      transition: all 0.25s ease;
    }

    .legend-bar {
      display: flex;
      flex-wrap: wrap;
      gap: 16px;
      margin-top: 14px;
      padding-top: 12px;
      border-top: 1px solid var(--border-color);
      font-size: 0.78rem;
      color: var(--text-muted);
    }

    .legend-item {
      display: flex;
      align-items: center;
      gap: 6px;
    }

    .dot {
      width: 10px;
      height: 10px;
      border-radius: 50%;
    }
  </style>
</head>
<body>
  <div class="container">
    <header class="topbar">
      <div class="brand">
        <div class="brand-pulse" id="brand-pulse"></div>
        <h1>CAREERPULSE</h1>
        <span>KALMAN-RTS + BAYES PAdj v1.0</span>
      </div>
      <div class="controls">
        <div id="player-buttons" style="display:flex; gap:8px; flex-wrap:wrap;"></div>
        <button id="toggle-counterfactual" class="toggle-btn active" onclick="toggleCounterfactual()">
          👻 Linha Contrafactual ("E se não lesionasse?")
        </button>
      </div>
    </header>

    <!-- REACTIVE HUD -->
    <section class="hud-grid">
      <div class="card reactive-border" id="identity-card">
        <div class="player-title" id="hud-name">Carregando...</div>
        <div class="player-sub" id="hud-meta">—</div>
        <div class="phase-badge" id="hud-phase">⚡ SELECIONE OU PASSE O MOUSE/DEDO</div>
        <div class="event-banner" id="hud-banner">
          <span id="hud-event-text">Deslize pelo gráfico para inspecionar cada momento da carreira.</span>
        </div>
      </div>

      <div class="card">
        <div class="metrics-row">
          <div class="metric-box">
            <div class="metric-label">Índice Técnico (RTS)</div>
            <div class="metric-val" id="hud-score">--</div>
            <div class="metric-sub" id="hud-ci">IC 95%: --</div>
          </div>
          <div class="metric-box">
            <div class="metric-label">Glória & Decisão</div>
            <div class="metric-val" id="hud-glory">--</div>
            <div class="metric-sub" id="hud-club">Clube: --</div>
          </div>
          <div class="metric-box">
            <div class="metric-label">Impacto no Jogo</div>
            <div class="metric-val" id="hud-g-xag">--</div>
            <div class="metric-sub" id="hud-prog">Prog: --</div>
          </div>
          <div class="metric-box">
            <div class="metric-label">Perda p/ Lesões</div>
            <div class="metric-val" id="hud-loss">--</div>
            <div class="metric-sub" id="hud-age">Idade: --</div>
          </div>
        </div>
      </div>

      <div class="card" style="padding: 10px;">
        <div id="radar-chart"></div>
      </div>
    </section>

    <!-- MAIN INTERACTIVE CHART -->
    <main class="chart-card">
      <div id="career-chart"></div>
      <div class="legend-bar">
        <div class="legend-item"><span class="dot" style="background:#ffd166; box-shadow:0 0 8px #ffd166;"></span> <b>God Mode / Glória (>85)</b>: Auge Técnico & Decisão</div>
        <div class="legend-item"><span class="dot" style="background:#00f5d4;"></span> <b>Prime (68–85)</b>: Alta Performance Sustentada</div>
        <div class="legend-item"><span class="dot" style="background:#3b82f6;"></span> <b>Regular (50–68)</b>: Titular Consistente</div>
        <div class="legend-item"><span class="dot" style="background:#ef476f;"></span> <b>Baixa / Vale de Lesão (<50)</b>: Queda Física ou Técnica</div>
        <div class="legend-item"><span class="dot" style="background:#a855f7;"></span> <b>Curva Fantasma Tracejada</b>: Projeção Contrafactual sem Lesões Graves</div>
      </div>
    </main>
  </div>

  <script>
    const BUNDLE_DATA = __INJECT_BUNDLE_JSON__;
    let currentPlayer = BUNDLE_DATA.players[0];
    let showCounterfactual = true;

    const mainChart = echarts.init(document.getElementById('career-chart'));
    const radarChart = echarts.init(document.getElementById('radar-chart'));

    const PHASE_THEMES = {
      GOD_MODE: {
        color: '#ffd166',
        glow: 'rgba(255, 209, 102, 0.28)',
        label: '👑 AUGE / ILUMINADO (GOD MODE)'
      },
      PRIME: {
        color: '#00f5d4',
        glow: 'rgba(0, 245, 212, 0.22)',
        label: '🔥 FASE PRIME (ALTO NÍVEL)'
      },
      REGULAR: {
        color: '#3b82f6',
        glow: 'rgba(59, 130, 246, 0.20)',
        label: '⚡ REGULAR / ESTÁVEL'
      },
      SLUMP: {
        color: '#f97316',
        glow: 'rgba(249, 115, 22, 0.20)',
        label: '📉 OSCILAÇÃO / BAIXA TÉCNICA'
      },
      INJURY_VALLEY: {
        color: '#ef476f',
        glow: 'rgba(239, 71, 111, 0.28)',
        label: '✚ VALE DE LESÃO / INATIVIDADE'
      }
    };

    function renderPlayerButtons() {
      const container = document.getElementById('player-buttons');
      container.innerHTML = '';
      BUNDLE_DATA.players.forEach(p => {
        const btn = document.createElement('button');
        btn.className = 'player-btn' + (p.id === currentPlayer.id ? ' active' : '');
        btn.textContent = p.name;
        btn.onclick = () => {
          currentPlayer = p;
          renderPlayerButtons();
          renderCharts();
          // Atualiza HUD com o ponto de auge do jogador ao carregar
          const peakIdx = currentPlayer.timeline.reduce((best, cur, i, arr) => cur.career_index > arr[best].career_index ? i : best, 0);
          updateHUD(currentPlayer.timeline[peakIdx]);
        };
        container.appendChild(btn);
      });
    }

    function toggleCounterfactual() {
      showCounterfactual = !showCounterfactual;
      const btn = document.getElementById('toggle-counterfactual');
      btn.classList.toggle('active', showCounterfactual);
      renderCharts();
    }

    function updateHUD(point) {
      if (!point) return;
      const theme = PHASE_THEMES[point.phase_state] || PHASE_THEMES.REGULAR;

      document.documentElement.style.setProperty('--accent-color', theme.color);
      document.documentElement.style.setProperty('--accent-glow', theme.glow);

      document.getElementById('hud-name').textContent = currentPlayer.name;
      document.getElementById('hud-meta').textContent = `${currentPlayer.position} • ${currentPlayer.nationality} • Pico: ${currentPlayer.summary.peak_index} pts`;

      const phaseEl = document.getElementById('hud-phase');
      phaseEl.textContent = theme.label;

      document.getElementById('hud-score').textContent = point.career_index.toFixed(1);
      document.getElementById('hud-score').style.color = theme.color;
      document.getElementById('hud-ci').textContent = `Banda Kalman: [${point.ci_lower} – ${point.ci_upper}]`;

      document.getElementById('hud-glory').textContent = point.glory_glow.toFixed(0);
      document.getElementById('hud-club').textContent = `${point.club} (${point.season})`;

      document.getElementById('hud-g-xag').textContent = `${point.goals}G | ${point.npxG} xG`;
      document.getElementById('hud-prog').textContent = `${point.prog_passes} Passes Prog • ${point.xAG} xAG`;

      const gap = (point.counterfactual_index - point.career_index).toFixed(1);
      document.getElementById('hud-loss').textContent = gap > 0.5 ? `-${gap} pts` : '0.0 pts';
      document.getElementById('hud-age').textContent = `Idade: ${point.age} anos (${point.date})`;

      const bannerText = document.getElementById('hud-event-text');
      if (point.glory_event) {
        bannerText.innerHTML = `<span style="color:#ffd166">${point.glory_icon} MOMENTO DE GLÓRIA: ${point.glory_event}</span>`;
      } else if (point.injury_name) {
        bannerText.innerHTML = `<span style="color:#ef476f">✚ LESÃO: ${point.injury_name} (${point.injury_days_missed} dias fora)</span>`;
      } else {
        bannerText.textContent = `${point.date} • ${point.club} • Elo Adv: ${point.opp_elo} • Minutos: ${point.minutes}'`;
      }

      // Atualiza mini-radar dos 4 Pilares Ortogonais naquele ponto exato do tempo
      const normPillar = (z) => Math.min(100, Math.max(10, Math.round(50 + z * 22)));
      radarChart.setOption({
        radar: {
          indicator: [
            { name: 'Finalização', max: 100 },
            { name: 'Criação/xT', max: 100 },
            { name: 'Retenção', max: 100 },
            { name: 'Defesa PAdj', max: 100 }
          ],
          radius: '62%',
          splitNumber: 3,
          axisName: { color: '#9ca3af', fontSize: 10, fontFamily: 'Inter' },
          splitArea: { areaStyle: { color: ['rgba(255,255,255,0.01)', 'rgba(255,255,255,0.03)'] } },
          splitLine: { lineStyle: { color: 'rgba(255,255,255,0.08)' } },
          axisLine: { lineStyle: { color: 'rgba(255,255,255,0.08)' } }
        },
        series: [{
          type: 'radar',
          data: [{
            value: [
              normPillar(point.z_pillar_finishing),
              normPillar(point.z_pillar_creation),
              normPillar(point.z_pillar_retention),
              normPillar(point.z_pillar_defense)
            ],
            areaStyle: { color: theme.glow },
            lineStyle: { color: theme.color, width: 2 },
            itemStyle: { color: theme.color }
          }]
        }]
      });
    }

    function renderCharts() {
      const tl = currentPlayer.timeline;
      const dates = tl.map(d => d.date);
      const scores = tl.map(d => d.career_index);
      const counterfactuals = tl.map(d => d.counterfactual_index);
      const ciLower = tl.map(d => d.ci_lower);
      const ciDiff = tl.map(d => +(d.ci_upper - d.ci_lower).toFixed(1));

      // Pinos de Momentos de Glória e Vales de Lesão
      const gloryPoints = [];
      tl.forEach((d, idx) => {
        if (d.glory_event) {
          gloryPoints.push({
            name: d.glory_event,
            coord: [d.date, d.career_index],
            value: d.glory_icon || '★',
            itemStyle: { color: '#ffd166', shadowBlur: 16, shadowColor: '#ffd166' },
            label: { color: '#000', fontWeight: 'bold', fontSize: 13 }
          });
        }
      });

      // Zonas sombreadas de lesão grave + faixas de clubes
      const markAreas = currentPlayer.injury_zones.map(iz => ([
        {
          name: `✚ ${iz.name}`,
          xAxis: iz.start_date,
          itemStyle: { color: 'rgba(239, 71, 111, 0.14)', borderColor: 'rgba(239, 71, 111, 0.4)', borderWidth: 1 },
          label: { color: '#fda4af', position: 'insideTop', fontSize: 10, fontFamily: 'JetBrains Mono' }
        },
        { xAxis: iz.end_date }
      ]));

      const option = {
        backgroundColor: 'transparent',
        animationDuration: 900,
        grid: { top: 38, right: 24, bottom: 75, left: 48 },
        tooltip: {
          trigger: 'axis',
          confine: true,
          backgroundColor: 'rgba(10, 14, 22, 0.92)',
          borderColor: 'rgba(255,255,255,0.15)',
          textStyle: { color: '#f3f4f6', fontFamily: 'Inter', fontSize: 12 },
          axisPointer: {
            type: 'cross',
            lineStyle: { color: 'rgba(255,255,255,0.35)', width: 1.5, type: 'dashed' },
            crossStyle: { color: 'rgba(255,255,255,0.25)' }
          },
          formatter: function (params) {
            const idx = params[0].dataIndex;
            const pt = currentPlayer.timeline[idx];
            updateHUD(pt);
            return `
              <div style="min-width:210px; line-height:1.45;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                  <b style="font-size:13px;">${pt.date} • ${pt.club}</b>
                  <span style="font-family:'JetBrains Mono'; font-size:11px; color:#9ca3af;">${pt.age} anos</span>
                </div>
                <div>Índice Kalman-RTS: <b style="color:var(--accent-color); font-size:14px;">${pt.career_index}</b> <span style="color:#9ca3af; font-size:11px;">(Glória: ${pt.glory_glow})</span></div>
                <div style="font-size:11px; color:#d1d5db; margin-top:4px;">
                  Gols: <b>${pt.goals}</b> (npxG: ${pt.npxG}) | xAG: <b>${pt.xAG}</b> | Prog: <b>${pt.prog_passes}</b>
                </div>
                ${pt.glory_event ? `<div style="margin-top:6px; padding:4px 6px; background:rgba(255,209,102,0.15); border-left:3px solid #ffd166; color:#ffd166; font-weight:600;">${pt.glory_icon} ${pt.glory_event}</div>` : ''}
                ${pt.injury_name ? `<div style="margin-top:6px; padding:4px 6px; background:rgba(239,71,111,0.15); border-left:3px solid #ef476f; color:#fda4af; font-weight:600;">✚ ${pt.injury_name} (${pt.injury_days_missed}d parados)</div>` : ''}
              </div>
            `;
          }
        },
        dataZoom: [
          { type: 'inside', start: 0, end: 100 },
          {
            type: 'slider',
            start: 0,
            end: 100,
            height: 26,
            bottom: 14,
            borderColor: 'rgba(255,255,255,0.08)',
            fillerColor: 'rgba(0, 245, 212, 0.12)',
            handleStyle: { color: '#00f5d4' },
            textStyle: { color: '#9ca3af' }
          }
        ],
        visualMap: {
          show: false,
           seriesIndex: 2,
          dimension: 1,
          pieces: [
            { gte: 85, color: '#ffd166' },
            { gte: 68, lt: 85, color: '#00f5d4' },
            { gte: 50, lt: 68, color: '#3b82f6' },
            { lt: 50, color: '#ef476f' }
          ]
        },
        xAxis: {
          type: 'category',
          data: dates,
          boundaryGap: false,
          axisLine: { lineStyle: { color: 'rgba(255,255,255,0.15)' } },
          axisLabel: { color: '#9ca3af', fontFamily: 'JetBrains Mono', fontSize: 11 }
        },
        yAxis: {
          type: 'value',
          min: 10,
          max: 100,
          name: 'ÍNDICE DE CARREIRA (0-100)',
          nameTextStyle: { color: '#9ca3af', fontFamily: 'JetBrains Mono', fontSize: 10, padding: [0, 0, 0, 20] },
          splitLine: { lineStyle: { color: 'rgba(255,255,255,0.05)', type: 'dashed' } },
          axisLabel: { color: '#9ca3af', fontFamily: 'JetBrains Mono', fontSize: 11 }
        },
        series: [
          // Série 0 & 1: Banda de Incerteza do Filtro de Kalman (Aura Sombreada)
          {
            name: 'CI Base',
            type: 'line',
            data: ciLower,
            lineStyle: { opacity: 0 },
            stack: 'kalman-band',
            symbol: 'none',
            silent: true
          },
          {
            name: 'Aura de Incerteza Kalman',
            type: 'line',
            data: ciDiff,
            lineStyle: { opacity: 0 },
            areaStyle: { color: 'rgba(59, 130, 246, 0.11)' },
            stack: 'kalman-band',
            symbol: 'none',
            silent: true
          },
          // Série 2: Curva Principal Suavizada (RTS Kalman) com VisualMap Dinâmico
          {
            name: 'Curva de Carreira (RTS)',
            type: 'line',
            data: scores,
            smooth: 0.35,
            symbol: 'circle',
            symbolSize: function (val, params) {
              const pt = currentPlayer.timeline[params.dataIndex];
              if (pt.glory_event) return 13;
              if (pt.injury_name) return 9;
              return 5;
            },
            lineStyle: {
              width: 3.8,
              shadowBlur: 14,
              shadowColor: 'rgba(0, 245, 212, 0.35)'
            },
            areaStyle: {
              opacity: 0.18
            },
            markPoint: {
              symbol: 'pin',
              symbolSize: 44,
              data: gloryPoints
            },
            markArea: {
              silent: true,
              data: markAreas
            }
          },
          // Série 3: Linha Contrafactual ("E se não tivesse lesionado?")
          {
            name: 'Projeção Contrafactual Sem Lesão',
            type: 'line',
            data: showCounterfactual ? counterfactuals : [],
            smooth: 0.35,
            symbol: 'none',
            lineStyle: {
              width: 2,
              type: 'dashed',
              color: '#a855f7'
            }
          }
        ]
      };

      mainChart.setOption(option, true);
    }

    window.addEventListener('resize', () => {
      mainChart.resize();
      radarChart.resize();
    });

    // Inicialização
    renderPlayerButtons();
    renderCharts();
    const initialPeakIdx = currentPlayer.timeline.reduce((best, cur, i, arr) => cur.career_index > arr[best].career_index ? i : best, 0);
    updateHUD(currentPlayer.timeline[initialPeakIdx]);
  </script>
</body>
</html>
"""


def build_interactive_webapp(output_dir: str = "web"):
    collector = MassiveDataCollector(output_dir=os.path.join(output_dir, "data"))
    collector.build_all_datasets()

    bundle_path = os.path.join(output_dir, "data", "careers_bundle.json")
    with open(bundle_path, "r", encoding="utf-8") as f:
        bundle_json_str = f.read()

    final_html = HTML_TEMPLATE.replace("__INJECT_BUNDLE_JSON__", bundle_json_str)
    index_path = os.path.join(output_dir, "index.html")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(final_html)

    return index_path
