"""Giriş noktası: pencereyi açar ve oyun döngüsünü başlatır.

    python main.py                         # oyunu başlatır
    python main.py --name EMRE --mute      # oyuncu adı, sessiz
    python main.py --screenshot shot.png   # penceresiz ekran görüntüsü
    python main.py --benchmark 300         # penceresiz performans ölçümü
"""
import argparse


def main() -> None:
    parser = argparse.ArgumentParser(description="3 Point Contest - ModernGL simülasyonu")
    parser.add_argument("--name", default="OYUNCU", help="oyuncu adı (skor tablosu için)")
    parser.add_argument("--seed", type=int, default=None, help="rastgelelik tohumu (tekrarlanabilir turnuva)")
    parser.add_argument("--mute", action="store_true", help="sesleri kapat")
    parser.add_argument("--width", type=int, default=1280)
    parser.add_argument("--height", type=int, default=720)
    parser.add_argument("--screenshot", metavar="PNG", help="pencere açmadan bir kare çizip kaydet")
    parser.add_argument("--camera", default="BROADCAST", choices=["SHOOTER", "BROADCAST"],
                        help="--screenshot için kamera")
    parser.add_argument("--benchmark", type=int, metavar="KARE", help="penceresiz performans ölçümü")
    args = parser.parse_args()
    size = (args.width, args.height)

    if args.screenshot:
        from src.app import offscreen_screenshot
        print("kaydedildi:", offscreen_screenshot(args.screenshot, size, args.camera))
        return
    if args.benchmark:
        from src.app import offscreen_benchmark
        for key, value in offscreen_benchmark(args.benchmark, size).items():
            print(f"{key:>10}: {value:.2f}" if isinstance(value, float) else f"{key:>10}: {value}")
        return

    from src.app import App
    from src.graphics.window import Window
    window = Window(*size, title="3 Point Contest")
    App(window.ctx, window, player_name=args.name, seed=args.seed, mute=args.mute).run()


if __name__ == "__main__":
    main()
