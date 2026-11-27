#version 330

uniform sampler2D u_font;

in vec2 v_uv;
in vec4 v_color;

out vec4 f_color;

void main() {
    float a = texture(u_font, v_uv).r;
    f_color = vec4(v_color.rgb, v_color.a * a);
}
