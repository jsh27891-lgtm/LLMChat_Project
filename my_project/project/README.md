# Ollama 로컬 LLM 터미널 챗봇

> API 키 없이 내 PC에서 Gemma 4 E2B와 대화하는 터미널 챗봇ㆍ[기간]ㆍ1인ㆍ기획, 설계, 구현

![Version](https://img.shields.io/badge/version-v1.0.0-orange)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Ollama](https://img.shields.io/badge/Ollama-local%20LLM-black)
![Dependencies](https://img.shields.io/badge/외부%20라이브러리-0개-brightgreen)

## 결과

- 외부 라이브러리: 0개 (표준 라이브러리만 사용)
- 첫 토큰까지 걸린 시간: [측정값]초 ([N]회 평균)

![실행 화면](images/demo.png)

## 문제

클라우드 LLM은 API 키와 사용료가 필요하고 대화가 외부 서버로 나갑니다. 로컬 LLM은 서버 실행과 모델 다운로드를 직접 해야 합니다.

## 내 역할

- Ollama `/api/chat` 스트리밍 클라이언트 구현
- 서버가 꺼져 있으면 자동 실행, 모델이 없으면 다운로드 안내
- `/reset`, `/system`, `/exit` 명령어와 Ctrl+C 생성 중단 설계

## 기술과 고른 이유

- Python 표준 라이브러리: `pip install` 없이 바로 실행
- Ollama: 모델 다운로드와 추론 서버를 REST API 하나로 처리
- Gemma 4 E2B: 일반 PC에서 돌아가고 한국어 대화 가능

## 사용 모델

- 모델: `hf.co/unsloth/gemma-4-E2B-it-GGUF` (Gemma 4 E2B)
- `it`: 대화용으로 추가 학습된 instruction-tuned 버전
- `GGUF`: Ollama가 바로 불러오는 모델 파일 형식
- `Q8_0`: 8비트 양자화. 원본보다 메모리를 적게 쓰고 품질 손실은 작음
- `--model` 옵션으로 Ollama에 설치된 다른 모델로 교체 가능

## 구조

![구조도](images/architecture.png)

```text
입력 → 서버 확인(없으면 실행) → 모델 확인(없으면 다운로드) → /api/chat 스트리밍 → 출력
```

## 트러블슈팅

**서버가 꺼져 있으면 실행 실패**
- 원인: 서버 상태를 확인하지 않고 `/api/chat`을 바로 호출
- 해결: `/api/version`으로 확인 후, 꺼져 있으면 `ollama serve`를 백그라운드로 실행하고 최대 30초간 1초마다 재확인
- 결과: 별도 명령어 없이 바로 대화 시작

**모델이 없으면 첫 질문에서 오류**
- 원인: 모델 설치 여부를 확인하지 않음
- 해결: `/api/tags`로 조회하고, 없으면 `[Y/n]`로 물은 뒤 `ollama pull` 실행
- 결과: Y만 누르면 설치까지 완료

**실패한 질문이 기록에 남아 다음 답변이 꼬임**
- 원인: 응답을 받기 전에 질문을 기록에 먼저 추가
- 해결: 오류나 빈 응답이면 해당 질문을 기록에서 제거
- 결과: 오류 후에도 대화 맥락 유지

## 실행 방법

```bash
# Ollama 설치: https://ollama.com
python LLMChat.py

# 옵션
python LLMChat.py --model hf.co/unsloth/gemma-4-E2B-it-GGUF:Q8_0
python LLMChat.py --system "너는 친절한 한국어 도우미야."
```

| 채팅 명령어 | 동작 |
|---|---|
| `/reset` | 대화 기록 초기화 |
| `/system` | 시스템 프롬프트 변경 |
| `/exit` | 종료 |

## 배운 점ㆍ다음 계획

- 배운 점: 스트리밍 응답은 줄 단위 JSON이라 줄마다 파싱해야 하고, 오류도 응답 중간에 `error` 필드로 올 수 있습니다.
- 다음 계획: 대화 기록 파일 저장, 답변 속도(토큰/초) 표시

## 회고ㆍ링크

- 회고: [잘한 점 / 아쉬운 점]
- 데모 영상: [링크]
- 저장소: https://github.com/jsh27891-lgtm/LLMChat_Project
