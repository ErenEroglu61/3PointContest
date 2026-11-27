"""GLFW pencere, OpenGL 3.3 core context ve girdi olayları."""
import glfw
import moderngl


class Window:
    def __init__(self, width: int = 1280, height: int = 720, title: str = "3 Point Contest",
                 vsync: bool = True, samples: int = 4):
        if not glfw.init():
            raise RuntimeError("GLFW başlatılamadı")
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
        glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, True)  # macOS için gerekli
        glfw.window_hint(glfw.SAMPLES, samples)              # MSAA kenar yumuşatma
        self.handle = glfw.create_window(width, height, title, None, None)
        if not self.handle:
            glfw.terminate()
            raise RuntimeError("Pencere oluşturulamadı (OpenGL 3.3 desteği gerekli)")
        glfw.make_context_current(self.handle)
        glfw.swap_interval(1 if vsync else 0)
        self.ctx = moderngl.create_context(require=330)

        self.key_events: list[tuple[int, int, int]] = []
        self.keys_down: set[int] = set()
        self.mouse_buttons: set[int] = set()
        self.mouse_delta = [0.0, 0.0]
        self.scroll = 0.0
        self._last_cursor: tuple[float, float] | None = None

        glfw.set_key_callback(self.handle, self._on_key)
        glfw.set_mouse_button_callback(self.handle, self._on_mouse_button)
        glfw.set_cursor_pos_callback(self.handle, self._on_cursor)
        glfw.set_scroll_callback(self.handle, self._on_scroll)

    # --- callback'ler ----------------------------------------------------
    def _on_key(self, _win, key, _scancode, action, mods):
        if action == glfw.PRESS:
            self.keys_down.add(key)
        elif action == glfw.RELEASE:
            self.keys_down.discard(key)
        if action in (glfw.PRESS, glfw.RELEASE):
            self.key_events.append((key, action, mods))

    def _on_mouse_button(self, _win, button, action, _mods):
        if action == glfw.PRESS:
            self.mouse_buttons.add(button)
        else:
            self.mouse_buttons.discard(button)

    def _on_cursor(self, _win, x, y):
        if self._last_cursor is not None:
            self.mouse_delta[0] += x - self._last_cursor[0]
            self.mouse_delta[1] += y - self._last_cursor[1]
        self._last_cursor = (x, y)

    def _on_scroll(self, _win, _dx, dy):
        self.scroll += dy

    # --- yardımcılar -----------------------------------------------------
    def poll(self) -> None:
        self.key_events.clear()
        self.mouse_delta = [0.0, 0.0]
        self.scroll = 0.0
        glfw.poll_events()

    def swap(self) -> None:
        glfw.swap_buffers(self.handle)

    @property
    def should_close(self) -> bool:
        return glfw.window_should_close(self.handle)

    def close(self) -> None:
        glfw.set_window_should_close(self.handle, True)

    @property
    def framebuffer_size(self) -> tuple[int, int]:
        return glfw.get_framebuffer_size(self.handle)

    @staticmethod
    def time() -> float:
        return glfw.get_time()

    def set_title(self, title: str) -> None:
        glfw.set_window_title(self.handle, title)

    def destroy(self) -> None:
        glfw.destroy_window(self.handle)
        glfw.terminate()
