# ai-map-touchup (Claude Code skill)

AI가 그린 일러스트 지도(Google Flow·Nano Banana, Gemini 등)를 **실제 일정과 위치에 맞게 검수하고 고치는** Claude Code 스킬입니다.

AI 지도는 그럴듯해 보여도 이런 실수가 자주 있습니다. 이 스킬은 이런 것들을 찾아서 고칩니다.

- 오타, 남아 있는 영어 라벨, 엉뚱한 라벨에 붙은 시간
- 같은 장소 이름이나 핀 번호, 식당이 두 번 나오는 중복 라벨
- 구간이 빠지거나 방향이 거꾸로이거나, 아무 데도 연결되지 않는 점선 동선
- 랜드마크가 도로 반대편에 있거나, 거리 이름이 다른 도로에 붙은 위치 오류

## 동작 방식

1. **검수:** 일정(방문 순서, 시간, 대체 장소)을 기준으로 지도마다 오타, 중복, 동선, 위치 문제를 한꺼번에 목록으로 만듭니다.
2. **이미지 도구 편집:** Flow 같은 도구의 편집 기능으로 글자 수정을 먼저 시도하고 결과를 확인합니다. CAPTCHA나 봇 차단이 뜨면 우회하지 않고 3단계로 넘어갑니다.
3. **로컬 보정:** `scripts/map_touchup.py`로 픽셀 단위로 확실하게 고칩니다.
   - 잘못된 점선을 한 번에 지우기(색상 검출 + 인페인팅, 핀·범례 보호)
   - 라벨 지우기, 새로 쓰기, 거리 이름을 도로 방향으로 회전
   - 구간마다 점선 동선 다시 그리기(끝 화살표와 중간 화살표)
   - "1 → 2" 같은 구간 배지, 대체 동선용 범례 항목 추가

## 설치

```bash
cp -r ai-map-touchup ~/.claude/skills/
pip install pillow numpy opencv-python-headless
```

## 스크립트 사용법

```bash
# 1) 좌표 읽기: 눈금이 있는 확대 크롭 만들기
python -I ai-map-touchup/scripts/map_touchup.py grid map.jpg zoom.png 460,490,780,700 --scale 2

# 2) 수정 명세(JSON) 적용
python -I ai-map-touchup/scripts/map_touchup.py apply map.jpg map_fixed.jpg spec.json
```

명세 예시는 `examples/rainy-day-route-fix.json`에 있습니다. 동선이 엉킨 지도에서 기존 빨간 점선을 모두 지우고, 1 → 2 → 3B → 4 → 숙소 순서로 다시 그린 뒤, 대체 장소 3A는 주황 점선과 범례로 표시한 실제 사례입니다. 지원하는 작업은 `strip_color`, `inpaint`, `fill`, `text`, `route`, `badge`, `legend_entry`이며, 자세한 설명은 스크립트 상단 docstring에 있습니다.

## 사용 예

```
1~5일차 지도에 남은 오타랑 중복 라벨 고쳐줘
동선 점선이 일정 순서랑 맞는지 확인하고 수정해
비 오는 날 지도에서 3A는 대체 동선으로 따로 표시해줘
```

## 팁

- 수정은 항상 **원본 이미지에서 다시** 적용하세요. 결과물에 덧칠하면 얼룩이 쌓입니다.
- 넓은 영역을 인페인팅하면 도로의 흰색이 블록으로 번집니다. 평평한 블록 위 라벨은 `fill`로 지우세요.
- 일러스트 지도라 위치는 대략적입니다. 실제로 길을 찾을 때는 지도 앱을 함께 쓰세요.

## 함께 쓰면 좋은 스킬

- [naver-trip-report-skill](https://github.com/mandu-416/naver-trip-report-skill): 네이버·구글을 크롤링해 여행 일정 보고서와 일자별 동선 지도를 만듭니다.

## License

MIT
