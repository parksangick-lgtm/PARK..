# 박상익출장음식 웹사이트

정적 웹사이트입니다. 빌드 도구 없이 브라우저에서 바로 열립니다.

## 구조
```
index.html         페이지 본문
assets/styles.css  스타일
assets/script.js   문의 폼 동작
```

## VS Code에서 작업하기
1. 이 저장소를 클론하고 VS Code로 폴더를 엽니다.
2. 확장 **Live Server**를 설치합니다.
3. `index.html`에서 우클릭 → *Open with Live Server*.
   저장할 때마다 브라우저가 자동으로 새로고침됩니다.

## 남은 작업
- [ ] 연락처·상호·주소 등 실제 정보로 교체 (`index.html`, `footer`)
- [ ] `assets/`에 상차림 사진을 넣고 `.ph` 자리를 `<img>`로 교체
- [ ] 메뉴 가격 확정
- [ ] 문의 폼을 실제 접수처에 연결 (`assets/script.js`의 TODO)
- [ ] 배포 (GitHub Pages: Settings → Pages → 브랜치 지정)
