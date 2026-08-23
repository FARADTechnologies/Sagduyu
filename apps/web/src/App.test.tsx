import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import App from "./App";

const alert = {
  alert_id: "alert_demo",
  created_at: "2025-06-15T09:12:00Z",
  window_start: "2025-06-15T09:00:00Z",
  window_end: "2025-06-15T09:12:00Z",
  risk_score: 82,
  risk_level: "high",
  summary: "8 hesap, 24 olay ve 3 ortak hedefte koordinasyon adayı oluşturdu.",
  account_ids: ["account_1", "account_2", "account_3"],
  event_ids: ["event_1", "event_2", "event_3"],
  signals: [
    { key: "temporal", label: "Eşzamanlılık", value: 0.9, weight: 0.22, contribution: 19.8, explanation: "Kısa zaman aralığı." },
  ],
  targets: [{ key: "tag:ortakcagri", event_count: 3, account_count: 3 }],
  graph: { node_count: 3, edge_count: 3, density: 1, strongest_pairs: [] },
  context_evidence: [],
  status: "pending",
  synthetic: true,
  engine_version: "0.1.0",
};

describe("moderasyon merkezi", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      if (String(input).includes("courtesy-check")) {
        return new Response(JSON.stringify({
          normalized_text: "bu fikir salak",
          transformations: ["separated_letters", "leetspeak"],
          risk_score: 58,
          level: "review",
          should_warn: true,
          warning: "Bu ifade incitici algılanabilir.",
          matches: [{ canonical_form: "salak", category: "kişiye yönelik aşağılama", contribution: 58 }],
          user_may_continue: true,
          method: "transparent_demo_baseline_v1",
          disclaimer: "Demo tabanıdır.",
        }), { status: 200 });
      }
      if (init?.body) {
        return new Response(JSON.stringify({ status: "confirmed" }), { status: 201 });
      }
      return new Response(JSON.stringify({ scenario: "coordinated-campaign", event_count: 24, alert_count: 1, alerts: [alert] }), { status: 200 });
    }));
  });

  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
  });

  it("alarm kanıtlarını ve insan kararı uyarısını gösterir", async () => {
    render(<App />);

    expect(await screen.findByRole("heading", { name: "Koordinasyon adayı" })).toBeInTheDocument();
    expect(screen.getByText("Eşzamanlılık")).toBeInTheDocument();
    expect(screen.getByText(/yaptırım otomatik uygulanmaz/i)).toBeInTheDocument();
  });

  it("gerekçeli moderatör kararını kaydeder", async () => {
    const user = userEvent.setup();
    render(<App />);

    await screen.findByRole("heading", { name: "Koordinasyon adayı" });
    await user.type(screen.getByLabelText("Karar gerekçesi"), "Sinyaller birlikte değerlendirildi.");
    await user.click(screen.getByRole("button", { name: "Gerekçeli kararı kaydet" }));

    await waitFor(() => expect(screen.getByRole("status")).toHaveTextContent("denetim kaydına"));
    expect(fetch).toHaveBeenCalledTimes(2);
  });

  it("nezaket uyarısını açıklar ve kullanıcı tercihini korur", async () => {
    const user = userEvent.setup();
    render(<App />);

    await screen.findByRole("heading", { name: "Koordinasyon adayı" });
    await user.click(screen.getByRole("button", { name: "Nezaket kontrolü" }));

    expect(await screen.findByText("kişiye yönelik aşağılama")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Yine de devam et" }));
    expect(
      screen.getByText("Kullanıcı tercihi korundu; demo gönderimi engellenmedi."),
    ).toBeInTheDocument();
  });

  it("duyurulmuş kampanya bağlamını skor dışı kanıt olarak gösterir", async () => {
    const contextualAlert = {
      ...alert,
      context_evidence: [{
        context_type: "public_announcement",
        label: "Duyurulmuş fidan dikme etkinliği",
        source_url: "https://example.test/public-announcement",
        disclosure_id: "announcement_demo",
        event_count: 6,
        account_count: 6,
        changes_risk_score: false,
        explanation: "Bu bilgi risk skorunu değiştirmez; kaynak doğrulaması gerekir.",
      }],
    };
    vi.mocked(fetch).mockResolvedValueOnce(new Response(JSON.stringify({
      scenario: "announced-campaign",
      event_count: 6,
      alert_count: 1,
      alerts: [contextualAlert],
    }), { status: 200 }));

    render(<App />);

    expect(await screen.findByRole("heading", { name: "Duyurulmuş fidan dikme etkinliği" })).toBeInTheDocument();
    expect(screen.getByText("BAĞLAM KANITI - SKORA ETKİ ETMEZ")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Duyuru kaynağını incele" })).toHaveAttribute(
      "href",
      "https://example.test/public-announcement",
    );
  });
});
