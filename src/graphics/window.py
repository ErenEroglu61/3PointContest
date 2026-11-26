import glfw
import moderngl


def create_window(width: int, height: int, title: str):
    if not glfw.init():
        raise RuntimeError("GLFW başlatılamadı")

    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
    glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
    glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, True)

    window = glfw.create_window(width, height, title, None, None)
    if not window:
        glfw.terminate()
        raise RuntimeError("Pencere oluşturulamadı")

    glfw.make_context_current(window)
    ctx = moderngl.create_context()
    return window, ctx