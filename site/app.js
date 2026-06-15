function resolveLocaleKey() {
  const params = new URLSearchParams(window.location.search);
  const value = params.get("lang");
  if (value && value.toLowerCase().startsWith("pt")) {
    return "pt-BR";
  }
  if (document.documentElement.lang.toLowerCase().startsWith("pt")) {
    return "pt-BR";
  }
  return "en";
}

const CURRENT_LOCALE = resolveLocaleKey();
document.documentElement.lang = CURRENT_LOCALE === "pt-BR" ? "pt-BR" : "en";

function numberLocale() {
  return CURRENT_LOCALE === "pt-BR" ? "pt-BR" : "en-US";
}

function uiCopy() {
  return window.CMIL_UI_COPY?.[CURRENT_LOCALE] || {};
}

function commonCopy() {
  return uiCopy().common || {};
}

function siteCopy() {
  return uiCopy().site || {};
}

function appCopy() {
  return uiCopy().app || {};
}

function setText(id, value) {
  const element = document.getElementById(id);
  if (element && value !== undefined) {
    element.textContent = value;
  }
}

function setHtml(id, value) {
  const element = document.getElementById(id);
  if (element && value !== undefined) {
    element.innerHTML = value;
  }
}

function setHref(id, value) {
  const element = document.getElementById(id);
  if (element && value !== undefined) {
    element.setAttribute("href", value);
  }
}

function setMetaDescription(value) {
  const element = document.getElementById("page-description");
  if (element && value !== undefined) {
    element.setAttribute("content", value);
  }
}

function formatNarrativeLabel(value) {
  return value.replaceAll("_", " ");
}

function formatDriverLabel(value) {
  if (CURRENT_LOCALE !== "pt-BR") {
    return formatNarrativeLabel(value);
  }
  const mapping = {
    derivatives_positioning: "posicionamento em derivativos",
    onchain_confirmation: "confirmacao on-chain",
    volume_strength: "forca de volume",
  };
  return mapping[value] || formatNarrativeLabel(value);
}

function formatRegimeLabel(value) {
  if (CURRENT_LOCALE !== "pt-BR") {
    return formatNarrativeLabel(value);
  }
  const mapping = {
    bullish_attention: "atencao altista",
    bearish_attention: "atencao baixista",
    mixed_attention: "atencao mista",
  };
  return mapping[value] || formatNarrativeLabel(value);
}

function formatDriverSummary(driverMix) {
  const leadingDriver = driverMix?.leading_driver || {};
  if (!leadingDriver.name) {
    return "N/A";
  }
  const shareLabel = formatPercent((leadingDriver.share || 0) * 100, 1);
  return `${formatDriverLabel(leadingDriver.name)} / ${shareLabel}`;
}

function formatManifestPath(value) {
  if (!value) {
    return "N/A";
  }
  const parts = String(value).split(/[/\\\\]+/).filter(Boolean);
  return parts.slice(-3).join("/");
}

function formatNumber(value, digits) {
  return new Intl.NumberFormat(numberLocale(), {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  }).format(Number(value));
}

function formatCompactNumber(value, digits = 1) {
  if (value === null || value === undefined) {
    return "N/A";
  }
  return new Intl.NumberFormat(numberLocale(), {
    notation: "compact",
    maximumFractionDigits: digits,
  }).format(Number(value));
}

function formatPercent(value, digits = 2) {
  if (value === null || value === undefined) {
    return "N/A";
  }
  return `${formatNumber(value, digits)}%`;
}

function formatDecimal(value, digits = 4) {
  if (value === null || value === undefined) {
    return "N/A";
  }
  return formatNumber(value, digits);
}

function formatGeneratedAt(value) {
  const date = new Date(value);
  const prefix = commonCopy().generatedAtPrefix || "Snapshot generated";
  return `${prefix} ${date.toLocaleString(numberLocale(), {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "UTC",
  })} UTC`;
}

function regimeTone(value) {
  if (value.includes("bullish")) {
    return "bullish";
  }
  if (value.includes("bearish")) {
    return "bearish";
  }
  return "neutral";
}

function buildTag(label, tone = "neutral") {
  const toneClass = {
    bullish: "tag-bullish",
    bearish: "tag-bearish",
    neutral: "tag-neutral",
  }[tone] || "tag-neutral";
  return `<span class="tag ${toneClass}">${label}</span>`;
}

function buildHeroMetric(label, value, copy) {
  const item = document.createElement("div");
  item.className = "hero-metric";
  item.innerHTML = `
    <strong>${value}</strong>
    <span>${label}: ${copy}</span>
  `;
  return item;
}

function buildOverviewCard(index, title, body, tone) {
  const item = document.createElement("article");
  item.className = `about-card box--${tone}`;
  item.innerHTML = `
    <span>${String(index + 1).padStart(2, "0")}</span>
    <h3>${title}</h3>
    <p>${body}</p>
  `;
  return item;
}

function buildPipelineNode(label, title, copy, tone) {
  const item = document.createElement("article");
  item.className = `pipeline-node box--${tone}`;
  item.innerHTML = `
    <p class="mini-label">${label}</p>
    <strong>${title}</strong>
    <span>${copy}</span>
  `;
  return item;
}

function buildArchitectureCard(line, index) {
  const item = document.createElement("article");
  item.className = "architecture-card";
  const parts = line.split(":");
  item.innerHTML = `
    <span class="architecture-step">${String(index + 1).padStart(2, "0")}</span>
    <h3>${parts[0]}</h3>
    <p>${parts.slice(1).join(":").trim()}</p>
  `;
  return item;
}

function buildSignalCard(signal, tone) {
  const item = document.createElement("article");
  item.className = `signal-card box--${tone}`;
  const label = commonCopy().signalLayerLabel || "Signal Layer";
  item.innerHTML = `
    <p class="mini-label">${label}</p>
    <h3>${signal.name}</h3>
    <p>${signal.description}</p>
  `;
  return item;
}

function buildBlueprintCard(item, tone) {
  const card = document.createElement("article");
  card.className = `signal-card box--${tone}`;
  card.innerHTML = `
    <p class="mini-label">${item.artifact}</p>
    <h3>${item.title}</h3>
    <p>${item.description}</p>
  `;
  return card;
}

function buildFeaturedStat(label, value, body) {
  const item = document.createElement("div");
  item.className = "featured-stat";
  item.innerHTML = `
    <span class="featured-label">${label}</span>
    <strong>${value}</strong>
    <p>${body}</p>
  `;
  return item;
}

function buildAppChip(label, value, body) {
  const item = document.createElement("article");
  item.className = "app-chip";
  item.innerHTML = `
    <p class="mini-label">${label}</p>
    <strong>${value}</strong>
    <p>${body}</p>
  `;
  return item;
}

function buildAppInsightCard(label, title, body, tone) {
  const item = document.createElement("article");
  item.className = `app-insight-card box--${tone}`;
  item.innerHTML = `
    <p class="mini-label">${label}</p>
    <strong>${title}</strong>
    <p>${body}</p>
  `;
  return item;
}

function renderAppRefreshStatus(data) {
  const refreshNote = document.getElementById("app-refresh-note");
  if (!refreshNote) {
    return;
  }

  const copy = appCopy();
  const watchLabel = commonCopy().watchLabel || "watch";
  const refreshPolicy = data.refresh_policy || {};
  const runMetadata = data.run_metadata || {};
  const cadenceLabel = CURRENT_LOCALE === "pt-BR"
    ? "A cada 12 horas"
    : (refreshPolicy.cadence_label || "Manual refresh");
  const cadenceDetail = CURRENT_LOCALE === "pt-BR"
    ? "A atualizacao automatica do snapshot roda em uma cadencia de 12 horas, com disparo manual disponivel pelo GitHub Actions."
    : (refreshPolicy.cadence_detail || "Snapshot publishing currently depends on manual pipeline execution.");
  const triggerLabel = refreshPolicy.trigger === "github_actions"
    ? (copy.refreshTriggerGithub || "GitHub Actions")
    : (copy.refreshTriggerManual || "manual workflow");

  refreshNote.innerHTML = `
    <div class="asset-item-top">
      <strong>${copy.refreshTitle || "Snapshot Freshness"}</strong>
      ${buildTag(CURRENT_LOCALE === "pt-BR" ? watchLabel : cadenceLabel.toLowerCase(), "neutral")}
    </div>
    <p>
      <strong>${cadenceLabel}</strong> ${(copy.refreshCadencePrefix || "publishing cadence via")} ${triggerLabel}. ${cadenceDetail}
    </p>
    <p class="app-mini-label">Run ${runMetadata.run_id || "local-run"} / Artifact ${runMetadata.artifact_version || "v1"}</p>
    <p class="app-mini-label">Manifest ${formatManifestPath(runMetadata.manifest_path)}</p>
    <p class="app-mini-label">${formatGeneratedAt(data.generated_at)}</p>
  `;
}

function buildAppMiniItem(title, value, body, tags = []) {
  const item = document.createElement("article");
  item.className = "app-mini-item";
  const tagRow = tags.length
    ? `<div class="asset-item-top">${tags.join("")}</div>`
    : "";
  item.innerHTML = `
    <div class="app-mini-row">
      <strong>${title}</strong>
      <span class="app-mini-label">${value}</span>
    </div>
    <p>${body}</p>
    ${tagRow}
  `;
  return item;
}

function buildAlertItem(title, body, tone = "neutral") {
  const watchLabel = commonCopy().watchLabel || "watch";
  const item = document.createElement("article");
  item.className = "app-alert-item";
  item.innerHTML = `
    <div class="asset-item-top">
      <strong>${title}</strong>
      ${buildTag(tone === "neutral" ? watchLabel : tone, tone)}
    </div>
    <p>${body}</p>
  `;
  return item;
}

function buildBarChartRow(label, valueLabel, fraction, tone = "default") {
  const item = document.createElement("div");
  item.className = "bar-row";
  const fillClass = tone === "amber" ? "bar-fill bar-fill--amber" : tone === "lavender" ? "bar-fill bar-fill--lavender" : "bar-fill";
  item.innerHTML = `
    <div class="bar-label-row">
      <strong>${label}</strong>
      <span class="app-mini-label">${valueLabel}</span>
    </div>
    <div class="bar-track">
      <div class="${fillClass}" style="width: ${Math.max(0, Math.min(100, fraction * 100))}%"></div>
    </div>
  `;
  return item;
}

function buildBuildDetail(title, body, tone) {
  const item = document.createElement("article");
  item.className = `box box--${tone}`;
  item.innerHTML = `
    <span class="featured-label">${title}</span>
    <h3>${title}</h3>
    <p>${body}</p>
  `;
  return item;
}

function buildRoadmapCard(item) {
  const card = document.createElement("article");
  card.className = "roadmap-card";
  card.innerHTML = `
    <div class="asset-item-top">
      <span class="roadmap-phase">${item[0]}</span>
      <span class="tag">${item[1]}</span>
    </div>
    <h3>${item[2]}</h3>
    <p>${item[3]}</p>
  `;
  return card;
}

function buildAssetTable(rows) {
  const labels = commonCopy().table || {};
  const table = document.createElement("table");
  const thead = document.createElement("thead");
  thead.innerHTML = `
    <tr>
      <th>${labels.asset || "Asset"}</th>
      <th>${labels.narrative || "Narrative"}</th>
      <th>${labels.attention || "Attention"}</th>
      <th>${labels.driver || "Driver"}</th>
      <th>${labels.regime || "Regime"}</th>
    </tr>
  `;
  const tbody = document.createElement("tbody");
  rows.forEach((row) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td class="table-strong">${row.symbol}</td>
      <td><span class="tag">${formatNarrativeLabel(row.narrative)}</span></td>
      <td>${formatNumber(row.attention_score, 2)}</td>
      <td>${formatDriverLabel(row.top_driver)}</td>
      <td>${buildTag(formatRegimeLabel(row.regime_tag), regimeTone(row.regime_tag))}</td>
    `;
    tbody.appendChild(tr);
  });
  table.append(thead, tbody);
  return table;
}

function buildNarrativeTable(rows) {
  const labels = commonCopy().table || {};
  const table = document.createElement("table");
  const thead = document.createElement("thead");
  thead.innerHTML = `
    <tr>
      <th>${labels.narrative || "Narrative"}</th>
      <th>${labels.assets || "Assets"}</th>
      <th>${labels.avgAttention || "Avg Attention"}</th>
      <th>${labels.avgConfirmation || "Avg Confirmation"}</th>
    </tr>
  `;
  const tbody = document.createElement("tbody");
  rows.forEach((row) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td class="table-strong">${formatNarrativeLabel(row.narrative)}</td>
      <td>${row.asset_count}</td>
      <td>${formatNumber(row.avg_attention_score, 2)}</td>
      <td>${formatNumber(row.avg_confirmation_score, 2)}</td>
    `;
    tbody.appendChild(tr);
  });
  table.append(thead, tbody);
  return table;
}

function buildAssetItem(row, isActive) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = `asset-item${isActive ? " is-active" : ""}`;
  button.dataset.symbol = row.symbol;
  button.innerHTML = `
    <div class="asset-item-top">
      <span class="asset-symbol">${row.symbol}</span>
      <span class="tag">${formatNarrativeLabel(row.narrative)}</span>
      ${buildTag(formatRegimeLabel(row.regime_tag), regimeTone(row.regime_tag))}
    </div>
    <p class="asset-meta">
      Attention ${formatNumber(row.attention_score, 2)} / Confirmation ${formatNumber(row.confirmation_score, 2)} /
      Driver ${formatDriverLabel(row.top_driver)}
    </p>
  `;
  return button;
}

function buildNarrativeItem(row, isActive) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = `asset-item${isActive ? " is-active" : ""}`;
  button.dataset.narrative = row.narrative;
  button.innerHTML = `
    <div class="asset-item-top">
      <span class="asset-symbol">${formatNarrativeLabel(row.narrative)}</span>
      <span class="tag">${row.asset_count} assets</span>
    </div>
    <p class="asset-meta">
      Avg attention ${formatNumber(row.avg_attention_score, 2)} / Avg confirmation ${formatNumber(row.avg_confirmation_score, 2)} /
      Leader ${row.leader_symbol}
    </p>
  `;
  return button;
}

function buildAssetDetail(row) {
  const copy = appCopy();
  const labels = commonCopy().detail || {};
  const wrapper = document.createElement("div");
  if (!row) {
    wrapper.innerHTML = `
      <div class="detail-copy">
        <p>${copy.detailEmpty || "Select an asset to inspect its narrative, regime, and current attention context."}</p>
      </div>
    `;
    return wrapper;
  }

  let signalSummary = "Volume and market-structure context remain the primary explanation right now.";
  if (CURRENT_LOCALE === "pt-BR") {
    signalSummary = "Volume e contexto de market structure seguem como a explicação principal neste momento.";
  }
  if (row.top_driver === "derivatives_positioning") {
    signalSummary = CURRENT_LOCALE === "pt-BR"
      ? "Posicionamento em derivativos é hoje a principal camada explicativa."
      : "Derivatives positioning is the leading explanatory layer right now.";
  } else if (row.top_driver === "onchain_confirmation") {
    signalSummary = CURRENT_LOCALE === "pt-BR"
      ? "Confirmação on-chain está ajudando a sustentar o perfil atual de atenção."
      : "On-chain confirmation is helping justify the current attention profile.";
  }

  const marketSummary = row.relative_strength_7d === null || row.relative_strength_7d === undefined
    ? (CURRENT_LOCALE === "pt-BR"
      ? "As features cross-sectional ainda não estão disponíveis para este ativo no snapshot exportado."
      : "Cross-sectional market features are not yet available for this asset in the exported snapshot.")
    : (CURRENT_LOCALE === "pt-BR"
      ? `${row.symbol} mostra ${formatPercent(row.relative_strength_7d)} de relative strength na janela recente de 7 dias, com ${formatCompactNumber(row.quote_volume)} em volume negociado.`
      : `${row.symbol} is showing ${formatPercent(row.relative_strength_7d)} relative strength over the recent 7-day window, with ${formatCompactNumber(row.quote_volume)} in quote volume.`);

  const derivativesSummary = row.open_interest
    ? (CURRENT_LOCALE === "pt-BR"
      ? `O contexto atual de derivativos inclui ${formatCompactNumber(row.open_interest, 2)} em open interest e funding de ${formatDecimal(row.funding_rate, 6)}.`
      : `Current derivatives context includes ${formatCompactNumber(row.open_interest, 2)} open interest and ${formatDecimal(row.funding_rate, 6)} funding.`)
    : (CURRENT_LOCALE === "pt-BR"
      ? "A leitura de derivativos ainda está mais rasa para este ativo, o que ajuda o explorer a mostrar onde a cobertura precisa evoluir."
      : "Derivatives detail is currently sparse for this asset, which makes the explorer useful for highlighting where coverage still needs to deepen.");

  wrapper.innerHTML = `
    <div class="detail-hero">
      <div class="asset-detail-top">
        <span class="detail-symbol">${row.symbol}</span>
        <span class="tag">${formatNarrativeLabel(row.narrative)}</span>
        ${buildTag(formatRegimeLabel(row.regime_tag), regimeTone(row.regime_tag))}
      </div>
      <div class="detail-score-row">
        <div class="detail-score">Attention ${formatNumber(row.attention_score, 2)}</div>
        <div class="detail-tag-row">
          <span class="tag">${formatDriverLabel(row.top_driver)}</span>
        </div>
      </div>
    </div>
    <div class="detail-grid">
      <div class="detail-metric">
        <span>${labels.attentionScore || "Attention score"}</span>
        <strong>${formatNumber(row.attention_score, 3)}</strong>
      </div>
      <div class="detail-metric">
        <span>${labels.confirmationScore || "Confirmation score"}</span>
        <strong>${formatNumber(row.confirmation_score, 4)}</strong>
      </div>
      <div class="detail-metric">
        <span>${labels.primaryDriver || "Primary driver"}</span>
        <strong>${formatDriverLabel(row.top_driver)}</strong>
      </div>
      <div class="detail-metric">
        <span>${labels.price || "Price"}</span>
        <strong>${row.close_price ? `$${formatCompactNumber(row.close_price, 2)}` : "N/A"}</strong>
      </div>
      <div class="detail-metric">
        <span>${labels.quoteVolume || "Quote volume"}</span>
        <strong>${formatCompactNumber(row.quote_volume, 2)}</strong>
      </div>
      <div class="detail-metric">
        <span>${labels.rs7d || "RS 7d"}</span>
        <strong>${formatPercent(row.relative_strength_7d)}</strong>
      </div>
      <div class="detail-metric">
        <span>${labels.breadth || "Breadth"}</span>
        <strong>${row.breadth_flag ? formatNarrativeLabel(row.breadth_flag) : "N/A"}</strong>
      </div>
      <div class="detail-metric">
        <span>${labels.crowding || "Crowding"}</span>
        <strong>${row.crowding_flag === null || row.crowding_flag === undefined ? "N/A" : row.crowding_flag ? (CURRENT_LOCALE === "pt-BR" ? "Elevado" : "Elevated") : (CURRENT_LOCALE === "pt-BR" ? "Contido" : "Contained")}</strong>
      </div>
      <div class="detail-metric">
        <span>${labels.openInterest || "Open interest"}</span>
        <strong>${formatCompactNumber(row.open_interest, 2)}</strong>
      </div>
    </div>
    <div class="detail-copy">
      <p>
        ${CURRENT_LOCALE === "pt-BR"
          ? `${row.symbol} hoje está dentro da narrativa <strong>${formatNarrativeLabel(row.narrative)}</strong>, com regime <strong>${formatRegimeLabel(row.regime_tag)}</strong>.`
          : `${row.symbol} currently sits inside the <strong>${formatNarrativeLabel(row.narrative)}</strong> narrative bucket, with a <strong>${formatRegimeLabel(row.regime_tag)}</strong> regime tag.`}
      </p>
      <p>${signalSummary}</p>
      <p>${marketSummary}</p>
      <p>${derivativesSummary}</p>
      <p>
        ${CURRENT_LOCALE === "pt-BR"
          ? "Este explorer é a primeira superfície com cara de produto construída diretamente sobre a mesma camada gold exportada usada na página de portfólio, e funciona como protótipo para uma plataforma mais profunda."
          : "This explorer is the first product-style surface built directly on top of the same exported gold layer used by the portfolio page, and acts as a prototype for a deeper platform experience."}
      </p>
    </div>
  `;
  return wrapper;
}

function buildComparePanel(selectedRow, compareRow) {
  const copy = appCopy();
  const labels = commonCopy().table || {};
  const wrapper = document.createElement("div");
  if (!selectedRow) {
    wrapper.innerHTML = `<p class="asset-meta">${CURRENT_LOCALE === "pt-BR" ? "Selecione um ativo para comparar." : "Select an asset to compare."}</p>`;
    return wrapper;
  }

  if (!compareRow || compareRow.symbol === selectedRow.symbol) {
    wrapper.innerHTML = `
      <div class="card-header compact">
        <h3>${copy.compareTitle || "Asset Comparison"}</h3>
        <p>${copy.compareEmpty || "Choose a second asset to compare against the selected one."}</p>
      </div>
    `;
    return wrapper;
  }

  const rows = [
    [labels.attention || "Attention", formatNumber(selectedRow.attention_score, 2), formatNumber(compareRow.attention_score, 2)],
    ["RS 7d", formatPercent(selectedRow.relative_strength_7d), formatPercent(compareRow.relative_strength_7d)],
    [CURRENT_LOCALE === "pt-BR" ? "Volume" : "Volume", formatCompactNumber(selectedRow.quote_volume, 2), formatCompactNumber(compareRow.quote_volume, 2)],
    [labels.regime || "Regime", formatRegimeLabel(selectedRow.regime_tag), formatRegimeLabel(compareRow.regime_tag)],
  ];

  wrapper.innerHTML = `
    <div class="card-header compact">
      <h3>${copy.compareTitle || "Asset Comparison"}</h3>
      <p>${CURRENT_LOCALE === "pt-BR" ? `${selectedRow.symbol} versus ${compareRow.symbol} nos primeiros sinais exportados do produto.` : `${selectedRow.symbol} versus ${compareRow.symbol} across the first exported product signals.`}</p>
    </div>
  `;

  const table = document.createElement("table");
  table.className = "mini-table";
  table.innerHTML = `
    <thead>
      <tr>
        <th>${labels.metric || "Metric"}</th>
        <th>${selectedRow.symbol}</th>
        <th>${compareRow.symbol}</th>
      </tr>
    </thead>
  `;
  const tbody = document.createElement("tbody");
  rows.forEach((row) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `<td>${row[0]}</td><td>${row[1]}</td><td>${row[2]}</td>`;
    tbody.appendChild(tr);
  });
  table.appendChild(tbody);
  wrapper.appendChild(table);
  return wrapper;
}

function buildNarrativePulsePanel(narrativeRow, peerRows) {
  const copy = appCopy();
  const labels = commonCopy().detail || {};
  const wrapper = document.createElement("div");
  if (!narrativeRow) {
    wrapper.innerHTML = `
      <div class="card-header compact">
        <h3>${copy.pulseTitle || "Narrative Pulse"}</h3>
        <p>${copy.pulseEmpty || "No narrative aggregation is available for the current selection."}</p>
      </div>
    `;
    return wrapper;
  }

  wrapper.innerHTML = `
    <div class="card-header compact">
      <h3>${copy.pulseTitle || "Narrative Pulse"}</h3>
      <p>${CURRENT_LOCALE === "pt-BR" ? `${formatNarrativeLabel(narrativeRow.narrative)} hoje é liderada por ${narrativeRow.leader_symbol} entre ${narrativeRow.asset_count} ativos acompanhados.` : `${formatNarrativeLabel(narrativeRow.narrative)} is currently led by ${narrativeRow.leader_symbol} across ${narrativeRow.asset_count} tracked assets.`}</p>
    </div>
    <div class="pulse-metrics">
      <div class="detail-metric">
        <span>${labels.avgAttention || "Avg attention"}</span>
        <strong>${formatNumber(narrativeRow.avg_attention_score, 2)}</strong>
      </div>
      <div class="detail-metric">
        <span>${labels.avgConfirmation || "Avg confirmation"}</span>
        <strong>${formatNumber(narrativeRow.avg_confirmation_score, 2)}</strong>
      </div>
      <div class="detail-metric">
        <span>${labels.leader || "Leader"}</span>
        <strong>${narrativeRow.leader_symbol}</strong>
      </div>
    </div>
  `;

  const peers = document.createElement("div");
  peers.className = "peer-list";
  peerRows.forEach((row) => {
    const item = document.createElement("div");
    item.className = "peer-item";
    item.innerHTML = `
      <span class="peer-symbol">${row.symbol}</span>
      <span>${formatNumber(row.attention_score, 2)}</span>
      ${buildTag(formatRegimeLabel(row.regime_tag), regimeTone(row.regime_tag))}
    `;
    peers.appendChild(item);
  });
  wrapper.appendChild(peers);
  return wrapper;
}

function buildNarrativeDetail(row, peerRows) {
  const copy = appCopy();
  const labels = commonCopy().detail || {};
  const wrapper = document.createElement("div");
  if (!row) {
    wrapper.innerHTML = `
      <div class="detail-copy">
        <p>${copy.narrativeDetailEmpty || "Select a narrative to inspect its current leader set and peer structure."}</p>
      </div>
    `;
    return wrapper;
  }

  const broadCount = row.regime_mix.filter((value) => value === "bearish_attention" || value === "bullish_attention").length;

  wrapper.innerHTML = `
    <div class="detail-hero">
      <div class="asset-detail-top">
        <span class="detail-symbol">${formatNarrativeLabel(row.narrative)}</span>
        <span class="tag">${row.asset_count} tracked assets</span>
      </div>
      <div class="detail-score-row">
        <div class="detail-score">Leader ${row.leader_symbol}</div>
      </div>
    </div>
    <div class="detail-grid">
      <div class="detail-metric">
        <span>${labels.avgAttention || "Avg attention"}</span>
        <strong>${formatNumber(row.avg_attention_score, 3)}</strong>
      </div>
      <div class="detail-metric">
        <span>${labels.avgConfirmation || "Avg confirmation"}</span>
        <strong>${formatNumber(row.avg_confirmation_score, 4)}</strong>
      </div>
      <div class="detail-metric">
        <span>${labels.directionalAssets || "Directional assets"}</span>
        <strong>${broadCount}/${row.asset_count}</strong>
      </div>
    </div>
    <div class="detail-copy">
      <p>
        ${CURRENT_LOCALE === "pt-BR"
          ? `${formatNarrativeLabel(row.narrative)} hoje é liderada por <strong>${row.leader_symbol}</strong> e reúne ${row.asset_count} ativos nesta primeira superfície pública.`
          : `${formatNarrativeLabel(row.narrative)} is currently led by <strong>${row.leader_symbol}</strong> and groups ${row.asset_count} assets in the first public analytical surface.`}
      </p>
      <p>
        ${CURRENT_LOCALE === "pt-BR"
          ? "Este modo por narrativa foi pensado para mostrar rotação e concentração no nível do cluster, oferecendo uma leitura mais próxima de research do que simplesmente escanear ativos isolados."
          : "This narrative mode is meant to show rotation and concentration patterns at the cluster level, which is a more research-oriented view than scanning individual assets one by one."}
      </p>
    </div>
  `;

  const peers = document.createElement("div");
  peers.className = "peer-list";
  peerRows.forEach((peer) => {
    const item = document.createElement("div");
    item.className = "peer-item";
    item.innerHTML = `
      <span class="peer-symbol">${peer.symbol}</span>
      <span>${formatNumber(peer.attention_score, 2)}</span>
      ${buildTag(formatRegimeLabel(peer.regime_tag), regimeTone(peer.regime_tag))}
    `;
    peers.appendChild(item);
  });
  wrapper.appendChild(peers);
  return wrapper;
}

function renderAppInsights(data) {
  const copy = appCopy();
  const signalStrip = document.getElementById("app-signal-strip");
  const insightGrid = document.getElementById("app-insight-grid");
  if (!signalStrip || !insightGrid) {
    return;
  }

  const topAsset = data.top_assets[0];
  const topNarrative = data.top_narratives[0];
  const driverMix = data.overview?.driver_mix || {};
  const bearishShare = `${data.overview.bearish_count}/${data.overview.asset_count}`;
  const mixedShare = `${data.overview.mixed_count}/${data.overview.asset_count}`;

  signalStrip.append(
    buildAppChip(
      copy.chips?.snapshotPosture || "Snapshot posture",
      bearishShare,
      CURRENT_LOCALE === "pt-BR" ? "Ativos hoje marcados como bearish attention na camada gold exportada." : "Assets currently tagged with bearish attention in the exported gold layer.",
    ),
    buildAppChip(
      copy.chips?.mixedRegimes || "Mixed regimes",
      mixedShare,
      CURRENT_LOCALE === "pt-BR" ? "Ativos em que o estado atual ainda não aparece como direcional limpo." : "Assets where the current state is not cleanly directional.",
    ),
    buildAppChip(
      copy.chips?.topAsset || "Top asset",
      topAsset?.symbol || "N/A",
      CURRENT_LOCALE === "pt-BR" ? "Líder atual de atenção dentro do universo acompanhado." : "Current attention leader in the tracked universe.",
    ),
    buildAppChip(
      copy.chips?.topNarrative || "Top narrative",
      formatNarrativeLabel(topNarrative?.narrative || "N/A"),
      CURRENT_LOCALE === "pt-BR" ? "Cluster líder por atenção agregada." : "Leading cluster by aggregated attention.",
    ),
    buildAppChip(
      copy.chips?.leadingDriver || "Leading driver",
      formatDriverSummary(driverMix),
      CURRENT_LOCALE === "pt-BR" ? "Mistura atual dos drivers mais relevantes na camada gold exportada." : "Current mix of the most relevant drivers in the exported gold layer.",
    ),
  );

  insightGrid.append(
    buildAppInsightCard(
      copy.insights?.leaderLabel || "Leader Read",
      CURRENT_LOCALE === "pt-BR" ? `${topAsset?.symbol || "N/A"} é o foco atual` : `${topAsset?.symbol || "N/A"} is the current focus`,
      topAsset
        ? (CURRENT_LOCALE === "pt-BR"
          ? `${topAsset.symbol} lidera o snapshot com ${formatNumber(topAsset.attention_score, 2)} de atenção e ${formatDriverLabel(topAsset.top_driver)} como principal camada explicativa.`
          : `${topAsset.symbol} leads the snapshot with ${formatNumber(topAsset.attention_score, 2)} attention and ${formatDriverLabel(topAsset.top_driver)} as the primary explanatory layer.`)
        : (CURRENT_LOCALE === "pt-BR" ? "Nenhum líder por ativo está disponível no export atual." : "No asset leader is available in the current export."),
      "health",
    ),
    buildAppInsightCard(
      copy.insights?.narrativeLabel || "Narrative Read",
      CURRENT_LOCALE === "pt-BR" ? `${formatNarrativeLabel(topNarrative?.narrative || "N/A")} está liderando` : `${formatNarrativeLabel(topNarrative?.narrative || "N/A")} is leading`,
      topNarrative
        ? (CURRENT_LOCALE === "pt-BR"
          ? `${formatNarrativeLabel(topNarrative.narrative)} hoje reúne ${topNarrative.asset_count} ativos acompanhados com atenção média de ${formatNumber(topNarrative.avg_attention_score, 2)}.`
          : `${formatNarrativeLabel(topNarrative.narrative)} currently groups ${topNarrative.asset_count} tracked assets with average attention of ${formatNumber(topNarrative.avg_attention_score, 2)}.`)
        : (CURRENT_LOCALE === "pt-BR" ? "Nenhuma narrativa líder está disponível no export atual." : "No narrative leader is available in the current export."),
      "models",
    ),
    buildAppInsightCard(
      copy.insights?.buildLabel || "Build Read",
      copy.insights?.buildTitle || "Product surface over one exported truth",
      copy.insights?.buildBody || "This app runs on the same generated payload used by the case study, which is the right boundary for evolving from portfolio artifact into a fuller analytical product.",
      "ops",
    ),
    buildAppInsightCard(
      copy.insights?.driverLabel || "Driver Read",
      CURRENT_LOCALE === "pt-BR"
        ? `${formatDriverLabel(driverMix.leading_driver?.name || "volume_strength")} domina a leitura atual`
        : `${formatDriverLabel(driverMix.leading_driver?.name || "volume_strength")} dominates the current read`,
      CURRENT_LOCALE === "pt-BR"
        ? `O snapshot mostra ${driverMix.counts?.derivatives_positioning ?? 0} ativos puxados por derivativos, ${driverMix.counts?.onchain_confirmation ?? 0} por confirmacao on-chain e ${driverMix.counts?.volume_strength ?? 0} por forca de volume.`
        : `The snapshot shows ${driverMix.counts?.derivatives_positioning ?? 0} assets led by derivatives, ${driverMix.counts?.onchain_confirmation ?? 0} by on-chain confirmation, and ${driverMix.counts?.volume_strength ?? 0} by volume strength.`,
      "health",
    ),
  );
}

function renderAppCommandCenter(data) {
  const leaderboard = document.getElementById("app-leaderboard");
  const rotationBoard = document.getElementById("app-rotation-board");
  const alerts = document.getElementById("app-alerts");
  if (!leaderboard || !rotationBoard || !alerts) {
    return;
  }
  const narrativeHealth = data.narrative_health || [];

  data.top_assets.slice(0, 5).forEach((row) => {
    leaderboard.appendChild(
      buildAppMiniItem(
        row.symbol,
        `Attn ${formatNumber(row.attention_score, 2)}`,
        `${formatNarrativeLabel(row.narrative)} / ${formatDriverLabel(row.top_driver)}`,
        [
          buildTag(formatRegimeLabel(row.regime_tag), regimeTone(row.regime_tag)),
          `<span class="tag">${formatNarrativeLabel(row.narrative)}</span>`,
        ],
      ),
    );
  });

  narrativeHealth.slice(0, 4).forEach((row) => {
    rotationBoard.appendChild(
      buildAppMiniItem(
        formatNarrativeLabel(row.narrative),
        `Leader ${row.leader_symbol || "N/A"}`,
        `${row.asset_count} assets / Avg attention ${formatNumber(row.avg_attention_score, 2)} / ${formatDriverLabel(row.leader_driver || "volume_strength")}`,
        [
          buildTag(formatRegimeLabel(row.leader_regime || "mixed_attention"), regimeTone(row.leader_regime || "mixed_attention")),
          `<span class="tag">${row.leader_symbol || "N/A"}</span>`,
        ],
      ),
    );
  });

  const topAsset = data.top_assets[0];
  if (topAsset) {
    alerts.appendChild(
      buildAlertItem(
        `${topAsset.symbol} is the primary attention leader`,
        CURRENT_LOCALE === "pt-BR"
          ? `${topAsset.symbol} hoje lidera o universo exportado com ${formatNumber(topAsset.attention_score, 2)} de atenção e ${formatDriverLabel(topAsset.top_driver)} como driver principal.`
          : `${topAsset.symbol} currently leads the exported universe with ${formatNumber(topAsset.attention_score, 2)} attention and ${formatDriverLabel(topAsset.top_driver)} as the main driver.`,
        regimeTone(topAsset.regime_tag),
      ),
    );
  }
  const mixedAsset = data.top_assets.find((row) => row.regime_tag === "mixed_attention");
  if (mixedAsset) {
    alerts.appendChild(
      buildAlertItem(
        CURRENT_LOCALE === "pt-BR" ? `${mixedAsset.symbol} está em regime misto` : `${mixedAsset.symbol} is in a mixed regime`,
        CURRENT_LOCALE === "pt-BR"
          ? `${mixedAsset.symbol} se destaca porque a atenção está alta, mas o regime continua misto, então faz mais sentido monitorar do que assumir convicção limpa.`
          : `${mixedAsset.symbol} stands out because its attention is notable while the regime remains mixed, which makes it useful for monitoring rather than clean conviction.`,
        "neutral",
      ),
    );
  }
  const topNarrative = narrativeHealth[0];
  if (topNarrative) {
    alerts.appendChild(
      buildAlertItem(
        CURRENT_LOCALE === "pt-BR"
          ? `${formatNarrativeLabel(topNarrative.narrative)} lidera a rotação entre clusters`
          : `${formatNarrativeLabel(topNarrative.narrative)} is leading cluster rotation`,
        CURRENT_LOCALE === "pt-BR"
          ? `${formatNarrativeLabel(topNarrative.narrative)} hoje aparece em primeiro por atenção média e está sendo carregada por ${topNarrative.leader_symbol}.`
          : `${formatNarrativeLabel(topNarrative.narrative)} currently ranks first by average attention, is led by ${topNarrative.leader_symbol}, and carries ${formatDriverLabel(topNarrative.leader_driver || "volume_strength")} as the primary driver.`,
        "bullish",
      ),
    );
  }
}

function renderAppVisuals(data) {
  const attentionBars = document.getElementById("app-attention-bars");
  const narrativeBars = document.getElementById("app-narrative-bars");
  const rsBars = document.getElementById("app-rs-bars");
  if (!attentionBars || !narrativeBars || !rsBars) {
    return;
  }

  const topAttention = Math.max(...data.top_assets.map((row) => row.attention_score), 1);
  const attentionList = document.createElement("div");
  attentionList.className = "bar-list";
  data.top_assets.slice(0, 5).forEach((row) => {
    attentionList.appendChild(
      buildBarChartRow(row.symbol, formatNumber(row.attention_score, 2), row.attention_score / topAttention, "default"),
    );
  });
  attentionBars.appendChild(attentionList);

  const topNarrative = Math.max(...data.narrative_explorer_rows.map((row) => row.avg_attention_score), 1);
  const narrativeList = document.createElement("div");
  narrativeList.className = "bar-list";
  data.narrative_explorer_rows.slice(0, 5).forEach((row) => {
    narrativeList.appendChild(
      buildBarChartRow(
        formatNarrativeLabel(row.narrative),
        formatNumber(row.avg_attention_score, 2),
        row.avg_attention_score / topNarrative,
        "amber",
      ),
    );
  });
  narrativeBars.appendChild(narrativeList);

  const rsRows = data.asset_explorer_rows
    .filter((row) => row.relative_strength_7d !== null && row.relative_strength_7d !== undefined)
    .sort((left, right) => right.relative_strength_7d - left.relative_strength_7d)
    .slice(0, 5);
  const maxRs = Math.max(...rsRows.map((row) => Math.abs(row.relative_strength_7d)), 1);
  const rsList = document.createElement("div");
  rsList.className = "bar-list";
  rsRows.forEach((row) => {
    rsList.appendChild(
      buildBarChartRow(
        row.symbol,
        formatPercent(row.relative_strength_7d),
        Math.abs(row.relative_strength_7d) / maxRs,
        "lavender",
      ),
    );
  });
  rsBars.appendChild(rsList);
}

function activateRevealAnimations() {
  const targets = document.querySelectorAll(
    ".hero, .about-shell, .cloud-pin, .featured-shell, .explorer-shell, .card, .architecture-card, .signal-card, .roadmap-card",
  );
  if (!("IntersectionObserver" in window)) {
    targets.forEach((item) => item.classList.add("is-visible"));
    return;
  }

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.14 },
  );

  targets.forEach((item) => observer.observe(item));
}

function applySiteStaticCopy(data) {
  const copy = siteCopy();
  if (copy.metaTitle) {
    document.title = copy.metaTitle;
  }
  setMetaDescription(copy.metaDescription);
  setText("site-brand-subtitle", copy.brandSubtitle);
  setHtml("site-side-note", copy.sideNoteHtml);
  setText("site-viz-label", copy.vizLabel);

  setHtml("side-link-overview", copy.sideLinks?.overview ? `${copy.sideLinks.overview} <span>&nearr;</span>` : undefined);
  setHtml("side-link-build", copy.sideLinks?.build ? `${copy.sideLinks.build} <span>&nearr;</span>` : undefined);
  setHtml("side-link-blueprint", copy.sideLinks?.blueprint ? `${copy.sideLinks.blueprint} <span>&nearr;</span>` : undefined);
  setHtml("side-link-explorer", copy.sideLinks?.explorer ? `${copy.sideLinks.explorer} <span>&nearr;</span>` : undefined);
  setHtml("side-link-app", copy.sideLinks?.app ? `${copy.sideLinks.app} <span>&nearr;</span>` : undefined);
  setHtml("side-link-roadmap", copy.sideLinks?.roadmap ? `${copy.sideLinks.roadmap} <span>&nearr;</span>` : undefined);

  setText("nav-link-overview", copy.nav?.overview);
  setText("nav-link-architecture", copy.nav?.architecture);
  setText("nav-link-blueprint", copy.nav?.blueprint);
  setText("nav-link-signals", copy.nav?.signals);
  setText("nav-link-explorer", copy.nav?.explorer);
  setText("nav-link-app", copy.nav?.app);
  setText("nav-link-roadmap", copy.nav?.roadmap);
  if (CURRENT_LOCALE === "pt-BR") {
    setText("nav-link-language", commonCopy().languageSwitchLabel || "EN");
    setHref("nav-link-language", commonCopy().siteLanguageHref || "./index.html");
    setHref("nav-link-app", "./app.html?lang=pt-BR");
    setHref("side-link-app", "./app.html?lang=pt-BR");
  }

  setText("hero-eyebrow", copy.hero?.eyebrow);
  setText("hero-link-primary", copy.hero?.primaryCta);
  setText("hero-link-secondary", copy.hero?.secondaryCta);
  if (CURRENT_LOCALE === "pt-BR") {
    setHref("hero-link-primary", "./app.html?lang=pt-BR");
  }

  setText("overview-eyebrow", copy.overview?.eyebrow);
  setHtml("overview-title", copy.overview?.titleHtml);
  setHtml("overview-body", copy.overview?.bodyHtml);
  setText("architecture-eyebrow", copy.architecture?.eyebrow);
  setText("architecture-title", copy.architecture?.title);
  setText("architecture-description", copy.architecture?.description);
  setText("build-eyebrow", copy.build?.eyebrow);
  setText("build-title", copy.build?.title);
  setText("build-question", copy.build?.question);
  setText("build-description", copy.build?.description);
  setText("signals-eyebrow", copy.signals?.eyebrow);
  setHtml("signals-title", copy.signals?.titleHtml);
  setText("blueprint-eyebrow", copy.blueprint?.eyebrow);
  setHtml("blueprint-title", copy.blueprint?.titleHtml);
  setText("explorer-eyebrow", copy.explorer?.eyebrow);
  setText("explorer-title", copy.explorer?.title);
  setText("asset-list-title", copy.explorer?.assetListTitle);
  setText("asset-list-description", copy.explorer?.assetListDescription);
  setText("selected-asset-title", copy.explorer?.selectedAssetTitle);
  setText("selected-asset-description", copy.explorer?.selectedAssetDescription);
  setText("narrative-list-title", copy.explorer?.narrativeListTitle);
  setText("narrative-list-description", copy.explorer?.narrativeListDescription);
  setText("selected-narrative-title", copy.explorer?.selectedNarrativeTitle);
  setText("selected-narrative-description", copy.explorer?.selectedNarrativeDescription);
  setText("snapshot-eyebrow", copy.snapshot?.eyebrow);
  setText("snapshot-title", copy.snapshot?.title);
  setText("snapshot-summary", copy.snapshot?.summary);
  setText("top-assets-title", copy.snapshot?.topAssetsTitle);
  setText("top-assets-description", copy.snapshot?.topAssetsDescription);
  setText("top-narratives-title", copy.snapshot?.topNarrativesTitle);
  setText("top-narratives-description", copy.snapshot?.topNarrativesDescription);
  setText("roadmap-eyebrow", copy.roadmap?.eyebrow);
  setHtml("roadmap-title", copy.roadmap?.titleHtml);
}

function applyAppStaticCopy() {
  const copy = appCopy();
  if (copy.metaTitle) {
    document.title = copy.metaTitle;
  }
  setMetaDescription(copy.metaDescription);
  setText("app-brand-subtitle", copy.brandSubtitle);
  setText("app-link-case-study", copy.caseStudyLink);
  setText("app-hero-eyebrow", copy.heroEyebrow);
  setText("app-leaderboard-title", copy.commandCenter?.leaderboardTitle);
  setText("app-leaderboard-description", copy.commandCenter?.leaderboardDescription);
  setText("app-rotation-title", copy.commandCenter?.rotationTitle);
  setText("app-rotation-description", copy.commandCenter?.rotationDescription);
  setText("app-alerts-title", copy.commandCenter?.alertsTitle);
  setText("app-alerts-description", copy.commandCenter?.alertsDescription);
  setText("app-attention-bars-title", copy.visuals?.attentionTitle);
  setText("app-attention-bars-description", copy.visuals?.attentionDescription);
  setText("app-narrative-bars-title", copy.visuals?.narrativeTitle);
  setText("app-narrative-bars-description", copy.visuals?.narrativeDescription);
  setText("app-rs-bars-title", copy.visuals?.rsTitle);
  setText("app-rs-bars-description", copy.visuals?.rsDescription);
  setText("app-explorer-eyebrow", copy.explorer?.eyebrow);
  setText("app-explorer-title", copy.explorer?.title);
  setText("asset-list-title", copy.explorer?.assetListTitle);
  setText("asset-list-description", copy.explorer?.assetListDescription);
  setText("selected-asset-title", copy.explorer?.selectedAssetTitle);
  setText("selected-asset-description", copy.explorer?.selectedAssetDescription);
  setText("narrative-list-title", copy.explorer?.narrativeListTitle);
  setText("narrative-list-description", copy.explorer?.narrativeListDescription);
  setText("selected-narrative-title", copy.explorer?.selectedNarrativeTitle);
  setText("selected-narrative-description", copy.explorer?.selectedNarrativeDescription);
  if (CURRENT_LOCALE === "pt-BR") {
    setText("app-link-language", commonCopy().languageSwitchLabel || "EN");
    setHref("app-link-language", commonCopy().appLanguageHref || "./app.html");
    setHref("app-link-case-study", "./index.html?lang=pt-BR");
    setHref("app-brand-link", "./index.html?lang=pt-BR");
  }
}

function renderExplorer(data) {
  const explorerLabels = commonCopy().explorer || {};
  const state = {
    rows: data.asset_explorer_rows.slice(),
    filteredRows: data.asset_explorer_rows.slice(),
    selectedSymbol: data.asset_explorer_rows[0]?.symbol || null,
    compareSymbol: "none",
    mode: "assets",
    selectedNarrative: data.narrative_explorer_rows[0]?.narrative || null,
  };

  const assetsModeButton = document.getElementById("explorer-mode-assets");
  const narrativesModeButton = document.getElementById("explorer-mode-narratives");
  const assetModePanel = document.getElementById("asset-mode-panel");
  const narrativeModePanel = document.getElementById("narrative-mode-panel");
  const narrativeFilter = document.getElementById("narrative-filter");
  const sortFilter = document.getElementById("sort-filter");
  const regimeFilter = document.getElementById("regime-filter");
  const compareFilter = document.getElementById("compare-asset-filter");
  const assetList = document.getElementById("asset-list");
  const assetDetail = document.getElementById("asset-detail");
  const comparePanel = document.getElementById("compare-panel");
  const narrativePulse = document.getElementById("narrative-pulse");
  const narrativeList = document.getElementById("narrative-list");
  const narrativeDetail = document.getElementById("narrative-detail");

  if (assetsModeButton) {
    assetsModeButton.textContent = explorerLabels.modeAssets || "Assets";
  }
  if (narrativesModeButton) {
    narrativesModeButton.textContent = explorerLabels.modeNarratives || "Narratives";
  }

  setText("label-narrative-filter", explorerLabels.filterNarrative || "Narrative");
  setText("label-sort-filter", explorerLabels.filterSort || "Sort by");
  setText("label-regime-filter", explorerLabels.filterRegime || "Regime");
  setText("label-compare-filter", explorerLabels.filterCompare || "Compare to");

  if (sortFilter?.options.length >= 3) {
    sortFilter.options[0].text = explorerLabels.sortAttention || "Attention";
    sortFilter.options[1].text = explorerLabels.sortRs7d || "RS 7d";
    sortFilter.options[2].text = explorerLabels.sortVolume || "Volume";
  }
  if (regimeFilter?.options.length >= 4) {
    regimeFilter.options[0].text = explorerLabels.allRegimes || "All regimes";
    regimeFilter.options[1].text = explorerLabels.bullish || "Bullish attention";
    regimeFilter.options[2].text = explorerLabels.bearish || "Bearish attention";
    regimeFilter.options[3].text = explorerLabels.mixed || "Mixed attention";
  }

  const narratives = ["all", ...new Set(data.asset_explorer_rows.map((row) => row.narrative))];
  narratives.forEach((narrative) => {
    const option = document.createElement("option");
    option.value = narrative;
    option.textContent = narrative === "all" ? (explorerLabels.allNarratives || "All narratives") : formatNarrativeLabel(narrative);
    narrativeFilter.appendChild(option);
  });

  const compareBase = document.createElement("option");
  compareBase.value = "none";
  compareBase.textContent = explorerLabels.noComparison || "No comparison";
  compareFilter.appendChild(compareBase);
  data.asset_explorer_rows.forEach((row) => {
    const option = document.createElement("option");
    option.value = row.symbol;
    option.textContent = row.symbol;
    compareFilter.appendChild(option);
  });

  function syncSelection() {
    const exists = state.filteredRows.some((row) => row.symbol === state.selectedSymbol);
    if (!exists) {
      state.selectedSymbol = state.filteredRows[0]?.symbol || null;
    }
  }

  function renderList() {
    assetList.innerHTML = "";
    state.filteredRows.forEach((row) => {
      const item = buildAssetItem(row, row.symbol === state.selectedSymbol);
      item.addEventListener("click", () => {
        state.selectedSymbol = row.symbol;
        renderList();
        renderDetail();
      });
      assetList.appendChild(item);
    });
  }

  function renderNarrativeList() {
    narrativeList.innerHTML = "";
    data.narrative_explorer_rows.forEach((row) => {
      const item = buildNarrativeItem(row, row.narrative === state.selectedNarrative);
      item.addEventListener("click", () => {
        state.selectedNarrative = row.narrative;
        renderNarrativeList();
        renderNarrativeDetail();
      });
      narrativeList.appendChild(item);
    });
  }

  function renderDetail() {
    assetDetail.innerHTML = "";
    const selected = state.filteredRows.find((row) => row.symbol === state.selectedSymbol);
    assetDetail.appendChild(buildAssetDetail(selected));

    comparePanel.innerHTML = "";
    const compareRow = state.rows.find((row) => row.symbol === state.compareSymbol);
    comparePanel.appendChild(buildComparePanel(selected, compareRow));

    narrativePulse.innerHTML = "";
    const narrativeRow = data.narrative_explorer_rows.find((row) => row.narrative === selected?.narrative);
    const peerRows = state.rows
      .filter((row) => row.narrative === selected?.narrative)
      .sort((left, right) => right.attention_score - left.attention_score);
    narrativePulse.appendChild(buildNarrativePulsePanel(narrativeRow, peerRows));
  }

  function renderNarrativeDetail() {
    narrativeDetail.innerHTML = "";
    const selected = data.narrative_explorer_rows.find((row) => row.narrative === state.selectedNarrative);
    const peerRows = state.rows
      .filter((row) => row.narrative === selected?.narrative)
      .sort((left, right) => right.attention_score - left.attention_score);
    narrativeDetail.appendChild(buildNarrativeDetail(selected, peerRows));
  }

  function syncModeUi() {
    const assetMode = state.mode === "assets";
    assetModePanel.classList.toggle("is-hidden", !assetMode);
    narrativeModePanel.classList.toggle("is-hidden", assetMode);
    assetsModeButton.classList.toggle("is-active", assetMode);
    narrativesModeButton.classList.toggle("is-active", !assetMode);
  }

  function applyFilters() {
    state.filteredRows = state.rows.filter((row) => {
      const narrativePass = narrativeFilter.value === "all" || row.narrative === narrativeFilter.value;
      const regimePass = regimeFilter.value === "all" || row.regime_tag === regimeFilter.value;
      return narrativePass && regimePass;
    });
    state.filteredRows.sort((left, right) => {
      const key = sortFilter.value;
      return (Number(right[key] || 0) - Number(left[key] || 0));
    });
    syncSelection();
    renderList();
    renderDetail();
  }

  narrativeFilter.addEventListener("change", applyFilters);
  sortFilter.addEventListener("change", applyFilters);
  regimeFilter.addEventListener("change", applyFilters);
  compareFilter.addEventListener("change", () => {
    state.compareSymbol = compareFilter.value;
    renderDetail();
  });

  assetsModeButton.addEventListener("click", () => {
    state.mode = "assets";
    syncModeUi();
  });

  narrativesModeButton.addEventListener("click", () => {
    state.mode = "narratives";
    syncModeUi();
  });

  applyFilters();
  renderNarrativeList();
  renderNarrativeDetail();
  syncModeUi();
}

function renderCaseStudyPage() {
  if (!document.getElementById("hero-title")) {
    return;
  }

  const data = window.CMIL_SITE_DATA;
  if (!data) {
    return;
  }
  const copy = siteCopy();
  const overviewCards = copy.overview?.cards || [
    ["Market structure", "Spot, derivatives, and on-chain context combined into one interpretable decision layer.", "health"],
    ["Databricks direction", "Built with medallion architecture logic so the local flow can evolve into jobs and Delta-backed layers.", "models"],
    ["Product framing", "Designed as a research operating layer, not as another thin crypto dashboard.", "ops"],
    ["Interactive future", "The embedded asset explorer is the first step toward a fuller live platform experience.", "health"],
  ];
  const pipelineNodes = copy.architecture?.pipelineNodes || [
    ["Bronze", "Public source capture", "Raw snapshots from CoinGecko, Binance, and DefiLlama preserved with extraction context.", "health"],
    ["Silver", "Normalized analytical tables", "Market, derivatives, and on-chain records shaped into cleaner reusable structures.", "ops"],
    ["Features", "Cross-surface signal layer", "Relative strength, open interest, funding, and capital-efficiency features prepared for scoring.", "models"],
    ["Gold", "Attention outputs", "Asset ranking, narrative aggregation, and interpretable drivers exported for product surfaces.", "health"],
  ];
  const buildStatsCopy = copy.build?.stats || [
    ["Pipeline layers", "4", "Bronze, silver, features, and gold shaped for lakehouse evolution."],
    ["Current assets", String(data.overview.asset_count), "Curated asset universe currently exposed in the public gold snapshot."],
    ["Narratives", String(data.overview.narrative_count), "Narrative buckets mapped into the first public analytical surface."],
    ["Explorer mode", "v1", "First embedded product interaction layer built on top of the same exported data."],
  ];
  const buildDetailsCopy = copy.build?.details || [
    ["Bundle-first deployment path", "The repo carries a Databricks bundle scaffold so workspace deployment becomes an extension of the same codebase instead of a separate manual setup step.", "health"],
    ["Pipeline orchestration path", "The bronze, silver, features, and gold stages are already separated as runnable scripts, which maps cleanly into Databricks Jobs or Lakeflow-style orchestration later.", "ops"],
    ["Feature layer design", "Signals such as relative strength, open interest, funding, and capital efficiency are modeled as reusable analytical components rather than one-off dashboard calculations.", "models"],
    ["App construction path", "The static case-study page and the embedded asset explorer share one exported site payload, which is the right product boundary for evolving toward a richer interactive application.", "health"],
  ];
  const roadmapItems = copy.roadmap?.items || [
    ["Phase 01", "in progress", "Expand asset coverage", "Increase the tracked universe and deepen derivatives plus on-chain coverage on a per-asset basis."],
    ["Phase 02", "planned", "Promote the pipeline", "Move from local JSONL artifacts to Delta-backed scheduled jobs with a more Databricks-native execution model."],
    ["Phase 03", "planned", "Deepen the product surface", "Add richer drilldowns, narrative rotation views, and stronger explanation layers inside the app."],
    ["Phase 04", "planned", "Improve public publishing", "Strengthen multilingual presentation and make the app feel even more like a research operating layer."],
  ];

  applySiteStaticCopy(data);
  const driverMix = data.overview?.driver_mix || {};
  const runMetadata = data.run_metadata || {};

  document.getElementById("hero-title").textContent = data.headline.title;
  document.getElementById("hero-subtitle").textContent = CURRENT_LOCALE === "pt-BR"
    ? "Uma plataforma de inteligência de mercado cripto orientada a Databricks para destacar quais ativos e narrativas merecem atenção, e por quê."
    : data.headline.subtitle;
  document.getElementById("generated-at").textContent = formatGeneratedAt(data.generated_at);

  const heroStats = document.getElementById("hero-stats");
  heroStats.append(
    buildHeroMetric(
      CURRENT_LOCALE === "pt-BR" ? "Ativos cobertos" : "Assets tracked",
      data.overview.asset_count,
      CURRENT_LOCALE === "pt-BR" ? "universo curado de atenção" : "curated attention universe",
    ),
    buildHeroMetric(
      CURRENT_LOCALE === "pt-BR" ? "Narrativas mapeadas" : "Narratives mapped",
      data.overview.narrative_count,
      CURRENT_LOCALE === "pt-BR" ? "cobertura temática inicial" : "seeded thematic coverage",
    ),
    buildHeroMetric(
      CURRENT_LOCALE === "pt-BR" ? "Regimes baixistas" : "Bearish regimes",
      data.overview.bearish_count,
      CURRENT_LOCALE === "pt-BR" ? "tag direcional atual da gold layer" : "current gold-layer directional tag",
    ),
    buildHeroMetric(
      CURRENT_LOCALE === "pt-BR" ? "Driver lider" : "Leading driver",
      formatDriverSummary(driverMix),
      CURRENT_LOCALE === "pt-BR" ? "mistura dominante de sinais no snapshot atual" : "dominant signal mix in the current snapshot",
    ),
  );

  const overview = document.getElementById("overview");
  overview.innerHTML = "";
  overviewCards.forEach((item, index) => {
    overview.appendChild(buildOverviewCard(index, item[0], item[1], item[2]));
  });

  const pipelineStrip = document.getElementById("pipeline-strip");
  pipelineStrip.innerHTML = "";
  pipelineNodes.forEach((item) => {
    pipelineStrip.appendChild(buildPipelineNode(item[0], item[1], item[2], item[3]));
  });

  const architecture = document.getElementById("architecture");
  data.architecture.forEach((line, index) => architecture.appendChild(buildArchitectureCard(line, index)));

  const buildStats = document.getElementById("build-stats");
  buildStats.innerHTML = "";
  buildStatsCopy.forEach((item) => {
    const value = item[1] === "dynamic_asset_count" ? String(data.overview.asset_count) : item[1] === "dynamic_narrative_count" ? String(data.overview.narrative_count) : item[1];
    buildStats.appendChild(buildFeaturedStat(item[0], value, item[2]));
  });
  buildStats.appendChild(
    buildFeaturedStat(
      CURRENT_LOCALE === "pt-BR" ? "Execucao" : "Execution",
      `Run ${runMetadata.run_id || "local-run"}`,
      `Artifact ${runMetadata.artifact_version || "v1"} / Manifest ${formatManifestPath(runMetadata.manifest_path)}`,
    ),
  );

  const buildDetails = document.getElementById("build-details");
  buildDetails.innerHTML = "";
  buildDetailsCopy.forEach((item) => {
    buildDetails.appendChild(buildBuildDetail(item[0], item[1], item[2]));
  });

  const signals = document.getElementById("signals");
  const tones = ["health", "models", "ops", "health"];
  data.signals.forEach((signal, index) => signals.appendChild(buildSignalCard(signal, tones[index % tones.length])));

  const blueprintGrid = document.getElementById("blueprint-grid");
  data.databricks_blueprint.forEach((item, index) => {
    blueprintGrid.appendChild(buildBlueprintCard(item, tones[index % tones.length]));
  });

  document.getElementById("top-assets").appendChild(buildAssetTable(data.top_assets));
  document.getElementById("top-narratives").appendChild(buildNarrativeTable(data.top_narratives));

  const roadmapGrid = document.getElementById("roadmap-grid");
  roadmapGrid.innerHTML = "";
  roadmapItems.forEach((item) => {
    roadmapGrid.appendChild(buildRoadmapCard(item));
  });

  renderExplorer(data);
  activateRevealAnimations();
}

function renderAppPage() {
  const shell = document.getElementById("app-shell");
  if (!shell) {
    return;
  }

  const data = window.CMIL_SITE_DATA;
  if (!data) {
    return;
  }
  const copy = appCopy();

  applyAppStaticCopy();

  document.getElementById("app-hero-title").textContent = `${data.headline.title} App`;
  document.getElementById("app-hero-subtitle").textContent = copy.heroSubtitle
    || "A dedicated interactive view on top of the exported gold-layer snapshot, designed as the next step beyond the portfolio case study.";
  document.getElementById("generated-at").textContent = formatGeneratedAt(data.generated_at);

  const appKpis = document.getElementById("app-kpis");
  appKpis.append(
    buildHeroMetric(
      CURRENT_LOCALE === "pt-BR" ? "Ativos cobertos" : "Assets tracked",
      data.overview.asset_count,
      CURRENT_LOCALE === "pt-BR" ? "universo exportado atual" : "current exported universe",
    ),
    buildHeroMetric(
      CURRENT_LOCALE === "pt-BR" ? "Narrativas" : "Narratives",
      data.narrative_explorer_rows.length,
      CURRENT_LOCALE === "pt-BR" ? "visões analíticas por cluster" : "cluster-level analytical views",
    ),
    buildHeroMetric(
      CURRENT_LOCALE === "pt-BR" ? "Principal ativo" : "Top asset",
      data.top_assets[0]?.symbol || "N/A",
      CURRENT_LOCALE === "pt-BR" ? "líder atual de atenção" : "current attention leader",
    ),
    buildHeroMetric(
      CURRENT_LOCALE === "pt-BR" ? "Principal narrativa" : "Top narrative",
      formatNarrativeLabel(data.top_narratives[0]?.narrative || "N/A"),
      CURRENT_LOCALE === "pt-BR" ? "líder atual por agregação" : "current aggregated leader",
    ),
  );

  renderAppRefreshStatus(data);
  renderAppInsights(data);
  renderAppCommandCenter(data);
  renderAppVisuals(data);
  renderExplorer(data);
}

renderCaseStudyPage();
renderAppPage();
