"""
비주얼 리그레션 모듈

기준(baseline) 스크린샷과 현재 스크린샷을 픽셀 비교하여 UI 변경을 감지합니다.

사용법:
    vc = VisualCompare("baselines/")
    result = vc.compare("step_1_pass.png", "Step 1")
    # result.match_percent → 98.5%
    # result.diff_image_path → "diffs/step_1_diff.png"
"""

import os
import math
from typing import Optional
from utils.logger import setup_logger  # type: ignore

logger = setup_logger(__name__)

try:
    from PIL import Image, ImageDraw, ImageChops  # type: ignore
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    logger.warning("Pillow 미설치. 'pip install Pillow' 실행 필요")


class CompareResult:
    """비교 결과"""

    def __init__(self, step_name: str = "", match_percent: float = 100.0,
                 diff_pixels: int = 0, total_pixels: int = 0,
                 diff_image_path: str = "", baseline_exists: bool = True,
                 error: str = ""):
        self.step_name = step_name
        self.match_percent = match_percent
        self.diff_pixels = diff_pixels
        self.total_pixels = total_pixels
        self.diff_image_path = diff_image_path
        self.baseline_exists = baseline_exists
        self.passed = match_percent >= 95.0 and not error  # 95% 이상이면 통과
        self.error = error

    def to_dict(self):
        return {
            "step_name": self.step_name,
            "match_percent": round(self.match_percent, 2),
            "diff_pixels": self.diff_pixels,
            "total_pixels": self.total_pixels,
            "diff_image_path": self.diff_image_path,
            "baseline_exists": self.baseline_exists,
            "passed": self.passed,
            "error": self.error
        }


class VisualCompare:
    """
    스크린샷 비교 엔진

    - 첫 실행: 기준 이미지(baseline) 저장
    - 이후 실행: baseline과 현재 스크린샷 비교 → 차이 리포트
    """

    def __init__(self, baseline_dir: str = "visual_baselines",
                 diff_dir: str = "visual_diffs",
                 threshold: float = 95.0):
        """
        Args:
            baseline_dir: 기준 이미지 저장 디렉토리
            diff_dir: 차이 이미지 저장 디렉토리
            threshold: 일치율 기준 (이하이면 실패, 기본 95%)
        """
        self.baseline_dir = baseline_dir
        self.diff_dir = diff_dir
        self.threshold = threshold
        self._results = []

        os.makedirs(baseline_dir, exist_ok=True)
        os.makedirs(diff_dir, exist_ok=True)

    def compare(self, current_screenshot_path: str,
                step_name: str = "") -> CompareResult:
        """
        스크린샷 비교

        Args:
            current_screenshot_path: 현재 스크린샷 경로
            step_name: 스텝 이름 (baseline 파일명으로 사용)

        Returns:
            CompareResult
        """
        if not HAS_PIL:
            return CompareResult(step_name=step_name, error="Pillow 미설치")

        if not os.path.exists(current_screenshot_path):
            return CompareResult(step_name=step_name, error="스크린샷 파일 없음")

        # baseline 파일명 결정
        safe_name = self._safe_filename(step_name or os.path.basename(current_screenshot_path))
        baseline_path = os.path.join(self.baseline_dir, f"{safe_name}.png")

        # baseline이 없으면 → 현재를 기준으로 저장
        if not os.path.exists(baseline_path):
            self._save_baseline(current_screenshot_path, baseline_path)
            result = CompareResult(
                step_name=step_name,
                match_percent=100.0,
                baseline_exists=False
            )
            self._results.append(result)
            logger.info(f"[Visual] Baseline 저장: {baseline_path}")
            return result

        # 비교 수행
        try:
            result = self._pixel_compare(baseline_path, current_screenshot_path, step_name)
            self._results.append(result)
            return result
        except Exception as e:
            result = CompareResult(step_name=step_name, error=str(e))
            self._results.append(result)
            return result

    def update_baseline(self, current_screenshot_path: str, step_name: str = ""):
        """기준 이미지를 현재 스크린샷으로 업데이트"""
        safe_name = self._safe_filename(step_name or os.path.basename(current_screenshot_path))
        baseline_path = os.path.join(self.baseline_dir, f"{safe_name}.png")
        self._save_baseline(current_screenshot_path, baseline_path)
        logger.info(f"[Visual] Baseline 업데이트: {baseline_path}")

    def get_results(self):
        """전체 비교 결과"""
        return self._results

    def format_summary(self) -> str:
        """비교 결과 텍스트 요약"""
        if not self._results:
            return ""

        total = len(self._results)
        passed = sum(1 for r in self._results if r.passed)
        new_baselines = sum(1 for r in self._results if not r.baseline_exists)

        lines = [
            "",
            "─" * 45,
            "🖼️ Visual Regression Summary",
            "─" * 45,
            f"  총 {total}개 비교 | ✅ {passed} 통과 | 🔴 {total - passed - new_baselines} 실패 | 🆕 {new_baselines} 신규",
        ]

        for r in self._results:
            if not r.baseline_exists:
                lines.append(f"  🆕 {r.step_name}: 새 baseline 저장")
            elif r.passed:
                lines.append(f"  ✅ {r.step_name}: {r.match_percent:.1f}% 일치")
            else:
                lines.append(f"  🔴 {r.step_name}: {r.match_percent:.1f}% 일치 (기준: {self.threshold}%)")

        lines.append("─" * 45)
        return "\n".join(lines)

    def reset(self):
        """결과 초기화"""
        self._results = []

    # ── Internal ──

    def _pixel_compare(self, baseline_path: str, current_path: str,
                       step_name: str) -> CompareResult:
        """두 이미지의 픽셀 비교"""
        baseline = Image.open(baseline_path).convert("RGB")
        current = Image.open(current_path).convert("RGB")

        # 크기가 다르면 baseline 크기로 리사이즈
        if baseline.size != current.size:
            current = current.resize(baseline.size, Image.LANCZOS)

        # 차이 이미지 생성
        diff = ImageChops.difference(baseline, current)

        # 차이 픽셀 수 계산 (임계값 적용)
        diff_data = diff.getdata()
        total_pixels = len(diff_data) # type: ignore
        diff_threshold = 30  # RGB 각 채널 30 이상 차이시 "다른 픽셀"로 판단
        diff_pixels = 0

        for pixel in diff_data:
            if any(ch > diff_threshold for ch in pixel): # type: ignore
                diff_pixels += 1 # type: ignore

        match_percent = float(((total_pixels - diff_pixels) / total_pixels * 100.0) if total_pixels > 0 else 100.0) # type: ignore

        # 차이 이미지 저장 (차이 부분을 빨간색으로 하이라이트)
        diff_image_path = ""
        if diff_pixels > 0:
            diff_image_path = self._create_diff_highlight(
                baseline, current, diff, step_name
            )

        logger.info(
            f"[Visual] {step_name}: {match_percent:.1f}% 일치 "
            f"({diff_pixels}/{total_pixels} 픽셀 차이)"
        )

        return CompareResult(
            step_name=step_name,
            match_percent=match_percent,
            diff_pixels=diff_pixels,
            total_pixels=total_pixels,
            diff_image_path=diff_image_path,
            baseline_exists=True
        )

    def _create_diff_highlight(self, baseline, current, diff, step_name: str) -> str:
        """차이 부분을 빨간색으로 하이라이트한 이미지 생성"""
        # 3분할 이미지: [baseline | current | diff highlight]
        w, h = baseline.size
        result = Image.new("RGB", (w * 3 + 20, h + 40), (30, 30, 30))
        draw = ImageDraw.Draw(result)

        # 라벨
        draw.text((w // 2 - 30, 5), "Baseline", fill=(150, 150, 150))
        draw.text((w + 10 + w // 2 - 30, 5), "Current", fill=(150, 150, 150))
        draw.text((w * 2 + 20 + w // 2 - 20, 5), "Diff", fill=(255, 80, 80))

        # 이미지 배치
        result.paste(baseline, (0, 30))
        result.paste(current, (w + 10, 30))

        # 차이 하이라이트 (차이 부분을 빨간 반투명 오버레이)
        highlight = current.copy()
        diff_data = diff.getdata()
        highlight_data = list(highlight.getdata())
        diff_threshold = 30

        for i, pixel in enumerate(diff_data):
            if any(ch > diff_threshold for ch in pixel):
                highlight_data[i] = (255, 50, 50)  # 빨간색

        highlight.putdata(highlight_data)
        result.paste(highlight, (w * 2 + 20, 30))

        # 저장
        safe_name = self._safe_filename(step_name)
        diff_path = os.path.join(self.diff_dir, f"{safe_name}_diff.png")
        result.save(diff_path)

        return diff_path

    def _save_baseline(self, source_path: str, dest_path: str):
        """baseline 이미지 저장"""
        if HAS_PIL:
            img = Image.open(source_path)
            img.save(dest_path)
        else:
            import shutil
            shutil.copy2(source_path, dest_path)

    def _safe_filename(self, name: str) -> str:
        """파일명으로 안전한 문자열 변환"""
        safe = "".join(c if c.isalnum() or c in ("_", "-") else "_" for c in name)
        return safe[:100]  # type: ignore
