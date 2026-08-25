const cfg = window.SITE_CONFIG || {};

// ── 연락처를 site.config.js 값으로 채웁니다 ──────────────
const telDigits = (cfg.phone || "").replace(/[^0-9+]/g, "");
const phoneLink = document.querySelector("#phone-link");
if (phoneLink) {
  phoneLink.href = `tel:${telDigits}`;
  phoneLink.textContent = `전화 문의 ${cfg.phone || ""}`.trim();
}
const kakaoLink = document.querySelector("#kakao-link");
if (kakaoLink && cfg.kakaoUrl) {
  kakaoLink.href = cfg.kakaoUrl;
  kakaoLink.hidden = false;
}
const hours = document.querySelector("#hours");
if (hours) hours.textContent = cfg.businessHours || "";
const footer = document.querySelector("#footer-info");
if (footer) {
  footer.textContent = [cfg.businessName, cfg.phone].filter(Boolean).join(" · ");
}

// ── 사진이 아직 없을 때 자리표시자로 대체 ─────────────────
const toPlaceholder = (img) => {
  const ph = document.createElement("div");
  ph.className = "ph";
  ph.textContent = img.alt || "사진 준비 중";
  // 자리표시자에 이미 같은 문구가 들어가므로 캡션은 숨깁니다.
  img.closest("figure")?.querySelector("figcaption")?.setAttribute("hidden", "");
  img.replaceWith(ph);
};
document.querySelectorAll(".gallery img").forEach((img) => {
  // 스크립트가 늦게 실행되어 이미 실패한 이미지도 잡아냅니다.
  if (img.complete && img.naturalWidth === 0) toPlaceholder(img);
  else img.addEventListener("error", () => toPlaceholder(img));
});

// ── 문의 폼 ──────────────────────────────────────────
const form = document.querySelector("#inquiry");
const result = document.querySelector("#result");

form?.addEventListener("submit", async (e) => {
  e.preventDefault();
  const button = form.querySelector("button");
  const data = new FormData(form);

  // 접수처가 아직 연결되지 않았으면 화면 확인만 하고 끝냅니다.
  if (!cfg.formEndpoint) {
    result.textContent =
      `${data.get("name")}님, 입력은 확인했지만 접수처가 아직 연결되지 않았습니다. ` +
      `${cfg.phone || ""} 로 전화 주시면 바로 안내해 드립니다.`;
    return;
  }

  button.disabled = true;
  button.textContent = "전송 중…";
  result.textContent = "";

  try {
    const res = await fetch(cfg.formEndpoint, {
      method: "POST",
      headers: { Accept: "application/json" },
      body: data,
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    result.textContent = `${data.get("name")}님, 문의가 접수되었습니다. 곧 연락드리겠습니다.`;
    form.reset();
  } catch (err) {
    console.error(err);
    result.textContent =
      `전송에 실패했습니다. 잠시 후 다시 시도하시거나 ${cfg.phone || ""} 로 연락 주세요.`;
  } finally {
    button.disabled = false;
    button.textContent = "문의 남기기";
  }
});
