#version 330

uniform vec2 u_screen;

in vec2 in_pos;     // piksel koordinatı (sol üst = 0,0)
in vec2 in_uv;
in vec4 in_color;

out vec2 v_uv;
out vec4 v_color;

void main() {
    vec2 ndc = vec2(in_pos.x / u_screen.x * 2.0 - 1.0, 1.0 - in_pos.y / u_screen.y * 2.0);
    gl_Position = vec4(ndc, 0.0, 1.0);
    v_uv = in_uv;
    v_color = in_color;
}
