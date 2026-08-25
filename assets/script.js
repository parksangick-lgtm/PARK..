// 문의 폼: 현재는 프런트에서만 처리합니다.
// 실제 접수를 받으려면 아래 TODO 위치에 폼 서비스(Formspree 등) 또는
// 자체 API 엔드포인트 주소를 연결하세요.
document.querySelector("#inquiry")?.addEventListener("submit", (e) => {
  e.preventDefault();
  const data = Object.fromEntries(new FormData(e.target));
  // TODO: fetch("<엔드포인트>", { method: "POST", body: JSON.stringify(data) })
  console.log("문의 내용:", data);
  document.querySelector("#result").textContent =
    `${data.name}님, 문의가 접수되었습니다. 곧 연락드리겠습니다.`;
  e.target.reset();
});
