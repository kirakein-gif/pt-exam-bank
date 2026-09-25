# -*- coding: utf-8 -*-
"""
PT국시 문제은행 갱신기
제작자: 나대현
- 문제 PDF + 정답 PDF + 풀이 PDF -> 개별 questions.local.json
- 모든 OCR/분석은 PC 안에서 처리합니다.
- 현재 KPTLE 최다빈출 적중문제 계열 레이아웃에 최적화되어 있습니다.
"""
from __future__ import annotations

import base64
import collections
import html
import json
import math
import os
import re
import shutil
import subprocess
import sys
import threading
import webbrowser
from pathlib import Path
from tkinter import Tk, StringVar, BooleanVar, IntVar, filedialog, messagebox, ttk

try:
    import cv2
    import fitz
    import numpy as np
    import pytesseract
except ImportError as e:
    raise SystemExit(
        "필수 모듈이 없습니다. 먼저 install.bat을 실행하세요.\n" + str(e)
    )

OCR_LANG = "kor+eng"
DPI = 200
ANSWER_TEMPLATES_B64 = {"1": ["iVBORw0KGgoAAAANSUhEUgAAACQAAAAkCAAAAADEa8dEAAAE3ElEQVQ4EQXBa2wTdQAA8P7v1bvrvdrrrc897MYGDpIFMQqaiJGHj6DEkAhCBD8YE4khygcDLkQxBoloFL9M/QJ+UUIgKioJBKMQCcgkDDbYo6xr17Vre23v2d71Hn9/P1DFKRvSni7ABbJLsRmjxZB0x+V1v5zFqbASEXQKZGne7FCwgxElwGEebQRIhAv4uAPdCrGU4FDStMEsRdUcuuOKqAGxAAxpMAocQGN6W3KdFoG0o6YJZhm6GQjpTgpv6AEKskq7K6TaLF6DQg2h7LZU5jAwwfGmw+sdkYB6OOCwDQtyiBo2fZQrMwRC+BU7Ce6EQ6bJ6h1Omo+jfssSiympiDi9GupCO+SieB3lwWwE9VpY0+8tqcMd2+gtm1AMIEQdD3jQo5A6RjhRMBPBcAvRCTLX7WA+8/U71/uH7nuZkGnweRSSS3BEdsF/LEpA2kBCTmnFwtnJ31kCrfU+//I6CyUcj3HzvkhpYBxFyKDYaKeNufVJl9+8a2NDOHyc6r6hIBZLILJF4gYYZ4KBoFhtxQJXxvyD4uq8G7HsyDdfbD3JlvCIDDDEoME079rBWKWVIJKpm1WRKetDmjP3xIVdT5/hS2Kl2q9DGkxz/lyKNBBmZNWXAxUcXzxU+IU1gonPT3z4piXIbYFXUqAggLu8RyX/fu2D0Zkbm+qvPgy++/7s6vmRTc8mN1ANnyslGZDlVa8j2syRM9+/pFmnPqKgtDDLA6d19dMzKdSTSa4SARN8FYnaLrdu/Rgp51ODxutXfuhD0zUy022VEa0Qd0wAiqxuY+1Ie+3pVWJFjXELe/VzTqe3TmLHS6M9yx7bDsRBk14KJmSjsaW+FC5oGXHuFesaYWA5fuTj797a6ZJytLoKFNIlU9Cc8NZPhgWt2B91npv4cUN2IFAPHz21xOb1Pl0ZAvPprJFugvAzM5MGi2lDpw5uP/uvyNZrqbOjX23PkmlbzoA8bQIUCXZW/JRK6yzm1N7Inu8TkDJkDxdGB2td6D3JA1MEJATfZuM/x4VQrgerHL0+31AZoZJeLVwiim4qR3fA7YCHUS0YOXLtXFrROKq62/9DaQ1ry9U9J14grFbvA1wC06QaxctE98lj4wNyLtZ45Le9+7dtKVWkTTsvXVBqbqxKS2BWLIvUMgjn92W+bbeouLxDn9I9qn3l7T37SX4JiE03Bu5KJtlRqBC382r6Vh64woGLt/W1vsdzf2JeXxn2YTkOLNKqaFtK0vXOvbfvszqR1YjHH+LyjvXHmuXN8D6bmGcjoI7VmaCrScgiW32s61a0wLmxhVA/c1OQ+ypVzBVmeiSQZapEUjV73OuD7Om/JvXdfLBzInUo+CTfySUhBFE5wIE8qCKZktNfvjewcurygTVr5MY2un3wIrJuDvY9OpbhUAsDy3TLSsowoS4G41UGCv+khPvRQblK4zIuVhCfbsQFMMd4FDScHrWYIJeweN3pwmSt359hV+bVLkxHEq1FERRgIyg1tQRyZxifdtbKtQGqMy5JNZ3hi6lQLo00Z0eAYisgZTqJeUpP3tjcvLMyYTQmXpyrE4MLmog+3DKGZEZA3muHeLyJ661hMOmJeE2MuXUftzlbpTFHjfGXn8LBPGooaxoKVxZ57i4VL2rxsPpg+5SJBYlfNy4n+O6pXvZ/xFZ6auAtHbEAAAAASUVORK5CYII="], "2": ["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"], "3": ["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"], "4": ["iVBORw0KGgoAAAANSUhEUgAAACQAAAAkCAAAAADEa8dEAAAE7klEQVQ4EQXBe2zUdAAA4P76bq93vd5r2912e98GbIAigakYxAcEEuMf8wEkGDHEoIISFYwYEyQaTESjJkwlkRAkESUQFQhRMJIQHOgA2WAbe937fb3e9a7ttf21fh/4dsvv/Zknzq6Pz4obx9ZG2WQ3uu/ditvwttzqYEWUKBf7DDAhVLJLctpAaqrXN9OIIFEqNBZGFTctSm1ozcNKBb4K6nhJIDAR2nWcz7OYQ+TkCtcqyXgG65TELgOkeRKMubJXh6mko+W6z0krLXGGxMY7lhTSixrRJqZOM4VaEwRJ3/inx2anOnznlrfNLEnQN4ZliDjiRLDQaGanQy5RFSiQbMqFpCzojmYHjSzP56ngvEUH47gHVn1GFUNqBIeDy23p+tCtzCZlLuScUFceeTG0EIm33w8QRq0rQ5m45ONUcDtgnl/uFvvyJafHGrvi/phTPZ41L7tCRbmjeq/fGQu4RTDZVjNtPteTTTWjF1+zfyq4hvoO7wTPjsBEM0w0oaAajoNCNdF4VF7oi8mOX48LxwOpSD6Uat3744r3uhiignilXLAALreKbklRO6F2/sB3W+Nyl6ZEXtoffaoj+9diJOZwSzBYBnNEFYRyqicTWH1wCPrTevcbv0X+zd1pbNv6ljBHBnNsQAE2MtruRbJhSXj+VIyn70N6EK4aTQrIOuJSIR/2x11UGVzrnYbNernr2CenQ6KXa8ztoqYHf3GmejOLv9iS84OiDymChKlIg0nBHLn85iK+4ruafmcw+8w3872J0bsH0waHLHBOCPKWxmMzdMua3h+KGocbjxnnHum7QACYPjFyy4mTWSeKglFvwtVqxB/2iIXp8gq1x1s8smfTGYNQ6lObt79OohkfSYISkSRYiTNWHV1dN5VTn+/aP7lh8KTscFs3Nx962tuYaG0GoFygPJID8kIF+a8PE/QoC5se/BnTIWNGPtuBzZqLaxUwbWhtZYWbPHRgmV7bNr57L5IYWnFFMpWCOvz+KwTMB1EdTNh2YdmdSG5l/z/X8lt3fzkxMDXQf7EajuGnP/jzAdCQW1Ac5PJGTxG2y4e+TYvrZ/srDktPkmFtNpY9OzIWNAuaYBBg3NabDcRh3hw+vPHEV2XKVmlbMHovKf7I0EF/jVfpug1uK2ynkoGBOzuWjcyn1p59yJt6cuCjbp/yauVGzEWIUEBxkBKJFmDiotVJrfmeSCBL4dUXyHwUv3hg73ZRZ5NQwFSwACXCSXElvePovp0f3qMCWObr/g3uoyc3vR2QTN8CFdDLYNKU3TgoNSt1V4QcvH6zw7/QjiFt3KJ12zATRWfcYVgHdQn6azVAA2jfsPbIz3lX1Obn/whvebzVaSzwbJ4QTB0kRDxkWoKKUvlUn3ThzN81xNXiP5Plwg26TOFVhTQa4G4Kb7IdjKVpKIO64oFKvZpcCoNsLkA0DIBouEPTwFSGDWhOUIQMgpJmienJZDyELVglL9FQMYi4+FoVFCoUKTuJKslXMQYpmk05JUjomN4QDNFw2irlsUQwr+NmycmoNE/rDkYpMXXa11ChRTrLMa5TrdA+RAJzNRpXGauAu7gKxao5h8W6LdCADKKkhC5Z5PmaCmSdRkoMW9GxGulBoroXID4Eahaj6RITUCo+OquDuUxYRz1MBbJlxYvIZqtlMYoN3XLdodlumKc8ZeV/TyuSTMqq8qYAAAAASUVORK5CYII="], "5": ["iVBORw0KGgoAAAANSUhEUgAAACQAAAAkCAAAAADEa8dEAAAE2ElEQVQ4EQXBe4gUZQAA8O+b9+y8d/f24d5Lzy4zzTIfqWVmculR/ZNQEYh/iBBIkCAlR0lYqPlMwkf0R0iCkogoWWqHcmliinLaae6d5921t3u7N7s7OzM7M99+szP9ftBGVqKOorYNVJ1UatOJGbnRBFfyOoRi6TVjJE3deDYOLctVTD9Z1ec5lQYfyXW7Xl1jnWk54LE6Laj/TS3FUJ8gM7rZhrKcRrCif3mxz/mqW348SxOx+HBxXfi3w4D1mh+HFVYcpwiKlpsjIo9HmedqhEsZUX5goTxGxkPomH7Ed0Q6tDkjzfg2gcGjNlqpK67ZwuhB28R4Kg0LFU4o1uQmkUINRMSyM6VqaEXrkshPeTRBsqHNcrDkSpFJI9pohnP/iSu5elK5x7XxlxaEsIBjZlSrYpmCZV1oMU3VsqOUGICjxv3BeWjJ2lleIo+jXGCori3U4CNLkXWOKgFMLzq5xZyzLLbi9gFv//IXbqXlhE4kSjRRheNIE4axUrcz2W3w9VWr9Gf0c4v6987b3A1lhASsJ0UTFhxNHcEddOnWnd2ffJ1LeJnCzV7mwtUTEw9SQSHGVKmIDidCOtC5CGlwy/YtH+67R3KhB5is13f9PtfIsZ1FGk/DqWYoTZlRQHbO/bYruf7vNUPMcOva7cWzB3duLPuARV5mDFZLIOYArrnv8HmmPf/mqtPZ54kqM94SPfDdhD+l+KVk04DFolYIMkS6+6XjZnj7o3d/np6MzZ62nK6pnn61EOXKVKMK8wZlVoTFA5+u3H5n6amDx0u5ZOTVwBJIe0PjFyshVZmmASt1H1jOkmN7R7Npou+kLvIGPtMa8KRz6egPGcnTOyUTPnUTVBEkL24dYJiRzU/wh93DZ+SrvJ+of9w/HPComqHL8BGSyHzcOTowOFHuXDL+xlnOSDHE3TYL/PjNH/ODBk74BpzGkSkqUcGvPHAd9rfmhlysZu66dGglRRw/PCAzYX6Oj+GkwI9RM4L+Dw71JkwLWHTbmLr/yupNgr/ppm026VyS9OBQRBhhcau1E3we5S6CRQLmg89+/eJtQG98730y4gAmT8BxShnjoefvOTmKhta/fLs2ReWufdX7ZaqD27KhkSl20vcZOEpETCRiLv/Ouj3NvhM930fhwCbiRnp0ac+RgttSynBVHj7mYDmIItS69fSFhXDd3RkxYzI5bklvXf4z5EUuBDJLwKekWnRVjGRrx7Udq/+aOOCS3btmGcfObV+R8njKhyxkYIHidV8i2Ah5fv/A7/NhMMOWauWfdve9uDbfhJ4hqi6Ewxp2YNAQlUo+fnHbmoUrYXAdH8nsWhHI2CGDmsBbHHyoBnWatABoH1LahZ4rWpVHC8RT9FMl0najk6qwQp2EOYZrNIOqn7atLgtUZp+SJule1qA9js7GFc8UFcuBT1gQIEB5WljXwpAirYZKlmAc10S+6mVcILs5Hw7KfBOxVCXuVRSKQoyOUhGdaDV1NWqZ7aiiEsUIHNa0CiWVSC1XTpNBTTL0aLvrJWzMoDxsB5NizCBgVpZyYqrISAW7gxijU0QNi6ChAmSyGDCsB0jEw0GBL9EzHYNCqJUe0wTHoAQMBaYCYJ3r8ppN15bhQ4VoQBaEyHFTyCD5MKQC0lORLoS6FicYf5JU/gcMcIFRuYJAHwAAAABJRU5ErkJggg=="]}


def find_tesseract() -> str | None:
    candidates = [
        shutil.which("tesseract"),
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    ]
    for p in candidates:
        if p and Path(p).exists():
            return str(p)
    return None


TESS = find_tesseract()
if TESS:
    pytesseract.pytesseract.tesseract_cmd = TESS


def require_tesseract():
    p = find_tesseract()
    if not p:
        raise RuntimeError("Tesseract OCR을 찾지 못했습니다. install.bat을 먼저 실행해 주세요.")
    pytesseract.pytesseract.tesseract_cmd = p
    langs = set(pytesseract.get_languages(config=""))
    missing = [x for x in ("kor", "eng") if x not in langs]
    if missing:
        raise RuntimeError("Tesseract 한글/영문 언어 데이터가 없습니다: " + ", ".join(missing))


def pix_to_bgr(pix):
    arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
    if pix.n == 4:
        return cv2.cvtColor(arr, cv2.COLOR_RGBA2BGR)
    return cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)


def render_page(doc: fitz.Document, pageno: int, dpi: int = DPI):
    mat = fitz.Matrix(dpi / 72, dpi / 72)
    pix = doc[pageno - 1].get_pixmap(matrix=mat, alpha=False)
    return pix_to_bgr(pix)


def parse_page_range(value: str, max_pages: int) -> list[int]:
    value = (value or "").strip()
    if not value:
        return list(range(1, max_pages + 1))
    pages = []
    for part in value.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-", 1)
            a, b = int(a), int(b)
            pages.extend(range(min(a, b), max(a, b) + 1))
        else:
            pages.append(int(part))
    pages = sorted(set(p for p in pages if 1 <= p <= max_pages))
    if not pages:
        raise ValueError("페이지 범위를 확인해 주세요.")
    return pages


def clean_text(s: str) -> str:
    s = s.replace("|", " ").replace("¦", " ").replace("：", ":")
    s = re.sub(r"\s+", " ", s).strip()
    return s.strip(" ·ㆍ-")


def detect_question_starts(img):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, np.array([90, 25, 25]), np.array([180, 255, 255]))
    n, _, stats, _ = cv2.connectedComponentsWithStats(mask, 8)
    H, W = img.shape[:2]
    comps = []
    for i in range(1, n):
        x, y, w, h, area = stats[i]
        if x < W * .23 and y > 80 and 12 <= h <= 65 and 4 <= w <= 50 and 80 <= area <= 1500:
            comps.append((x, y, w, h, area))

    groups = []
    for c in sorted(comps, key=lambda z: z[1]):
        if not groups or abs(c[1] - groups[-1][0]) > 12:
            groups.append([c[1], [c]])
        else:
            groups[-1][1].append(c)

    starts = []
    for y, grp in groups:
        x0 = min(c[0] for c in grp)
        x1 = max(c[0] + c[2] for c in grp)
        crop = img[max(0, y - 12): min(H, y + 65), max(0, x0 - 22): min(W, x1 + 30)]
        txt = pytesseract.image_to_string(
            crop, lang="eng",
            config="--psm 7 -c tessedit_char_whitelist=0123456789"
        ).strip()
        m = re.search(r"\d{1,3}", txt)
        if m:
            q = int(m.group())
            if 1 <= q <= 250:
                starts.append((q, int(y), int(x0)))

    out = []
    for item in starts:
        if out and abs(item[1] - out[-1][1]) < 20:
            continue
        out.append(item)
    return out


def detect_choice_markers(qimg):
    gray = cv2.cvtColor(qimg, cv2.COLOR_BGR2GRAY)
    _, th = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY_INV)
    contours, _ = cv2.findContours(th, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    cand = []
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        area = cv2.contourArea(c)
        per = cv2.arcLength(c, True)
        circ = 4 * math.pi * area / (per * per) if per else 0
        if 19 <= w <= 31 and 19 <= h <= 32 and .72 <= w / h <= 1.30 and circ > .72:
            cand.append((x, y, w, h, area, circ))

    pts = []
    for z in sorted(cand, key=lambda z: (z[1], z[0], -z[4])):
        x, y, w, h, *_ = z
        cx, cy = x + w / 2, y + h / 2
        if any((cx - p[0]) ** 2 + (cy - p[1]) ** 2 < 64 for p in pts):
            continue
        pts.append((cx, cy, x, y, w, h))

    rows = []
    for p in sorted(pts, key=lambda p: (p[1], p[0])):
        if not rows or abs(p[1] - np.mean([a[1] for a in rows[-1]])) > 18:
            rows.append([p])
        else:
            rows[-1].append(p)

    out = []
    for row in rows:
        row = sorted(row, key=lambda p: p[0])
        sel = []
        for p in row:
            if not sel or p[0] - sel[-1][0] > 120:
                sel.append(p)
        if 1 <= len(sel) <= 3:
            out.extend(sel)

    out = [p for p in sorted(out, key=lambda p: (p[1], p[0])) if p[1] > 25]
    return out[:5]


def extract_question_crop(qimg, qnum: int):
    markers = detect_choice_markers(qimg)
    if len(markers) != 5:
        return None, f"보기 기호 {len(markers)}개 감지"

    rows = []
    for p in markers:
        if not rows or abs(p[1] - np.mean([a[1] for a in rows[-1]])) > 18:
            rows.append([p])
        else:
            rows[-1].append(p)

    first_y = min(p[1] for p in markers)
    qreg = qimg[:max(20, int(first_y - 10)), :]
    qtxt = clean_text(pytesseract.image_to_string(qreg, lang=OCR_LANG, config="--psm 6"))
    qtxt = re.sub(r"^[^가-힣A-Za-z0-9]*[0O]?\s*" + re.escape(str(qnum).zfill(2)) + r"\s*", "", qtxt)
    qtxt = re.sub(r"^[^가-힣A-Za-z0-9]*" + re.escape(str(qnum)) + r"\s*", "", qtxt)

    choices = []
    H, W = qimg.shape[:2]
    for ri, row in enumerate(rows):
        row = sorted(row, key=lambda p: p[0])
        ry = int(np.mean([p[1] for p in row]))
        next_ry = int(np.mean([p[1] for p in rows[ri + 1]])) if ri + 1 < len(rows) else min(H, ry + 70)
        y0 = max(0, ry - 18)
        y1 = min(H, (next_ry - 5) if ri + 1 < len(rows) else ry + 65)
        for j, p in enumerate(row):
            x0 = max(0, int(p[0] + 18))
            x1 = int(row[j + 1][0] - 18) if j + 1 < len(row) else W - 15
            cimg = qimg[y0:y1, x0:x1]
            txt = clean_text(pytesseract.image_to_string(cimg, lang=OCR_LANG, config="--psm 6"))
            txt = re.sub(r"^[^가-힣A-Za-z0-9(]+", "", txt)
            choices.append(txt)

    return {
        "number": qnum,
        "question": qtxt,
        "choices": choices[:5],
    }, None


def extract_questions(pdf_path: str, pages: list[int], start_q: int, end_q: int, progress=None):
    doc = fitz.open(pdf_path)
    res = []
    issues = []
    for pi, pageno in enumerate(pages, 1):
        if progress:
            progress(f"문제 PDF 분석 중 - {pageno}쪽", pi / max(1, len(pages)))
        img = render_page(doc, pageno)
        starts = detect_question_starts(img)
        H, W = img.shape[:2]
        for i, (q, y, _) in enumerate(starts):
            if q < start_q or q > end_q:
                continue
            y0 = max(0, y - 15)
            y1 = starts[i + 1][1] - 15 if i + 1 < len(starts) else H - 70
            crop = img[y0:y1, 70:W - 60]
            item, err = extract_question_crop(crop, q)
            if item:
                item["source_question_page"] = pageno
                res.append(item)
            else:
                issues.append(f"문제 {q}번: {err}")
    # same number can appear if a combined PDF contains multiple sections; keep first in requested range
    uniq = {}
    for q in res:
        uniq.setdefault(q["number"], q)
    return [uniq[k] for k in sorted(uniq)], issues


def _decode_template(b64_text: str):
    arr = np.frombuffer(base64.b64decode(b64_text), np.uint8)
    return cv2.imdecode(arr, cv2.IMREAD_GRAYSCALE)


def _norm_marker(crop):
    _, bw = cv2.threshold(crop, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    contours, _ = cv2.findContours(bw, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    best = None
    H, W = bw.shape
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        area = cv2.contourArea(c)
        per = cv2.arcLength(c, True)
        circ = 4 * math.pi * area / (per * per) if per else 0
        cx, cy = x + w / 2, y + h / 2
        dist = (cx - W / 2) ** 2 + (cy - H / 2) ** 2
        if 15 <= w <= 32 and 15 <= h <= 32 and circ > .45:
            sc = area - dist * 1.5
            if best is None or sc > best[0]:
                best = (sc, x, y, w, h)
    if best:
        _, x, y, w, h = best
        pad = 2
        sub = bw[max(0, y - pad):min(H, y + h + pad), max(0, x - pad):min(W, x + w + pad)]
    else:
        sub = bw

    h, w = sub.shape
    s = max(h, w) + 4
    canvas = np.zeros((s, s), np.uint8)
    oy, ox = (s - h) // 2, (s - w) // 2
    canvas[oy:oy + h, ox:ox + w] = sub
    return cv2.resize(canvas, (40, 40), interpolation=cv2.INTER_AREA).astype(np.float32) / 255


def _corr(a, b):
    aa, bb = a - a.mean(), b - b.mean()
    d = np.linalg.norm(aa) * np.linalg.norm(bb)
    return float((aa * bb).sum() / d) if d else -1


ANSWER_REFS = {
    int(d): [_norm_marker(_decode_template(x)) for x in arr]
    for d, arr in ANSWER_TEMPLATES_B64.items()
}


def classify_answer_marker(img, cx, cy):
    crop = cv2.cvtColor(
        img[int(cy - 18):int(cy + 18), int(cx - 18):int(cx + 18)],
        cv2.COLOR_BGR2GRAY
    )
    m = _norm_marker(crop)
    scores = {d: max(_corr(m, r) for r in refs) for d, refs in ANSWER_REFS.items()}
    ordered = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    best, second = ordered[0], ordered[1]
    return best[0], best[1], best[1] - second[1]


def ocr_cell_num(img, cx, cy):
    crop = img[int(cy - 18):int(cy + 18), max(0, int(cx - 70)):max(1, int(cx - 18))]
    txt = pytesseract.image_to_string(
        crop, lang="eng",
        config="--psm 7 -c tessedit_char_whitelist=0123456789"
    ).strip()
    m = re.search(r"\d{1,3}", txt)
    return int(m.group()) if m else None


def detect_answer_grid(img):
    H, W = img.shape[:2]
    y0, y1 = int(H * .05), int(H * .55)
    x0, x1 = 0, int(W * .62)
    reg = img[y0:y1, x0:x1]
    gray = cv2.cvtColor(reg, cv2.COLOR_BGR2GRAY)
    g = cv2.GaussianBlur(gray, (3, 3), 0)
    circles = cv2.HoughCircles(
        g, cv2.HOUGH_GRADIENT, 1.1, 15,
        param1=100, param2=18, minRadius=8, maxRadius=14
    )
    if circles is None:
        return []

    pts = [(float(x), float(y), float(r)) for x, y, r in circles[0]]
    bins = collections.Counter(round(x / 10) * 10 for x, y, r in pts)
    peaks = [x for x, c in bins.most_common(7) if c >= 4][:5]
    if len(peaks) < 4:
        return []
    peaks = sorted(peaks)

    selected = [(x, y, r) for x, y, r in pts if min(abs(x - xp) for xp in peaks) < 12]
    ys = sorted(y for x, y, r in selected)
    clusters = []
    for y in ys:
        if not clusters or y - np.mean(clusters[-1]) > 15:
            clusters.append([y])
        else:
            clusters[-1].append(y)
    rows = [float(np.mean(c)) for c in clusters if len(c) >= max(3, len(peaks) - 1)]

    cells = []
    for ry in rows:
        for xp in peaks:
            cx, cy = x0 + xp, y0 + ry
            qnum = ocr_cell_num(img, cx, cy)
            if qnum is None:
                continue
            ans, score, margin = classify_answer_marker(img, cx, cy)
            cells.append((qnum, ans, score, margin))
    return cells


def extract_answers(pdf_path: str, pages: list[int], start_q: int, end_q: int, progress=None):
    doc = fitz.open(pdf_path)
    answers = {}
    issues = []
    for pi, pageno in enumerate(pages, 1):
        if progress:
            progress(f"정답 PDF 분석 중 - {pageno}쪽", pi / max(1, len(pages)))
        img = render_page(doc, pageno)
        cells = detect_answer_grid(img)
        for q, ans, score, margin in cells:
            if start_q <= q <= end_q:
                answers[q] = {
                    "answer": ans,
                    "score": round(score, 3),
                    "margin": round(margin, 3),
                    "page": pageno,
                }
                if score < .55 or margin < .04:
                    issues.append(f"정답 {q}번: 인식 신뢰도가 낮습니다({ans}번, score={score:.2f}).")
    return answers, issues


def heading_candidate(line: str, expected: int) -> bool:
    s = line.strip()
    nums = re.findall(r"\d{2,3}", s)
    if len(nums) != 1 or int(nums[0]) != expected:
        return False
    rest = re.sub(r"\d", "", s)
    return not bool(re.search(r"[A-Za-z가-힣]", rest))


def extract_explanations(pdf_path: str, pages: list[int], start_q: int, end_q: int, progress=None):
    doc = fitz.open(pdf_path)
    exp = collections.defaultdict(list)
    current = None
    expected = start_q

    for pi, pageno in enumerate(pages, 1):
        if progress:
            progress(f"풀이 PDF 분석 중 - {pageno}쪽", pi / max(1, len(pages)))
        img = render_page(doc, pageno)
        H, W = img.shape[:2]
        for side in ("left", "right"):
            if side == "left":
                crop = img[int(H * .10):int(H * .96), int(W * .04):int(W * .51)]
            else:
                crop = img[int(H * .10):int(H * .96), int(W * .49):int(W * .96)]
            txt = pytesseract.image_to_string(crop, lang=OCR_LANG, config="--psm 6")
            for raw in txt.splitlines():
                ln = raw.strip(" |")
                if not ln:
                    continue
                if expected <= end_q and heading_candidate(ln, expected):
                    current = expected
                    expected += 1
                    continue
                if current is None:
                    continue
                if "KPTLE" in ln:
                    continue
                exp[current].append(ln)

    result = {q: clean_text(" ".join(lines)) for q, lines in exp.items()}
    issues = [f"풀이 {q}번: 해설을 찾지 못했습니다." for q in range(start_q, end_q + 1) if not result.get(q)]
    return result, issues


def build_bank(bank_name, problem_pdf, answer_pdf, explanation_pdf,
               problem_pages, answer_pages, explanation_pages,
               start_q, end_q, output_dir, progress=None):
    require_tesseract()
    issues = []

    questions, q_issues = extract_questions(problem_pdf, problem_pages, start_q, end_q, progress)
    issues.extend(q_issues)

    answers, a_issues = extract_answers(answer_pdf, answer_pages, start_q, end_q, progress)
    issues.extend(a_issues)

    explanations, e_issues = extract_explanations(
        explanation_pdf, explanation_pages, start_q, end_q, progress
    )
    issues.extend(e_issues)

    qmap = {q["number"]: q for q in questions}
    bank_questions = []
    for n in range(start_q, end_q + 1):
        q = qmap.get(n)
        if not q:
            issues.append(f"문제 {n}번: 문제를 찾지 못했습니다.")
            continue
        a = answers.get(n)
        if not a:
            issues.append(f"정답 {n}번: 정답을 찾지 못했습니다.")
            continue

        bank_questions.append({
            "id": f"{re.sub(r'[^0-9A-Za-z가-힣]+', '-', bank_name).strip('-')}-{n:03d}",
            "set": bank_name,
            "session": "",
            "subject": bank_name,
            "number": n,
            "question": q["question"],
            "choices": q["choices"],
            "answer": a["answer"],
            "explanation": explanations.get(n, "등록된 해설이 없습니다."),
            "source": (
                f"문제 PDF {Path(problem_pdf).name} {q.get('source_question_page', '')}쪽 / "
                f"정답 PDF {Path(answer_pdf).name} {a.get('page', '')}쪽"
            ),
            "_review": {
                "answer_score": a.get("score"),
                "answer_margin": a.get("margin"),
                "needs_review": (
                    not explanations.get(n)
                    or len(q.get("choices", [])) != 5
                    or a.get("score", 0) < .55
                    or a.get("margin", 0) < .04
                ),
            },
        })

    bank = {
        "name": bank_name,
        "creator": "나대현",
        "version": 1,
        "source_type": "local_pdf_ocr",
        "questions": bank_questions,
    }

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    safe = re.sub(r'[\\/:*?"<>|]+', "_", bank_name).strip() or "questions"
    json_path = output_dir / f"{safe}.json"
    review_path = output_dir / f"{safe}_검수.html"

    with json_path.open("w", encoding="utf-8") as f:
        json.dump(bank, f, ensure_ascii=False, indent=2)

    create_review_html(bank, review_path, issues)

    if progress:
        progress("완료", 1.0)
    return json_path, review_path, issues, bank


def create_review_html(bank, path: Path, issues: list[str]):
    data = json.dumps(bank, ensure_ascii=False).replace("</", "<\\/")
    issues_html = "".join(f"<li>{html.escape(x)}</li>" for x in issues) or "<li>자동 검사에서 별도 경고가 없습니다.</li>"
    doc = """<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><title>PT국시 문제은행 검수</title>
<style>
body{font-family:'Malgun Gothic',sans-serif;background:#f4f6fa;color:#182033;margin:0;padding:28px}
.wrap{max-width:1100px;margin:auto} h1{margin:0 0 8px} .sub{color:#69758a;margin-bottom:22px} .creator{color:#8b95a5;font-size:12px;margin:-12px 0 18px}
.box,.q{background:#fff;border:1px solid #e0e5ee;border-radius:14px;padding:18px;margin:12px 0}
.q.bad{border-color:#e9a7a1} label{display:block;font-size:12px;font-weight:700;color:#6f7b8f;margin:9px 0 5px}
input[type=text],textarea,select{width:100%;box-sizing:border-box;border:1px solid #d8deea;border-radius:8px;padding:9px;font:inherit}
textarea{min-height:72px} .choices{display:grid;grid-template-columns:1fr 1fr;gap:8px}
button{border:0;background:#3157d5;color:#fff;border-radius:10px;padding:12px 16px;font-weight:700;cursor:pointer}
.warn{color:#a33} .toolbar{position:sticky;top:0;background:#f4f6fa;padding:8px 0;z-index:2}
</style></head><body><div class="wrap">
<h1>PT국시 문제은행 검수</h1><div class="sub" id="summary"></div><div class="creator">제작자 · 나대현</div>
<div class="box"><strong>자동 검사</strong><ul>""" + issues_html + """</ul></div>
<div class="toolbar"><button onclick="downloadJson()">수정된 문제은행 JSON 다운로드</button></div>
<div id="list"></div>
</div>
<script>
const bank = """ + data + """;
const list = document.getElementById('list');
document.getElementById('summary').textContent = bank.name + ' · ' + bank.questions.length + '문항';
bank.questions.forEach((q, idx)=>{
  const d=document.createElement('div'); d.className='q'+(q._review&&q._review.needs_review?' bad':'');
  d.innerHTML=`<h3>${q.number}번 ${q._review&&q._review.needs_review?'<span class="warn">· 확인 권장</span>':''}</h3>
  <label>문제</label><textarea data-k="question">${esc(q.question)}</textarea>
  <label>보기</label><div class="choices">${q.choices.map((c,i)=>`<input type="text" data-choice="${i}" value="${attr(c)}">`).join('')}</div>
  <label>정답</label><select data-k="answer">${[1,2,3,4,5].map(n=>`<option value="${n}" ${n===q.answer?'selected':''}>${n}</option>`).join('')}</select>
  <label>풀이</label><textarea data-k="explanation">${esc(q.explanation||'')}</textarea>`;
  d.querySelector('[data-k="question"]').oninput=e=>q.question=e.target.value;
  d.querySelector('[data-k="answer"]').onchange=e=>q.answer=Number(e.target.value);
  d.querySelector('[data-k="explanation"]').oninput=e=>q.explanation=e.target.value;
  d.querySelectorAll('[data-choice]').forEach(el=>el.oninput=e=>q.choices[Number(el.dataset.choice)]=e.target.value);
  list.appendChild(d);
});
function esc(s){return String(s??'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')}
function attr(s){return esc(s).replace(/"/g,'&quot;')}
function downloadJson(){
  const clean=JSON.parse(JSON.stringify(bank));
  clean.questions.forEach(q=>delete q._review);
  const blob=new Blob([JSON.stringify(clean,null,2)],{type:'application/json;charset=utf-8'});
  const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=(bank.name||'questions')+'.json';a.click();
  setTimeout(()=>URL.revokeObjectURL(a.href),1000);
}
</script></body></html>"""
    path.write_text(doc, encoding="utf-8")


class App:
    def __init__(self, root):
        self.root = root
        root.title("PT국시 문제은행 갱신기")
        root.geometry("820x690")
        root.minsize(760, 620)

        self.bank_name = StringVar(value="PT국시 문제은행")
        self.problem = StringVar()
        self.answer = StringVar()
        self.explanation = StringVar()
        self.same = BooleanVar(value=True)
        self.problem_pages = StringVar()
        self.answer_pages = StringVar()
        self.explanation_pages = StringVar()
        self.start_q = IntVar(value=1)
        self.end_q = IntVar(value=10)
        self.output_dir = StringVar(value=str(Path.home() / "PT국시" / "문제은행"))

        frm = ttk.Frame(root, padding=22)
        frm.pack(fill="both", expand=True)

        ttk.Label(frm, text="PT국시 문제은행 갱신기", font=("Malgun Gothic", 20, "bold")).pack(anchor="w")
        ttk.Label(frm, text="문제 PDF + 정답 PDF + 풀이 PDF 한 세트를 개별 문제은행(JSON)으로 만듭니다. 모든 처리는 이 PC 안에서 진행됩니다.").pack(anchor="w", pady=(4, 18))

        grid = ttk.Frame(frm)
        grid.pack(fill="x")
        self._row_file(grid, 0, "문제 PDF", self.problem)
        self._row_file(grid, 1, "정답 PDF", self.answer)
        self._row_file(grid, 2, "풀이 PDF", self.explanation)

        ttk.Checkbutton(
            grid, text="정답과 풀이가 같은 PDF", variable=self.same,
            command=self._same_changed
        ).grid(row=3, column=1, sticky="w", pady=5)

        ttk.Label(grid, text="문제은행 이름").grid(row=4, column=0, sticky="w", pady=6)
        ttk.Entry(grid, textvariable=self.bank_name).grid(row=4, column=1, columnspan=2, sticky="ew", pady=6)

        ranges = ttk.LabelFrame(frm, text="범위 설정", padding=12)
        ranges.pack(fill="x", pady=14)
        ttk.Label(ranges, text="문제 PDF 페이지").grid(row=0, column=0, sticky="w")
        ttk.Entry(ranges, textvariable=self.problem_pages, width=18).grid(row=0, column=1, padx=6)
        ttk.Label(ranges, text="예: 9-10").grid(row=0, column=2, sticky="w")

        ttk.Label(ranges, text="정답 PDF 페이지").grid(row=1, column=0, sticky="w")
        ttk.Entry(ranges, textvariable=self.answer_pages, width=18).grid(row=1, column=1, padx=6)
        ttk.Label(ranges, text="예: 5").grid(row=1, column=2, sticky="w")

        ttk.Label(ranges, text="풀이 PDF 페이지").grid(row=2, column=0, sticky="w")
        ttk.Entry(ranges, textvariable=self.explanation_pages, width=18).grid(row=2, column=1, padx=6)
        ttk.Label(ranges, text="예: 5-6").grid(row=2, column=2, sticky="w")

        ttk.Label(ranges, text="문제번호").grid(row=3, column=0, sticky="w", pady=(8, 0))
        qf = ttk.Frame(ranges)
        qf.grid(row=3, column=1, columnspan=2, sticky="w", pady=(8, 0))
        ttk.Spinbox(qf, from_=1, to=250, textvariable=self.start_q, width=7).pack(side="left")
        ttk.Label(qf, text=" ~ ").pack(side="left")
        ttk.Spinbox(qf, from_=1, to=250, textvariable=self.end_q, width=7).pack(side="left")

        out = ttk.LabelFrame(frm, text="저장 위치", padding=12)
        out.pack(fill="x")
        ttk.Entry(out, textvariable=self.output_dir).pack(side="left", fill="x", expand=True)
        ttk.Button(out, text="폴더 선택", command=self.pick_output).pack(side="left", padx=(8, 0))

        self.progress = ttk.Progressbar(frm, mode="determinate")
        self.progress.pack(fill="x", pady=(18, 8))
        self.status = StringVar(value="준비")
        ttk.Label(frm, textvariable=self.status).pack(anchor="w")

        self.log = ttk.Treeview(frm, columns=("msg",), show="headings", height=7)
        self.log.heading("msg", text="처리 로그")
        self.log.column("msg", width=700)
        self.log.pack(fill="both", expand=True, pady=8)

        self.btn = ttk.Button(frm, text="문제은행 만들기", command=self.start)
        self.btn.pack(anchor="e", pady=(4, 0))

        ttk.Label(frm, text="제작자 · 나대현").pack(anchor="w", pady=(8, 0))

        grid.columnconfigure(1, weight=1)
        self._same_changed()

    def _row_file(self, parent, row, label, var):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=6)
        ttk.Entry(parent, textvariable=var).grid(row=row, column=1, sticky="ew", padx=6, pady=6)
        ttk.Button(parent, text="선택", command=lambda v=var: self.pick_pdf(v)).grid(row=row, column=2, pady=6)

    def pick_pdf(self, var):
        p = filedialog.askopenfilename(filetypes=[("PDF", "*.pdf")])
        if p:
            var.set(p)
            if var is self.answer and self.same.get():
                self.explanation.set(p)

    def pick_output(self):
        p = filedialog.askdirectory()
        if p:
            self.output_dir.set(p)

    def _same_changed(self):
        if self.same.get() and self.answer.get():
            self.explanation.set(self.answer.get())

    def add_log(self, msg):
        self.log.insert("", "end", values=(msg,))
        self.log.yview_moveto(1)

    def update_progress(self, msg, value):
        self.root.after(0, lambda: self._ui_progress(msg, value))

    def _ui_progress(self, msg, value):
        self.status.set(msg)
        self.progress["value"] = max(0, min(100, value * 100))
        self.add_log(msg)

    def start(self):
        if self.same.get():
            self.explanation.set(self.answer.get())
        vals = [self.problem.get(), self.answer.get(), self.explanation.get()]
        if not all(vals) or not all(Path(x).exists() for x in vals):
            messagebox.showerror("확인", "문제/정답/풀이 PDF를 모두 선택해 주세요.")
            return
        if self.start_q.get() > self.end_q.get():
            messagebox.showerror("확인", "문제번호 범위를 확인해 주세요.")
            return

        self.btn.configure(state="disabled")
        self.log.delete(*self.log.get_children())
        threading.Thread(target=self._worker, daemon=True).start()

    def _worker(self):
        try:
            pdoc = fitz.open(self.problem.get())
            adoc = fitz.open(self.answer.get())
            edoc = fitz.open(self.explanation.get())
            pp = parse_page_range(self.problem_pages.get(), pdoc.page_count)
            ap = parse_page_range(self.answer_pages.get(), adoc.page_count)
            ep = parse_page_range(self.explanation_pages.get(), edoc.page_count)
            pdoc.close(); adoc.close(); edoc.close()

            json_path, review_path, issues, bank = build_bank(
                self.bank_name.get().strip() or "PT국시 문제은행",
                self.problem.get(), self.answer.get(), self.explanation.get(),
                pp, ap, ep, self.start_q.get(), self.end_q.get(),
                self.output_dir.get(), self.update_progress
            )
            self.root.after(0, lambda: self._done(json_path, review_path, issues, bank))
        except Exception as e:
            self.root.after(0, lambda: self._failed(str(e)))

    def _done(self, json_path, review_path, issues, bank):
        self.btn.configure(state="normal")
        self.progress["value"] = 100
        self.status.set(f"완료 - {len(bank['questions'])}문항")
        msg = (
            f"문제은행 생성 완료\n\n"
            f"JSON: {json_path}\n"
            f"검수화면: {review_path}\n\n"
            f"확인 권장 항목: {len(issues)}개"
        )
        messagebox.showinfo("완료", msg)
        try:
            webbrowser.open(review_path.as_uri())
        except Exception:
            pass

    def _failed(self, msg):
        self.btn.configure(state="normal")
        self.status.set("오류")
        self.add_log("오류: " + msg)
        messagebox.showerror("오류", msg)


def main():
    root = Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()