# 3 Point Contest


## İçindekiler
- 1. [Proje Hakkında](#proje-hakkında)
- 2. [Motivasyon](#motivasyon)
- 3. [Yöntem](#yöntem)
- 4. [Proje Yapısı](#proje-yapısı)
- 5. [Kurulum](#kurulum)
- 6. [Kullanım](#kullanım)
- 7. [Deneyler](#deneyler)
- 8. [Yol Haritas](#yol-haritası)
- 9. [Ekip](#ekip)
- 10. [Kaynakça](#kaynakça)
## Proje Hakkında
Bu proje, 2026 State Farm NBA 3-Point Contest kurallarını uygulayan, ModernGL ile geliştirilmiş interaktif bir 3B simülasyondur. Kullanıcı, sahadaki beş ana atış noktası ve iki Logodan (Sahanın ortası) pedestalı arasında top atarak 70 saniye içinde mümkün olduğunca yüksek puan toplamaya çalışır.

Projede iki ana bileşen bulunur:

- **Oyun motoru:** Puanlama, atış sırası, money topu ve mavi money eliminasyonu, tiebreaker ve şampiyonluk turu kurallarını grafikten bağımsız olarak uygular. Test edilebilir bir Python modülüdür.
- **Görsel katman:** Saha, pota, toplar ve pedestallerden oluşan 3B sahneyi ModernGL ile çizer. Oyun motorunun durumunu okuyarak ekrana yansıtır.

Proje, iki tur ve sekiz oyunculu bir turnuva formatını destekler.
## Motivasyon
NBA 3-Point Contest,vBu projede, 2026 State Farm 3-Point Contest kurallarını bir bilgisayar oyununa dönüştürmeyi hedefliyoruz.

Projenin iki temel motivasyonu var:

- **Kuralların doğru modellenmesi:** Yarışmada puanlar, atış sırası, eliminasyon kuralları ve tiebreaker mantığı birbirine bağlı. Bu kuralları bir oyun motoru olarak kodlamak, gerçek dünyadaki karmaşık bir kuralı programatik olarak düşünmeyi gerektiriyor.
- **Grafiğin gerçek bir sahneye dönüşmesi:** ModernGL ile saha, pota, toplar ve pedestallerden oluşan bir 3D ortam kurmak, bilgisayar grafiğinin temel kavramlarını (koordinat sistemleri, kamera, shader'lar) uygulamalı olarak bilgimizi test etmek.

Bu iki parça ayrı tutulduğunda hem test edilebilir bir oyun mantığı hem de bağımsız çalışan bir görsel katman ortaya çıkar. Proje, kuralların doğru çalışıp çalışmadığını ekranda görmeyi ve görüntünün arkasındaki mantığı açıklayabilmeyi bir arada hedefliyor.

## Yöntem
| Kütüphane | Kullanım Amacı |
|-----------|----------------|
| ModernGL  | OpenGL 3.3 çizim ve shader yönetimi |
| GLFW      | Pencere ve girdi yönetimi |
| NumPy     | Vertex verisi ve matris işlemleri |
## Proje Yapısı
````
3-point-contest/
├── main.py                  # Giriş noktası: pencereyi açar, oyun döngüsünü başlatır
├── requirements.txt         # moderngl, glfw, numpy (pip freeze ile)
├── README.md
├── .gitignore
├── src/
│   ├── __init__.py
│   ├── contest/             # Oyun motoru (Eren: kuralların kodlanması)
│   │   ├── __init__.py
│   │   ├── locations.py     # 5 ana lokasyon ve "From the Logo" pedestalları, sıra tanımları
│   │   ├── balls.py         # Top türleri: NBA topu (1 puan), money (2 puan), mavi money (3 puan)
│   │   ├── rack.py          # Rack durumu, sıra kontrolü, eliminasyon
│   │   ├── scoring.py       # Puan hesabı, skor toplamı
│   │   ├── timer.py         # 70 saniyelik süre ve 30 saniyelik tiebreaker
│   │   └── tournament.py    # İlk tur, şampiyonluk turu, tiebreaker akışı
│   ├── graphics/            # Görsel katman (Emre: ModernGL çevre tasarımı)
│   │   ├── __init__.py
│   │   ├── window.py        # GLFW pencere ve OpenGL context kurulumu
│   │   ├── renderer.py      # Çizim döngüsü, clear ve draw çağrıları
│   │   ├── camera.py        # View ve projection matrisleri
│   │   ├── mesh.py          # VBO, VAO oluşturma
│   │   ├── court.py         # Saha, çizgiler, "From the Logo" çıkartması
│   │   ├── hoop.py          # Pota ve file
│   │   ├── ball_objects.py  # Topların 3B gösterimi
│   │   ├── shaders/
│   │   │   ├── basic.vert
│   │   │   └── basic.frag
│   │   └── utils/
│   │       ├── __init__.py
│   │       └── math_utils.py
│   └── app.py               # Motor ve grafik katmanını birbirine bağlar
├── assets/                  # Saha dokusu, model dosyaları (ileride)
└── tests/
    ├── test_scoring.py      # Puan kuralları
    ├── test_rack_order.py   # Sıra ve eliminasyon kuralları
    └── test_tournament.py   # Tiebreaker ve sıralama
````
## Kurulum

## Kullanım

## Deneyler

## Yol Haritası
- [x] Kural dokümanının incelenmesi ve proje planlaması
- [x] Proje iskeletinin oluşturulması (klasör yapısı, git, requirements.txt)
- [x] `contest/` oyun motorunun yazılması
  - [x] Atış lokasyonları ve pedestallerin tanımlanması
  - [x] Top türleri ve puan hesabı
  - [x] Rack sıra kontrolü ve eliminasyon
  - [x] 70 saniyelik zamanlayıcı ve 30 saniyelik tiebreaker
  - [x] İlk tur, şampiyonluk turu ve tiebreaker akışı
- [ ] `tests/` altında kural testlerinin yazılması
- [ ] ModernGL ile zemin, pota ve topların çizilmesi
- [ ] Shader'lar ve kamera kontrolü
- [ ] Motor ile grafik katmanının `app.py` üzerinden bağlanması
- [ ] README'nin son hali ve ekran görüntüsü
## Ekip
| Ad Soyad    | Öğrenci No | Rol / Sorumluluk            |
|-------------|------------|-----------------------------|
| Eren Eroğlu | 170424035  | Oyun motoru kodlanması      |
| Emre Turan  | 170425501  | ModernGL ile Çevre tasarımı |
## Kaynakça

https://pr.nba.com/wp-content/uploads/sites/46/2026/02/2026-State-Farm-3-Point-Contest-Rules.pdf <- Kurallar