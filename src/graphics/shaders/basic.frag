#version 330

// Malzeme türleri
const int MAT_COLOR = 0;       // düz renk + Phong
const int MAT_TEXTURE = 1;     // dokulu (saha zemini)
const int MAT_BALL = 2;        // NBA topu (turuncu, siyah dikiş)
const int MAT_MONEY = 3;       // money topu (kırmızı-beyaz-mavi paneller)
const int MAT_BLUE_MONEY = 4;  // mavi money topu (parlayan)
const int MAT_UNLIT = 5;       // ışıksız (file çizgileri)

uniform int u_material;
uniform vec3 u_color;
uniform float u_alpha;
uniform float u_shininess;
uniform float u_specular;
uniform float u_emissive;
uniform float u_time;
uniform bool u_receive_shadow;

uniform vec3 u_light_dir;     // ışığa doğru (normalize)
uniform vec3 u_camera_pos;
uniform sampler2D u_texture;
uniform sampler2DShadow u_shadow_map;

in vec3 v_world;
in vec3 v_normal;
in vec3 v_local_normal;
in vec2 v_uv;
in vec4 v_light_space;

out vec4 f_color;

float shadow_factor(vec3 n) {
    vec3 p = v_light_space.xyz / v_light_space.w * 0.5 + 0.5;
    if (p.z > 1.0 || p.x < 0.0 || p.x > 1.0 || p.y < 0.0 || p.y > 1.0) return 1.0;
    float bias = max(0.0025 * (1.0 - dot(n, u_light_dir)), 0.0008);
    vec2 texel = 1.0 / vec2(textureSize(u_shadow_map, 0));
    float lit = 0.0;
    // 3x3 PCF: yumuşak gölge kenarı
    for (int x = -1; x <= 1; x++)
        for (int y = -1; y <= 1; y++)
            lit += texture(u_shadow_map, vec3(p.xy + vec2(x, y) * texel * 1.5, p.z - bias));
    return lit / 9.0;
}

float hash(vec3 p) {
    return fract(sin(dot(p, vec3(12.9898, 78.233, 37.719))) * 43758.5453);
}

// Basketbol dikişleri: iki büyük çember + iki eğri dikiş
float seam_mask(vec3 n) {
    float w = 0.045;
    float s = min(abs(n.x), abs(n.y));
    float curve = abs(abs(n.z) - 0.72 + 0.45 * n.y * n.y);
    s = min(s, curve * 1.6);
    return 1.0 - smoothstep(w * 0.6, w, s);
}

vec3 ball_albedo(vec3 n, int mat) {
    float pebble = (hash(floor(n * 90.0)) - 0.5) * 0.08;
    vec3 base;
    if (mat == MAT_BALL) {
        base = vec3(0.86, 0.38, 0.11);
    } else if (mat == MAT_MONEY) {
        int panel = int(n.x > 0.0) + 2 * int(n.y > 0.0);
        if (abs(n.z) > 0.72 - 0.45 * n.y * n.y) panel = 3 - panel;
        vec3 colors[4] = vec3[4](vec3(0.85, 0.10, 0.14), vec3(0.95, 0.95, 0.95),
                                 vec3(0.10, 0.25, 0.80), vec3(0.95, 0.95, 0.95));
        base = colors[panel];
    } else {
        int panel = int(n.x > 0.0) + int(n.y > 0.0);
        base = (panel == 1) ? vec3(0.30, 0.65, 1.0) : vec3(0.05, 0.25, 0.85);
    }
    base += pebble;
    vec3 seam_color = (mat == MAT_BALL) ? vec3(0.04) : vec3(0.08, 0.08, 0.12);
    if (mat == MAT_BLUE_MONEY) seam_color = vec3(0.92);
    return mix(base, seam_color, seam_mask(n));
}

void main() {
    if (u_material == MAT_UNLIT) {
        f_color = vec4(u_color, u_alpha);
        return;
    }

    vec3 n = normalize(v_normal);
    vec3 albedo = u_color;
    if (u_material == MAT_TEXTURE) {
        albedo = texture(u_texture, v_uv).rgb;
    } else if (u_material >= MAT_BALL) {
        albedo = ball_albedo(normalize(v_local_normal), u_material);
    }

    vec3 l = normalize(u_light_dir);
    vec3 v = normalize(u_camera_pos - v_world);
    vec3 h = normalize(l + v);

    float shadow = u_receive_shadow ? shadow_factor(n) : 1.0;
    // Yarım küre ortam ışığı: yukarı bakan yüzeyler biraz daha aydınlık
    float hemi = 0.5 + 0.5 * n.y;
    vec3 ambient = mix(vec3(0.18, 0.19, 0.24), vec3(0.42, 0.40, 0.38), hemi);
    float diffuse = max(dot(n, l), 0.0);
    float spec = pow(max(dot(n, h), 0.0), u_shininess) * u_specular;

    vec3 color = albedo * (ambient + diffuse * 0.85 * shadow) + vec3(spec) * shadow;

    // Arena spotları: sahanın ortasına düşen hafif sıcak ışık havuzu
    float pool = exp(-dot(v_world.xz - vec2(0.0, 5.0), v_world.xz - vec2(0.0, 5.0)) / 260.0);
    color *= 0.82 + 0.3 * pool;

    if (u_emissive > 0.0) {
        float pulse = 0.65 + 0.35 * sin(u_time * 5.0);
        color += albedo * u_emissive * pulse;
    }

    // Uzaklık sisi: arka plan rengine karış
    float dist = length(u_camera_pos - v_world);
    float fog = 1.0 - exp(-dist * 0.012);
    color = mix(color, vec3(0.03, 0.04, 0.08), fog * 0.6);

    // Basit gamma düzeltmesi
    color = pow(max(color, 0.0), vec3(1.0 / 1.1));
    f_color = vec4(color, u_alpha);
}
