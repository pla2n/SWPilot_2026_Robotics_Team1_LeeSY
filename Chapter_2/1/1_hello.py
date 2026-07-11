#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
import sys

def main():
    # 1. 대상 디렉토리 및 파일 경로 설정
    target_dir = Path('/test')
    filepath = target_dir / 'result.txt'
    
    # 2. 디렉토리 존재 여부 확인 (예외 방지)
    if not target_dir.exists():
        print(f"[오류] {target_dir} 디렉토리가 존재하지 않습니다.")
        print(">> 해결: 터미널에서 'sudo mkdir /test' 명령어를 실행하여 디렉토리를 먼저 생성해주세요.")
        sys.exit(1)
        
    # 3. 파일 생성 및 쓰기 시도 (권한 예외 처리 포함)
    try:
        with filepath.open("w", encoding="utf-8") as file:
            file.write("Hello Linux\n")
        print(f"[성공] {filepath} 파일에 'Hello Linux' 작성을 완료했습니다.")
        
    except PermissionError:
        # 일반 사용자 권한으로 루트 디렉토리에 접근할 때 발생하는 에러 처리
        print(f"[권한 오류] {filepath}에 파일을 쓸 수 있는 권한이 없습니다.")
        print(">> 해결: 루트 디렉토리 접근을 위해 최고 관리자 권한이 필요합니다. 'sudo python3 1_hello.py'로 실행해주세요.")
        sys.exit(1)
        
    except Exception as e:
        print(f"[예외 발생] 알 수 없는 오류가 발생했습니다: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()