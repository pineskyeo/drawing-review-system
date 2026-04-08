# 도면 검토 자동화 시스템

AutoCAD 도면(DWG/DXF)을 검토 규칙과 대조하여 위반 사항을 자동으로 찾아주는 도구입니다.

## 이런 분을 위한 도구입니다

- AutoCAD 도면을 수작업으로 크로스체크하는 분
- PE BAR, SCHEMATIC, LAYOUT 간 정합성을 확인하는 분
- 검토 기준을 문서화하고 재사용하고 싶은 분

---

## Windows에서 시작하기 (별도 설치 없음)

> Python, Git 등 아무것도 설치할 필요 없습니다.
> 브라우저와 Claude Desktop만 있으면 됩니다.

### Step 1: 다운로드 (1분)

1. 아래 링크를 크롬(Chrome)으로 열어주세요:
   **https://github.com/pineskyeo/drawing-review-system**

2. 초록색 **`<> Code`** 버튼 클릭

3. **`Download ZIP`** 클릭

4. 다운로드된 ZIP 파일에서 **마우스 오른쪽 클릭** → **"모두 추출"**

5. 추출 위치: 바탕화면이나 원하는 곳 (예: `C:\Users\내이름\Desktop\drawing-review-system`)

### Step 2: 설치 (3분)

1. 압축 푼 폴더를 열어주세요

2. **`setup_windows.bat`** 파일을 찾아서 **더블클릭**
   - 검은 창(명령 프롬프트)이 열리면서 자동으로 설치됩니다
   - Python이 없어도 괜찮아요 — 내장된 Python이 자동으로 설치됩니다
   - "설치 완료!" 메시지가 나올 때까지 기다려주세요 (2-3분)

3. 아무 키나 눌러서 창을 닫으세요

> ⚠️ "Windows가 PC를 보호했습니다" 메시지가 나오면:
> **"추가 정보"** 클릭 → **"실행"** 클릭

### Step 3: Claude에서 열기

1. **Claude Desktop** (또는 Claude Code) 을 열어주세요

2. 워크스페이스를 압축 푼 폴더로 설정하세요

3. Claude에게 이렇게 말하세요:

> **"설치해줘"**

→ Claude가 나머지 설정을 자동으로 합니다

### Step 4: 도면 검토

1. **AutoCAD**에서 검토할 도면을 열어주세요

2. **Ctrl+Shift+S** (다른 이름으로 저장) → 파일 형식을 **"DXF"** 로 변경 → 저장

3. Claude에게 DXF 파일을 첨부하고 이렇게 말하세요:

> **"이 도면 검토해줘"**

→ 자동으로 검토 → 리포트 생성

---

## macOS에서 시작하기

```bash
git clone https://github.com/pineskyeo/drawing-review-system.git
cd drawing-review-system
chmod +x setup_mac.sh && ./setup_mac.sh
```

또는 Claude Code에서 워크스페이스 잡고 "설치해줘"

---

## Claude에게 할 수 있는 말들

| 말 | 하는 일 |
|----|--------|
| **"설치해줘"** | 환경 설정 |
| **"이 도면 검토해줘"** + DXF 첨부 | 전체 검토 → 리포트 생성 |
| **"이런 기준도 확인해줘: ○○○"** | 검토 규칙 추가 |
| **"기준 PDF 처리해줘"** + PDF 첨부 | PDF에서 규칙 자동 추출 |
| **"규칙 검수해줘"** | 현재 규칙 상태 확인 |
| **"vault 상태 보여줘"** | 규칙 요약 |

---

## 현재 검토 규칙 (7개)

| ID | 규칙 | 자동 |
|----|------|------|
| PE-001 | PE BAR 케이블이 SCHEMATIC에 존재하는지 | O |
| PE-002 | PE BAR POLE 수 일치 | O |
| PE-003 | PE BAR 파츠 명칭 일치 | O |
| PE-004 | BAR 쌍 POLE 합산 검증 | O |
| LO-001 | LAYOUT PB 수량 일치 | O |
| SC-001 | SCHEMATIC CP 번호 존재 | O |
| SC-002 | 3 PHASE 인버터 크로스체크 | O |

검토하면서 **"이런 것도 확인해줘"** 라고 하면 규칙이 계속 추가됩니다.
검토 후에는 Claude가 **추가로 확인하면 좋을 기준도 제안**합니다.

---

## 자주 묻는 질문

**Q: DWG 파일은 바로 안 되나요?**
A: DXF로 변환해야 합니다. AutoCAD에서 Ctrl+Shift+S → DXF로 저장하면 됩니다.

**Q: 인터넷 없이 되나요?**
A: 최초 설치 시에만 인터넷이 필요합니다 (패키지 다운로드). 이후에는 오프라인으로 됩니다. (단, LLM 판단 기능은 인터넷 필요)

**Q: 규칙은 어디에 저장되나요?**
A: `standards-vault/10-Rules/` 폴더에 Markdown 파일로 저장됩니다. Obsidian으로 열어서 볼 수도 있어요.

**Q: 리포트는 어디에 나오나요?**
A: `standards-vault/40-Reviews/` 폴더 + `reports/날짜/` 폴더에 Markdown으로 저장됩니다.
