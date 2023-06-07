import pygame.draw
import pygame.font
import pygame.mixer
from pydub import AudioSegment

from component.Button import Button
from component.Audio import Audio
from setting import *
from utils.common import clamp


class Player:
    def __init__(self, setting=DEFAULT_PLAYER_SETTING):
        pygame.mixer.init()
        self._music = pygame.mixer.music

        self._playing_pos = 0
        self._volume = 50.0

        self._last = False
        self._playing = False
        self._end = False

        self._song = None

        self._song_name = SongName()
        self._audio = Audio()
        self._sound_bar = SoundBar()
        self._playback_bar = PlayBackBar()
        self._setting = setting

        self._btn_play = Button("play", (75, 75), (1015, 150))
        self._btn_pause = Button("pause", (65, 65), (1015, 150))
        self._btn_reset = Button("reset", (60, 60), (1070, 150))

    def change_song(self, filename):
        self.reset()
        self._song = filename
        self._song_name.update_song(filename[7:])
        self._playback_bar._duration = AudioSegment.from_mp3(self._song).duration_seconds
        self.set_volume()

        self.start()
        self.pause()

    def reset(self):
        self._playing_pos = 0
        self._song = None
        self._last = False
        self._playing = False
        self._end = False
        self._playback_bar.reset()
        self._song_name.reset()

    def start(self):
        self._audio.load(self._song)
        self._music.load(self._song)
        self._music.play(0)

    def restart(self):
        if self._end:
            self._playing = True

        self._end = False
        self._playing_pos = 0
        self._music.play(0)
        self._playback_bar.set_pos((0, 0))

        if not self._playing:
            self.pause()

    def check_restart(self):
        if self._end:
            self.restart()

    def reverse_state(self):
        self._playing = not self._playing

    def volume_btn_pressed(self, pos):
        if self._sound_bar.btn_volume.rect.collidepoint(pos):
            self._sound_bar.reverse_state()

    def play_btn_pressed(self, pos):
        if self._btn_pause.rect.collidepoint(pos):
            self.reverse_state()
            self.check_restart()

    def play_btn_compressed(self):
        if self._playing:
            self.unpause()
        else:
            self.pause()

    def reset_btn_pressed(self, pos):
        if self._btn_reset.rect.collidepoint(pos):
            self._btn_reset.state = True

    def reset_btn_compressed(self):
        if self._btn_reset.state:
            self.restart()
            self._btn_reset.state = False

    def play_bar_pressed(self, pos):
        if self._playback_bar.rect.collidepoint(pos) or self._playback_bar.line_rect.collidepoint(pos):
            self.set_time(self._playback_bar.set_pos(pos))
            self.last = self.playing
            self.pause()
            self._playback_bar.state = True

    def play_bar_compressed(self):
        if self._playback_bar.state:
            self._playback_bar.state = False
            if self.last:
                if not self.end:
                    self.unpause()

    def play_bar_mov(self, pos):
        if self._playback_bar.state:
            self.set_time(self._playback_bar.set_pos(pos))

    def sound_bar_pressed(self, pos):
        if self._sound_bar.rect.collidepoint(pos) or self._sound_bar.line_rect.collidepoint(pos):
            self._sound_bar.set_pos(pos)
            self._sound_bar.state = True

    def sound_bar_compressed(self):
        if self._sound_bar.state:
            self._sound_bar.state = False

    def sound_bar_mov(self, pos):
        if self._sound_bar.state:
            self._sound_bar.set_pos(pos)

    def pause(self):
        self._music.pause()
        self._playing = False

    def unpause(self):
        self._music.unpause()
        self._playing = True

    def stop(self):
        self._music.stop()

    def set_time(self, time):
        if self._end:
            self._playing_pos = 0
            self._music.play(0)
        if time >= self._playback_bar.duration:
            time = self._playback_bar.duration
        else:
            self._end = False

        self._playing_pos = self._music.get_pos() - time * 1000
        self._music.set_pos(time)
        if not self._playing:
            self._music.pause()

    def get_time(self, delta_time):
        time = (self._music.get_pos() - self._playing_pos) / 1000

        if time + delta_time >= self._playback_bar.duration:
            print("The end")
            time = self._playback_bar.duration
            self._end = True
            self._playing = False

        return time

    def get_volume(self):
        return self._music.get_volume()

    def set_volume(self):
        self._music.set_volume(self._volume / 100)

    def add_song(self, song):
        self._music.queue(song)

    def showing(self, screen, delta_time):
        self._volume = self._sound_bar.get_pos()
        self.set_volume()
        screen.blit(self._song_name.surface, (X_START, Y_START + PLAYBACK_BAR_MARGIN_TOP + 40))
        self._audio.update_bars(screen, delta_time, self.get_time(delta_time))

        if self.playing:
            screen.blit(self._btn_pause.img, self._btn_pause.rect)
            self._playback_bar.moving(self.get_time(delta_time))
        else:
            screen.blit(self._btn_play.img, self._btn_play.rect)

        screen.blit(self._btn_reset.img, self._btn_reset.rect)

        self._sound_bar.show(screen)
        self._playback_bar.show(screen)

    @property
    def playing(self):
        return self._playing

    @property
    def last(self):
        return self._last

    @last.setter
    def last(self, value):
        self._last = value

    @property
    def end(self):
        return self._end

    @property
    def song_name(self):
        return self._song_name


class SoundBar:
    def __init__(self):
        self._rect = pygame.Rect(SOUND_BAR_X_START + SOUND_BAR_LENGTH / 2 - BAR_CIRCLE_RADIUS / 2,
                                 SOUND_BAR_Y - BAR_CIRCLE_RADIUS, BAR_CIRCLE_SIZE, BAR_CIRCLE_SIZE)
        self._line_rect = pygame.Rect(SOUND_BAR_X_START - BAR_CIRCLE_RADIUS, SOUND_BAR_Y - BAR_CIRCLE_RADIUS - 10,
                                      SOUND_BAR_LENGTH + BAR_CIRCLE_SIZE, BAR_CIRCLE_SIZE + 20)

        self._btn_volume = Button("volume", (50, 50), (SOUND_BAR_X_START - 26, SOUND_BAR_Y))
        self._btn_mute = Button("mute", (50, 50), (SOUND_BAR_X_START - 26, SOUND_BAR_Y))
        self._last = 0
        self._mute = False
        self._state = False

    def get_pos(self):
        delta_x = self._rect.centerx - SOUND_BAR_X_START
        return delta_x / (SOUND_BAR_LENGTH / 100)

    def set_pos(self, pos):
        mx = clamp(SOUND_BAR_X_START, SOUND_BAR_X_END, pos[0])
        self._rect.centerx = mx
        self._mute = True if mx == SOUND_BAR_X_START else False

    def reverse_state(self):
        self._mute = not self._mute
        if self._mute:
            self._last = self._rect.centerx
            self._rect.centerx = SOUND_BAR_X_START
        else:
            self._rect.centerx = self._last

    def show(self, screen):
        cx, cy = self._rect.center
        if self._state:
            self._rect.size = BAR_CIRCLE_SIZE + 2, BAR_CIRCLE_SIZE + 2
        else:
            self._rect.size = BAR_CIRCLE_SIZE, BAR_CIRCLE_SIZE

        pygame.draw.line(screen, DEFAULT_COLOR, (SOUND_BAR_X_START, SOUND_BAR_Y), (SOUND_BAR_X_END, SOUND_BAR_Y),
                         width=LINE_WIDTH)
        gray_line = pygame.Rect(cx, SOUND_BAR_Y - LINE_WIDTH // 2,
                                SOUND_BAR_LENGTH - (cx - SOUND_BAR_X_START) + 1, LINE_WIDTH)
        pygame.draw.rect(screen, DEFAULT_COLOR_GRAY, gray_line)
        self._rect.center = cx, cy
        pygame.draw.rect(screen, DEFAULT_COLOR, self._rect, border_radius=int(self._rect.h / 2))

        if self._mute:
            screen.blit(self._btn_mute.img, self._btn_mute.rect)
        else:
            screen.blit(self._btn_volume.img, self._btn_volume.rect)

    @property
    def rect(self):
        return self._rect

    @property
    def line_rect(self):
        return self._line_rect

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, value):
        self._state = value

    @property
    def btn_volume(self):
        return self._btn_volume


class PlayBackBar:
    def __init__(self):
        self.font = pygame.font.Font("fonts/Arial.ttf", 19)
        self._rect = pygame.Rect(X_START - BAR_CIRCLE_RADIUS, PLAYBACK_BAR_Y - BAR_CIRCLE_RADIUS,
                                 BAR_CIRCLE_SIZE, BAR_CIRCLE_SIZE)
        self._line_rect = pygame.Rect(X_START - BAR_CIRCLE_RADIUS, PLAYBACK_BAR_Y - BAR_CIRCLE_RADIUS - 10,
                                      LENGTH + BAR_CIRCLE_SIZE, BAR_CIRCLE_SIZE + 20)
        self._duration = 0
        self._state = False

    def reset(self):
        self._duration = 0
        self._state = False
        self._rect = pygame.Rect(X_START - BAR_CIRCLE_RADIUS, PLAYBACK_BAR_Y - BAR_CIRCLE_RADIUS,
                                 BAR_CIRCLE_SIZE, BAR_CIRCLE_SIZE)

    def get_pos(self):
        delta_x = self._rect.centerx - X_START
        return delta_x / (LENGTH / self._duration)

    def moving(self, time):
        delta_x = time * (LENGTH / self._duration)
        self._rect.centerx = X_START + delta_x

    def set_pos(self, pos):
        mx = clamp(X_START, X_END, pos[0])
        self._rect.centerx = mx
        return self.get_pos()

    def show_time(self):
        now = int(self.get_pos())
        duration = int(self._duration)
        time = "{:>d}:{:02d} / {:>d}:{:02d}".format(now // 60, now % 60, duration // 60, duration % 60)
        time = self.font.render(time, True, DEFAULT_COLOR)
        surface = pygame.Surface((time.get_width(), time.get_height()), flags=pygame.HWSURFACE).convert_alpha()
        surface.fill((255, 255, 255, 0))
        surface.blit(time, (0, 0))
        return surface

    def show(self, screen):
        cx, cy = self._rect.center
        if self._state:
            self._rect.size = BAR_CIRCLE_SIZE + 2, BAR_CIRCLE_SIZE + 2
        else:
            self._rect.size = BAR_CIRCLE_SIZE, BAR_CIRCLE_SIZE

        pygame.draw.line(screen, DEFAULT_COLOR, (X_START, PLAYBACK_BAR_Y), (X_END, PLAYBACK_BAR_Y), width=LINE_WIDTH)
        pygame.draw.line(screen, DEFAULT_COLOR, (X_START, PLAYBACK_BAR_Y), (self._rect.centerx, PLAYBACK_BAR_Y),
                         width=LINE_WIDTH + 2)
        self._rect.center = cx, cy
        pygame.draw.rect(screen, DEFAULT_COLOR, self._rect, border_radius=int(self._rect.h / 2))
        screen.blit(self.show_time(), (X_START, Y_START + PLAYBACK_BAR_MARGIN_TOP / 2 - 11))

    @property
    def rect(self):
        return self._rect

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, value):
        self._state = value

    @property
    def duration(self):
        return self._duration

    @property
    def line_rect(self):
        return self._line_rect


class SongName:
    def __init__(self, font_size=40):
        self.font = pygame.font.Font(DEFAULT_FONT, font_size)
        self.name = None
        self.surface = None
        self.x = 0

        self.fps = 10
        self.fps_counter = pygame.USEREVENT + 1

    def reset(self):
        self.name = None
        self.surface = None
        self.x = 0

    def update_song(self, song):
        self.name = self.font.render("   " + song + "   ", True, DEFAULT_COLOR)
        self.surface = pygame.Surface((572, self.name.get_height()), flags=pygame.HWSURFACE).convert_alpha()

    def show_name(self):
        self.surface.fill((255, 255, 255, 0))
        self.x -= 1
        if self.x < -self.name.get_width():
            self.x = 0

        self.surface.blit(self.name, (self.x, 0))
        self.surface.blit(self.name, (self.x + self.name.get_width(), 0))