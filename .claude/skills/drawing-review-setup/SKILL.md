---
name: drawing-review-setup
description: 도면 검토 시스템 초기 설치 및 환경 설정을 실행한다.
  trigger when 사용자가 "설치해줘", "셋업해줘", "setup", "환경 설정"을 요청할 때.
---

# Drawing Review Setup

도면 검토 시스템의 초기 설치를 수행하는 스킬.
사용자가 개발을 전혀 모른다고 가정하고 안내한다.

## 실행 순서

### 1. Python 확인
```bash
python --version
```
또는 Windows에서:
```bash
python3 --version
```

#### Python이 이미 있으면 → Step 2로 이동

#### Python이 없으면 → 사용자에게 설치 방법 안내

아래 3가지 방법을 순서대로 제안한다. 사용자 상황에 맞는 걸 선택하게 한다.

**방법 A: 일반 설치 (exe 실행 가능할 때 — 가장 쉬움)**

사용자에게 아래 내용을 안내:

---
Python을 설치해야 합니다. 아래 순서대로 해주세요:

1. 크롬(Chrome)을 열고 주소창에 입력하세요: **https://www.python.org/downloads/**
2. 화면에 큰 노란 버튼 **"Download Python 3.xx.x"** 가 보입니다 → 클릭
3. 다운로드된 파일을 실행하세요
4. ⚠️ **중요!** 설치 화면 맨 아래에 **"Add Python to PATH"** 체크박스가 있습니다 → **반드시 체크!**
5. **"Install Now"** 클릭
6. 설치가 끝나면 **"Close"** 클릭
7. 다시 저한테 와서 **"설치해줘"** 라고 해주세요
---

**방법 B: ZIP으로 설치 (회사 보안으로 exe 실행이 안 될 때)**

사용자에게 아래 내용을 안내:

---
회사에서 exe 설치가 막혀있군요. ZIP 버전으로 설치할 수 있습니다.

**1단계: Python ZIP 다운로드**
1. 크롬을 열고 주소창에 입력하세요: **https://www.python.org/downloads/**
2. 노란 버튼 아래에 있는 버전 번호(예: Python 3.12.x)를 클릭하세요
3. 스크롤을 내려서 **"Files"** 표를 찾으세요
4. **"Windows embeddable package (64-bit)"** 를 찾아서 클릭 → zip 파일이 다운로드됩니다

**2단계: 압축 풀기**
1. 다운로드된 zip 파일에서 **마우스 오른쪽 클릭** → **"압축 풀기"** 또는 **"모두 추출"**
2. 풀 위치를 **C:\python** 으로 지정하세요 (폴더가 없으면 새로 만들어요)
3. 압축을 풀면 C:\python 안에 python.exe 등 파일들이 보여야 합니다

**3단계: pip 설치 (패키지 설치 도구)**
1. 크롬 주소창에 입력하세요: **https://bootstrap.pypa.io/get-pip.py**
2. 화면에 글자가 잔뜩 나옵니다 → **Ctrl+S** 눌러서 저장하세요
3. 저장 위치를 **C:\python** 으로 선택
4. 이 대화창에서 저한테 아래 명령을 실행해달라고 해주세요:
   ```
   C:\python\python.exe C:\python\get-pip.py
   ```

**4단계: PATH 설정**
1. 제가 도와드릴게요. "PATH 설정해줘" 라고 해주세요
   (Claude가 실행할 명령: )
   ```
   setx PATH "%PATH%;C:\python;C:\python\Scripts"
   ```
2. 터미널을 껐다가 다시 열어주세요
3. 다시 **"설치해줘"** 라고 해주세요
---

**방법 C: Microsoft Store (스토어가 열리는 경우)**

사용자에게 아래 내용을 안내:

---
1. 키보드에서 **Windows 키** 를 누르세요
2. **"store"** 라고 타이핑하세요 → **Microsoft Store** 가 뜨면 클릭
3. Store 위쪽 검색창에 **"Python 3.12"** 입력 → 검색
4. **"Python 3.12"** (Microsoft Corporation 배포) → **"받기"** 또는 **"설치"** 클릭
5. 설치가 끝나면 다시 **"설치해줘"** 라고 해주세요
---

Python 설치 후 사용자가 다시 오면, Step 1부터 다시 실행하여 python이 있는지 확인.

### 2. pip 확인 및 패키지 설치 (자동)
```bash
pip --version
```
pip이 없으면:
```bash
python -m ensurepip --upgrade
```
그래도 없으면 get-pip.py 방법 안내 (위 방법 B의 3단계).

패키지 설치:
```bash
pip install -r requirements.txt
```
실패하면:
```bash
pip install --user -r requirements.txt
```
그래도 실패하면 에러 메시지를 보고 구체적으로 안내.

### 3. 폴더 확인 및 생성 (자동)
다음 폴더가 없으면 생성:
- `data/cache/`
- `data/chroma_db/`
- `inbox/`
- `in_progress/`
- `reports/`
- `logs/`

### 4. DWG 변환기 확인 (자동)
```bash
python -c "from scripts.common.config import DWG2DXF_BIN; print(DWG2DXF_BIN or 'NOT FOUND')"
```
- **있으면**: "DWG 파일을 직접 검토할 수 있습니다."
- **없으면**: 아래 안내

---
DWG 변환기가 없지만 괜찮아요!
**AutoCAD에서 DXF로 저장**하면 됩니다:

1. AutoCAD에서 도면을 여세요
2. **Ctrl+Shift+S** (다른 이름으로 저장)
3. 파일 형식을 **"AutoCAD DXF (*.dxf)"** 로 변경
4. 저장
5. 이 DXF 파일을 저한테 주시면 됩니다
---

### 5. RAG 인덱스 빌드 (자동)
```bash
python scripts/review/rag_search.py --build-index --vault standards-vault
```
sentence-transformers 다운로드에 시간이 걸릴 수 있음 (첫 실행 시 약 1-2분).
실패하면 일단 건너뛰고 나중에 재시도 안내.

### 6. 완료 안내

사용자에게:

---
✅ **설치 완료!**

사용법:
1. AutoCAD에서 도면을 **DXF**로 저장하세요 (Ctrl+Shift+S → 파일 형식: DXF)
2. 저한테 DXF 파일을 첨부하고 **"이 도면 검토해줘"** 라고 하세요
3. 검토하면서 **"이런 기준도 확인해줘"** 라고 하면 규칙이 자동으로 추가됩니다
---

## Claude가 직접 할 수 없는 것 (안내만 함)
- ⛔ Python 설치 → 위 방법 A/B/C 안내
- ⛔ Git 설치 → git-scm.com 또는 ZIP 다운로드 안내
- ⛔ AutoCAD 실행/DXF 저장 → 사용자가 직접
- ⛔ 관리자 권한이 필요한 시스템 설정 → IT팀 문의 안내
