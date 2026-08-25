# 박상익출장음식 웹사이트

빌드 도구 없는 정적 웹사이트입니다. 브라우저에서 바로 열립니다.

## 구조
```
index.html          페이지 본문
site.config.js      ★ 연락처·폼 접수처 설정 (여기만 고치면 됩니다)
assets/styles.css   스타일
assets/script.js    연락처 채우기 · 갤러리 · 문의 폼 전송
assets/img/         상차림 사진 (gallery-1.jpg ~ gallery-4.jpg)
.vscode/            Live Server 설정 및 확장 추천
```

## VS Code에서 작업하기
1. 폴더를 엽니다. 우측 하단에 "추천 확장 설치" 알림이 뜨면 눌러 설치하세요
   (**Live Server**, **Prettier**).
2. `index.html`에서 우클릭 → *Open with Live Server*.
   `http://127.0.0.1:5500` 이 열리고, 저장할 때마다 자동 새로고침됩니다.

## 실제 정보 채우기
`site.config.js` 한 파일만 고치면 페이지 전체(전화 버튼, 푸터)에 반영됩니다.

```js
phone: "010-1234-5678",   // 실제 전화번호
kakaoUrl: "https://...",  // 카카오톡 채널 (없으면 "" — 버튼이 자동으로 숨겨집니다)
businessHours: "매일 09:00 – 20:00",
formEndpoint: "",          // 아래 "문의 폼 연결" 참고
```

메뉴 가격은 `index.html`의 `<p class="price">문의</p>` 부분을 직접 고치세요.

## 사진 넣기
`assets/img/`에 `gallery-1.jpg` ~ `gallery-4.jpg` 이름으로 넣으면 자동으로 표시됩니다.
파일이 없는 동안에는 회색 자리표시자가 대신 나오므로 페이지가 깨지지 않습니다.
가로로 넓은 사진(4:3 비율)이 가장 잘 맞습니다.

## 문의 폼 연결
1. https://formspree.io 가입 (무료 요금제로 월 50건까지 접수 가능)
2. New Form → 알림 받을 이메일 입력 → 생성
3. 받은 주소(`https://formspree.io/f/xxxxxxx`)를 `site.config.js`의
   `formEndpoint`에 붙여넣습니다.
4. 사이트에서 직접 한 번 테스트 문의를 보내면, Formspree가 첫 메일로
   주소 확인을 요청합니다. 확인해야 이후 문의가 메일로 도착합니다.

`formEndpoint`가 비어 있는 동안에는 폼이 전송되지 않고, 대신 전화로
연락해 달라는 안내가 표시됩니다.

## 남은 작업
- [ ] `site.config.js`에 실제 전화번호·카톡 주소 입력
- [ ] 메뉴 가격 확정 (`index.html`)
- [ ] `assets/img/`에 상차림 사진 4장 추가
- [ ] Formspree 폼 생성 후 `formEndpoint` 연결
- [ ] 배포 — GitHub Pages (Settings → Pages → 브랜치 선택)
