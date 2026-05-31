# SALZIP — 청년 1인가구 주거 매칭 + 깡통전세 진단

> 공공데이터를 점수 알고리즘으로 융합해 "직장 통근 + 생활 인프라 + 주거 안전"을 한 번에 진단하는 멀티 에이전트 매칭 서비스.

## 모노레포 구조

```
salzip/
├── client/    React Native + Expo Router 앱 (iOS / Android / Web)
└── server/    FastAPI + PostgreSQL + LangChain 멀티에이전트
```

각 패키지는 독립적으로 실행·테스트 가능합니다.

## 핵심 기능

- **매물 매칭** — 직장 주소·라이프스타일·예산 → 후보 동네 Top-5 + 매물 추천
- **깡통전세 위험도 진단** — 매물별 환산보증금 / 동네·유형별 매매 실거래 → 추정 전세가율 기반 4축 점수
- **멀티 에이전트 분석** — 위험·시세·입지·지원사업 4 도메인 병렬 분석 + 종합 에이전트 (SSE 토큰 스트리밍)
- **출퇴근 시간 측정** — ODSAY 대중교통 API
- **청년 지원사업 자격 매칭** — 사용자 프로필 기준 자동 판정

## 데이터 출처 (공공)

- 국토교통부 실거래가 (전세 · 매매)
- 한국부동산원 R-ONE 시계열
- HUG 보증사고 통계
- 행정안전부 침수흔적도 / 침수예상도
- 카카오 로컬 (생활 인프라)
- ODSAY 대중교통 길찾기

## 시작하기

### Server

```bash
cd server
cp .env.example .env       # 키 채워 넣기
uv sync
docker compose -f docker-compose.dev.yml up -d
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

### Client

```bash
cd client
cp .env.example .env       # EXPO_PUBLIC_KAKAO_JS_KEY 채우기 (지도 SDK)
npm install
npx expo start
```

> `src/constants/env.ts`에서 백엔드 API base URL을 토글합니다 (dev `localhost:8000` ↔ prod 도메인).

## 기술 스택

| Layer | Tech |
|---|---|
| Client | React Native, Expo Router, NativeWind, Zustand, TanStack Query |
| Server | FastAPI, SQLAlchemy 2.x (Core), asyncpg, PostgreSQL |
| AI | LangChain `create_agent`, OpenAI `gpt-4o-mini`, Server-Sent Events |
| Infra | Docker Compose, Alembic |

## License

MIT — see [`LICENSE`](./LICENSE).
