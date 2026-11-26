"""Giriş noktası: pencereyi açar ve render döngüsünü çalıştırır."""
import glfw

from src.graphics.court import Court
from src.graphics.renderer import Renderer
from src.graphics.window import create_window

WIDTH, HEIGHT = 1280, 720


def main() -> None:
    window, ctx = create_window(WIDTH, HEIGHT, "3 Point Contest")
    try:
        fb_width, fb_height = glfw.get_framebuffer_size(window)
        renderer = Renderer(ctx, fb_width, fb_height)
        court = Court(ctx, renderer.program)

        while not glfw.window_should_close(window):
            if glfw.get_key(window, glfw.KEY_ESCAPE) == glfw.PRESS:
                break

            renderer.begin_frame()
            renderer.draw(court.vao, court.color)

            glfw.swap_buffers(window)
            glfw.poll_events()
    finally:
        glfw.terminate()


if __name__ == "__main__":
    main()