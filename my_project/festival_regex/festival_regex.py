"""
2026 전주대학교 대동제 & 밤샘 해커톤 통합 운영 로그 - 정규표현식 추출 프로그램

강의자료 [07. 람다와 정규표현식 2]에서 다룬 함수만 사용해서 작성했다.
  - re.compile()  : 패턴 객체 만들기
  - findall()     : 매칭되는 문자열을 모두 리스트로 반환 (그룹이 있으면 튜플 리스트)
  - finditer()    : 매칭 결과를 match 객체로 하나씩 반환
  - match()       : 문자열 처음부터 매칭되는지 검사
  - search()      : 문자열 전체에서 처음 매칭되는 위치 검사
  - group(), start(), end(), span() : match 객체 메서드
  - re.VERBOSE, re.MULTILINE(re.M) : 컴파일 옵션
  - lambda + map / filter / functools.reduce
"""

import os
import re
from functools import reduce

# 로그 파일은 이 스크립트와 같은 폴더에 있다고 가정한다.
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'festival_log.txt')


def load_log(path):
    """로그 파일을 UTF-8로 읽어 문자열 하나로 반환한다."""
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


# ------------------------------------------------------------------
# 정규표현식 패턴 (re.compile로 미리 컴파일해 두고 재사용한다)
# ------------------------------------------------------------------

# [1] 이메일: re.VERBOSE 옵션을 써서 패턴 안에 주석을 달았다.
EMAIL_PATTERN = re.compile(r"""
    [A-Za-z0-9._]+      # 아이디: 영문, 숫자, 점(.), 밑줄(_)이 1개 이상
    @                   # 골뱅이
    [A-Za-z0-9-]+       # 도메인 첫 부분: @ 바로 뒤에 반드시 문자가 있어야 함 (@. 제외)
    \.                  # 점
    [A-Za-z.]+          # 나머지 도메인: ac.kr / com / naver.com 등
""", re.VERBOSE)

# [2] 전화번호: 010으로 시작하고 구분자는 - . 공백 중 하나, 4자리-4자리
PHONE_PATTERN = re.compile(r'010[-. ]\d{4}[-. ]\d{4}')

# [3] 학번/학과: [202로 시작하는 9자리 학번 / 학과명] → 그룹 2개 → findall이 튜플 반환
STUDENT_PATTERN = re.compile(r'\[(202\d{6})\s*/\s*([^\]]+)\]')

# [4-1] GitHub 저장소 주소: http 또는 https, github.com/계정/저장소
GITHUB_PATTERN = re.compile(r'https?://github\.com/[\w.-]+/[\w.-]+')

# [4-2] 2026년 축제 쿠폰: FEST-2026-영문/숫자 4자리
COUPON_PATTERN = re.compile(r'FEST-2026-[A-Z0-9]{4}')

# [5] 부스별 매출: 줄 맨 앞(^)이 "- "로 시작하고 "매출: 금액원" 이 있는 줄
#     re.MULTILINE 옵션을 줘야 ^ 가 각 줄의 시작에 매칭된다.
SALES_PATTERN = re.compile(r'^- (.+) 매출: ([\d,]+)원', re.MULTILINE)


# ------------------------------------------------------------------
# 추출 함수
# ------------------------------------------------------------------

def extract_emails(text):
    return EMAIL_PATTERN.findall(text)


def extract_phones(text):
    return PHONE_PATTERN.findall(text)


def extract_students(text):
    return STUDENT_PATTERN.findall(text)       # [(학번, 학과), ...]


def extract_github(text):
    return GITHUB_PATTERN.findall(text)


def extract_coupons(text):
    return COUPON_PATTERN.findall(text)


def extract_sales(text):
    """finditer로 부스명과 매출 문자열을 뽑고, lambda로 정수 변환한다."""
    booths = []
    amounts = []
    for m in SALES_PATTERN.finditer(text):
        booths.append(m.group(1))
        amounts.append(m.group(2))

    # '1,350,000' -> 1350000  (콤마 제거 후 int 변환)
    amounts = list(map(lambda x: int(x.replace(',', '')), amounts))
    return booths, amounts


def is_full_match(pattern, s):
    """문자열 s 전체가 pattern과 정확히 일치하는지 match()와 end()로 확인한다."""
    m = pattern.match(s)
    return m is not None and m.end() == len(s)


# ------------------------------------------------------------------
# 출력
# ------------------------------------------------------------------

def print_title(title):
    print()
    print('=' * 60)
    print(title)
    print('=' * 60)


def main():
    text = load_log(LOG_FILE)

    # [1] 이메일
    print_title('[1] 유효한 이메일 주소')
    emails = extract_emails(text)
    for i, email in enumerate(emails, 1):
        print(f'{i}. {email}')
    print(f'→ 총 {len(emails)}개')

    # [2] 전화번호
    print_title('[2] 010 휴대전화 번호')
    phones = extract_phones(text)
    for i, phone in enumerate(phones, 1):
        print(f'{i}. {phone}')
    print(f'→ 총 {len(phones)}개')

    # [3] 학번 / 학과
    print_title('[3] 학번(202로 시작하는 9자리)과 학과 - 튜플')
    students = extract_students(text)
    for student in students:
        print(student)
    print(f'→ 총 {len(students)}명')

    # [4] GitHub 링크와 쿠폰
    print_title('[4] GitHub 저장소 링크 & 2026 축제 쿠폰')
    print('<GitHub>')
    for url in extract_github(text):
        print(' -', url)
    print('<쿠폰>')
    for coupon in extract_coupons(text):
        print(' -', coupon)

    # [5] 매출
    print_title('[5] 부스별 매출과 총매출')
    booths, amounts = extract_sales(text)
    for booth, amount in zip(booths, amounts):
        print(f'{booth:<20} {amount:>12,}원')

    total = reduce(lambda x, y: x + y, amounts)
    print('-' * 40)
    print(f'{"총매출":<20} {total:>12,}원')

    # 보너스: filter + lambda 로 150만 원 이상 부스만 고르기
    best = list(filter(lambda pair: pair[1] >= 1500000, zip(booths, amounts)))
    print('\n150만 원 이상 매출 부스:', [name for name, _ in best])

    # match 객체 메서드 확인 (group / start / end / span)
    print('\n<match 객체 메서드 확인 - 첫 번째 매출 줄>')
    m = SALES_PATTERN.search(text)
    print('group()  :', m.group())
    print('group(1) :', m.group(1))
    print('group(2) :', m.group(2))
    print('start()  :', m.start(), '/ end():', m.end(), '/ span():', m.span())

    # 제외 대상 검증
    print_title('[검증] 제외되어야 하는 값이 정말 걸러지는가?')
    checks = [
        ('이메일',   EMAIL_PATTERN,           'hyunwoo@.ac.kr'),
        ('전화번호', PHONE_PATTERN,           '010-123-4567'),
        ('전화번호', PHONE_PATTERN,           '063-3290-1114'),
        ('학번',     re.compile(r'202\d{6}'), '20261122'),
        ('학번',     re.compile(r'202\d{6}'), '999900000'),
        ('GitHub',   GITHUB_PATTERN,          'https://gitlab.com/yujin-dev/demo-project'),
        ('쿠폰',     COUPON_PATTERN,          'FEST-2025-OLD9'),
    ]
    for kind, pattern, value in checks:
        result = '통과' if is_full_match(pattern, value) else '제외'
        print(f'{kind:<6} {value:<45} → {result}')


if __name__ == '__main__':
    main()
