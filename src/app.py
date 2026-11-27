"""Oyun motoru ile grafik katmanını birbirine bağlar: ekran akışı, girdi, HUD ve ses."""
import math
import random
import time
from datetime import datetime
from enum import Enum
from pathlib import Path

import numpy as np

from src.audio import SoundBank
from src.contest.ai import ai_players, simulate_round
from src.contest.balls import BallType
from src.contest.locations import MAIN_LOCATIONS, SPOT_LABELS
from src.contest.records import HighScores, ScoreRecord
from src.contest.scoring import ShotStatus
from src.contest.timer import ROUND_SECONDS, format_clock
from src.contest.tournament import PHASE_LABELS, Player, Tournament
from src.game import layout
from src.game.round import GameRound, RoundPhase
from src.graphics.ball_object import preview_balls, round_balls
from src.graphics.camera import CameraMode, CameraRig
from src.graphics.hud import HUD
from src.graphics.renderer import Renderer
from src.graphics.utils.image import save_png
from src.physics.shot import SWEET_SPOT

WHITE = (1, 1, 1, 1)
GREY = (0.6, 0.62, 0.68, 1)
GOLD = (1.0, 0.82, 0.25, 1)
RED = (1.0, 0.3, 0.3, 1)
GREEN = (0.35, 0.95, 0.45, 1)
BLUE = (0.35, 0.65, 1.0, 1)
PANEL = (0.02, 0.03, 0.08, 0.72)

BALL_COLORS = {
    BallType.NBA: (0.93, 0.48, 0.13, 1),
    BallType.MONEY: (0.9, 0.2, 0.25, 1),
    BallType.BLUE_MONEY: (0.25, 0.55, 1.0, 1),
}
SHORT_LABELS = {"corner_left": "SK", "wing_left": "SKN", "logo_left": "SL", "center": "T",
                "logo_right": "GL", "wing_right": "GKN", "corner_right": "GK"}


class Mode(Enum):
    MENU = "menu"
    SELECT_RACK = "select_rack"
    PLAYING = "playing"
    SUMMARY = "summary"
    STANDINGS = "standings"
    FINISHED = "finished"


class App:
    def __init__(self, ctx, window=None, player_name: str = "OYUNCU", seed: int | None = None,
                 mute: bool = False, scores_path: Path | str | None = None):
        self.ctx = ctx
        self.window = window
        self.renderer = Renderer(ctx)
        self.hud = HUD(ctx)
        self.rig = CameraRig()
        self.sound = SoundBank(enabled=not mute and window is not None)
        self.rng = random.Random(seed)
        self.player_name = player_name.upper()[:14]
        self.highscores = HighScores(scores_path) if scores_path else HighScores()

        self.mode = Mode.MENU
        self.time = 0.0
        self.fps = 0.0
        self.rack_choice = len(MAIN_LOCATIONS) - 1
        self.round: GameRound | None = None
        self.tournament: Tournament | None = None
        self.ai_profiles = {}
        self.ai_log: list[str] = []
        self.human: Player | None = None
        self.round_duration = ROUND_SECONDS
        self.round_phase_label = "ANTRENMAN"
        self.last_rank: int | None = None
        self.messages: list[list] = []   # [metin, renk, kalan_süre, boyut]
        self.show_help = False
        self.status_line = ""

    # ==================================================================
    # Akış
    def start_practice(self) -> None:
        self.tournament = None
        self.round_duration = ROUND_SECONDS
        self.round_phase_label = "ANTRENMAN"
        self.mode = Mode.SELECT_RACK

    def start_tournament(self) -> None:
        self.ai_profiles = ai_players(7, self.rng)
        self.human = Player(self.player_name, human=True)
        self.tournament = Tournament([self.human, *self.ai_profiles], self.rng)
        self.ai_log = []
        self._run_ai_turns()
        self.mode = Mode.STANDINGS

    def _run_ai_turns(self) -> None:
        t = self.tournament
        while t.current_turn is not None and not t.current_turn.player.human:
            turn = t.current_turn
            seq = simulate_round(self.ai_profiles[turn.player], turn.duration, self.rng)
            t.submit_score(seq.score)
            self.ai_log.append(f"{turn.player.name}: {seq.score}")

    def begin_round(self) -> None:
        money_rack = MAIN_LOCATIONS[self.rack_choice].name
        if self.tournament is not None:
            turn = self.tournament.current_turn
            self.round_duration = turn.duration
            self.round_phase_label = PHASE_LABELS[turn.phase]
        self.round = GameRound(money_rack, self.round_duration, rng=self.rng)
        self.rig.mode = CameraMode.SHOOTER
        self.rig.update(0.0, self.round.player_position(), snap=True)
        self.messages.clear()
        self.mode = Mode.PLAYING

    def finish_round(self) -> None:
        score = self.round.score
        mode = "tournament" if self.tournament is not None else "practice"
        self.last_rank = self.highscores.add(ScoreRecord(self.player_name, score, mode))
        try:
            self.highscores.save()
        except OSError:
            pass
        self.mode = Mode.SUMMARY

    def continue_after_summary(self) -> None:
        if self.tournament is None:
            self.mode = Mode.MENU
            return
        self.tournament.submit_score(self.round.score)
        self._run_ai_turns()
        self.mode = Mode.FINISHED if self.tournament.finished else Mode.STANDINGS

    def continue_after_standings(self) -> None:
        if self.tournament.finished:
            self.mode = Mode.FINISHED
        else:
            self.mode = Mode.SELECT_RACK

    # ==================================================================
    # Girdi
    def handle_input(self, dt: float) -> None:
        import glfw
        w = self.window
        for key, action, _mods in w.key_events:
            if action != glfw.PRESS:
                if key == glfw.KEY_SPACE and self.mode is Mode.PLAYING and action == glfw.RELEASE:
                    self.round.release()
                continue
            if key == glfw.KEY_F12:
                self.screenshot()
            elif key == glfw.KEY_F1:
                self.show_help = not self.show_help
            elif key == glfw.KEY_C:
                mode = self.rig.cycle()
                self.flash(f"KAMERA: {mode.value}", WHITE, 1.2, 3)
            self._on_key(key)

        if self.rig.mode is CameraMode.FREE:
            fwd = (glfw.KEY_W in w.keys_down) - (glfw.KEY_S in w.keys_down)
            right = (glfw.KEY_D in w.keys_down) - (glfw.KEY_A in w.keys_down)
            up = (glfw.KEY_E in w.keys_down) - (glfw.KEY_Q in w.keys_down)
            self.rig.move(fwd, right, up, dt)
            if glfw.MOUSE_BUTTON_RIGHT in w.mouse_buttons or glfw.MOUSE_BUTTON_LEFT in w.mouse_buttons:
                self.rig.rotate(*w.mouse_delta)
        if w.scroll:
            self.rig.zoom(w.scroll)

    def _on_key(self, key: int) -> None:
        import glfw
        m = self.mode
        if m is Mode.MENU:
            if key in (glfw.KEY_ENTER, glfw.KEY_KP_ENTER, glfw.KEY_T):
                self.start_tournament()
            elif key == glfw.KEY_P:
                self.start_practice()
            elif key == glfw.KEY_ESCAPE:
                self.window.close()
        elif m is Mode.SELECT_RACK:
            if key in (glfw.KEY_LEFT, glfw.KEY_A):
                self.rack_choice = (self.rack_choice - 1) % len(MAIN_LOCATIONS)
            elif key in (glfw.KEY_RIGHT, glfw.KEY_D):
                self.rack_choice = (self.rack_choice + 1) % len(MAIN_LOCATIONS)
            elif glfw.KEY_1 <= key <= glfw.KEY_5:
                self.rack_choice = key - glfw.KEY_1
            elif key in (glfw.KEY_ENTER, glfw.KEY_KP_ENTER):
                self.begin_round()
            elif key == glfw.KEY_ESCAPE:
                self.mode = Mode.MENU
        elif m is Mode.PLAYING:
            if key == glfw.KEY_SPACE:
                self.round.press()
            elif key == glfw.KEY_TAB:
                if self.round.skip():
                    self.flash("LOGO ATLANDI - MAVI MONEY ELENIR", GREY, 1.6, 3)
            elif key == glfw.KEY_ESCAPE:
                self.round = None
                self.tournament = None
                self.mode = Mode.MENU
        elif m is Mode.SUMMARY:
            if key in (glfw.KEY_ENTER, glfw.KEY_KP_ENTER, glfw.KEY_SPACE):
                self.continue_after_summary()
        elif m is Mode.STANDINGS:
            if key in (glfw.KEY_ENTER, glfw.KEY_KP_ENTER, glfw.KEY_SPACE):
                self.continue_after_standings()
            elif key == glfw.KEY_ESCAPE:
                self.mode = Mode.MENU
        elif m is Mode.FINISHED:
            if key in (glfw.KEY_ENTER, glfw.KEY_KP_ENTER, glfw.KEY_ESCAPE):
                self.tournament = None
                self.mode = Mode.MENU

    # ==================================================================
    # Güncelleme
    def flash(self, text: str, color=WHITE, duration: float = 1.2, size: float = 5) -> None:
        self.messages.append([text, color, duration, size])

    def update(self, dt: float) -> None:
        self.time += dt
        for msg in self.messages:
            msg[2] -= dt
        self.messages = [m for m in self.messages if m[2] > 0][-4:]

        if self.mode is Mode.PLAYING and self.round is not None:
            self.round.update(dt)
            self._handle_round_events()
            focus = self.round.flying[-1].body.position if self.round.flying else None
            self.rig.update(dt, self.round.player_position(), focus)
            if self.round.done:
                self.finish_round()
        elif self.mode is Mode.PLAYING:
            self.mode = Mode.MENU
        elif self.mode is Mode.SELECT_RACK:
            if self.rig.mode is CameraMode.SHOOTER:
                self.rig.mode = CameraMode.BROADCAST
            spot = MAIN_LOCATIONS[self.rack_choice].name
            self.rig.update(dt, layout.SPOT_POSITIONS[spot])
        elif self.mode in (Mode.MENU, Mode.STANDINGS, Mode.FINISHED):
            if self.rig.mode is CameraMode.FREE:
                self.rig.update(dt, (0, 0))
            else:
                a = self.time * 0.12
                self.rig.camera.eye = np.array([math.sin(a) * 15.0, 6.5, 6.0 + math.cos(a) * 13.0])
                self.rig.camera.target = np.array([0.0, 1.8, 3.5])

    def _handle_round_events(self) -> None:
        for kind, data in self.round.drain_events():
            if kind == "made":
                if data["void"]:
                    self.flash("GIRDI AMA SAYILMADI", RED, 1.3)
                    self.sound.play("swish")
                else:
                    pts = data["points"]
                    color = BALL_COLORS[data["ball"]] if data["ball"] is not BallType.NBA else GREEN
                    label = {1: "+1", 2: "+2 MONEY!", 3: "+3 LOGO!"}[pts]
                    self.flash(label, color, 1.0, 7 if pts > 1 else 6)
                    self.sound.play("money" if pts > 1 else "swish")
            elif kind == "void":
                text = {ShotStatus.VOID_OUT_OF_SEQUENCE: "SIRA DISI - GECERSIZ",
                        ShotStatus.VOID_ELIMINATED: "ELENMIS TOP - GECERSIZ",
                        ShotStatus.VOID_LINE_VIOLATION: "CIZGI IHLALI"}[data["status"]]
                self.flash(text, RED, 1.4, 3)
            elif kind == "rim":
                self.sound.play("rim")
            elif kind == "board":
                self.sound.play("board")
            elif kind == "floor":
                self.sound.play("bounce")
            elif kind == "buzzer":
                self.flash("SURE DOLDU!", RED, 2.0, 6)
                self.sound.play("buzzer")
            elif kind == "all_shot":
                self.flash("TUM TOPLAR ATILDI!", GOLD, 2.0, 5)
            elif kind == "countdown":
                self.sound.play("tick")
            elif kind == "go":
                self.flash("BASLA!", GOLD, 0.9, 9)
                self.sound.play("go")

    # ==================================================================
    # Çizim
    def net_sway(self) -> float:
        if self.round is None:
            return 0.0
        t = self.round.time - self.round.last_made_time
        if t < 0 or t > 2.5:
            return 0.0
        return math.exp(-2.2 * t) * (0.55 + 0.45 * math.cos(t * 13.0))

    def draw(self, fbo, size: tuple[int, int]) -> None:
        player = None
        highlight = None
        if self.mode is Mode.PLAYING and self.round is not None:
            balls = round_balls(self.round)
            money_rack = self.round.seq.money_rack
            if self.rig.mode is not CameraMode.SHOOTER:
                player = (self.round.player_position(), self.round.facing())
        else:
            money_rack = MAIN_LOCATIONS[self.rack_choice].name
            balls = preview_balls(money_rack)
            if self.mode is Mode.SELECT_RACK:
                highlight = layout.SPOT_POSITIONS[money_rack]
        self.renderer.render(fbo, size, self.rig.camera, balls, money_rack, self.time,
                             self.net_sway(), highlight, player)
        self.draw_hud(*size)
        self.hud.flush(*size)

    def draw_hud(self, w: int, h: int) -> None:
        {
            Mode.MENU: self._hud_menu,
            Mode.SELECT_RACK: self._hud_select,
            Mode.PLAYING: self._hud_playing,
            Mode.SUMMARY: self._hud_summary,
            Mode.STANDINGS: self._hud_standings,
            Mode.FINISHED: self._hud_standings,
        }[self.mode](w, h)
        hud = self.hud
        if self.window is not None:
            hud.text(w - 12, 10, f"{self.fps:4.0f} FPS", 2, GREY, align="right")
        for i, (text, color, remaining, size) in enumerate(self.messages):
            alpha = min(1.0, remaining * 3)
            rise = (1.0 - min(1.0, remaining)) * 30
            hud.text(w / 2, h * 0.30 + i * (size * 10) - rise, text, size, (*color[:3], alpha), align="center")
        if self.show_help:
            self._hud_help(w, h)

    # --- ekranlar ------------------------------------------------------
    def _hud_menu(self, w, h):
        hud = self.hud
        hud.rect(0, 0, w, h, (0, 0, 0, 0.3))
        hud.rect(w / 2 - 330, h * 0.42 - 30, 660, 400, PANEL)
        hud.text(w / 2, h * 0.14, "3 POINT CONTEST", 10, GOLD, align="center")
        hud.text(w / 2, h * 0.14 + 85, "MODERNGL UCLUK YARISMASI SIMULASYONU", 3, WHITE, align="center")
        y = h * 0.42
        for line, color in (("ENTER  TURNUVA (8 OYUNCU, 2 TUR)", WHITE), ("P      ANTRENMAN (70 SN)", WHITE),
                            ("F1     KONTROLLER", GREY), ("ESC    CIKIS", GREY)):
            hud.text(w / 2 - 260, y, line, 4, color)
            y += 42
        top = self.highscores.top(5)
        y += 30
        hud.text(w / 2, y, "EN YUKSEK SKORLAR", 3, GOLD, align="center")
        y += 34
        if not top:
            hud.text(w / 2, y, "HENUZ KAYIT YOK", 3, GREY, align="center")
        for i, r in enumerate(top, 1):
            mode = "TURNUVA" if r.mode == "tournament" else "ANTRENMAN"
            hud.text(w / 2 - 280, y, f"{i}. {r.name:<14} {r.score:>3}  {mode:<9} {r.date[:10]}", 3, WHITE)
            y += 28

    def _hud_select(self, w, h):
        hud = self.hud
        spot = MAIN_LOCATIONS[self.rack_choice].name
        hud.rect(0, h - 190, w, 190, PANEL)
        hud.text(w / 2, h - 175, "ALL MONEY RACK NEREDE OLSUN?", 4, GOLD, align="center")
        x0 = w / 2 - 5 * 230 / 2
        for i, s in enumerate(MAIN_LOCATIONS):
            selected = i == self.rack_choice
            x = x0 + i * 230
            hud.rect(x + 5, h - 125, 220, 50, (0.85, 0.15, 0.2, 0.9) if selected else (0.15, 0.17, 0.25, 0.85))
            hud.text(x + 115, h - 110, f"{i + 1} {SPOT_LABELS[s.name]}", 3, WHITE, align="center")
        hud.text(w / 2, h - 55, "<- ->  VEYA 1-5 SEC     ENTER BASLA     ESC GERI", 3, GREY, align="center")
        if self.tournament is not None and self.tournament.current_turn is not None:
            turn = self.tournament.current_turn
            hud.text(20, 20, f"{PHASE_LABELS[turn.phase]} - SIRA SENDE ({int(turn.duration)} SN)", 3, GOLD)
        hud.text(20, 50, f"SECIM: {SPOT_LABELS[spot]}  (5 MONEY TOPU, HER BIRI 2 PUAN)", 3, WHITE)

    def _hud_playing(self, w, h):
        hud, r = self.hud, self.round
        # Süre
        remaining = r.timer.remaining
        clock_color = RED if remaining < 10 and r.phase is RoundPhase.LIVE else WHITE
        hud.rect(w / 2 - 120, 8, 240, 80, PANEL)
        hud.text(w / 2, 18, format_clock(remaining), 8, clock_color, align="center")
        hud.rect(w / 2 - 110, 78, 220 * remaining / r.timer.duration, 5, clock_color)
        # Skor ve oyuncu
        hud.rect(w - 230, 34, 218, 90, PANEL)
        hud.text(w - 220, 44, "SKOR", 3, GREY)
        hud.text(w - 24, 60, str(r.score), 8, GOLD, align="right")
        hud.rect(12, 8, 400, 92, PANEL)
        hud.text(24, 18, self.player_name, 4, WHITE)
        hud.text(24, 52, self.round_phase_label, 3, GOLD)
        hud.text(24, 76, f"KAMERA: {self.rig.mode.value}  KALAN TOP: {r.seq.balls_left}", 2, GREY)
        # Geri sayım
        if r.phase is RoundPhase.COUNTDOWN:
            hud.text(w / 2, h * 0.38, str(math.ceil(r.countdown)), 16, GOLD, align="center")
        self._hud_rack_tracker(w, h)
        self._hud_meter(w, h)
        hints = "SPACE: BASILI TUT, YESIL ALANDA BIRAK   C: KAMERA   F1: YARDIM   ESC: MENU"
        if r.can_skip:
            hints = "TAB: LOGOYU ATLA   " + hints
        hud.text(w / 2, h - 22, hints, 2, GREY, align="center")

    def _hud_rack_tracker(self, w, h):
        hud, r = self.hud, self.round
        box, gap, group_gap = 20, 4, 22
        widths = [len(s.balls) * (box + gap) - gap for s in r.stations]
        total = sum(widths) + group_gap * (len(widths) - 1)
        x = w / 2 - total / 2
        y = h - 96
        hud.rect(x - 16, y - 34, total + 32, 72, PANEL)
        result_for = {(res.station, res.ball_index): res for res in r.seq.results}
        for si, (station, width) in enumerate(zip(r.stations, widths)):
            current = si == r.player_station
            hud.text(x + width / 2, y - 26, SHORT_LABELS[station.name], 2, GOLD if current else GREY, align="center")
            if current:
                hud.frame(x - 4, y - 4, width + 8, box + 8, GOLD, 2)
            for bi, ball in enumerate(station.balls):
                bx = x + bi * (box + gap)
                color = BALL_COLORS[ball.type]
                res = result_for.get((station.name, bi))
                if ball.eliminated and res is None:
                    hud.rect(bx, y, box, box, (0.25, 0.25, 0.3, 0.9))
                    hud.rect(bx + 3, y + box / 2 - 1, box - 6, 3, RED)
                elif res is None:
                    hud.rect(bx, y, box, box, color)
                elif res.status is ShotStatus.PENDING:
                    hud.frame(bx, y, box, box, WHITE, 2)
                elif res.status is ShotStatus.MADE:
                    hud.rect(bx, y, box, box, GREEN)
                    hud.frame(bx, y, box, box, color, 3)
                elif res.status is ShotStatus.MISSED:
                    hud.rect(bx, y, box, box, (0.18, 0.18, 0.22, 0.9))
                else:
                    hud.rect(bx, y, box, box, (0.5, 0.05, 0.08, 0.95))
                    hud.text(bx + box / 2, y + 3, "X", 2, WHITE, align="center", shadow=False)
            x += width + group_gap

    def _hud_meter(self, w, h):
        hud, r = self.hud, self.round
        bw, bh = 34, 260
        x, y = w - 80, h / 2 - bh / 2
        hud.rect(x - 8, y - 36, bw + 16, bh + 52, PANEL)
        hud.text(x + bw / 2, y - 28, "GUC", 2, GREY, align="center")
        hud.rect(x, y, bw, bh, (0.12, 0.12, 0.16, 1))
        zone_lo, zone_hi = SWEET_SPOT - 0.05, SWEET_SPOT + 0.05
        hud.rect(x, y + bh * (1 - zone_hi), bw, bh * (zone_hi - zone_lo), (0.2, 0.75, 0.3, 0.85))
        value = r.meter.value if r.meter.charging else 0.0
        if value > 0:
            good = abs(value - SWEET_SPOT) <= 0.05
            hud.rect(x + 5, y + bh * (1 - value), bw - 10, bh * value, GREEN if good else (1.0, 0.65, 0.2, 0.95))
        hud.frame(x, y, bw, bh, WHITE, 2)

    def _hud_summary(self, w, h):
        hud, r = self.hud, self.round
        hud.rect(w / 2 - 360, h * 0.2, 720, 420, PANEL)
        hud.text(w / 2, h * 0.2 + 25, "TUR BITTI", 6, GOLD, align="center")
        hud.text(w / 2, h * 0.2 + 95, f"{r.score} PUAN", 10, WHITE, align="center")
        made = sum(1 for res in r.seq.results if res.status is ShotStatus.MADE)
        shots = len(r.seq.results)
        void = sum(1 for res in r.seq.results if res.status.is_void)
        pct = 100 * made / shots if shots else 0
        y = h * 0.2 + 200
        for line in (f"ISABET: {made}/{shots}  (%{pct:.0f})", f"GECERSIZ ATIS: {void}",
                     f"MONEY RACK: {SPOT_LABELS[r.seq.money_rack]}"):
            hud.text(w / 2, y, line, 3, WHITE, align="center")
            y += 34
        if self.last_rank is not None and self.last_rank <= 5:
            hud.text(w / 2, y + 10, f"REKOR TABLOSUNDA {self.last_rank}. SIRA!", 4, GOLD, align="center")
        hud.text(w / 2, h * 0.2 + 385, "ENTER: DEVAM", 3, GREY, align="center")

    def _hud_standings(self, w, h):
        hud, t = self.hud, self.tournament
        if t is None:
            return
        hud.rect(40, 30, w - 80, h - 60, PANEL)
        title = "TURNUVA BITTI" if t.finished else PHASE_LABELS[t.phase]
        hud.text(w / 2, 50, title, 6, GOLD, align="center")

        col_x = 80
        y = 130
        hud.text(col_x, y, "ILK TUR", 4, GOLD)
        y += 44
        for p in t.order:
            score = t.first_round_scores.get(p)
            marker = ">" if p in t.finalists else " "
            color = BLUE if p.human else WHITE
            champ = " (S)" if p.defending_champion else ""
            hud.text(col_x, y, f"{marker} {p.name + champ:<18} {'-' if score is None else score:>3}", 3, color)
            y += 30

        col_x = w / 2 + 20
        y = 130
        for i, tb in enumerate(t.tiebreakers, 1):
            hud.text(col_x, y, f"{PHASE_LABELS[tb.phase]} #{i}", 3, GOLD)
            y += 32
            for p, score in tb.scores.items():
                hud.text(col_x, y, f"  {p.name:<18} {score:>3}", 3, BLUE if p.human else WHITE)
                y += 28
            y += 10
        if t.finalists or t.championship_scores:
            hud.text(col_x, y, "SAMPIYONLUK TURU", 4, GOLD)
            y += 44
            for p in sorted(t.finalists, key=lambda p: t.first_round_scores[p]):
                score = t.championship_scores.get(p)
                hud.text(col_x, y, f"  {p.name:<18} {'-' if score is None else score:>3}", 3,
                         BLUE if p.human else WHITE)
                y += 30

        if t.finished:
            hud.text(w / 2, h - 130, f"SAMPIYON: {t.champion.name}", 7, GOLD, align="center")
            hud.text(w / 2, h - 60, "ENTER: ANA MENU", 3, GREY, align="center")
        else:
            turn = t.current_turn
            hud.text(w / 2, h - 110, f"SIRADAKI: {turn.player.name}  ({PHASE_LABELS[turn.phase]}, "
                                     f"{int(turn.duration)} SN)", 4, WHITE, align="center")
            hud.text(w / 2, h - 60, "ENTER: ATISA HAZIRLAN   ESC: MENU", 3, GREY, align="center")

    def _hud_help(self, w, h):
        hud = self.hud
        lines = [
            "KONTROLLER",
            "SPACE      BASILI TUT: GUC BARI, BIRAK: AT",
            "TAB        LOGO PEDESTALINI ATLA",
            "C          KAMERA: OYUNCU / YAYIN / SERBEST",
            "WASD Q E   SERBEST KAMERA HAREKETI",
            "FARE SURUK SERBEST KAMERA BAKIS",
            "TEKERLEK   YAKINLASTIR",
            "F12        EKRAN GORUNTUSU",
            "",
            "KURALLAR",
            "NBA TOPU 1, MONEY 2, MAVI MONEY (LOGO) 3 PUAN",
            "MONEY TOPU RACK'TEKI SON TOPTUR",
            "LOGO ATLANIRSA MAVI MONEY ELENIR",
        ]
        bw, bh = 760, 40 + len(lines) * 30
        x, y = w / 2 - bw / 2, h / 2 - bh / 2
        hud.rect(x, y, bw, bh, (0.02, 0.03, 0.08, 0.92))
        for i, line in enumerate(lines):
            hud.text(x + 30, y + 22 + i * 30, line, 3, GOLD if line in ("KONTROLLER", "KURALLAR") else WHITE)

    # ==================================================================
    def screenshot(self, path: Path | str | None = None) -> Path:
        w, h = self.window.framebuffer_size if self.window else (0, 0)
        data = np.frombuffer(self.ctx.screen.read(components=3), dtype=np.uint8).reshape(h, w, 3)
        path = Path(path or Path("screenshots") / f"shot_{datetime.now():%Y%m%d_%H%M%S}.png")
        save_png(path, data)
        self.flash("EKRAN GORUNTUSU KAYDEDILDI", WHITE, 1.2, 3)
        return path

    def run(self) -> None:
        window = self.window
        last = window.time()
        fps_acc, fps_frames = 0.0, 0
        while not window.should_close:
            now = window.time()
            dt = min(0.05, now - last)
            last = now
            window.poll()
            self.handle_input(dt)
            self.update(dt)
            size = window.framebuffer_size
            if size[0] > 0 and size[1] > 0:
                self.draw(self.ctx.screen, size)
            window.swap()
            fps_acc += dt
            fps_frames += 1
            if fps_acc >= 0.5:
                self.fps = fps_frames / fps_acc
                fps_acc, fps_frames = 0.0, 0
        window.destroy()


# ======================================================================
# Penceresiz çalışma: ekran görüntüsü ve performans ölçümü
def _offscreen_app(size, seed, scores_path=None):
    import moderngl
    ctx = moderngl.create_standalone_context(require=330)
    fbo = ctx.framebuffer(color_attachments=[ctx.renderbuffer(size, 4)],
                          depth_attachment=ctx.depth_renderbuffer(size))
    app = App(ctx, window=None, seed=seed, mute=True, scores_path=scores_path or Path("data") / "_offscreen.json")
    return ctx, fbo, app


def _scripted_round(app: App, seconds: float, camera: CameraMode) -> None:
    """Sahneyi bir turun ortasına getirir: yarı isabetli bir bot birkaç atış yapar."""
    app.begin_round()
    app.rig.mode = camera
    r = app.round
    dt = 1 / 60
    target = SWEET_SPOT
    shots = 0
    t = 0.0
    while t < seconds:
        if r.can_shoot and not r.meter.charging:
            r.press()
            target = SWEET_SPOT + (0.0 if shots % 3 else 0.12)
        if r.meter.charging and r.meter.phase < 0.5 and r.meter.value >= target:
            r.release()
            shots += 1
        app.update(dt)
        t += dt


def offscreen_screenshot(path: str, size=(1280, 720), camera: str = "BROADCAST", seconds: float = 9.0,
                         seed: int = 3) -> Path:
    ctx, fbo, app = _offscreen_app(size, seed)
    mode = CameraMode[camera]
    if mode is CameraMode.FREE:
        mode = CameraMode.BROADCAST
    app.rack_choice = 4
    _scripted_round(app, seconds, mode)
    if mode is CameraMode.SHOOTER:
        # oyuncu bakışında elde top görünsün: güç barını yarıya doldur
        app.round.press()
        for _ in range(30):
            app.update(1 / 60)
    for _ in range(90):  # kamera yumuşatması otursun
        app.rig.update(1 / 60, app.round.player_position())
    app.draw(fbo, size)
    data = np.frombuffer(fbo.read(components=3), dtype=np.uint8).reshape(size[1], size[0], 3)
    return save_png(path, data)


def offscreen_benchmark(frames: int = 300, size=(1280, 720), seed: int = 3) -> dict:
    ctx, fbo, app = _offscreen_app(size, seed)
    _scripted_round(app, 4.0, CameraMode.BROADCAST)
    times = []
    for _ in range(frames):
        start = time.perf_counter()
        app.update(1 / 60)
        app.draw(fbo, size)
        ctx.finish()
        times.append(time.perf_counter() - start)
    times.sort()
    avg = sum(times) / len(times)
    return {
        "frames": frames,
        "resolution": f"{size[0]}x{size[1]}",
        "renderer": ctx.info.get("GL_RENDERER", "?"),
        "avg_ms": avg * 1000,
        "p95_ms": times[int(len(times) * 0.95)] * 1000,
        "fps": 1.0 / avg,
    }
