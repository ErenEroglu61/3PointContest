#version 330

uniform mat4 u_model;
uniform mat4 u_light_vp;

in vec3 in_position;

void main() {
    gl_Position = u_light_vp * u_model * vec4(in_position, 1.0);
}
