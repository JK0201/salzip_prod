# SALZIP Server

FastAPI + PostgreSQL + LangChain 멀티에이전트 백엔드.

## 빠른 시작

```bash
cp .env.example .env             # 키 채우기
uv sync
docker compose -f docker-compose.dev.yml up -d   # Postgres
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

`/docs`에서 OpenAPI 확인.

## 핵심 엔드포인트

| Method | Path | 설명 |
|---|---|---|
| `POST` | `/api/v1/session` | 익명 세션 토큰 발급 (Bearer) |
| `POST` | `/api/v1/recommend` | 사용자 프로필 → 동네 Top-5 + 매물 추천 |
| `GET`  | `/api/v1/recommend/latest` | 최근 추천 결과 조회 |
| `POST` | `/api/v1/listings/{id}/analyze` | 매물 분석 SSE (멀티에이전트 토큰 스트리밍) |

## 멀티에이전트 SSE

`POST /api/v1/listings/{id}/analyze`는 `text/event-stream`으로 다음 이벤트를 순차 발행합니다.

| event | data |
|---|---|
| `route` | `{ agents: ["risk","sise","locale","support","synth"] }` |
| `scores` | 4 도메인 결정론 점수 (`risk` / `sise` / `locale` / `support`) |
| `agent_start` | `{ agent }` |
| `token` | `{ agent, delta }` — LLM 토큰 |
| `agent_done` | `{ agent }` |
| `agent_error` | `{ agent, error }` |
| `done` | `{}` |

설계 원칙: **점수는 결정론(같은 입력 → 같은 결과), 해석·경고·종합은 LLM**.

## 도메인 점수 산식

### 위험도 (4축, 100점 만점, 매물 단위)

| 축 | 가중 | 산출 |
|---|---|---|
| 전세가율 | 0.5 | 매물 환산보증금 / (동네·유형 평당 매매가 × 매물 면적) → 90% 임계 정규화 |
| 사고 | 0.1 | 전국 HUG 보증사고 통계 (log10 정규화, 시장 신호) |
| 침수 | 0.2 | 행안부 침수흔적도 폴리곤 판정 (매물 단위) |
| HUG 보증 | 0.2 | 매물 추정 전세가율 90% 이하 시 가입 가능 |

매물 매매 표본 < 5건일 경우 동네 평균으로 폴백.

### 시세
매물 환산보증금 vs 동일 동네·유형·면적대 매물 중위값 비교.

### 입지
`area_metrics` 8 카테고리(카페·음식점·문화·공원·마트·지하철·병원·약국) + 라이프스타일 태그 매칭.

### 지원사업
사용자 프로필(나이·소득·세대 유형) → 청년 지원사업 자격 자동 판정.

## 데이터 출처 (공공)

| 카테고리 | 출처 |
|---|---|
| 매물 실거래 (전세·매매) | 국토교통부 실거래가 API |
| 시장 추세 | 한국부동산원 R-ONE |
| 보증사고 | HUG (data.go.kr 15002597) |
| 침수 | 행정안전부 침수흔적도 |
| 인프라 | 카카오 로컬 |
| 통근 | ODSAY 대중교통 |

## 기술 스택

| Layer | Tech |
|---|---|
| Web | FastAPI, Uvicorn |
| DB | PostgreSQL 16, SQLAlchemy 2.x Core (Async), asyncpg |
| 마이그레이션 | Alembic |
| AI | LangChain `create_agent`, ChatOpenAI (`gpt-4o-mini`) |
| Telemetry | LangSmith (opt-in) |

## 디렉토리 구조

```
server/
├── app/
│   ├── api/v1/        FastAPI 라우터
│   ├── core/          settings, deps, exceptions
│   ├── db/            tables (Core MetaData)
│   ├── repositories/  DAO 헬퍼
│   ├── schemas/       Pydantic IO
│   └── services/
│       ├── agents/    4 도메인 + synth 에이전트 + 프롬프트
│       ├── risk.py    위험도 4축 산식
│       ├── sise.py    시세 비교
│       ├── locale.py  입지 카운트
│       ├── support.py 지원사업 매칭
│       └── odsay.py   대중교통
├── alembic/           DB 마이그레이션
└── tests/             pytest + asyncio_mode=auto
```

## 테스트

```bash
uv run pytest                 # 전체
uv run pytest tests/api/      # 라우터만
uv run ruff check .           # 린트
```
