#version 330

uniform mat4 u_model;
uniform mat4 u_view;
uniform mat4 u_proj;
uniform mat4 u_light_vp;

in vec3 in_position;
in vec3 in_normal;
in vec2 in_uv;

out vec3 v_world;
out vec3 v_normal;
out vec3 v_local_normal;
out vec2 v_uv;
out vec4 v_light_space;

void main() {
    vec4 world = u_model * vec4(in_position, 1.0);
    v_world = world.xyz;
    v_normal = mat3(transpose(inverse(u_model))) * in_normal;
    v_local_normal = in_normal;
    v_uv = in_uv;
    v_light_space = u_light_vp * world;
    gl_Position = u_proj * u_view * world;
}
