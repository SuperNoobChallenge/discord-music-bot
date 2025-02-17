import discord
from discord.ext import commands
import yt_dlp
import asyncio
from collections import defaultdict, deque
import concurrent.futures

# FFmpeg 옵션 설정
ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

# 유튜브 DL 옵션
ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'
}

# 서버(길드)별 예약 큐 및 수동 스킵 플래그
queues = defaultdict(deque)
manual_skip = defaultdict(bool)

intents = discord.Intents.default()
intents.message_content = True

# CPU-bound 작업에 적합한 프로세스 풀 생성 (원하는 코어 수를 max_workers로 지정 가능)
process_executor = concurrent.futures.ProcessPoolExecutor(max_workers=4)
API_KEY = ''

def make_pickleable(obj):
    """
    재귀적으로 객체를 순회하며 dict, list, tuple 등 표준 파이썬 객체로 변환합니다.
    """
    if isinstance(obj, dict):
        return {k: make_pickleable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [make_pickleable(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(make_pickleable(item) for item in obj)
    # dict-like한 객체 (예: HTTPHeaderDict 등)를 일반 dict로 변환 시도
    elif hasattr(obj, 'keys') and hasattr(obj, '__getitem__'):
        try:
            return dict(obj)
        except Exception:
            return obj
    else:
        return obj

def run_extraction(url, download):
    ytdl_instance = yt_dlp.YoutubeDL(ytdl_format_options)
    data = ytdl_instance.extract_info(url, download=download)
    # 반환된 데이터를 피클링 가능한 객체로 변환
    data = make_pickleable(data)
    return data

async def get_title(url):
    loop = asyncio.get_event_loop()
    data = await loop.run_in_executor(process_executor, run_extraction, url, False)
    if 'entries' in data:
        data = data['entries'][0]
    return data.get('title', '제목 없음')

ffmpeg_executable = r"C:\ffmpeg\bin\ffmpeg.exe"
class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(process_executor, run_extraction, url, not stream)
        if 'entries' in data:
            data = data['entries'][0]
        filename = data['url'] if stream else yt_dlp.YoutubeDL(ytdl_format_options).prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, executable=ffmpeg_executable, **ffmpeg_options), data=data)


# Bot 클래스를 상속받아 setup_hook() 내에서 비동기 작업을 스케줄합니다.
class MyBot(commands.Bot):
    async def setup_hook(self):
        # 봇이 준비되면 auto_disconnect_loop()를 백그라운드로 실행합니다.
        self.loop.create_task(self.auto_disconnect_loop())

    async def auto_disconnect_loop(self):
        await self.wait_until_ready()
        while not self.is_closed():
            for vc in self.voice_clients:
                # vc.channel.members에는 봇 자신도 포함되므로, 봇 혼자 있을 경우 길이==1
                if len(vc.channel.members) == 1:
                    try:
                        if vc.guild.text_channels:
                            await vc.guild.text_channels[0].send("채널에 아무도 없어 자동으로 퇴장합니다.")
                    except Exception as e:
                        print(f"알림 전송 오류: {e}")
                    await vc.disconnect()
            await asyncio.sleep(300)  # 300초, 즉 5분 대기
bot = MyBot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')

@bot.command()
async def join(ctx):
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        await channel.connect()
        await ctx.send(f"{channel} 채널에 입장했습니다.")
    else:
        await ctx.send("음성 채널에 먼저 접속해주세요.")

@bot.command()
async def add(ctx, *, url):
    if ctx.voice_client is None:
        if ctx.author.voice:
            await ctx.author.voice.channel.connect()
        else:
            return await ctx.send("음성 채널에 연결되어 있지 않습니다.")
    async with ctx.typing():
        try:
            title = await get_title(url)
        except Exception as e:
            await ctx.send(f"정보 추출 실패: {e}")
            return
    guild_id = ctx.guild.id
    queues[guild_id].append((url, title))
    await ctx.send(f"예약에 추가되었습니다: {title}")
    if ctx.voice_client and not ctx.voice_client.is_playing():
        await play_next(ctx.guild)

@bot.command()
async def play(ctx, *, url):
    if ctx.voice_client is None:
        if ctx.author.voice:
            await ctx.author.voice.channel.connect()
        else:
            return await ctx.send("음성 채널에 연결되어 있지 않습니다.")
    if ctx.voice_client.is_playing():
        manual_skip[ctx.guild.id] = True
        ctx.voice_client.stop()
    async with ctx.typing():
        player = await YTDLSource.from_url(url, loop=bot.loop, stream=True)
        ctx.voice_client.play(player, after=lambda e: bot.loop.create_task(after_play(ctx.guild)))
    await ctx.send(f"재생 중: {player.title}")

async def after_play(guild):
    if manual_skip.get(guild.id, False):
        manual_skip[guild.id] = False
        return
    await play_next(guild)

async def play_next(guild):
    voice_client = discord.utils.get(bot.voice_clients, guild=guild)
    if voice_client is None:
        return
    if not voice_client.is_playing() and queues[guild.id]:
        next_item = queues[guild.id].popleft()
        if isinstance(next_item, tuple):
            next_url, queued_title = next_item
        else:
            next_url = next_item
            queued_title = None
        try:
            player = await YTDLSource.from_url(next_url, loop=bot.loop, stream=True)
        except Exception as e:
            print(f"예약된 노래 재생 오류: {e}")
            if guild.system_channel:
                await guild.system_channel.send(f"예약된 노래 재생 오류: {e}")
            return
        voice_client.play(player, after=lambda e: bot.loop.create_task(after_play(guild)))
        if guild.text_channels:
            channel = guild.text_channels[0]
            await channel.send(f"재생 중: {player.title}")

@bot.command()
async def playlist(ctx):
    guild_id = ctx.guild.id
    if not queues[guild_id]:
        await ctx.send("예약된 곡이 없습니다.")
        return
    msg = "현재 예약된 곡 목록:\n"
    for idx, item in enumerate(queues[guild_id], start=1):
        if isinstance(item, tuple):
            title = item[1]
        else:
            try:
                title = await get_title(item)
            except Exception:
                title = item
        msg += f"{idx}. {title}\n"
    await ctx.send(msg)

@bot.command()
async def delete(ctx):
    if ctx.voice_client.is_playing():
        ctx.voice_client.stop()

@bot.command(name="delete_index")
async def delete_index(ctx, *, idx: int):
    guild_id = ctx.guild.id
    if 0 < idx <= len(queues[guild_id]):
        temp_list = list(queues[guild_id])
        removed = temp_list.pop(idx - 1)
        queues[guild_id] = deque(temp_list)
        if isinstance(removed, tuple):
            removed_title = removed[1]
        else:
            removed_title = removed
        await ctx.send(f"예약 큐에서 제거되었습니다: {removed_title}")
    else:
        await ctx.send("유효하지 않은 인덱스입니다.")

@bot.command()
async def hint(ctx):
    help_text = (
        "**봇 명령어 도움말**\n\n"
        "**!join** - 음성 채널에 봇을 입장시킵니다.\n"
        "**!add [유튜브 URL]** - 유튜브 URL을 예약 큐에 추가하고 제목을 가져옵니다.\n"
        "**!play [유튜브 URL]** - 지정한 URL의 음원을 즉시 재생합니다.\n"
        "**!playlist** - 예약 큐에 있는 곡들의 목록을 출력합니다.\n"
        "**!delete** - 현재 재생 중인 음원을 취소합니다.\n"
        "**!delete_index [인덱스]** - 예약 큐에서 지정한 인덱스의 곡을 제거합니다.\n"
        "**!leave** - 봇이 음성 채널에서 퇴장합니다."
    )
    await ctx.send(help_text)

@bot.command()
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("음성 채널에서 퇴장했습니다.")

if __name__ == '__main__':
    bot.run(API_KEY)
