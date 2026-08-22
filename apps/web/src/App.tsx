import { FormEvent, useEffect, useMemo, useState } from "react";
import type { CSSProperties } from "react";

import { replayScenario, submitDecision } from "./api";
import type { CoordinationAlert, ReviewStatus } from "./types";

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

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand" aria-label="SAĞDUYU moderasyon merkezi">
          <span className="brand-mark" aria-hidden="true">S</span>
          <span>
            <strong>SAĞDUYU</strong>
            <small>Moderasyon Merkezi</small>
          </span>
        </div>
        <div className="system-state"><span aria-hidden="true" /> Sistem hazır</div>
      </header>

      <main>
        <section className="intro" aria-labelledby="page-title">
          <div>
            <p className="eyebrow">KOORDİNASYON İNCELEME ALANI</p>
            <h1 id="page-title">Sinyali görün, kanıtla karar verin.</h1>
            <p>İçerik doğruluğunu değil, hesapların birlikte hareket etme örüntülerini inceler.</p>
          </div>
          <div className="scenario-control">
            <label htmlFor="scenario">Demo senaryosu</label>
            <div>
              <select
                id="scenario"
                value={scenario}
                onChange={(event) => setScenario(event.target.value)}
              >
                {SCENARIOS.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}
              </select>
              <button type="button" onClick={() => void runScenario(scenario)} disabled={loading}>
                {loading ? "Analiz ediliyor…" : "Senaryoyu çalıştır"}
              </button>
            </div>
          </div>
        </section>

        {error && <div className="message message--error" role="alert">{error}</div>}
        {notice && <div className="message message--success" role="status">{notice}</div>}

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
      </main>
    </div>
  );
}

export default App;
