"""Ollama로 서빙하는 Gemma 4 E2B (unsloth GGUF) 터미널 챗 프로그램.

사전 준비:
    1) Ollama 설치 (꺼져 있으면 이 프로그램이 자동으로 실행, 기본 http://localhost:11434)
    2) 모델 받기 (처음 실행 시 이 프로그램이 물어보고 대신 받아줍니다)
           ollama pull hf.co/unsloth/gemma-4-E2B-it-GGUF

사용:
    python LLMChat.py
    python LLMChat.py --model hf.co/unsloth/gemma-4-E2B-it-GGUF:Q8_0
    python LLMChat.py --system "너는 친절한 한국어 도우미야."

채팅 중 명령어:
    /reset   대화 기록 초기화
    /system  시스템 프롬프트 변경
    /exit    종료 (Ctrl+C, Ctrl+D 도 가능)
"""

import argparse
import json
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request

DEFAULT_MODEL = "hf.co/unsloth/gemma-4-E2B-it-GGUF"
DEFAULT_HOST = "http://localhost:11434"


class OllamaClient:
    def __init__(self, host: str, model: str):
        self.host = host.rstrip("/")
        self.model = model

    def _request(self, path: str, payload: dict | None = None, timeout: float = 600):
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        req = urllib.request.Request(
            self.host + path,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST" if data is not None else "GET",
        )
        return urllib.request.urlopen(req, timeout=timeout)

    def is_running(self) -> bool:
        try:
            self._request("/api/version", timeout=3).close()
            return True
        except (urllib.error.URLError, OSError):
            return False

    def has_model(self) -> bool:
        with self._request("/api/tags", timeout=10) as res:
            models = json.load(res).get("models", [])
        names = {m["name"] for m in models}
        # 태그 생략 시 Ollama 는 :latest 로 취급
        return self.model in names or f"{self.model}:latest" in names

    def chat_stream(self, messages: list[dict]):
        """응답 토큰을 하나씩 yield 한다."""
        payload = {"model": self.model, "messages": messages, "stream": True}
        with self._request("/api/chat", payload) as res:
            for line in res:
                if not line.strip():
                    continue
                chunk = json.loads(line)
                if "error" in chunk:
                    raise RuntimeError(chunk["error"])
                yield chunk.get("message", {}).get("content", "")
                if chunk.get("done"):
                    break


def ensure_server(client: OllamaClient, wait_seconds: int = 30) -> None:
    """Ollama 서버가 꺼져 있으면 `ollama serve` 를 백그라운드로 자동 실행한다."""
    if client.is_running():
        return
    if shutil.which("ollama") is None:
        sys.exit("ollama 실행 파일을 찾을 수 없습니다. https://ollama.com 에서 설치하세요.")

    print("Ollama 서버가 꺼져 있어 자동으로 실행합니다...", end="", flush=True)
    kwargs: dict = {}
    if sys.platform == "win32":
        # 이 프로그램을 종료해도 서버가 계속 살아있도록 분리 + 콘솔 창 숨김
        kwargs["creationflags"] = (
            subprocess.DETACHED_PROCESS
            | subprocess.CREATE_NEW_PROCESS_GROUP
            | subprocess.CREATE_NO_WINDOW
        )
    else:
        kwargs["start_new_session"] = True
    subprocess.Popen(
        ["ollama", "serve"],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        **kwargs,
    )

    for _ in range(wait_seconds):
        if client.is_running():
            print(" 완료")
            return
        print(".", end="", flush=True)
        time.sleep(1)
    sys.exit(f"\nOllama 서버({client.host})가 {wait_seconds}초 안에 시작되지 않았습니다.")


def ensure_model(client: OllamaClient) -> None:
    if client.has_model():
        return
    print(f"모델 '{client.model}' 이(가) 로컬에 없습니다.")
    answer = input("지금 내려받을까요? (용량이 수 GB 일 수 있음) [Y/n] ").strip().lower()
    if answer in ("", "y", "yes"):
        result = subprocess.run(["ollama", "pull", client.model])
        if result.returncode != 0:
            sys.exit("모델 다운로드에 실패했습니다.")
    else:
        sys.exit(f"종료합니다. 직접 받으려면: ollama pull {client.model}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Ollama + Gemma 4 E2B 챗")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Ollama 모델 이름")
    parser.add_argument("--host", default=DEFAULT_HOST, help="Ollama 서버 주소")
    parser.add_argument("--system", default="", help="시스템 프롬프트")
    args = parser.parse_args()

    client = OllamaClient(args.host, args.model)

    ensure_server(client)
    ensure_model(client)

    system_prompt = args.system
    history: list[dict] = []

    def build_messages() -> list[dict]:
        base = [{"role": "system", "content": system_prompt}] if system_prompt else []
        return base + history

    print(f"모델: {client.model}")
    print("명령어: /reset  /system  /exit\n")

    while True:
        try:
            user_input = input("나> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n종료합니다.")
            break

        if not user_input:
            continue
        if user_input in ("/exit", "/quit"):
            break
        if user_input == "/reset":
            history.clear()
            print("[대화 기록을 초기화했습니다]\n")
            continue
        if user_input == "/system":
            system_prompt = input("새 시스템 프롬프트> ").strip()
            history.clear()
            print("[시스템 프롬프트를 변경하고 대화를 초기화했습니다]\n")
            continue

        history.append({"role": "user", "content": user_input})
        print("AI> ", end="", flush=True)
        reply = ""
        try:
            for token in client.chat_stream(build_messages()):
                reply += token
                print(token, end="", flush=True)
        except KeyboardInterrupt:
            print("\n[생성 중단]")
        except (urllib.error.URLError, RuntimeError, OSError) as e:
            print(f"\n[오류] {e}")
            history.pop()  # 실패한 질문은 기록에서 제거
            continue
        print("\n")

        if reply:
            history.append({"role": "assistant", "content": reply})
        else:
            history.pop()


if __name__ == "__main__":
    main()
