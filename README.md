# 사용하는 방법
!hint 로 기본 명령어 확인 가능

## 초기 설정

### 가상환경 생성

    python3 -m venv venv

### 가상환경 활성화 (bash 기준)

    source venv/bin/activate

### 라이브러리 설치

    pip install discord.py yt_dlp
    pip install PyNaCl
    sudo apt install ffmpeg

## 코드 실행

    # 디스코드 봇 생성
    추천 글 : https://scvtwo.tistory.com/196

    BOT PERMISSIONS 에서 체크할 항목
        (Text Permission)
        Send Messages
        Read Message History
        Embed Links
        Use External Emojis
        Add Reactions
        Attach Files

        (Voice Permission)
        Connect
        Speak

    토큰 복사해서 main.py 38번줄 'YOUR API KEY' 안쪽에 삽입
    37번 줄 max_workers = 4 사용할 CPU 코어 수로 수정
    가상환경 활성화한 다음 아래 명령어를 콘솔에 입력해 실행
    python main.py

## 자동 실행(선택사항)

    # PM2 설치치
    sudo apt update
    sudo apt install nodejs npm
    sudo npm install -g pm2

    # 자동 실행 설정
    프로젝트 폴더에서
    pm2 start ./main.py --interpreter ./venv/bin/python
    pm2 startup
    하고 출력되는 문장에서 command: 뒤 문장 복사 후 실행
    ex) 
    username@raspberrypi:~ $ pm2 startup
    [PM2] Init System found: systemd
    [PM2] To setup the Startup Script, copy/paste the following command: sudo env PATH=$PATH:/usr/bin /usr/local/lib/node_modules/pm2/bin/pm2 startup systemd -u username --hp /home/username
    
    command:뒤의 문장 실행
    sudo env PATH=$PATH:/usr/bin /usr/local/lib/node_modules/pm2/bin/pm2 startup systemd -u username --hp /home/username

    pm2 save
    끝
