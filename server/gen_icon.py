"""生成应用图标：品牌色 Lucide 麦克风（透明背景、无底色），多尺寸 ICO。"""
from pathlib import Path

from PIL import Image

MIC_PNG = Path(__file__).parent / "mic.png"
SIZES = [16, 20, 24, 32, 40, 48, 64, 128, 256]


def main() -> None:
    mic = Image.open(MIC_PNG).convert("RGBA")
    big = mic.resize((256, 256), Image.Resampling.LANCZOS)
    big.save("icon.png")
    big.save(
        "icon.ico",
        format="ICO",
        sizes=[(s, s) for s in SIZES],
    )
    print("icon.png / icon.ico generated (multi-size)")


if __name__ == "__main__":
    main()
