import { FormEvent, useEffect, useMemo, useState } from "react";
import type { CSSProperties } from "react";

import { checkCourtesy, replayScenario, submitDecision } from "./api";
import type { CoordinationAlert, CourtesyAssessment, ReviewStatus } from "./types";

const SCENARIOS = [
  { value: "coordinated-campaign", label: "Koordineli paylaş-sil ağı" },
  { value: "announced-campaign", label: "Duyurulmuş meşru kampanya" },
  { value: "organic-discussion", label: "Organik tartışma" },
];

const STATUS_LABELS: Record<ReviewStatus, string> = {
  pending: "İnceleme bekliyor",
  confirmed: "Koordinasyon doğrulandı",
  dismissed: "Alarm reddedildi",
  needs_more_data: "Ek veri gerekli",
};

const RISK_LABELS = {
  low: "Düşük",
  medium: "Orta",
  high: "Yüksek",
  critical: "Kritik",
};

function formatTime(value: string): string {
  return new Intl.DateTimeFormat("tr-TR", {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  }).format(new Date(value));
}

function targetLabel(value: string): string {
  const [kind, ...rest] = value.split(":");
  const labels: Record<string, string> = { target: "Hedef", url: "Bağlantı", tag: "Etiket" };
  return `${labels[kind] ?? "Nesne"}: ${rest.join(":")}`;
}

function App() {
  const [activeView, setActiveView] = useState<"network" | "courtesy">("network");
  const [scenario, setScenario] = useState(SCENARIOS[0].value);
  const [alerts, setAlerts] = useState<CoordinationAlert[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [reason, setReason] = useState("");
  const [decisionStatus, setDecisionStatus] = useState<Exclude<ReviewStatus, "pending">>(
    "confirmed",
  );
  const [saving, setSaving] = useState(false);
  const [notice, setNotice] = useState("");
  const [courtesyText, setCourtesyText] = useState("Bu fikri s 4 l 4 k buluyorum.");
  const [courtesyResult, setCourtesyResult] = useState<CourtesyAssessment | null>(null);
  const [checkingCourtesy, setCheckingCourtesy] = useState(false);

  const selected = useMemo(
    () => alerts.find((alert) => alert.alert_id === selectedId) ?? alerts[0] ?? null,
    [alerts, selectedId],
  );

  async function runScenario(nextScenario: string) {
    setLoading(true);
    setError("");
    setNotice("");
    try {
      const result = await replayScenario(nextScenario);
      setAlerts(result.alerts);
      setSelectedId(result.alerts[0]?.alert_id ?? null);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Beklenmeyen bir hata oluştu.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void runScenario(SCENARIOS[0].value);
  }, []);

  async function handleDecision(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selected || reason.trim().length < 3) return;
    setSaving(true);
    setNotice("");
    try {
      const decision = await submitDecision(selected.alert_id, decisionStatus, reason.trim());
      setAlerts((current) =>
        current.map((alert) =>
          alert.alert_id === selected.alert_id ? { ...alert, status: decision.status } : alert,
        ),
      );
      setReason("");
      setNotice("Gerekçeli karar denetim kaydına eklendi.");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Karar kaydedilemedi.");
    } finally {
      setSaving(false);
    }
  }

  async function handleCourtesyCheck(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!courtesyText.trim()) return;
    setCheckingCourtesy(true);
    setError("");
    try {
      setCourtesyResult(await checkCourtesy(courtesyText.trim()));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Nezaket kontrolü tamamlanamadı.");
    } finally {
      setCheckingCourtesy(false);
    }
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand" aria-label="SAĞDUYU moderasyon merkezi">
          <span className="brand-mark" aria-hidden="true">S</span>
          <span>
            <strong>SAĞDUYU</strong>
            <small>Sosyal bağışıklık katmanı</small>
          </span>
        </div>
        <nav className="product-nav" aria-label="Ürün alanları" role="tablist">
          <button
            aria-controls="network-panel"
            aria-selected={activeView === "network"}
            className={activeView === "network" ? "is-active" : ""}
            id="network-tab"
            onClick={() => setActiveView("network")}
            role="tab"
            type="button"
          >
            <span className="nav-icon nav-icon--network" aria-hidden="true" />
            Ağ inceleme
          </button>
          <button
            aria-controls="courtesy-panel"
            aria-selected={activeView === "courtesy"}
            className={activeView === "courtesy" ? "is-active" : ""}
            id="courtesy-tab"
            onClick={() => setActiveView("courtesy")}
            role="tab"
            type="button"
          >
            <span className="nav-icon nav-icon--courtesy" aria-hidden="true" />
            Nezaket katmanı
          </button>
        </nav>
        <div className="system-state"><span aria-hidden="true" /> Sistem hazır</div>
      </header>

      <main>
        {error && <div className="message message--error" role="alert">{error}</div>}
        {notice && <div className="message message--success" role="status">{notice}</div>}

        {activeView === "network" ? (
          <section
            aria-labelledby="page-title"
            aria-live="polite"
            id="network-panel"
            role="tabpanel"
          >
            <header className="view-bar">
              <div className="view-title">
                <p className="eyebrow">KOORDİNASYON İNCELEMESİ</p>
                <h1 id="page-title">Kanıta dayalı moderasyon çalışma alanı</h1>
                <p>Hesapların birlikte hareket etme örüntülerini inceleyin; kararı gerekçesiyle kaydedin.</p>
              </div>
              <div className="scenario-control">
                <label htmlFor="scenario">İnceleme senaryosu</label>
                <div>
                  <select
                    id="scenario"
                    value={scenario}
                    onChange={(event) => setScenario(event.target.value)}
                  >
                    {SCENARIOS.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}
                  </select>
                  <button type="button" onClick={() => void runScenario(scenario)} disabled={loading}>
                    {loading ? "Analiz ediliyor…" : "Analizi çalıştır"}
                  </button>
                </div>
              </div>
            </header>

            <div className="workspace">
          <aside className="queue" aria-label="Alarm kuyruğu">
            <div className="section-heading">
              <div><p className="eyebrow">ALARM KUYRUĞU</p><h2>İncelenecek ağlar</h2></div>
              <span className="count">{alerts.length}</span>
            </div>

            {loading ? (
              <div className="empty-state" role="status"><span className="loader" />Ağ örüntüleri çıkarılıyor…</div>
            ) : alerts.length === 0 ? (
              <div className="empty-state"><strong>Kritik örüntü bulunmadı</strong><span>Bu senaryo alarm eşiğini aşmadı.</span></div>
            ) : (
              <div className="alert-list">
                {alerts.map((alert) => (
                  <button
                    className={`alert-row ${selected?.alert_id === alert.alert_id ? "is-active" : ""}`}
                    key={alert.alert_id}
                    onClick={() => setSelectedId(alert.alert_id)}
                    type="button"
                  >
                    <span className={`risk-dot risk-dot--${alert.risk_level}`} aria-hidden="true" />
                    <span className="alert-row__body">
                      <strong>{alert.account_ids.length} hesaplı ağ</strong>
                      <small>{alert.targets[0] ? targetLabel(alert.targets[0].key) : "Ortak hedef yok"}</small>
                      <span className={`status status--${alert.status}`}>{STATUS_LABELS[alert.status]}</span>
                    </span>
                    <span className="alert-score">{Math.round(alert.risk_score)}<small>/100</small></span>
                  </button>
                ))}
              </div>
            )}
          </aside>

          <section className="evidence" aria-label="Alarm kanıtları">
            {!selected ? (
              <div className="empty-state empty-state--large"><strong>İncelenecek alarm yok</strong><span>Başka bir senaryo çalıştırabilir veya yeni olay gönderebilirsiniz.</span></div>
            ) : (
              <>
                <div className="evidence-header">
                  <div>
                    <div className="badge-row">
                      <span className={`risk-badge risk-badge--${selected.risk_level}`}>{RISK_LABELS[selected.risk_level]} risk</span>
                      {selected.synthetic && <span className="neutral-badge">Sentetik demo</span>}
                      <span className={`status status--${selected.status}`}>{STATUS_LABELS[selected.status]}</span>
                    </div>
                    <h2>Koordinasyon adayı</h2>
                    <p>{selected.summary}</p>
                  </div>
                  <div
                    className={`score-ring score-ring--${selected.risk_level}`}
                    aria-label={`Risk skoru ${selected.risk_score}`}
                    style={{ "--risk-score": `${selected.risk_score}%` } as CSSProperties}
                  >
                    <strong>{Math.round(selected.risk_score)}</strong><span>risk skoru</span>
                  </div>
                </div>

                <div className="metric-grid">
                  <article><span>Hesap</span><strong>{selected.graph.node_count}</strong><small>birlikte inceleniyor</small></article>
                  <article><span>Güçlü bağ</span><strong>{selected.graph.edge_count}</strong><small>eşik üzeri ilişki</small></article>
                  <article><span>Ağ yoğunluğu</span><strong>%{Math.round(selected.graph.density * 100)}</strong><small>olası bağların oranı</small></article>
                  <article><span>Olay</span><strong>{selected.event_ids.length}</strong><small>kanıt penceresinde</small></article>
                </div>

                {selected.context_evidence.length > 0 && (
                  <aside className="context-evidence" aria-labelledby="context-evidence-title">
                    <div className="context-evidence__icon" aria-hidden="true">i</div>
                    <div>
                      <p className="eyebrow">BAĞLAM KANITI - SKORA ETKİ ETMEZ</p>
                      <h3 id="context-evidence-title">{selected.context_evidence[0].label}</h3>
                      <p>{selected.context_evidence[0].explanation}</p>
                      <a href={selected.context_evidence[0].source_url} target="_blank" rel="noreferrer">
                        Duyuru kaynağını incele
                      </a>
                    </div>
                    <dl>
                      <div><dt>Hesap</dt><dd>{selected.context_evidence[0].account_count}</dd></div>
                      <div><dt>Olay</dt><dd>{selected.context_evidence[0].event_count}</dd></div>
                    </dl>
                  </aside>
                )}

                <div className="evidence-grid">
                  <article className="panel signals-panel">
                    <div className="panel-title"><div><p className="eyebrow">AÇIKLANABİLİR SKOR</p><h3>Sinyal katkıları</h3></div><span>v{selected.engine_version}</span></div>
                    <div className="signal-list">
                      {selected.signals.map((signal) => (
                        <div className="signal" key={signal.key}>
                          <div><strong>{signal.label}</strong><span>+{signal.contribution.toFixed(1)} puan</span></div>
                          <div className="signal-track"><span style={{ width: `${signal.value * 100}%` }} /></div>
                          <p>{signal.explanation}</p>
                        </div>
                      ))}
                    </div>
                  </article>

                  <article className="panel network-panel">
                    <div className="panel-title"><div><p className="eyebrow">İLİŞKİ HARİTASI</p><h3>Hesap ağı</h3></div><span>{selected.graph.edge_count} bağ</span></div>
                    <div className="network" aria-label={`${selected.graph.node_count} hesaplı ağ görünümü`}>
                      <div className="network-hub">ORTAK<br />HEDEF</div>
                      {selected.account_ids.slice(0, 8).map((account, index) => (
                        <div className={`network-node network-node--${index}`} key={account} title={account}>{index + 1}</div>
                      ))}
                    </div>
                    <div className="account-list" aria-label="İlişkili hesaplar">
                      {selected.account_ids.slice(0, 8).map((account) => <span key={account}>{account}</span>)}
                    </div>
                  </article>

                  <article className="panel targets-panel">
                    <div className="panel-title"><div><p className="eyebrow">ORTAK NESNELER</p><h3>Hedef kanıtları</h3></div></div>
                    <div className="target-table">
                      {selected.targets.slice(0, 6).map((target) => (
                        <div key={target.key}><strong>{targetLabel(target.key)}</strong><span>{target.account_count} hesap</span><span>{target.event_count} olay</span></div>
                      ))}
                    </div>
                  </article>

                  <article className="panel timeline-panel">
                    <div className="panel-title"><div><p className="eyebrow">ZAMAN PENCERESİ</p><h3>Hareket özeti</h3></div></div>
                    <div className="timeline">
                      <div><span /> <p><small>Başlangıç</small><strong>{formatTime(selected.window_start)}</strong></p></div>
                      <div className="timeline-line"><i /><b>{selected.event_ids.length} olay</b></div>
                      <div><span /> <p><small>Bitiş</small><strong>{formatTime(selected.window_end)}</strong></p></div>
                    </div>
                  </article>
                </div>

                <form className="decision-panel" onSubmit={handleDecision}>
                  <div><p className="eyebrow">İNSAN KARARI</p><h3>İncelemeyi sonuçlandır</h3><p>Sistem yalnızca karar desteği sunar; yaptırım otomatik uygulanmaz.</p></div>
                  <fieldset>
                    <legend>Karar</legend>
                    <div className="decision-options">
                      {(["confirmed", "dismissed", "needs_more_data"] as const).map((status) => (
                        <label key={status}><input type="radio" name="decision" value={status} checked={decisionStatus === status} onChange={() => setDecisionStatus(status)} /><span>{STATUS_LABELS[status]}</span></label>
                      ))}
                    </div>
                  </fieldset>
                  <label className="reason-field" htmlFor="reason">Karar gerekçesi<textarea id="reason" value={reason} onChange={(event) => setReason(event.target.value)} minLength={3} required placeholder="İncelediğiniz sinyalleri ve karar nedenini yazın…" /></label>
                  <button className="primary-action" type="submit" disabled={saving || reason.trim().length < 3}>{saving ? "Kaydediliyor…" : "Gerekçeli kararı kaydet"}</button>
                </form>
              </>
            )}
          </section>
            </div>
          </section>
        ) : (
          <section
            aria-labelledby="courtesy-title"
            id="courtesy-panel"
            role="tabpanel"
          >
            <div className="courtesy-view">
              <header className="courtesy-hero">
                <p className="eyebrow">GÖNDERİ ÖNCESİ NEZAKET KATMANI</p>
                <h1 id="courtesy-title">Düşünün, düzenleyin, seçiminizi koruyun.</h1>
                <p>
                  Türkçedeki karakter maskeleme girişimlerini açıklar ve paylaşmadan önce
                  düşünme fırsatı verir. İçeriğiniz sizin onayınız olmadan değiştirilmez.
                </p>
                <div className="principle-list" aria-label="Nezaket katmanı ilkeleri">
                  <span><b aria-hidden="true">01</b> Açıklanabilir uyarı</span>
                  <span><b aria-hidden="true">02</b> Kullanıcı kontrolü</span>
                  <span><b aria-hidden="true">03</b> Otomatik yaptırım yok</span>
                </div>
              </header>

              <div className="courtesy-workspace">
                <form className="composer-card" onSubmit={handleCourtesyCheck}>
                  <div className="composer-heading">
                    <div>
                      <p className="eyebrow">YENİ GÖNDERİ</p>
                      <h2>Paylaşımınızı hazırlayın</h2>
                    </div>
                    <span>{courtesyText.length} / 5000</span>
                  </div>
                  <label htmlFor="courtesy-text">Gönderi metni</label>
                  <textarea
                    id="courtesy-text"
                    maxLength={5000}
                    onChange={(event) => {
                      setCourtesyText(event.target.value);
                      setCourtesyResult(null);
                    }}
                    required
                    value={courtesyText}
                  />
                  <div className="composer-footer">
                    <p>Kontrol yalnızca bu metin üzerinde çalışır.</p>
                    <button type="submit" disabled={checkingCourtesy}>
                      {checkingCourtesy ? "Kontrol ediliyor…" : "Nezaket kontrolü"}
                    </button>
                  </div>

                  {courtesyResult && (
                    <div className={`courtesy-result courtesy-result--${courtesyResult.level}`} role="status">
                      <div className="courtesy-result__summary">
                        <span className="courtesy-score">{Math.round(courtesyResult.risk_score)}</span>
                        <p>
                          <small>NEZAKET DEĞERLENDİRMESİ</small>
                          <strong>
                            {courtesyResult.should_warn
                              ? courtesyResult.warning
                              : "Belirgin bir nezaket riski bulunmadı."}
                          </strong>
                          <span>{courtesyResult.disclaimer}</span>
                        </p>
                      </div>
                      {courtesyResult.matches.length > 0 && (
                        <div className="match-list" aria-label="Açıklanan ifadeler">
                          {courtesyResult.matches.map((match) => (
                            <span key={match.canonical_form}>
                              <b>{match.canonical_form}</b>{match.category}
                            </span>
                          ))}
                        </div>
                      )}
                      <div className="courtesy-actions">
                        <button type="button" onClick={() => setCourtesyResult(null)}>Metni düzenle</button>
                        <button
                          type="button"
                          onClick={() => setNotice("Kullanıcı tercihi korundu; demo gönderimi engellenmedi.")}
                        >
                          Yine de devam et
                        </button>
                      </div>
                    </div>
                  )}
                </form>

                <aside className="courtesy-guide" aria-label="Değerlendirme yaklaşımı">
                  <p className="eyebrow">NASIL ÇALIŞIR?</p>
                  <h2>Kararı sizin yerinize vermez.</h2>
                  <ol>
                    <li><span>1</span><div><strong>Metni çözümler</strong><p>Ayrık harfleri, sayı ile değiştirilmiş karakterleri ve görünmez işaretleri tanır.</p></div></li>
                    <li><span>2</span><div><strong>Nedeni açıklar</strong><p>Uyarıya hangi ifadenin ve dönüşümün yol açtığını görünür kılar.</p></div></li>
                    <li><span>3</span><div><strong>Seçimi size bırakır</strong><p>Düzenleyebilir veya uyarıyı gördükten sonra paylaşmaya devam edebilirsiniz.</p></div></li>
                  </ol>
                  <div className="privacy-note">
                    <span aria-hidden="true">✓</span>
                    <p><strong>Şeffaf varsayılan</strong>Metin engellenmez; kullanıcı kararı korunur.</p>
                  </div>
                </aside>
              </div>
            </div>
          </section>
        )}
      </main>
    </div>
  );
}

export default App;
