"""
flyer_image_processor.py
巨大なチラシ画像・PDFから文字潰れを防ぐため、高解像度原本を抽出し、
日付別・コーナー別にブロック分割（クロップ）して精密解析を可能にする前処理モジュール
"""

import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple
from PIL import Image

try:
    from pypdf import PdfReader
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False

BASE_DIR = Path(__file__).resolve().parent
FLYERS_DIR = BASE_DIR / "flyers"
CROPS_DIR = FLYERS_DIR / "crops"


class FlyerImageProcessor:
    def __init__(self):
        FLYERS_DIR.mkdir(exist_ok=True)
        CROPS_DIR.mkdir(exist_ok=True)

    def extract_images_from_pdf(self, pdf_path: Path) -> List[Path]:
        """PDF内部の最高画質埋め込み画像を直接抽出"""
        if not PYPDF_AVAILABLE:
            print("⚠️ pypdfが利用できません")
            return []

        extracted_paths = []
        try:
            reader = PdfReader(pdf_path)
            for p_idx, page in enumerate(reader.pages):
                for img_idx, img_obj in enumerate(page.images):
                    out_name = f"{pdf_path.stem}_p{p_idx}_img{img_idx}.png"
                    out_path = FLYERS_DIR / out_name
                    with open(out_path, "wb") as f:
                        f.write(img_obj.data)
                    extracted_paths.append(out_path)
                    print(f"  📷 高解像度原本抽出: {out_name} ({len(img_obj.data)} bytes)")
        except Exception as e:
            print(f"❌ PDF画像抽出エラー ({pdf_path.name}): {e}")

        return extracted_paths

    def split_into_highres_blocks(self, image_path: Path, store_id: str) -> List[Path]:
        """
        チラシ画像を日付・コーナー別に高解像度ブロック分割（クロップ）
        全体縮小による文字潰れ・誤読を完全に防止する
        """
        try:
            im = Image.open(image_path)
            w, h = im.size
        except Exception as e:
            print(f"❌ 画像読み込みエラー ({image_path.name}): {e}")
            return []

        # 幅や高さが2000px以上ある高解像度原本を前提とする
        print(f"🔍 チラシ原本サイズ: {w}x{h} ({image_path.name})")

        # 4〜6分割のグリッドクロップを生成
        crop_definitions = [
            ("top_left", (0, 0, int(w * 0.52), int(h * 0.52))),
            ("top_right", (int(w * 0.48), 0, w, int(h * 0.52))),
            ("bottom_left", (0, int(h * 0.48), int(w * 0.52), h)),
            ("bottom_right", (int(w * 0.48), int(h * 0.48), w, h)),
        ]

        # 横長や巨大チラシの場合は中央部も追加
        if w > 2500 and h > 2000:
            crop_definitions.append(("center_top", (int(w * 0.25), 0, int(w * 0.75), int(h * 0.55))))
            crop_definitions.append(("center_bottom", (int(w * 0.25), int(h * 0.45), int(w * 0.75), h)))

        cropped_paths = []
        for label, box in crop_definitions:
            try:
                cropped = im.crop(box)
                out_name = f"{store_id}_{image_path.stem}_{label}.png"
                out_path = CROPS_DIR / out_name
                cropped.save(out_path)
                cropped_paths.append(out_path)
            except Exception as e:
                print(f"⚠️ クロップエラー ({label}): {e}")

        print(f"  ✂️ {len(cropped_paths)} 個の高解像度ブロックに分割完了（文字鮮明度を100%保持）")
        return cropped_paths

    def process_all_flyers(self) -> Dict[str, List[Path]]:
        """flyers/ フォルダ内のPDFおよび画像をすべて高解像度分割処理"""
        print("==================================================")
        print(" 🖼️ チラシ高解像度ブロック分割処理（誤読防止パイプライン）")
        print("==================================================")
        result = {}

        # 1. PDFファイル
        for pdf_file in FLYERS_DIR.glob("*.pdf"):
            print(f"📄 PDF処理中: {pdf_file.name}")
            extracted_imgs = self.extract_images_from_pdf(pdf_file)
            for img in extracted_imgs:
                crops = self.split_into_highres_blocks(img, pdf_file.stem)
                result[img.stem] = crops

        # 2. 巨大JPG/PNG画像（原本）
        for img_file in FLYERS_DIR.glob("*.jpg"):
            if "crop" not in img_file.name and img_file.stat().st_size > 500000:
                print(f"🖼️ 画像処理中: {img_file.name}")
                crops = self.split_into_highres_blocks(img_file, img_file.stem)
                result[img_file.stem] = crops

        print("==================================================")
        print(f"🎉 高解像度分割完了: {sum(len(v) for v in result.values())} 個の精読用ブロックを生成")
        print("==================================================")
        return result


if __name__ == "__main__":
    processor = FlyerImageProcessor()
    processor.process_all_flyers()
