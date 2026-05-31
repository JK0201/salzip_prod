# SALZIP Client

React Native + Expo Router 앱 (iOS / Android / Web).

## 빠른 시작

```bash
cp .env.example .env             # EXPO_PUBLIC_KAKAO_JS_KEY 채우기
npm install
npx expo start
```

플랫폼별 명령:

```bash
npm run ios       # iOS Simulator
npm run android   # Android Emulator
npm run web       # 웹 빌드
```

> 백엔드 API base URL은 `src/constants/env.ts`에서 dev/prod 토글.

## 기술 스택

| Layer | Tech |
|---|---|
| UI | React Native 0.85 · NativeWind (Tailwind) |
| 라우팅 | Expo Router (파일 기반) |
| 상태 | Zustand (클라이언트), TanStack 패턴 (서버) |
| 네트워킹 | axios, react-native-sse (멀티에이전트 토큰 스트리밍) |
| 지도 | 카카오 지도 JavaScript SDK (web) |
| 마크다운 | react-native-markdown-display (LLM 답변 렌더) |
| 언어 | TypeScript strict |

## 디렉토리 구조

```
client/
├── src/
│   ├── app/           Expo Router 진입점 (파일 기반 라우팅)
│   │   ├── (onboarding)/  5스텝 진단 + 결과
│   │   ├── (main)/        탭 네비 (홈/검색/즐겨찾기/지원사업/마이)
│   │   └── listing/[id]   매물 상세 + SSE 멀티에이전트
│   ├── components/    공통 컴포넌트
│   │   └── listing/   DomainPanel, DomainDetailSheet, SaljipChatModal,
│   │                  ExtraActions, sheets/ (Route/Email/Contract/Negotiation/Landlord)
│   ├── api/           백엔드 호출 (analyze.ts, recommend.ts, client.ts)
│   ├── store/         Zustand 스토어 (Diagnosis, Session, Favorite)
│   ├── hooks/         커스텀 훅 (useMockStream 등)
│   ├── constants/     env, listingImages, queryKeys
│   ├── types/         공통 타입
│   └── utils/         순수 유틸
├── assets/            폰트·이미지
└── public/            웹 정적 자산
```

## 주요 화면

| 화면 | 경로 | 설명 |
|---|---|---|
| 진단 시작 | `(onboarding)/start` | 서비스 소개 |
| 5스텝 진단 | `(onboarding)/diagnosis/step1~5` | 직장·라이프스타일·예산·인적사항 |
| 매칭 결과 | `(onboarding)/diagnosis/complete` | 동네 Top-5 카카오 지도 |
| 매물 상세 | `listing/[id]` | 사진·메타 + 5 도메인 SSE 분석 + 살집이 챗봇 |

## 매물 상세 — 멀티에이전트 SSE

매물 진입 시 `POST /api/v1/listings/{id}/analyze` 호출.

- `route` 이벤트로 활성 에이전트 5종 라우팅
- `scores` 이벤트로 결정론 점수 4 도메인 페이로드 수신
- `token` 이벤트마다 도메인별 LLM 답변 토큰 점진 렌더 (마크다운)
- `synth` 종합 답변은 최상단 히어로 카드
- 4 도메인 미니 타일 탭 시 `DomainDetailSheet`로 풀 분석 표시

## 환경 변수

| 키 | 용도 |
|---|---|
| `EXPO_PUBLIC_KAKAO_JS_KEY` | 매칭 결과 화면 카카오 지도 SDK |
