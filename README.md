# 오늘의 발견 — 나만의 데일리 뉴스레터

매일 아침, 당신의 취향에 맞으면서 **아직 모르는** 것들을 찾아 보내주는 자동 뉴스레터입니다.
남성복 · 빈티지 · 음악 · 영상 · 자동차 · 서브컬처 — 여섯 갈래로, Claude가 매일 웹을 뒤져
"오늘의 발견"을 골라 Apple / Jony Ive / LoveFrom 무드의 메일로 보내드립니다.

---

## 어떻게 작동하나요

```
매일 아침 (GitHub Actions 예약 실행)
        │
        ▼
 taste_profile.md  ←  당신의 취향이 적힌 파일
        │
        ▼
 curate.py  →  Claude API (웹 검색) 로 오늘의 6가지 발견을 찾음
        │
        ▼
 email_template.py  →  크림빛 에디토리얼 이메일로 렌더링
        │
        ▼
   Gmail 로 발송  →  당신의 받은편지함
```

핵심: **`taste_profile.md` 파일이 당신의 취향을 기억합니다.** Claude는 대화가 끝나면
기억하지 못하지만, 이 파일에 취향이 적혀 있으니 매일 그걸 읽고 큐레이션합니다.
취향이 바뀌거나 추가하고 싶으면 이 파일만 고치면 됩니다.

---

## 준비물 (3가지)

1. **GitHub 계정** (무료) — 자동 실행을 맡아줍니다
2. **Gmail 계정** — 메일을 보낼 주소
3. **Anthropic API 키** — Claude가 검색·큐레이션하는 데 필요 (https://console.anthropic.com 에서 발급)

> 비용 안내: 하루 한 통 기준 API 비용은 매우 적습니다(웹 검색 + 짧은 생성).
> GitHub Actions 예약 실행은 공개/비공개 저장소 모두 무료 한도 안에서 충분합니다.

---

## 설정 방법 (처음 한 번만)

### 1단계 — Gmail 앱 비밀번호 만들기

일반 비밀번호가 아니라 "앱 비밀번호"가 필요합니다. (2단계 인증이 켜져 있어야 발급됩니다.)

1. https://myaccount.google.com/security 접속
2. **2단계 인증**이 꺼져 있다면 먼저 켜기
3. https://myaccount.google.com/apppasswords 접속
4. 앱 이름을 아무거나 입력 (예: `newsletter`) → **만들기**
5. 화면에 뜨는 **16자리 비밀번호**(예: `abcd efgh ijkl mnop`)를 복사해 둡니다
   - 이건 다시 볼 수 없으니 안전한 곳에 잠깐 보관하세요

### 2단계 — 이 폴더를 GitHub 저장소로 올리기

GitHub에서 새 저장소(repository)를 하나 만든 뒤(비공개 추천), 이 `newsletter` 폴더의
내용을 올립니다. 터미널을 쓴다면:

```bash
cd newsletter
git init
git add .
git commit -m "오늘의 발견 뉴스레터"
git branch -M main
git remote add origin https://github.com/<your-username>/<your-repo>.git
git push -u origin main
```

> GitHub 웹사이트에서 "Add file → Upload files"로 드래그해서 올려도 됩니다.
> 단, `.github/workflows/daily-newsletter.yml` 경로(폴더 구조)는 그대로 유지되어야 합니다.

### 3단계 — 비밀 값(Secrets) 등록하기

GitHub 저장소 페이지에서:

**Settings → Secrets and variables → Actions → New repository secret**

아래 4개를 각각 등록합니다. (이름은 정확히 똑같이)

| 이름 | 값 |
|------|-----|
| `ANTHROPIC_API_KEY` | 당신의 Anthropic API 키 (`sk-ant-...`) |
| `GMAIL_ADDRESS` | 보내는 Gmail 주소 |
| `GMAIL_APP_PASSWORD` | 1단계에서 만든 16자리 앱 비밀번호 |
| `RECIPIENT_EMAIL` | 받을 주소 (보내는 주소와 같아도 됨) |

### 4단계 — 동작 확인 (수동 실행)

예약 시간을 기다리지 말고 바로 테스트해보세요.

저장소의 **Actions** 탭 → 왼쪽에서 **오늘의 발견 — Daily Newsletter** 선택 →
오른쪽 **Run workflow** 버튼 클릭.

1~2분 뒤 받은편지함을 확인하세요. 메일이 도착했다면 끝입니다. 🎉
이제부터는 매일 아침 자동으로 옵니다.

---

## 발송 시간 바꾸기

`.github/workflows/daily-newsletter.yml` 파일의 이 줄을 고치면 됩니다:

```yaml
    - cron: '0 22 * * *'
```

`'분 시 * * *'` 형식이며 **UTC 기준**입니다. 한국 시간(KST)은 UTC+9 이므로:

| 받고 싶은 시간 (한국) | cron 값 |
|----------------------|---------|
| 아침 7시 | `'0 22 * * *'` |
| 아침 8시 | `'0 23 * * *'` |
| 아침 9시 | `'0 0 * * *'` |
| 오전 6시 | `'0 21 * * *'` |

> GitHub 예약 실행은 트래픽에 따라 몇 분 늦을 수 있습니다(정상입니다).

---

## 취향 바꾸기 / 추가하기

`taste_profile.md` 를 열어서 자유롭게 고치세요. 좋아하는 브랜드·뮤지션·감독·차종을
더 넣거나, "AVOID" 목록(관심 없는 것)을 늘리면 큐레이션이 더 정확해집니다.
고친 뒤 GitHub에 다시 push(또는 웹에서 편집·커밋)하면 다음 날부터 반영됩니다.

맨 아래 **CURATION RULES** 섹션은 "어떻게 고를지"에 대한 지침입니다. 예를 들어
"카테고리당 하나가 아니라 두 개씩" 원하면 여기 문구를 바꾸고, 카테고리를 더하거나
빼고 싶으면 `curate.py` 의 `CATEGORIES` 목록도 함께 맞춰주세요.

---

## 내 컴퓨터에서 직접 돌려보기 (선택)

자동 실행 없이 로컬에서 테스트하려면:

```bash
cd newsletter
pip install -r requirements.txt
cp .env.example .env          # .env 를 열어 실제 값 입력
set -a && source .env && set +a
DRY_RUN=1 python curate.py    # 발송 없이 last_issue.html 만 생성 (디자인 확인용)
python curate.py              # 실제로 메일 발송
```

`last_issue.html` 을 브라우저로 열면 그날 메일을 미리 볼 수 있습니다.

---

## 파일 구성

```
newsletter/
├── taste_profile.md                 # ← 당신의 취향 (여기를 고치세요)
├── curate.py                        # 메인 스크립트 (검색·큐레이션·발송)
├── email_template.py                # 이메일 디자인 (Apple/Ive/LoveFrom 무드)
├── requirements.txt                 # 파이썬 의존성
├── .env.example                     # 로컬 테스트용 환경변수 예시
├── README.md                        # 이 파일
└── .github/
    └── workflows/
        └── daily-newsletter.yml     # 매일 아침 자동 실행 설정
```

---

## 문제 해결

- **메일이 안 와요** → Actions 탭에서 실행 로그를 확인하세요. 빨간 X가 있으면 로그에
  원인이 적혀 있습니다. 대개 Secret 이름 오타이거나 앱 비밀번호 문제입니다.
- **스팸함에 들어가요** → 받은편지함의 첫 메일에서 "스팸 아님" 표시를 하거나,
  보내는 주소를 연락처에 추가하세요.
- **`Missing required environment variable`** → 해당 Secret이 등록되지 않았거나 이름이
  다릅니다. 표의 이름과 정확히 일치하는지 확인하세요.
- **JSON 관련 오류로 가끔 실패** → 스크립트가 자동으로 한 번 재시도합니다. 계속 실패하면
  `NEWSLETTER_MODEL` 을 `claude-opus-4-8` 로 바꿔보세요.

---

매일 아침, 트렌드가 아니라 트렌드가 참조하는 것들을.
