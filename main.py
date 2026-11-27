from src.graphics.hoop import Hoop
import glfw

from src.graphics.court import Court
from src.graphics.renderer import Renderer
from src.graphics.window import create_window
from src.graphics.spots import MAIN_POSITIONS, FROM_THE_LOGO_POSITIONS
from src.graphics.ball_object import build_sphere_vao, build_scene

WIDTH, HEIGHT = 1280, 720


def main() -> None:
    window, ctx = create_window(WIDTH, HEIGHT, "3 Point Contest")
    try:
        fb_width, fb_height = glfw.get_framebuffer_size(window)
        renderer = Renderer(ctx, fb_width, fb_height)
        court = Court(ctx, renderer.program)
        hoops = [Hoop(ctx, renderer.program, side=1.0), Hoop(ctx, renderer.program, side=-1.0)]
        sphere = build_sphere_vao(ctx, renderer.program)
        balls = build_scene(all_money_spot="top")

        while not glfw.window_should_close(window):
            if glfw.get_key(window, glfw.KEY_ESCAPE) == glfw.PRESS:
                break

            renderer.begin_frame()
            renderer.draw(court.vao, court.color)

            for hoop in hoops:
                renderer.draw(hoop.rim_vao, hoop.color, hoop.mode)

            for ball in balls:
                renderer.draw(sphere, ball.color, position=ball.position)

            glfw.swap_buffers(window)
            glfw.poll_events()
    finally:
        glfw.terminate()


if __name__ == "__main__":
    main()