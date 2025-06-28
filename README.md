# 사용하는 방법
!hint 로 기본 명령어 확인 가능

!join - 음성 채널에 봇을 입장시킵니다.

!add [유튜브 URL] - 유튜브 URL을 예약 큐에 추가하고 제목을 가져옵니다.

!play [유튜브 URL] - 지정한 URL의 음원을 즉시 재생합니다.

!playlist - 예약 큐에 있는 곡들의 목록을 출력합니다.

!delete - 현재 재생 중인 음원을 취소합니다.

!delete_index [인덱스] - 예약 큐에서 지정한 인덱스의 곡을 제거합니다.

!leave - 봇이 음성 채널에서 퇴장합니다.

# 서버 열기 귀찮으면 코랩에서 실행 가능
https://colab.research.google.com/drive/1X7XmM2_11FSm5VyuZOZbK2WRCRANLMQi?usp=sharing#scrollTo=9SpbXeZkvpJE


# 라즈베리파이 기준이기 때문에 원도우에서는 추가적인 설정이 필요할 수 있음
## 초기 설정

### 가상환경 생성

    python3 -m venv venv

### 가상환경 활성화 (bash 기준)

    source venv/bin/activate

### 라이브러리 설치

    pip install discord.py yt_dlp
    pip install PyNaCl
    sudo apt install ffmpeg
    windows에서 실행하는 경우 main_windows.py의 41번 줄의 경로를 ffmpeg.exe파일 위치로 수정

## 인터넷 업로드 속도가 느린 환경이라면 
    11번 줄의 'options': '-vn' 을 'options': '-vn -b:a 64k' 으로 수정
    16번 줄의 'format': 'bestaudio/best', 을 'format': 'bestaudio[abr<=64]', 으로 수정

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
