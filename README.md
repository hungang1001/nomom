
# Global Poverty Rankings — Streamlit App

이 리포지토리는 **세계 각국의 국제 빈곤선($2.15/일) 기준 빈곤율**을 이용해
국가별 **빈곤 순위(연도별)** 혹은 **빈곤율(%)**을 선 그래프로 시각화하는 Streamlit 앱입니다.

## 파일 구성
```
app.py                  # Streamlit 앱 본문
requirements.txt        # 의존성
data/sample_poverty_215.csv  # API 실패 시 사용할 샘플 데이터
```

## 동작 방식
- 기본적으로 **월드뱅크 API(SI.POV.DDAY)** 에서 최신 데이터를 불러옵니다.
- API가 실패하면 `data/sample_poverty_215.csv`를 자동 사용합니다.
- 좌측 사이드바에서 연도 범위, 국가, Y축 모드(빈곤율 vs 순위)를 선택할 수 있습니다.

## 로컬 실행
```bash
pip install -r requirements.txt
streamlit run app.py
```

## 배포(https://streamlit.io)
1. 본 폴더를 GitHub에 업로드 (예: `username/poverty-line-app`)
2. Streamlit Community Cloud에서 **New app** → 해당 리포지토리/브랜치 선택 → `app.py` 지정
3. Deploy 후 접속

## 주의 사항
- **'순위'는 연도별로 빈곤율(%)이 높은 국가가 1위**가 되도록 계산합니다.
- 국가·연도별 결측이 많을 수 있어, 비교 시 같은 연도 구간을 선택해 보세요.
