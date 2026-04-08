# 🖼️ Magic Restore (Lite Ver.)

무거운 딥러닝 AI 모델을 배제하고, 전통적이고 강력한 OpenCV의 인페인팅(Inpainting) 알고리즘을 활용하여 가볍고 빠르게 동작하는 이미지 복원 도구입니다. 훼손된 옛날 사진의 스크래치나 불필요한 얼룩을 직관적인 UI를 통해 손쉽게 제거할 수 있습니다.

## ✨ 주요 기능 및 특징

* **초경량 & 독립 실행:** 복잡한 파이썬 환경 구축 없이 `.exe` 파일 하나로 즉시 실행 가능합니다.
* **3가지 맞춤형 복원 모드 지원:**
  * **NS 복원 (Navier-Stokes):** 길게 긁힌 상처나 선형 훼손 복원에 최적화
  * **Telea 복원 (Fast Marching):** 동그란 곰팡이, 얼룩, 물방울 자국 복원에 탁월
  * **도장툴 (Clone Stamp):** 반복되는 패턴이나 질감을 직접 복사하여 정밀하게 덮어쓰기
* **직관적인 조작:** 마우스 휠을 이용한 부드러운 확대/축소 및 드래그 화면 이동 기능 제공

> **Notice:** 본 프로그램은 더 나은 서비스 제공과 에러 수정을 위해 익명화된 최소한의 사용 통계(기능 클릭 수 등)를 수집합니다.

## 🚀 다운로드 및 바로 실행 (일반 사용자용)

파이썬 설치나 코딩 지식 없이 바로 프로그램을 사용하고 싶으신 분들은 아래 링크에서 실행 파일을 다운로드해 주세요.

* **[youtube]** [youtube](https://youtu.be/78EH925mXL0)
 
* **[Windows용 .exe 파일 다운로드]** [magic_restore_lite.exe](https://github.com/gohard-lab/magic_restorer/releases/latest)

*(다운로드 후 `magic_restore_lite.exe`를 더블클릭하면 바로 실행됩니다.)*

* **[Google Colab에서 실행해보기]** [Google Colab](<https://colab.research.google.com/drive/1FES7fWwIV75bE8E59QDjE4-k8m6LSvoc?hl=ko#scrollTo=W_d7Dy5rORLi](https://colab.research.google.com/drive/1FES7fWwIV75bE8E59QDjE4-k8m6LSvoc?hl=ko#scrollTo=W_d7Dy5rORLi>)


## ⌨️ 단축키 및 조작법

| 키 / 마우스 | 기능 설명 |
| :--- | :--- |
| **`M`** | 복원 모드 변경 (NS ↔ Telea ↔ 도장툴) |
| **`Z`** / **`X`** | 붓 크기 축소 / 확대 |
| **`Space Bar`** | 선택 영역 복원 실행 |
| **`S`** | 작업 완료된 이미지 저장 |
| **`우클릭`** | (도장툴) 복사할 깨끗한 원본 위치 지정 |
| **`Shift + 좌클릭`** | 두 점을 연결하는 직선 긋기 |
| **`Ctrl + Z`** | 실행 취소 (Undo) |

## 🛠 개발 환경 구축 및 소스코드 실행 (개발자용)

이 프로젝트는 `requirements.txt` 대신 최신 파이썬 패키지 관리 표준인 `pyproject.toml`과 `uv`를 사용하여 의존성을 관리합니다.

### 1. 저장소 클론 (GitHub 소스 링크)
```bash
git clone [https://github.com/gohard-lab/magic_restore.git](https://github.com/gohard-lab/magic_restore.git)
cd magic_restore
