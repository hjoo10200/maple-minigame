import base64
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="허접한 인내의 숲",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    .block-container {
        max-width: 1040px;
        padding-top: 1.2rem;
    }

    h1 {
        font-size: 1.55rem !important;
        margin-bottom: 0.2rem !important;
    }

    .stCaption {
        margin-bottom: 0.35rem;
    }

    </style>
    """,
    unsafe_allow_html=True,
)

st.title("허접한 인내의 숲")
st.caption("화살표 또는 WASD 이동, Space 점프")

bgm_path = Path(__file__).resolve().parent / "엘리니아 필드.mp3"
if bgm_path.exists():
    st.audio(bgm_path, format="audio/mpeg", loop=True, autoplay=True, width=320)


def image_to_data_url(path: Path | None = None, uploaded_file=None) -> str:
    if path is not None and path.exists():
        image_bytes = path.read_bytes()
        mime_type = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".webp": "image/webp",
        }.get(path.suffix.lower(), "image/png")
    elif uploaded_file is not None:
        image_bytes = uploaded_file.getvalue()
        mime_type = uploaded_file.type or "image/png"
    else:
        return ""

    encoded_image = base64.b64encode(image_bytes).decode("ascii")
    return f"data:{mime_type};base64,{encoded_image}"


default_spritesheet = Path(__file__).resolve().parent / "spritesheet.webp"
default_character = Path(__file__).resolve().parent / "character.png"
default_exit_portal = Path(__file__).resolve().parent / "exit_portal.png"
default_background = Path(__file__).resolve().parent / "elinia.png"
default_star_projectile = Path(__file__).resolve().parent / "표창.png"
default_npc = Path(__file__).resolve().parent / "npc.png"
background_data_url = ""
character_data_url = ""
portal_data_url = ""
star_data_url = ""
npc_data_url = ""

if default_background.exists():
    background_data_url = image_to_data_url(default_background)

if default_exit_portal.exists():
    portal_data_url = image_to_data_url(default_exit_portal)

if default_star_projectile.exists():
    star_data_url = image_to_data_url(default_star_projectile)

if default_npc.exists():
    npc_data_url = image_to_data_url(default_npc)

if default_spritesheet.exists():
    character_data_url = image_to_data_url(default_spritesheet)
elif default_character.exists():
    character_data_url = image_to_data_url(default_character)
else:
    uploaded_character = st.file_uploader(
        "플레이어 캐릭터 이미지",
        type=["png", "jpg", "jpeg", "webp"],
        label_visibility="collapsed",
    )

    if uploaded_character is not None:
        character_data_url = image_to_data_url(uploaded_file=uploaded_character)
    else:
        st.caption(
            "캐릭터 이미지를 spritesheet.webp 또는 character.png로 저장하거나 여기 업로드하면 "
            "그 캐릭터가 직접 움직입니다."
        )


game_html = """
    <div class="game-shell">
      <canvas id="game" width="960" height="551" aria-label="bad forest platform game"></canvas>
      <div class="hud">
        <button id="restart">처음부터</button>
        <button id="prev-stage">이전</button>
        <button id="next-stage">다음</button>
        <button id="demo-run">자동플레이</button>
        <span id="status">대충 시작!</span>
      </div>
    </div>

    <style>
    html, body {
      margin: 0;
      background: #0d1f18;
    }

    .game-shell {
      width: min(960px, 100%);
      margin: 0 auto;
      user-select: none;
      font-family: Arial, sans-serif;
    }

    #game {
      width: 100%;
      aspect-ratio: 1212 / 696;
      display: block;
      background: #132f24;
      image-rendering: pixelated;
      border: 1px solid rgba(222, 255, 198, 0.26);
      border-radius: 8px;
      box-sizing: border-box;
      box-shadow:
        0 24px 80px rgba(0, 0, 0, 0.45),
        inset 0 0 0 1px rgba(255, 255, 255, 0.08);
    }

    .hud {
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 8px 0 0;
      color: #dff7d5;
      font-size: 14px;
    }

    button {
      border: 1px solid rgba(224, 255, 203, 0.35);
      border-radius: 6px;
      background: linear-gradient(#284b34, #14281f);
      color: #eaffdf;
      padding: 5px 10px;
      font-weight: 700;
      cursor: pointer;
    }
    </style>

    <script>
    const canvas = document.getElementById("game");
    const ctx = canvas.getContext("2d");
    const statusText = document.getElementById("status");
    const restartButton = document.getElementById("restart");
    const prevStageButton = document.getElementById("prev-stage");
    const nextStageButton = document.getElementById("next-stage");
    const demoRunButton = document.getElementById("demo-run");
    const suppliedBackground = "__BACKGROUND_DATA_URL__";
    const suppliedCharacter = "__CHARACTER_DATA_URL__";
    const suppliedPortal = "__PORTAL_DATA_URL__";
    const suppliedStar = "__STAR_DATA_URL__";
    const suppliedNpc = "__NPC_DATA_URL__";
    const backgroundImage = new Image();
    const characterImage = new Image();
    const portalImage = new Image();
    const starImage = new Image();
    const npcImage = new Image();
    const characterCanvas = document.createElement("canvas");
    const characterCtx = characterCanvas.getContext("2d");
    const spriteFrameCanvas = document.createElement("canvas");
    const spriteFrameCtx = spriteFrameCanvas.getContext("2d", { willReadFrequently: true });
    const starCanvas = document.createElement("canvas");
    const starCtx = starCanvas.getContext("2d", { willReadFrequently: true });
    const npcCanvas = document.createElement("canvas");
    const npcCtx = npcCanvas.getContext("2d", { willReadFrequently: true });
    let hasSuppliedBackground = false;
    let hasCharacterSprite = false;
    let hasPortalImage = false;
    let hasStarImage = false;
    let hasNpcImage = false;
    let hasCharacterSheet = false;
    let characterSpriteBounds = { x: 0, y: 0, w: 1, h: 1 };
    let npcSpriteBounds = { x: 0, y: 0, w: 52, h: 70 };

    if (suppliedBackground) {
      backgroundImage.src = suppliedBackground;
      backgroundImage.onload = () => {
        hasSuppliedBackground = true;
      };
    }

    if (suppliedCharacter) {
      characterImage.src = suppliedCharacter;
      characterImage.onload = () => {
        characterCanvas.width = characterImage.naturalWidth;
        characterCanvas.height = characterImage.naturalHeight;
        characterCtx.clearRect(0, 0, characterCanvas.width, characterCanvas.height);
        characterCtx.drawImage(characterImage, 0, 0);
        hasCharacterSheet = characterImage.naturalWidth >= 1400 && characterImage.naturalHeight >= 1600;
        characterSpriteBounds = findOpaqueBounds(
          characterCtx.getImageData(0, 0, characterCanvas.width, characterCanvas.height)
        );
        hasCharacterSprite = true;
      };
    }

    if (suppliedPortal) {
      portalImage.src = suppliedPortal;
      portalImage.onload = () => {
        hasPortalImage = true;
      };
    }

    function makeEdgeWhiteTransparent(imageData) {
      const { width, height, data } = imageData;
      const visited = new Uint8Array(width * height);
      const stack = [];

      function isNearWhite(pixelIndex) {
        const offset = pixelIndex * 4;
        return data[offset + 3] > 0 && data[offset] > 235 && data[offset + 1] > 235 && data[offset + 2] > 235;
      }

      function addPixel(x, y) {
        if (x < 0 || y < 0 || x >= width || y >= height) return;
        const pixelIndex = y * width + x;
        if (visited[pixelIndex] || !isNearWhite(pixelIndex)) return;
        visited[pixelIndex] = 1;
        stack.push(pixelIndex);
      }

      for (let x = 0; x < width; x++) {
        addPixel(x, 0);
        addPixel(x, height - 1);
      }
      for (let y = 0; y < height; y++) {
        addPixel(0, y);
        addPixel(width - 1, y);
      }

      while (stack.length) {
        const pixelIndex = stack.pop();
        const offset = pixelIndex * 4;
        data[offset + 3] = 0;
        const x = pixelIndex % width;
        const y = Math.floor(pixelIndex / width);
        addPixel(x + 1, y);
        addPixel(x - 1, y);
        addPixel(x, y + 1);
        addPixel(x, y - 1);
      }

      return imageData;
    }

    function findOpaqueBounds(imageData) {
      const { width, height, data } = imageData;
      let minX = width;
      let minY = height;
      let maxX = -1;
      let maxY = -1;

      for (let y = 0; y < height; y++) {
        for (let x = 0; x < width; x++) {
          const alpha = data[(y * width + x) * 4 + 3];
          if (alpha <= 18) continue;
          minX = Math.min(minX, x);
          minY = Math.min(minY, y);
          maxX = Math.max(maxX, x);
          maxY = Math.max(maxY, y);
        }
      }

      if (maxX < minX || maxY < minY) {
        return { x: 0, y: 0, w: width, h: height };
      }

      return {
        x: minX,
        y: minY,
        w: maxX - minX + 1,
        h: maxY - minY + 1,
      };
    }

    function isSpriteSheetBackdropPixel(data, pixelIndex) {
      const offset = pixelIndex * 4;
      const r = data[offset];
      const g = data[offset + 1];
      const b = data[offset + 2];
      const a = data[offset + 3];
      if (a <= 18) return true;

      const hotMagenta = r >= 120 && g <= 55 && b >= 95;
      const deepPurple = r >= 60 && g <= 35 && b >= 60 && Math.abs(r - b) <= 95;
      const artifactBlue = b >= 150 && r <= 70 && g <= 95;
      const artifactGreen = g >= 85 && r <= 45 && b <= 45;
      const artifactRed = r >= 130 && g <= 35 && b <= 45;
      return hotMagenta || deepPurple || artifactBlue || artifactGreen || artifactRed;
    }

    function makeSpriteSheetBackdropTransparent(imageData) {
      const { width, height, data } = imageData;
      const seen = new Uint8Array(width * height);
      const stack = [];

      function addPixel(x, y) {
        if (x < 0 || y < 0 || x >= width || y >= height) return;
        const pixelIndex = y * width + x;
        if (seen[pixelIndex] || !isSpriteSheetBackdropPixel(data, pixelIndex)) return;
        seen[pixelIndex] = 1;
        stack.push(pixelIndex);
      }

      for (let x = 0; x < width; x++) {
        addPixel(x, 0);
        addPixel(x, height - 1);
      }
      for (let y = 0; y < height; y++) {
        addPixel(0, y);
        addPixel(width - 1, y);
      }

      while (stack.length) {
        const pixelIndex = stack.pop();
        data[pixelIndex * 4 + 3] = 0;
        const x = pixelIndex % width;
        const y = Math.floor(pixelIndex / width);
        addPixel(x + 1, y);
        addPixel(x - 1, y);
        addPixel(x, y + 1);
        addPixel(x, y - 1);
      }

      return imageData;
    }

    function cleanSpriteCell(sprite) {
      spriteFrameCanvas.width = sprite.sw;
      spriteFrameCanvas.height = sprite.sh;
      spriteFrameCtx.clearRect(0, 0, sprite.sw, sprite.sh);
      spriteFrameCtx.drawImage(characterCanvas, sprite.sx, sprite.sy, sprite.sw, sprite.sh, 0, 0, sprite.sw, sprite.sh);
      const pixels = spriteFrameCtx.getImageData(0, 0, sprite.sw, sprite.sh);
      spriteFrameCtx.putImageData(makeSpriteSheetBackdropTransparent(pixels), 0, 0);
      return findOpaqueBounds(spriteFrameCtx.getImageData(0, 0, sprite.sw, sprite.sh));
    }

    function buildStarProjectile() {
      const crop = { x: 386, y: 34, w: 160, h: 154 };
      const size = 72;
      starCanvas.width = size;
      starCanvas.height = size;
      starCtx.clearRect(0, 0, size, size);
      starCtx.imageSmoothingEnabled = false;
      starCtx.drawImage(starImage, crop.x, crop.y, crop.w, crop.h, 0, 0, size, size);
      const pixels = starCtx.getImageData(0, 0, size, size);
      starCtx.putImageData(makeEdgeWhiteTransparent(pixels), 0, 0);
      hasStarImage = true;
    }

    if (suppliedStar) {
      starImage.src = suppliedStar;
      starImage.onload = buildStarProjectile;
    }

    if (suppliedNpc) {
      npcImage.src = suppliedNpc;
      npcImage.onload = () => {
        npcCanvas.width = npcImage.naturalWidth;
        npcCanvas.height = npcImage.naturalHeight;
        npcCtx.clearRect(0, 0, npcCanvas.width, npcCanvas.height);
        npcCtx.drawImage(npcImage, 0, 0);
        npcSpriteBounds = findOpaqueBounds(npcCtx.getImageData(0, 0, npcCanvas.width, npcCanvas.height));
        hasNpcImage = true;
      };
    }

    ctx.imageSmoothingEnabled = false;

    const keys = new Set();
    const world = { width: 960, height: 1650, gravity: 0.55 };
    const spriteGrid = {
      x: [0, 200, 400, 600, 800, 1000, 1200, 1366],
      y: [0, 210, 420, 630, 835, 1040, 1260, 1460, 1660],
      w: 170,
      h: 190,
    };
    const spriteBoundsCache = new Map();

    function spriteCell(row, col) {
      return {
        sx: spriteGrid.x[col],
        sy: spriteGrid.y[row],
        sw: spriteGrid.w,
        sh: spriteGrid.h,
      };
    }

    const spriteAnimations = {
      idle: [
        spriteCell(0, 0),
        spriteCell(0, 1),
        spriteCell(0, 2),
        spriteCell(0, 3),
        spriteCell(0, 4),
        spriteCell(0, 5),
      ],
      run: [
        spriteCell(1, 0),
        spriteCell(1, 1),
        spriteCell(1, 2),
        spriteCell(1, 3),
        spriteCell(1, 4),
        spriteCell(1, 5),
        spriteCell(1, 6),
        spriteCell(1, 7),
        spriteCell(2, 0),
        spriteCell(2, 1),
        spriteCell(2, 2),
        spriteCell(2, 3),
        spriteCell(2, 4),
        spriteCell(2, 5),
        spriteCell(2, 6),
        spriteCell(2, 7),
      ],
      jump: [
        spriteCell(4, 0),
        spriteCell(4, 1),
        spriteCell(4, 2),
        spriteCell(4, 3),
        spriteCell(4, 4),
      ],
      rope: [
        spriteCell(3, 0),
        spriteCell(3, 1),
        spriteCell(3, 2),
        spriteCell(3, 3),
      ],
      fall: [
        spriteCell(5, 6),
      ],
    };

    const npcStageMessages = [
      [
        "천천히 가. 급하면 바로 떨어진다.",
        "점프는 끝까지 누르면 조금 더 높아.",
        "발판 가운데를 보고 착지해.",
        "괜찮아. 처음 숲은 몸풀기야.",
      ],
      [
        "창은 타이밍만 보면 지나갈 수 있어.",
        "튀어나온 뒤 들어갈 때가 기회야.",
        "표창보다 창 소리를 먼저 봐.",
        "서두르지 말고 한 칸씩.",
      ],
      [
        "표창 리듬을 보고 뛰어.",
        "좁은 발판은 멈춰서 숨 고르자.",
        "떨어질 것 같으면 반대로 살짝.",
        "여긴 손보다 침착함 싸움이야.",
      ],
      [
        "여기부터 손이 좀 바빠질 거야.",
        "표창 지나간 직후가 제일 편해.",
        "멀리 뛰기 전에 착지점을 먼저 봐.",
        "급한 점프는 숲이 다 받아먹는다.",
      ],
      [
        "마지막이야. 침착하게 한 발씩.",
        "작은 발판은 짧게 눌러.",
        "창이 들어간 순간 바로 넘어가.",
        "여기 깨면 진짜 인내 인정.",
      ],
    ];

    const stages = [
      {
        name: "인내의 숲 <1단계>: 끊긴 발판",
        height: 1650,
        tint: "#dfffd1",
        start: { x: 78, y: 1546 },
        goal: { x: 720, y: 54, w: 160, h: 90 },
        checkpoints: [
          { x: 590, y: 1016, w: 22, h: 45 },
          { x: 116, y: 698, w: 22, h: 45 },
          { x: 520, y: 390, w: 22, h: 45 },
        ],
        ropes: [],
        spikes: [],
        platforms: [
          { x: 42, y: 1600, w: 190, h: 15 },
          { x: 248, y: 1538, w: 160, h: 14 },
          { x: 450, y: 1472, w: 160, h: 14 },
          { x: 650, y: 1404, w: 160, h: 14 },
          { x: 500, y: 1324, w: 155, h: 14 },
          { x: 310, y: 1248, w: 155, h: 14 },
          { x: 116, y: 1170, w: 150, h: 14 },
          { x: 338, y: 1096, w: 150, h: 14 },
          { x: 588, y: 1020, w: 150, h: 14 },
          { x: 762, y: 940, w: 140, h: 14 },
          { x: 546, y: 858, w: 145, h: 14 },
          { x: 326, y: 780, w: 145, h: 14 },
          { x: 112, y: 702, w: 140, h: 14 },
          { x: 344, y: 628, w: 140, h: 14 },
          { x: 584, y: 552, w: 140, h: 14 },
          { x: 748, y: 474, w: 136, h: 14 },
          { x: 520, y: 394, w: 136, h: 14 },
          { x: 294, y: 316, w: 132, h: 14 },
          { x: 520, y: 236, w: 132, h: 14 },
          { x: 752, y: 146, w: 140, h: 14 },
        ],
        hazards: [
          { x: 492, y: 1288, r: 11, dx: 1.25, min: 360, max: 700, type: "star" },
          { x: 650, y: 246, r: 11, dx: -1.15, min: 548, max: 840, type: "star" },
        ],
      },
      {
        name: "인내의 숲 <2단계>: 창과 투사체",
        height: 1780,
        tint: "#c7ffd8",
        start: { x: 812, y: 1670 },
        goal: { x: 54, y: 55, w: 160, h: 90 },
        checkpoints: [
          { x: 744, y: 1276, w: 22, h: 45 },
          { x: 274, y: 518, w: 22, h: 45 },
        ],
        ropes: [],
        spikes: [
          { platform: 4, dir: "up", align: 0.55, span: 64, length: 42, phase: 30, period: 165 },
          { platform: 8, dir: "up", align: 0.48, span: 54, length: 44, phase: 70, period: 160 },
          { platform: 12, dir: "up", align: 0.52, span: 58, length: 44, phase: 110, period: 155 },
        ],
        platforms: [
          { x: 748, y: 1720, w: 172, h: 15 },
          { x: 545, y: 1612, w: 132, h: 14 },
          { x: 332, y: 1508, w: 128, h: 14 },
          { x: 590, y: 1392, w: 126, h: 14 },
          { x: 750, y: 1280, w: 118, h: 14 },
          { x: 514, y: 1182, w: 116, h: 14 },
          { x: 274, y: 1088, w: 118, h: 14 },
          { x: 74, y: 990, w: 118, h: 14 },
          { x: 240, y: 900, w: 112, h: 14 },
          { x: 470, y: 812, w: 112, h: 14 },
          { x: 710, y: 724, w: 108, h: 14 },
          { x: 512, y: 612, w: 110, h: 14 },
          { x: 272, y: 522, w: 106, h: 14 },
          { x: 64, y: 430, w: 106, h: 14 },
          { x: 260, y: 340, w: 100, h: 14 },
          { x: 530, y: 258, w: 100, h: 14 },
          { x: 300, y: 206, w: 100, h: 14 },
          { x: 52, y: 148, w: 150, h: 14 },
        ],
        hazards: [
          { x: 720, y: 1568, r: 12, dx: -1.55, min: 420, max: 860, type: "star" },
          { x: 166, y: 928, r: 12, dx: 1.45, min: 42, max: 510, type: "star" },
          { x: 778, y: 686, r: 12, dx: -1.5, min: 510, max: 884, type: "star" },
          { x: 520, y: 214, r: 11, dx: 1.35, min: 260, max: 780, type: "star" },
        ],
      },
      {
        name: "인내의 숲 <3단계>: 엇박자 가지길",
        height: 1720,
        tint: "#eaffbd",
        start: { x: 72, y: 1610 },
        goal: { x: 724, y: 58, w: 160, h: 90 },
        checkpoints: [
          { x: 566, y: 1238, w: 22, h: 45 },
          { x: 318, y: 624, w: 22, h: 45 },
          { x: 640, y: 186, w: 22, h: 45 },
        ],
        ropes: [],
        spikes: [
          { platform: 2, dir: "up", align: 0.44, span: 58, length: 46, phase: 0, period: 150 },
          { platform: 6, dir: "up", align: 0.52, span: 54, length: 48, phase: 55, period: 148 },
          { platform: 10, dir: "up", align: 0.46, span: 52, length: 48, phase: 102, period: 146 },
          { platform: 13, dir: "up", align: 0.5, span: 50, length: 48, phase: 20, period: 142 },
        ],
        platforms: [
          { x: 38, y: 1660, w: 170, h: 15 },
          { x: 268, y: 1544, w: 124, h: 14 },
          { x: 532, y: 1442, w: 118, h: 14 },
          { x: 724, y: 1324, w: 108, h: 14 },
          { x: 518, y: 1242, w: 108, h: 14 },
          { x: 298, y: 1156, w: 102, h: 14 },
          { x: 90, y: 1068, w: 104, h: 14 },
          { x: 316, y: 978, w: 100, h: 14 },
          { x: 574, y: 892, w: 100, h: 14 },
          { x: 760, y: 806, w: 98, h: 14 },
          { x: 526, y: 716, w: 98, h: 14 },
          { x: 286, y: 628, w: 96, h: 14 },
          { x: 80, y: 540, w: 96, h: 14 },
          { x: 312, y: 450, w: 92, h: 14 },
          { x: 564, y: 360, w: 92, h: 14 },
          { x: 742, y: 270, w: 96, h: 14 },
          { x: 610, y: 190, w: 86, h: 14 },
          { x: 710, y: 160, w: 178, h: 14 },
        ],
        hazards: [
          { x: 330, y: 1490, r: 12, dx: 1.75, min: 242, max: 760, type: "star" },
          { x: 188, y: 1036, r: 12, dx: 1.9, min: 72, max: 472, type: "star" },
          { x: 650, y: 860, r: 13, dx: -1.85, min: 320, max: 860, type: "star" },
          { x: 452, y: 580, r: 12, dx: -1.95, min: 128, max: 720, type: "star" },
          { x: 610, y: 318, r: 12, dx: 1.7, min: 300, max: 850, type: "star" },
          { x: 780, y: 246, r: 11, dx: -1.45, min: 610, max: 900, type: "star" },
        ],
      },
      {
        name: "인내의 숲 <4단계>: 표창 순찰층",
        height: 1700,
        tint: "#d5ffc8",
        start: { x: 820, y: 1588 },
        goal: { x: 68, y: 58, w: 160, h: 90 },
        checkpoints: [
          { x: 650, y: 1264, w: 22, h: 45 },
          { x: 594, y: 582, w: 22, h: 45 },
        ],
        ropes: [],
        spikes: [
          { platform: 3, dir: "up", align: 0.45, span: 52, length: 50, phase: 20, period: 128 },
          { platform: 5, dir: "up", align: 0.55, span: 54, length: 50, phase: 68, period: 124 },
          { platform: 8, dir: "up", align: 0.5, span: 52, length: 52, phase: 104, period: 120 },
          { platform: 11, dir: "up", align: 0.5, span: 50, length: 52, phase: 12, period: 118 },
          { platform: 14, dir: "up", align: 0.48, span: 48, length: 50, phase: 82, period: 116 },
        ],
        platforms: [
          { x: 748, y: 1640, w: 170, h: 15 },
          { x: 598, y: 1530, w: 102, h: 14 },
          { x: 744, y: 1408, w: 86, h: 14 },
          { x: 650, y: 1268, w: 84, h: 14 },
          { x: 430, y: 1160, w: 84, h: 14 },
          { x: 196, y: 1050, w: 82, h: 14 },
          { x: 52, y: 940, w: 82, h: 14 },
          { x: 268, y: 846, w: 78, h: 14 },
          { x: 512, y: 760, w: 78, h: 14 },
          { x: 742, y: 674, w: 76, h: 14 },
          { x: 594, y: 586, w: 74, h: 14 },
          { x: 372, y: 500, w: 74, h: 14 },
          { x: 148, y: 414, w: 72, h: 14 },
          { x: 328, y: 330, w: 70, h: 14 },
          { x: 562, y: 246, w: 70, h: 14 },
          { x: 304, y: 210, w: 70, h: 14 },
          { x: 52, y: 150, w: 180, h: 14 },
        ],
        hazards: [
          { x: 602, y: 1470, r: 13, dx: -2.15, min: 320, max: 880, type: "star" },
          { x: 140, y: 1220, r: 13, dx: 2.05, min: 70, max: 420, type: "star" },
          { x: 560, y: 864, r: 13, dx: -2.0, min: 216, max: 880, type: "star" },
          { x: 318, y: 706, r: 12, dx: 2.0, min: 76, max: 780, type: "star" },
          { x: 756, y: 418, r: 12, dx: -1.9, min: 520, max: 900, type: "star" },
          { x: 310, y: 214, r: 12, dx: 2.0, min: 52, max: 660, type: "star" },
          { x: 470, y: 1110, r: 11, dy: 1.55, minY: 990, maxY: 1228, type: "star" },
          { x: 690, y: 640, r: 11, dy: -1.65, minY: 526, maxY: 760, type: "star" },
        ],
      },
      {
        name: "인내의 숲 <5단계>: 허브 무더기",
        height: 1900,
        tint: "#ecffd2",
        ascentShrink: true,
        start: { x: 70, y: 1798 },
        goal: { x: 680, y: 58, w: 190, h: 100 },
        checkpoints: [
          { x: 340, y: 1248, w: 22, h: 45 },
          { x: 546, y: 516, w: 22, h: 45 },
        ],
        ropes: [],
        spikes: [
          { platform: 2, dir: "up", align: 0.5, span: 56, length: 48, phase: 0, period: 132 },
          { platform: 4, dir: "up", align: 0.56, span: 54, length: 50, phase: 46, period: 126 },
          { platform: 6, dir: "up", align: 0.44, span: 50, length: 50, phase: 88, period: 124 },
          { platform: 8, dir: "up", align: 0.54, span: 48, length: 52, phase: 118, period: 120 },
          { platform: 10, dir: "up", align: 0.48, span: 46, length: 52, phase: 30, period: 118 },
          { platform: 13, dir: "up", align: 0.5, span: 42, length: 50, phase: 92, period: 116 },
          { platform: 16, dir: "up", align: 0.5, span: 38, length: 48, phase: 145, period: 114 },
          { platform: 19, dir: "up", align: 0.52, span: 34, length: 46, phase: 64, period: 112 },
        ],
        platforms: [
          { x: 42, y: 1848, w: 190, h: 15 },
          { x: 279, y: 1764, w: 172, h: 14 },
          { x: 520, y: 1682, w: 158, h: 14 },
          { x: 750, y: 1592, w: 146, h: 14 },
          { x: 530, y: 1504, w: 136, h: 14 },
          { x: 306, y: 1420, w: 128, h: 14 },
          { x: 85, y: 1338, w: 120, h: 14 },
          { x: 304, y: 1252, w: 112, h: 14 },
          { x: 541, y: 1172, w: 106, h: 14 },
          { x: 754, y: 1088, w: 100, h: 14 },
          { x: 548, y: 1006, w: 94, h: 14 },
          { x: 326, y: 924, w: 88, h: 14 },
          { x: 108, y: 842, w: 84, h: 14 },
          { x: 340, y: 762, w: 80, h: 14 },
          { x: 572, y: 680, w: 76, h: 14 },
          { x: 764, y: 598, w: 72, h: 14 },
          { x: 546, y: 518, w: 68, h: 14 },
          { x: 328, y: 440, w: 64, h: 14 },
          { x: 120, y: 362, w: 60, h: 14 },
          { x: 349, y: 286, w: 58, h: 14 },
          { x: 578, y: 216, w: 56, h: 14 },
          { x: 715, y: 160, w: 150, h: 14 },
        ],
        hazards: [
          { x: 604, y: 1638, r: 11, dx: -2.25, min: 328, max: 870, type: "star" },
          { x: 174, y: 1304, r: 11, dx: 2.12, min: 58, max: 548, type: "star" },
          { x: 764, y: 1054, r: 11, dx: -2.18, min: 432, max: 884, type: "star" },
          { x: 306, y: 808, r: 10, dx: 2.08, min: 70, max: 612, type: "star" },
          { x: 634, y: 562, r: 10, dx: -2.0, min: 382, max: 858, type: "star" },
          { x: 416, y: 326, r: 10, dx: 1.92, min: 96, max: 706, type: "star" },
          { x: 462, y: 1510, r: 10, dy: 1.7, minY: 1376, maxY: 1660, type: "star" },
          { x: 720, y: 960, r: 10, dy: -1.82, minY: 804, maxY: 1118, type: "star" },
          { x: 214, y: 662, r: 10, dy: 1.74, minY: 520, maxY: 844, type: "star" },
          { x: 508, y: 238, r: 9, dy: -1.55, minY: 156, maxY: 360, type: "star" },
        ],
      },
    ];

    const platformWidthRules = [
      { scale: 1.00, min: 132, max: 190 },
      { scale: 0.88, min: 96, max: 150 },
      { scale: 0.76, min: 78, max: 126 },
      { scale: 0.63, min: 58, max: 108 },
      { scale: 0.72, min: 38, max: 118 },
    ];

    const platformGuardRules = [
      { step: 9, max: 0, targetTotal: 2, r: 9, speed: 1.0, range: 64, yOffset: 58 },
      { step: 5, max: 1, targetTotal: 4, r: 10, speed: 1.25, range: 82, yOffset: 57 },
      { step: 4, max: 1, targetTotal: 6, r: 10, speed: 1.45, range: 94, yOffset: 56 },
      { step: 3, max: 2, targetTotal: 9, r: 11, speed: 1.62, range: 108, yOffset: 55 },
      { step: 3, max: 2, targetTotal: 11, r: 10, speed: 1.82, range: 118, yOffset: 54 },
    ];

    const platformGrassBottomOffset = -3;

    function platformSurfaceY(platform) {
      return platform.y + platformGrassBottomOffset;
    }

    function preparePlatforms(stageConfig, stageIndex) {
      const rule = platformWidthRules[Math.min(stageIndex, platformWidthRules.length - 1)];
      return stageConfig.platforms.map((platform) => {
        const centerX = platform.x + platform.w / 2;
        const ascentProgress = Math.max(0, Math.min(1, 1 - platform.y / stageConfig.height));
        const ascentScale = stageConfig.ascentShrink ? 1 - ascentProgress * 0.38 : 1;
        const width = Math.round(Math.max(rule.min, Math.min(rule.max, platform.w * rule.scale * ascentScale)));
        return {
          ...platform,
          x: Math.round(centerX - width / 2),
          w: width,
        };
      });
    }

    function prepareHazards(stageConfig, stageIndex, stagePlatforms) {
      const baseHazards = stageConfig.hazards.map((hazard) => ({ ...hazard }));
      const rule = platformGuardRules[Math.min(stageIndex, platformGuardRules.length - 1)];
      const targetTotal = rule.targetTotal;
      const pinnedHazards = baseHazards.filter((hazard) => hazard.pinned);
      const roamingHazards = baseHazards.filter((hazard) => !hazard.pinned);
      const baseCount = Math.max(0, Math.min(roamingHazards.length, targetTotal - rule.max - pinnedHazards.length));
      const keptBaseHazards = [...roamingHazards.slice(0, baseCount), ...pinnedHazards];
      const guardCount = Math.max(0, Math.min(rule.max, targetTotal - keptBaseHazards.length));
      const guardPlatforms = stagePlatforms
        .map((platform, index) => ({ platform, index }))
        .filter(({ index }) => index > 0 && index < stagePlatforms.length - 1 && index % rule.step === 0)
        .slice(0, guardCount);

      const guardHazards = guardPlatforms.map(({ platform, index }, guardIndex) => {
        const min = Math.max(28, Math.round(platform.x - rule.range));
        const max = Math.min(world.width - 28, Math.round(platform.x + platform.w + rule.range));
        const direction = (guardIndex + stageIndex) % 2 === 0 ? 1 : -1;
        const speed = rule.speed + (guardIndex % 3) * 0.16;
        const startX = Math.max(min + rule.r, Math.min(max - rule.r, Math.round(platform.x + platform.w / 2 + direction * platform.w * 0.32)));

        return {
          x: startX,
          y: Math.max(92, Math.round(platform.y - rule.yOffset)),
          r: rule.r,
          dx: direction * speed,
          min,
          max,
          type: "star",
          platformGuard: true,
        };
      });

      return [...keptBaseHazards, ...guardHazards];
    }

    function prepareSpikes(stageConfig, stagePlatforms) {
      return (stageConfig.spikes || []).map((spike) => {
        if (spike.platform === undefined) return { ...spike };

        const platform = stagePlatforms[spike.platform];
        if (!platform) return { ...spike };

        const span = Math.round(Math.min(spike.span || platform.w, platform.w + 12));
        const align = spike.align ?? 0.5;
        const centerX = platform.x + platform.w * align;
        const x = Math.round(Math.max(platform.x - 6, Math.min(platform.x + platform.w + 6 - span, centerX - span / 2)));
        const y = platformSurfaceY(platform);

        return {
          ...spike,
          dir: "up",
          x,
          y,
          w: span,
          h: 24,
        };
      });
    }

    let currentStage = 0;
    let stage = stages[currentStage];
    let platforms = preparePlatforms(stage, currentStage);
    let checkpoints = stage.checkpoints;
    let hazards = prepareHazards(stage, currentStage, platforms);
    let ropes = stage.ropes || [];
    let spikes = prepareSpikes(stage, platforms);
    let clearTimer = 0;
    let frame = 0;
    let demoMode = false;
    let demoIndex = 0;
    let demoRoute = [];
    let cameraY = 0;
    let stageStartedAt = performance.now();
    let stageFinishElapsedMs = null;
    let npcBubbleText = "";
    let npcBubbleMessageIndex = -1;
    let npcBubbleStartFrame = -9999;
    let npcBubbleNextFrame = 0;
    const npcBubbleVisibleFrames = 135;
    const npcBubbleHiddenFrames = 80;

    const player = {
      x: stage.start.x,
      y: stage.start.y,
      w: 22,
      h: 34,
      vx: 0,
      vy: 0,
      grounded: false,
      checkpoint: { ...stage.start },
      deaths: 0,
      onRope: false,
      facing: 1,
      coyote: 0,
      jumpBuffer: 0,
      lastJump: false,
      won: false
    };

    function getStageStartSpot() {
      const startPlatform = platforms[0];
      return {
        x: stage.start.x,
        y: startPlatform ? Math.round(platformSurfaceY(startPlatform) - player.h) : stage.start.y,
      };
    }

    function loadStage(index) {
      currentStage = (index + stages.length) % stages.length;
      stage = stages[currentStage];
      world.height = stage.height;
      platforms = preparePlatforms(stage, currentStage);
      checkpoints = stage.checkpoints;
      hazards = prepareHazards(stage, currentStage, platforms);
      ropes = stage.ropes || [];
      spikes = prepareSpikes(stage, platforms);
      clearTimer = 0;
      stageStartedAt = performance.now();
      stageFinishElapsedMs = null;
      demoMode = false;
      demoIndex = 0;
      demoRoute = [];
      npcBubbleText = "";
      npcBubbleMessageIndex = -1;
      npcBubbleStartFrame = -9999;
      npcBubbleNextFrame = frame;
      const startSpot = getStageStartSpot();
      cameraY = Math.max(0, Math.min(world.height - canvas.height, startSpot.y - 360));
      player.checkpoint = { ...startSpot };
      player.deaths = 0;
      reset(false);
      statusText.textContent = `${stage.name} 시작`;
    }

    function reset(toCheckpoint = true) {
      const spot = toCheckpoint ? player.checkpoint : getStageStartSpot();
      player.x = spot.x;
      player.y = spot.y;
      player.vx = 0;
      player.vy = 0;
      player.onRope = false;
      player.facing = 1;
      player.coyote = 0;
      player.jumpBuffer = 0;
      player.lastJump = false;
      player.won = false;
    }

    function makeDemoRoute() {
      const route = platforms
        .map((p) => ({
          x: Math.round(p.x + p.w / 2 - player.w / 2),
          y: Math.round(platformSurfaceY(p) - player.h),
        }))
        .sort((a, b) => b.y - a.y);

      route.unshift(getStageStartSpot());
      route.push({
        x: Math.round(stage.goal.x + stage.goal.w / 2 - player.w / 2),
        y: Math.round(stage.goal.y + stage.goal.h - player.h),
      });

      return route;
    }

    function getHumanControls() {
      return {
        left: keys.has("ArrowLeft") || keys.has("a"),
        right: keys.has("ArrowRight") || keys.has("d"),
        up: keys.has("ArrowUp") || keys.has("w"),
        down: keys.has("ArrowDown") || keys.has("s"),
        jump: keys.has(" "),
      };
    }

    function getBotControls() {
      if (!demoMode || demoRoute.length === 0) return getHumanControls();

      let target = demoRoute[Math.min(demoIndex, demoRoute.length - 1)];
      const centerX = player.x + player.w / 2;
      const targetX = target.x + player.w / 2;
      const dx = targetX - centerX;
      const dy = target.y - player.y;

      if (Math.abs(dx) < 22 && Math.abs(dy) < 34) {
        demoIndex += 1;
        target = demoRoute[Math.min(demoIndex, demoRoute.length - 1)];
      }

      if (demoIndex >= demoRoute.length) {
        demoMode = false;
        return { left: false, right: false, up: false, down: false, jump: false };
      }

      const nextDx = target.x + player.w / 2 - centerX;
      const nextDy = target.y - player.y;
      const usefulRope = ropes.find((rope) => {
        const horizontallyNear = Math.abs(rope.x - centerX) < 70;
        const verticalSpan = player.y > rope.y - 45 && target.y < player.y;
        return horizontallyNear && verticalSpan;
      });

      const controls = {
        left: nextDx < -16,
        right: nextDx > 16,
        up: false,
        down: false,
        jump: false,
      };

      if (usefulRope) {
        controls.left = centerX > usefulRope.x + 8;
        controls.right = centerX < usefulRope.x - 8;
        controls.up = Math.abs(centerX - usefulRope.x) < 22;
        controls.jump = controls.up && player.y < target.y + 35;
        return controls;
      }

      if (player.grounded && nextDy < -12) {
        controls.jump = true;
      }

      if (!player.grounded && player.vy < 0 && Math.abs(nextDx) < 28) {
        controls.left = false;
        controls.right = false;
      }

      return controls;
    }

    function rectsOverlap(a, b) {
      return a.x < b.x + b.w && a.x + a.w > b.x && a.y < b.y + b.h && a.y + a.h > b.y;
    }

    function getSpikePeriod(spike) {
      return (spike.period || 140) * 1.32;
    }

    function getSpikeExtend(spike) {
      const period = getSpikePeriod(spike);
      const t = ((frame + spike.phase) % period) / period;
      if (t < 0.16) return t / 0.16;
      if (t < 0.35) return 1;
      if (t < 0.5) return 1 - (t - 0.35) / 0.15;
      return 0;
    }

    function getSpikeLength(spike) {
      return spike.length || 48;
    }

    function startNpcBubble() {
      const messages = npcStageMessages[Math.min(currentStage, npcStageMessages.length - 1)] || npcStageMessages[0];
      if (!messages.length) return;

      npcBubbleMessageIndex = (npcBubbleMessageIndex + 1) % messages.length;
      npcBubbleText = messages[npcBubbleMessageIndex];
      npcBubbleStartFrame = frame;
      npcBubbleNextFrame = frame + npcBubbleVisibleFrames + npcBubbleHiddenFrames;
    }

    function updateNpcBubble() {
      if (frame >= npcBubbleNextFrame) {
        startNpcBubble();
      }
    }

    function getNpcBubbleAlpha() {
      if (!npcBubbleText) return 0;

      const age = frame - npcBubbleStartFrame;
      if (age < 0 || age > npcBubbleVisibleFrames) return 0;

      return 1;
    }

    function splatDeath() {
      player.deaths += 1;
      statusText.textContent = `떨어짐 ${player.deaths}번. 침착하게 다시.`;
      reset(true);
    }

    function update() {
      frame += 1;
      updateNpcBubble();

      if (player.won) {
        clearTimer += 1;
        if (clearTimer > 85) {
          loadStage(currentStage + 1);
        }
        return;
      }

      const controls = demoMode ? getBotControls() : getHumanControls();
      const { left, right, up, down, jump } = controls;
      const jumpPressed = jump && !player.lastJump;
      player.lastJump = jump;
      if (jumpPressed || (up && !player.onRope)) {
        player.jumpBuffer = 8;
      } else {
        player.jumpBuffer = Math.max(0, player.jumpBuffer - 1);
      }

      player.facing = left && !right ? -1 : 1;
      const playerBox = { x: player.x, y: player.y, w: player.w, h: player.h };
      const touchingRope = ropes.find((rope) => rectsOverlap(playerBox, { x: rope.x - 8, y: rope.y, w: 16, h: rope.h }));

      if (touchingRope && (up || down)) {
        player.onRope = true;
        player.x += (touchingRope.x - player.x - player.w / 2) * 0.22;
        player.vx = 0;
        player.vy = up ? -3.2 : down ? 3.2 : 0;
      }

      if (player.onRope) {
        if (!touchingRope) {
          player.onRope = false;
        } else {
          player.x += (touchingRope.x - player.x - player.w / 2) * 0.22;
          player.vx = left ? -1.4 : right ? 1.4 : 0;
          player.vy = up ? -3.45 : down ? 3.45 : 0;

          if (jumpPressed) {
            player.onRope = false;
            player.vy = -10.8;
            player.vx = left ? -4.9 : right ? 4.9 : player.facing * 3.1;
            player.jumpBuffer = 0;
          }
        }
      }

      if (!player.onRope) {
        const targetSpeed = (right ? 1 : 0) * 5.25 - (left ? 1 : 0) * 5.25;
        const accel = player.grounded ? 0.34 : 0.23;
        const friction = player.grounded ? 0.78 : 0.94;

        if (left || right) {
          player.vx += (targetSpeed - player.vx) * accel;
        } else {
          player.vx *= friction;
        }

        player.vx = Math.max(-5.6, Math.min(5.6, player.vx));

        if (player.grounded) {
          player.coyote = 7;
        } else {
          player.coyote = Math.max(0, player.coyote - 1);
        }

        if (player.jumpBuffer > 0 && player.coyote > 0) {
          player.vy = -11.9;
          player.grounded = false;
          player.coyote = 0;
          player.jumpBuffer = 0;
        }

        if (!jump && !up && player.vy < -4.2) {
          player.vy *= 0.82;
        }

        player.vy += player.vy < 0 ? 0.42 : 0.62;
        player.vy = Math.min(player.vy, 12.8);
      }

      player.x += player.vx;
      player.x = Math.max(0, Math.min(world.width - player.w, player.x));

      const beforeY = player.y;
      player.y += player.vy;
      player.grounded = false;

      for (const p of platforms) {
        const surfaceY = platformSurfaceY(p);
        const horizontalOverlap = player.x < p.x + p.w && player.x + player.w > p.x;
        const crossedSurface = beforeY + player.h <= surfaceY + 6 && player.y + player.h >= surfaceY - 3;
        if (horizontalOverlap && crossedSurface && player.vy >= 0) {
          player.y = surfaceY - player.h;
          player.vy = 0;
          player.grounded = true;
          player.coyote = 7;
        }
      }

      for (const h of hazards) {
        h.x += h.dx || 0;
        h.y += h.dy || 0;
        if (h.min !== undefined && h.max !== undefined && (h.x < h.min || h.x > h.max)) h.dx *= -1;
        if (h.minY !== undefined && h.maxY !== undefined && (h.y < h.minY || h.y > h.maxY)) h.dy *= -1;
        const badBox = h.type === "necki"
          ? { x: h.x - h.w / 2, y: h.y - h.h / 2, w: h.w, h: h.h }
          : { x: h.x - h.r, y: h.y - h.r, w: h.r * 2, h: h.r * 2 };
        if (rectsOverlap(player, badBox)) splatDeath();
      }

      for (const spike of spikes) {
        const extend = getSpikeExtend(spike);
        if (extend < 0.9) continue;

        const length = getSpikeLength(spike) * extend;
        let spikeBox = { x: spike.x, y: spike.y - length, w: spike.w, h: length };
        if (rectsOverlap(player, spikeBox)) splatDeath();
      }

      for (const c of checkpoints) {
        if (rectsOverlap(player, c)) {
          player.checkpoint = { x: c.x - 10, y: Math.round(checkpointSurfaceY(c) - player.h) };
          statusText.textContent = "체크포인트. 좀 살았다.";
        }
      }

      if (player.y > world.height + 120) splatDeath();

      if (rectsOverlap(player, stage.goal)) {
        player.won = true;
        clearTimer = 0;
        stageFinishElapsedMs = performance.now() - stageStartedAt;
        statusText.textContent = `${stage.name} 성공. 사망 ${player.deaths}번.`;
      }
    }

    function drawBadLine(x1, y1, x2, y2, color, width = 2) {
      ctx.strokeStyle = color;
      ctx.lineWidth = width;
      ctx.beginPath();
      ctx.moveTo(Math.round(x1), Math.round(y1));
      ctx.lineTo(Math.round(x2), Math.round(y2));
      ctx.stroke();
    }

    function drawLeafCluster(x, y, scale, base, highlight) {
      ctx.save();
      ctx.translate(x, y);
      ctx.scale(scale, scale);
      ctx.fillStyle = base;
      for (let i = 0; i < 9; i++) {
        const px = Math.cos(i * 1.9) * (18 + (i % 3) * 7);
        const py = Math.sin(i * 1.7) * (10 + (i % 4) * 4);
        ctx.beginPath();
        ctx.ellipse(px, py, 26 - (i % 2) * 5, 18 + (i % 3) * 3, i * 0.45, 0, Math.PI * 2);
        ctx.fill();
      }
      ctx.fillStyle = highlight;
      for (let i = 0; i < 5; i++) {
        ctx.beginPath();
        ctx.ellipse(-22 + i * 12, -12 + (i % 2) * 8, 12, 7, -0.5, 0, Math.PI * 2);
        ctx.fill();
      }
      ctx.restore();
    }

    function drawLightRay(x, width, alpha) {
      const ray = ctx.createLinearGradient(x, 0, x + width, 0);
      ray.addColorStop(0, `rgba(255,255,220,0)`);
      ray.addColorStop(0.5, `rgba(255,255,220,${alpha})`);
      ray.addColorStop(1, `rgba(255,255,220,0)`);
      ctx.fillStyle = ray;
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x + width, 0);
      ctx.lineTo(x + width * 0.72, canvas.height);
      ctx.lineTo(x - width * 0.28, canvas.height);
      ctx.closePath();
      ctx.fill();
    }

    function drawSoftEllipse(x, y, w, h, color) {
      ctx.fillStyle = color;
      ctx.beginPath();
      ctx.ellipse(x, y, w, h, 0, 0, Math.PI * 2);
      ctx.fill();
    }

    function drawCanopyBand(cameraY, depth, baseY, alpha) {
      const y = baseY - (cameraY * depth) % 240;
      for (let row = -1; row < 5; row++) {
        for (let i = 0; i < 11; i++) {
          const x = -80 + i * 108 + ((row + currentStage) % 2) * 38;
          const cy = y + row * 190 + (i % 3) * 18;
          drawLeafCluster(
            x,
            cy,
            1.05 + (i % 3) * 0.18,
            `rgba(27, 105, 47, ${alpha})`,
            `rgba(179, 229, 91, ${alpha * 0.45})`
          );
        }
      }
    }

    function drawTreeColumn(x, cameraY, width, palette, depth) {
      const parallaxY = -(cameraY * depth) % 620;
      const trunk = ctx.createLinearGradient(x, 0, x + width, 0);
      trunk.addColorStop(0, palette.dark);
      trunk.addColorStop(0.35, palette.mid);
      trunk.addColorStop(0.62, palette.light);
      trunk.addColorStop(1, palette.dark);

      for (let y = parallaxY - 680; y < canvas.height + 680; y += 620) {
        ctx.fillStyle = trunk;
        ctx.beginPath();
        ctx.moveTo(x + width * 0.18, y - 60);
        ctx.bezierCurveTo(x - width * 0.1, y + 190, x + width * 0.85, y + 310, x + width * 0.5, y + 640);
        ctx.lineTo(x + width, y + 650);
        ctx.bezierCurveTo(x + width * 0.65, y + 360, x + width * 1.15, y + 200, x + width * 0.62, y - 70);
        ctx.closePath();
        ctx.fill();

        ctx.strokeStyle = palette.line;
        ctx.lineWidth = 4;
        ctx.beginPath();
        ctx.moveTo(x + width * 0.45, y);
        ctx.bezierCurveTo(x + width * 0.2, y + 160, x + width * 0.7, y + 310, x + width * 0.38, y + 560);
        ctx.stroke();

        ctx.strokeStyle = palette.vine;
        ctx.lineWidth = 5;
        ctx.beginPath();
        ctx.moveTo(x + width * 0.8, y + 20);
        ctx.bezierCurveTo(x + width * 0.25, y + 130, x + width * 0.9, y + 280, x + width * 0.28, y + 480);
        ctx.stroke();

        ctx.strokeStyle = palette.glow || "rgba(204,255,157,0.16)";
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(x + width * 0.54, y + 20);
        ctx.bezierCurveTo(x + width * 0.9, y + 170, x + width * 0.25, y + 350, x + width * 0.58, y + 590);
        ctx.stroke();
      }
    }

    function drawBackground(cameraY) {
      if (hasSuppliedBackground) {
        const imageRatio = backgroundImage.naturalWidth / backgroundImage.naturalHeight;
        const canvasRatio = canvas.width / canvas.height;
        let sx = 0;
        let sw = backgroundImage.naturalWidth;

        if (imageRatio > canvasRatio) {
          sw = backgroundImage.naturalHeight * canvasRatio;
          sx = (backgroundImage.naturalWidth - sw) / 2;
        }

        const visibleHeight = sw / canvasRatio;
        const maxScroll = Math.max(0, backgroundImage.naturalHeight - visibleHeight);
        const worldScrollable = Math.max(1, world.height - canvas.height);
        const scrollRatio = Math.max(0, Math.min(1, cameraY / worldScrollable));
        const sy = maxScroll * (0.14 + scrollRatio * 0.72);

        ctx.drawImage(backgroundImage, sx, sy, sw, visibleHeight, 0, 0, canvas.width, canvas.height);
        return;
      }

      const gradient = ctx.createLinearGradient(0, 0, 0, canvas.height);
      gradient.addColorStop(0, "#eafdce");
      gradient.addColorStop(0.18, "#bde89d");
      gradient.addColorStop(0.52, stage.tint);
      gradient.addColorStop(1, "#245c39");
      ctx.fillStyle = gradient;
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      drawSoftEllipse(540, 94, 430, 120, "rgba(255,255,218,0.25)");
      drawLightRay(80, 120, 0.42);
      drawLightRay(562, 160, 0.38);
      drawLightRay(742, 92, 0.25);

      drawCanopyBand(cameraY, 0.05, -40, 0.18);

      drawTreeColumn(-70, cameraY, 170, {
        dark: "rgba(44,92,33,0.45)",
        mid: "rgba(86,137,47,0.50)",
        light: "rgba(137,184,71,0.45)",
        line: "rgba(44,92,33,0.35)",
        vine: "rgba(27,111,38,0.35)",
        glow: "rgba(210,255,158,0.16)"
      }, 0.14);
      drawTreeColumn(105, cameraY, 210, {
        dark: "rgba(39,85,31,0.50)",
        mid: "rgba(91,142,50,0.55)",
        light: "rgba(151,190,76,0.50)",
        line: "rgba(32,82,31,0.38)",
        vine: "rgba(24,102,37,0.38)",
        glow: "rgba(216,255,165,0.18)"
      }, 0.2);
      drawTreeColumn(585, cameraY, 260, {
        dark: "rgba(38,83,33,0.48)",
        mid: "rgba(104,151,59,0.52)",
        light: "rgba(174,203,91,0.45)",
        line: "rgba(33,75,32,0.38)",
        vine: "rgba(20,97,36,0.36)",
        glow: "rgba(229,255,174,0.18)"
      }, 0.18);
      drawTreeColumn(810, cameraY, 190, {
        dark: "rgba(34,78,31,0.44)",
        mid: "rgba(88,134,48,0.50)",
        light: "rgba(138,184,76,0.42)",
        line: "rgba(31,70,32,0.36)",
        vine: "rgba(23,93,38,0.32)",
        glow: "rgba(219,255,168,0.14)"
      }, 0.16);

      drawCanopyBand(cameraY, 0.12, 30, 0.3);

      const leafOffset = -(cameraY * 0.1) % 160;
      for (let i = 0; i < 18; i++) {
        const x = (i * 91 + currentStage * 37) % 1040 - 40;
        const y = ((i * 59 + leafOffset) % 710) - 80;
        drawLeafCluster(
          x,
          y,
          0.75 + (i % 4) * 0.12,
          i % 2 ? "rgba(40,137,50,0.58)" : "rgba(68,159,58,0.52)",
          "rgba(184,231,102,0.36)"
        );
      }

      ctx.strokeStyle = "rgba(21,102,36,0.55)";
      ctx.lineWidth = 4;
      for (let i = 0; i < 20; i++) {
        const x = 15 + i * 54;
        const sway = Math.sin((i + currentStage) * 1.7) * 24;
        ctx.beginPath();
        ctx.moveTo(x, -40);
        ctx.bezierCurveTo(x + sway, 120, x - sway, 280, x + sway * 0.4, 620);
        ctx.stroke();
      }

      for (let i = 0; i < 42; i++) {
        const x = (i * 97 + currentStage * 41) % canvas.width;
        const y = (i * 53 + currentStage * 29 - cameraY * 0.04) % canvas.height;
        ctx.fillStyle = i % 2 ? "rgba(255,255,214,0.58)" : "rgba(178,255,135,0.48)";
        ctx.fillRect(x, y, 3 + (i % 3) * 2, 3 + (i % 2) * 2);
      }

      ctx.fillStyle = "rgba(47,99,40,0.16)";
      ctx.fillRect(0, canvas.height - 64, canvas.width, 64);

      const vignette = ctx.createRadialGradient(
        canvas.width * 0.55,
        canvas.height * 0.4,
        80,
        canvas.width * 0.55,
        canvas.height * 0.45,
        640
      );
      vignette.addColorStop(0, "rgba(255,255,255,0)");
      vignette.addColorStop(1, "rgba(5,24,14,0.34)");
      ctx.fillStyle = vignette;
      ctx.fillRect(0, 0, canvas.width, canvas.height);
    }

    function drawPlatform(p, cameraY, index) {
      const y = p.y - cameraY;
      ctx.fillStyle = "rgba(0, 0, 0, 0.24)";
      ctx.beginPath();
      ctx.ellipse(p.x + p.w / 2, y + 30, p.w * 0.46, 14, 0, 0, Math.PI * 2);
      ctx.fill();

      const logGradient = ctx.createLinearGradient(p.x, y - 8, p.x, y + 28);
      logGradient.addColorStop(0, "#be8741");
      logGradient.addColorStop(0.28, "#875528");
      logGradient.addColorStop(0.72, "#5a3418");
      logGradient.addColorStop(1, "#28180c");
      ctx.fillStyle = logGradient;
      ctx.fillRect(p.x, y - 2, p.w, p.h + 9);
      ctx.strokeStyle = "rgba(20, 12, 5, 0.92)";
      ctx.lineWidth = 2;
      ctx.strokeRect(p.x, y - 2, p.w, p.h + 9);

      ctx.fillStyle = "rgba(255, 220, 137, 0.18)";
      ctx.fillRect(p.x + 3, y, p.w - 6, 3);
      ctx.fillStyle = "rgba(24, 12, 5, 0.22)";
      ctx.fillRect(p.x + 3, y + p.h + 2, p.w - 6, 5);

      for (let x = p.x + 6; x < p.x + p.w; x += 27) {
        const ring = ctx.createRadialGradient(x - 4, y + 12, 3, x, y + 12, 18);
        ring.addColorStop(0, "#d7a45d");
        ring.addColorStop(0.42, "#a66f34");
        ring.addColorStop(1, "#553018");
        ctx.fillStyle = ring;
        ctx.beginPath();
        ctx.arc(x, y + 14, 17, 0, Math.PI * 2);
        ctx.fill();
        ctx.strokeStyle = "#241206";
        ctx.stroke();
        ctx.strokeStyle = "#5b3518";
        ctx.beginPath();
        ctx.arc(x - 2, y + 13, 9, 0, Math.PI * 1.85);
        ctx.stroke();
      }

      const moss = ctx.createLinearGradient(p.x, y - 12, p.x, y + 4);
      moss.addColorStop(0, "#91e860");
      moss.addColorStop(0.5, "#35a940");
      moss.addColorStop(1, "#167234");
      ctx.fillStyle = moss;
      ctx.beginPath();
      ctx.moveTo(p.x + 4, y - 7);
      for (let x = p.x + 8; x < p.x + p.w - 6; x += 12) {
        ctx.lineTo(x, y - 9 - ((x + index) % 3));
        ctx.lineTo(x + 6, y - 5);
      }
      ctx.lineTo(p.x + p.w - 4, y - 5);
      ctx.lineTo(p.x + p.w - 4, y + 1);
      ctx.lineTo(p.x + 4, y + 1);
      ctx.closePath();
      ctx.fill();

      ctx.fillStyle = "#0f6c2a";
      if (index % 2 === 0) {
        ctx.beginPath();
        ctx.moveTo(p.x + 28, y + 16);
        ctx.lineTo(p.x + 46, y + 16);
        ctx.lineTo(p.x + 36, y + 54);
        ctx.closePath();
        ctx.fill();
      }
      if (index % 3 === 0) {
        ctx.beginPath();
        ctx.moveTo(p.x + p.w - 38, y + 16);
        ctx.lineTo(p.x + p.w - 21, y + 16);
        ctx.lineTo(p.x + p.w - 28, y + 58);
        ctx.closePath();
        ctx.fill();
      }

      ctx.strokeStyle = "#3c2411";
      ctx.lineWidth = 3;
      drawBadLine(p.x + 6, y - 8, p.x + 22, y - 18, "#4c2c13", 3);
      drawBadLine(p.x + p.w - 7, y - 7, p.x + p.w - 26, y - 17, "#4c2c13", 3);

      ctx.fillStyle = "#f7e783";
      ctx.fillRect(p.x + 5, y - 12, 7, 7);
      ctx.fillRect(p.x + p.w - 12, y - 12, 7, 7);
    }

    function drawHazard(h, cameraY) {
      const y = h.y - cameraY;
      if (h.type === "necki") {
        const direction = Math.sign(h.dx || 1);
        const wave = Math.sin(frame * 0.12 + h.x * 0.02);

        ctx.save();
        ctx.translate(h.x, y);
        ctx.scale(direction, 1);
        ctx.shadowColor = "rgba(6, 37, 25, 0.55)";
        ctx.shadowBlur = 7;

        const body = ctx.createLinearGradient(-28, -8, 28, 10);
        body.addColorStop(0, "#172a22");
        body.addColorStop(0.34, "#2d6f39");
        body.addColorStop(0.68, "#84c85d");
        body.addColorStop(1, "#183525");
        ctx.fillStyle = body;

        ctx.beginPath();
        ctx.ellipse(-16, wave * 2, 18, 9, -0.18, 0, Math.PI * 2);
        ctx.ellipse(3, -wave * 1.6, 20, 10, 0.12, 0, Math.PI * 2);
        ctx.ellipse(22, -2 + wave, 12, 9, 0.1, 0, Math.PI * 2);
        ctx.fill();

        ctx.shadowBlur = 0;
        ctx.strokeStyle = "#0b1712";
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(-31, 4);
        ctx.bezierCurveTo(-14, -7 + wave, 7, 9 - wave, 31, -2);
        ctx.stroke();

        ctx.fillStyle = "#f6ffe2";
        ctx.fillRect(18, -8, 4, 4);
        ctx.fillRect(28, -7, 4, 4);
        ctx.fillStyle = "#07100c";
        ctx.fillRect(20, -7, 2, 2);
        ctx.fillRect(30, -6, 2, 2);

        ctx.restore();
        return;
      }

      if (h.type === "star") {
        ctx.save();
        ctx.translate(h.x, y);
        ctx.rotate(frame * 0.28 * Math.sign(h.dx || 1));

        if (hasStarImage) {
          const size = h.r * 4.4;
          ctx.imageSmoothingEnabled = false;
          ctx.shadowColor = "rgba(160, 230, 255, 0.55)";
          ctx.shadowBlur = 8;
          ctx.drawImage(starCanvas, -size / 2, -size / 2, size, size);
          ctx.shadowBlur = 0;
        } else {
          ctx.shadowColor = "rgba(165, 235, 255, 0.75)";
          ctx.shadowBlur = 10;

          ctx.fillStyle = "#dff9ff";
          ctx.strokeStyle = "#1d5d8f";
          ctx.lineWidth = 2.4;
          ctx.beginPath();
          for (let i = 0; i < 8; i++) {
            const angle = -Math.PI / 2 + i * Math.PI / 4;
            const radius = i % 2 === 0 ? h.r + 7 : h.r * 0.42;
            const px = Math.cos(angle) * radius;
            const py = Math.sin(angle) * radius;
            if (i === 0) ctx.moveTo(px, py);
            else ctx.lineTo(px, py);
          }
          ctx.closePath();
          ctx.fill();
          ctx.stroke();

          ctx.shadowBlur = 0;
          ctx.fillStyle = "#5bd7ff";
          ctx.beginPath();
          ctx.arc(0, 0, h.r * 0.35, 0, Math.PI * 2);
          ctx.fill();

          ctx.strokeStyle = "rgba(255,255,255,0.9)";
          ctx.lineWidth = 1.5;
          ctx.beginPath();
          ctx.moveTo(-h.r * 0.6, -h.r * 0.2);
          ctx.lineTo(h.r * 0.55, h.r * 0.15);
          ctx.stroke();
        }

        ctx.restore();
        return;
      }

      ctx.fillStyle = "#b55328";
      ctx.beginPath();
      ctx.arc(h.x, y, h.r, 0, Math.PI * 2);
      ctx.fill();
      ctx.strokeStyle = "#111";
      ctx.lineWidth = 2;
      ctx.stroke();
      ctx.fillStyle = "#fff";
      ctx.fillRect(h.x - 8, y - 6, 5, 5);
      ctx.fillRect(h.x + 3, y - 6, 5, 5);
      ctx.fillStyle = "#111";
      ctx.fillRect(h.x - 6, y - 4, 3, 3);
      ctx.fillRect(h.x + 5, y - 4, 3, 3);
      drawBadLine(h.x - 8, y + 7, h.x + 8, y + 10, "#111", 2);
    }

    function drawRope(rope, cameraY) {
      const y = rope.y - cameraY;
      ctx.strokeStyle = "#6b451d";
      ctx.lineWidth = 4;
      drawBadLine(rope.x, y, rope.x, y + rope.h, "#6b451d", 4);
      ctx.strokeStyle = "#b98b45";
      ctx.lineWidth = 2;
      for (let step = 8; step < rope.h; step += 18) {
        drawBadLine(rope.x - 7, y + step, rope.x + 7, y + step, "#b98b45", 2);
      }
    }

    function drawSpike(spike, cameraY) {
      const y = spike.y - cameraY;
      const extend = getSpikeExtend(spike);
      const length = getSpikeLength(spike) * Math.max(0.08, extend);
      const flash = extend > 0.72 ? 1 : 0.45;

      ctx.save();
      ctx.lineCap = "round";
      ctx.lineJoin = "round";

      const count = Math.max(2, Math.floor(spike.w / 30));
      const slotY = y - 8;
      ctx.fillStyle = "#2b1b0e";
      ctx.fillRect(spike.x - 4, slotY - 4, spike.w + 8, 12);
      ctx.fillStyle = "#7a431f";
      ctx.fillRect(spike.x, slotY - 1, spike.w, 5);
      ctx.strokeStyle = "#1b1008";
      ctx.lineWidth = 2;
      ctx.strokeRect(spike.x - 4, slotY - 4, spike.w + 8, 12);

      for (let i = 0; i < count; i++) {
        const x = spike.x + 12 + i * ((spike.w - 24) / Math.max(1, count - 1));
        const dir = -1;
        const baseY = y;
        const tipY = baseY + dir * length;
        const shaftEndY = tipY - dir * 14;

        ctx.strokeStyle = `rgba(52, 31, 14, ${flash})`;
        drawBadLine(x, baseY, x, shaftEndY, ctx.strokeStyle, 6);

        ctx.strokeStyle = `rgba(178, 104, 36, ${flash})`;
        drawBadLine(x - 2, baseY + dir * 4, x - 2, shaftEndY, ctx.strokeStyle, 3);

        ctx.fillStyle = `rgba(218, 226, 218, ${flash})`;
        ctx.strokeStyle = "#263037";
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(x, tipY);
        ctx.lineTo(x - 8, tipY - dir * 16);
        ctx.lineTo(x, tipY - dir * 10);
        ctx.lineTo(x + 8, tipY - dir * 16);
        ctx.closePath();
        ctx.fill();
        ctx.stroke();
      }
      ctx.restore();
    }

    function checkpointSurfaceY(c) {
      const centerX = c.x + c.w / 2;
      const surfaceHint = c.y + 1;
      const platform = platforms
        .filter((p) => centerX >= p.x - 10 && centerX <= p.x + p.w + 10)
        .sort((a, b) => Math.abs(platformSurfaceY(a) - surfaceHint) - Math.abs(platformSurfaceY(b) - surfaceHint))[0];

      return platform ? platformSurfaceY(platform) : surfaceHint;
    }

    function drawCheckpoint(c, cameraY) {
      const baseY = checkpointSurfaceY(c);
      const x = c.x + c.w / 2;
      const y = baseY - cameraY;
      const active = Math.abs(player.checkpoint.x - (c.x - 10)) < 1 && Math.abs(player.checkpoint.y - Math.round(baseY - player.h)) < 1;
      const pulse = 0.78 + Math.sin(frame * 0.08 + x * 0.04) * 0.22;
      const glowAlpha = active ? 0.7 : 0.45;

      ctx.save();
      ctx.translate(Math.round(x), Math.round(y));
      ctx.imageSmoothingEnabled = false;

      ctx.fillStyle = "rgba(0, 0, 0, 0.24)";
      ctx.beginPath();
      ctx.ellipse(0, 4, 20, 5, 0, 0, Math.PI * 2);
      ctx.fill();

      const glow = ctx.createRadialGradient(0, -54, 2, 0, -54, 35);
      glow.addColorStop(0, `rgba(181, 255, 255, ${glowAlpha})`);
      glow.addColorStop(0.45, `rgba(63, 216, 255, ${glowAlpha * 0.45})`);
      glow.addColorStop(1, "rgba(22, 93, 180, 0)");
      ctx.fillStyle = glow;
      ctx.beginPath();
      ctx.arc(0, -54, 35 + pulse * 3, 0, Math.PI * 2);
      ctx.fill();

      ctx.fillStyle = "#513016";
      ctx.fillRect(-4, -39, 8, 40);
      ctx.fillStyle = "#9a632c";
      ctx.fillRect(-2, -38, 3, 38);
      ctx.strokeStyle = "#1b1008";
      ctx.lineWidth = 2;
      ctx.strokeRect(-4, -39, 8, 40);

      const board = ctx.createLinearGradient(-28, -44, 28, -24);
      board.addColorStop(0, "#b77c38");
      board.addColorStop(0.48, "#e5b25b");
      board.addColorStop(1, "#76501f");
      ctx.fillStyle = board;
      ctx.fillRect(-28, -45, 56, 18);
      ctx.strokeStyle = "#211307";
      ctx.lineWidth = 2;
      ctx.strokeRect(-28, -45, 56, 18);

      ctx.fillStyle = "rgba(255, 244, 171, 0.45)";
      ctx.fillRect(-24, -42, 48, 3);
      ctx.fillStyle = active ? "#fff8b8" : "#f1f7d7";
      ctx.font = "bold 9px Arial";
      ctx.textAlign = "center";
      ctx.fillText("SAVE", 0, -32);

      ctx.fillStyle = active ? "#fbfffd" : "#d7fbff";
      ctx.strokeStyle = active ? "#2366ff" : "#145aa8";
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(0, -76 - pulse * 2);
      ctx.lineTo(14, -58);
      ctx.lineTo(0, -40 + pulse);
      ctx.lineTo(-14, -58);
      ctx.closePath();
      ctx.fill();
      ctx.stroke();

      ctx.fillStyle = "rgba(45, 209, 255, 0.65)";
      ctx.beginPath();
      ctx.moveTo(0, -71);
      ctx.lineTo(7, -58);
      ctx.lineTo(0, -47);
      ctx.lineTo(-7, -58);
      ctx.closePath();
      ctx.fill();

      ctx.fillStyle = "#fffdf0";
      for (let i = 0; i < 4; i++) {
        const angle = frame * 0.025 + i * Math.PI / 2;
        const sx = Math.cos(angle) * (22 + (i % 2) * 5);
        const sy = -58 + Math.sin(angle) * 16;
        ctx.fillRect(Math.round(sx), Math.round(sy), 3, 3);
      }

      ctx.fillStyle = "#2d8c3e";
      ctx.beginPath();
      ctx.ellipse(-11, -2, 12, 5, -0.35, 0, Math.PI * 2);
      ctx.ellipse(10, -2, 11, 5, 0.28, 0, Math.PI * 2);
      ctx.fill();

      ctx.restore();
    }

    function drawRewardPile(goal, cameraY) {
      if (currentStage !== 1 && currentStage !== 4) return;

      const x = goal.x + goal.w / 2;
      const y = goal.y - cameraY + goal.h + 10;
      const isHerbPile = currentStage === 4;

      ctx.save();
      ctx.translate(x, y);
      ctx.fillStyle = "rgba(12, 33, 17, 0.28)";
      ctx.beginPath();
      ctx.ellipse(0, 9, 52, 12, 0, 0, Math.PI * 2);
      ctx.fill();

      for (let i = 0; i < 16; i++) {
        const angle = i * 0.76;
        const stemX = Math.cos(angle) * (12 + (i % 4) * 5);
        const stemY = 8 - (i % 5) * 2;
        ctx.strokeStyle = isHerbPile ? "#237c32" : "#2f8f3f";
        ctx.lineWidth = 2;
        drawBadLine(stemX, stemY, stemX + Math.cos(angle) * 8, stemY - 18 - (i % 3) * 4, ctx.strokeStyle, 2);

        ctx.fillStyle = isHerbPile ? "#89e066" : (i % 2 === 0 ? "#ff82bd" : "#ffe07a");
        ctx.beginPath();
        ctx.ellipse(stemX + Math.cos(angle) * 9, stemY - 20 - (i % 3) * 4, 5 + (i % 2), 8, angle, 0, Math.PI * 2);
        ctx.fill();
      }

      ctx.fillStyle = isHerbPile ? "#5fc947" : "#ff6aaa";
      ctx.beginPath();
      ctx.ellipse(0, 2, 34, 13, 0, 0, Math.PI * 2);
      ctx.fill();
      ctx.restore();
    }

    function roundedRectPath(x, y, w, h, r) {
      ctx.beginPath();
      ctx.moveTo(x + r, y);
      ctx.lineTo(x + w - r, y);
      ctx.quadraticCurveTo(x + w, y, x + w, y + r);
      ctx.lineTo(x + w, y + h - r);
      ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
      ctx.lineTo(x + r, y + h);
      ctx.quadraticCurveTo(x, y + h, x, y + h - r);
      ctx.lineTo(x, y + r);
      ctx.quadraticCurveTo(x, y, x + r, y);
      ctx.closePath();
    }

    function wrapText(text, maxWidth) {
      const words = text.split(" ");
      const lines = [];
      let line = "";

      for (const word of words) {
        const testLine = line ? `${line} ${word}` : word;
        if (ctx.measureText(testLine).width <= maxWidth || !line) {
          line = testLine;
        } else {
          lines.push(line);
          line = word;
        }
      }

      if (line) lines.push(line);
      return lines.slice(0, 3);
    }

    function drawNpcSpeechBubble(centerX, headY, text, alpha = 1) {
      if (!text || alpha <= 0) return;

      ctx.save();
      ctx.globalAlpha = alpha;
      ctx.font = "bold 12px Arial";
      ctx.textBaseline = "middle";

      const maxTextWidth = 154;
      const lines = wrapText(text, maxTextWidth);
      const lineHeight = 15;
      const paddingX = 12;
      const paddingY = 9;
      const textWidth = Math.max(...lines.map((line) => ctx.measureText(line).width));
      const bubbleW = Math.round(Math.max(82, Math.min(188, textWidth + paddingX * 2)));
      const bubbleH = Math.round(lines.length * lineHeight + paddingY * 2);
      const x = Math.round(Math.max(8, Math.min(canvas.width - bubbleW - 8, centerX - bubbleW / 2)));
      const popOffset = Math.round((1 - alpha) * 5);
      const y = Math.round(Math.max(10, headY - bubbleH - 18 + popOffset));
      const tailX = Math.max(x + 20, Math.min(x + bubbleW - 20, centerX));

      ctx.fillStyle = "rgba(0, 0, 0, 0.24)";
      roundedRectPath(x + 2, y + 3, bubbleW, bubbleH, 8);
      ctx.fill();

      ctx.fillStyle = "rgba(250, 255, 247, 0.96)";
      roundedRectPath(x, y, bubbleW, bubbleH, 8);
      ctx.fill();

      ctx.strokeStyle = "#2f5f86";
      ctx.lineWidth = 2;
      roundedRectPath(x, y, bubbleW, bubbleH, 8);
      ctx.stroke();

      ctx.fillStyle = "rgba(250, 255, 247, 0.96)";
      ctx.beginPath();
      ctx.moveTo(tailX - 8, y + bubbleH - 1);
      ctx.lineTo(tailX + 8, y + bubbleH - 1);
      ctx.lineTo(tailX - 1, y + bubbleH + 11);
      ctx.closePath();
      ctx.fill();
      ctx.strokeStyle = "#2f5f86";
      ctx.beginPath();
      ctx.moveTo(tailX - 8, y + bubbleH - 1);
      ctx.lineTo(tailX - 1, y + bubbleH + 11);
      ctx.lineTo(tailX + 8, y + bubbleH - 1);
      ctx.stroke();

      ctx.fillStyle = "#1f3142";
      ctx.textAlign = "center";
      lines.forEach((line, index) => {
        const textY = y + paddingY + lineHeight / 2 + index * lineHeight;
        ctx.fillText(line, x + bubbleW / 2, textY);
      });

      ctx.restore();
    }

    function drawStartNpc(cameraY) {
      if (!hasNpcImage) return;

      const startPlatform = platforms[0];
      const npcScale = 1.08;
      const drawW = Math.round(npcSpriteBounds.w * npcScale);
      const drawH = Math.round(npcSpriteBounds.h * npcScale);
      const baseY = startPlatform ? platformSurfaceY(startPlatform) : stage.start.y + player.h;
      const startCenterX = stage.start.x + player.w / 2;
      const preferRight = stage.start.x < world.width / 2;
      let centerX = startCenterX + (preferRight ? 62 : -54);

      if (startPlatform) {
        const minX = startPlatform.x + drawW / 2 + 6;
        const maxX = startPlatform.x + startPlatform.w - drawW / 2 - 6;
        centerX = minX <= maxX
          ? Math.max(minX, Math.min(maxX, centerX))
          : startPlatform.x + startPlatform.w / 2;
      }

      centerX = Math.max(drawW / 2 + 8, Math.min(world.width - drawW / 2 - 8, centerX));

      const x = Math.round(centerX - drawW / 2);
      const y = Math.round(baseY - drawH - cameraY);
      const screenBaseY = Math.round(baseY - cameraY);
      const bubbleAlpha = getNpcBubbleAlpha();

      ctx.save();
      ctx.imageSmoothingEnabled = false;
      drawNpcSpeechBubble(centerX, y + 8, npcBubbleText, bubbleAlpha);
      ctx.fillStyle = "rgba(0,0,0,0.22)";
      ctx.beginPath();
      ctx.ellipse(centerX, screenBaseY + 2, Math.max(14, drawW * 0.28), 4, 0, 0, Math.PI * 2);
      ctx.fill();
      ctx.drawImage(
        npcCanvas,
        npcSpriteBounds.x,
        npcSpriteBounds.y,
        npcSpriteBounds.w,
        npcSpriteBounds.h,
        x,
        y,
        drawW,
        drawH
      );
      ctx.restore();
    }

    function drawGoal(cameraY) {
      const goal = stage.goal;
      const centerX = goal.x + goal.w / 2;
      const centerY = goal.y - cameraY + goal.h / 2;
      const pulse = Math.sin(frame * 0.08) * 0.06 + 1;
      const size = Math.min(goal.w, goal.h) * 1.38 * pulse;

      ctx.save();
      ctx.translate(centerX, centerY);
      ctx.rotate(frame * 0.01);

      ctx.globalAlpha = 0.32;
      ctx.fillStyle = "#4be9ff";
      ctx.beginPath();
      ctx.ellipse(0, 0, size * 0.58, size * 0.58, 0, 0, Math.PI * 2);
      ctx.fill();
      ctx.globalAlpha = 1;

      if (hasPortalImage) {
        ctx.rotate(-frame * 0.018);
        ctx.drawImage(portalImage, -size / 2, -size / 2, size, size);
      } else {
        for (let i = 0; i < 5; i++) {
          const radius = size * (0.26 + i * 0.055);
          const alpha = 0.78 - i * 0.12;
          const ring = ctx.createRadialGradient(0, 0, radius * 0.72, 0, 0, radius * 1.15);
          ring.addColorStop(0, `rgba(20, 84, 179, 0)`);
          ring.addColorStop(0.48, `rgba(72, 216, 255, ${alpha})`);
          ring.addColorStop(0.73, `rgba(18, 98, 230, ${alpha * 0.95})`);
          ring.addColorStop(1, `rgba(3, 24, 95, 0)`);

          ctx.rotate(0.42 + frame * 0.003);
          ctx.strokeStyle = ring;
          ctx.lineWidth = 10 - i;
          ctx.beginPath();
          ctx.arc(0, 0, radius, Math.PI * 0.1, Math.PI * 1.86);
          ctx.stroke();
        }

        for (let i = 0; i < 18; i++) {
          const angle = i * 0.74 + frame * 0.035;
          const radius = size * (0.32 + (i % 4) * 0.045);
          ctx.fillStyle = i % 3 === 0 ? "#ffffff" : "#5fefff";
          ctx.globalAlpha = 0.52 + (i % 3) * 0.12;
          ctx.fillRect(Math.cos(angle) * radius, Math.sin(angle) * radius, 4 + (i % 2) * 3, 2);
        }
        ctx.globalAlpha = 1;

        ctx.strokeStyle = "rgba(190, 246, 255, 0.92)";
        ctx.lineWidth = 5;
        ctx.beginPath();
        ctx.arc(0, 0, size * 0.34, 0, Math.PI * 2);
        ctx.stroke();

        ctx.strokeStyle = "rgba(15, 70, 190, 0.9)";
        ctx.lineWidth = 9;
        ctx.beginPath();
        ctx.arc(0, 0, size * 0.46, Math.PI * 0.15, Math.PI * 1.75);
        ctx.stroke();
      }

      ctx.restore();
      drawRewardPile(goal, cameraY);
    }

    function drawLimb(x1, y1, x2, y2, width, color) {
      ctx.strokeStyle = color;
      ctx.lineWidth = width;
      ctx.lineCap = "round";
      ctx.beginPath();
      ctx.moveTo(x1, y1);
      ctx.lineTo(x2, y2);
      ctx.stroke();
    }

    function selectSpriteFrame() {
      if (player.onRope) {
        const frames = spriteAnimations.rope;
        return frames[Math.floor(frame / 8) % frames.length];
      }

      if (!player.grounded) {
        const frames = player.vy > 7 ? spriteAnimations.fall : spriteAnimations.jump;
        return frames[Math.floor(frame / 7) % frames.length];
      }

      if (Math.abs(player.vx) > 0.35) {
        const frames = spriteAnimations.run;
        return frames[Math.floor(frame / 7) % frames.length];
      }

      const frames = spriteAnimations.idle;
      return frames[0];
    }

    function getSpriteOpaqueBounds(sprite) {
      const key = `${sprite.sx}:${sprite.sy}:${sprite.sw}:${sprite.sh}`;
      if (spriteBoundsCache.has(key)) return spriteBoundsCache.get(key);

      let bounds = { x: 0, y: 0, w: sprite.sw, h: sprite.sh };
      if (hasCharacterSheet) {
        bounds = cleanSpriteCell(sprite);
      }

      spriteBoundsCache.set(key, bounds);
      return bounds;
    }

    function drawPlayer(cameraY) {
      const screenX = player.x + player.w / 2;
      const screenY = player.y - cameraY + player.h;
      const facing = player.facing;

      if (hasCharacterSheet) {
        const sprite = selectSpriteFrame();
        const spriteBounds = getSpriteOpaqueBounds(sprite);
        const characterScale = 0.7;
        const drawW = Math.round((player.onRope ? 90 : 98) * characterScale);
        const drawH = Math.round((player.onRope ? 116 : 124) * characterScale);
        const footY = ((spriteBounds.y + spriteBounds.h) / sprite.sh) * drawH;
        const drawX = Math.round(screenX - drawW / 2);
        const drawY = Math.round(screenY - footY);
        const scaleX = drawW / sprite.sw;
        const scaleY = drawH / sprite.sh;
        const croppedX = Math.round(drawX + spriteBounds.x * scaleX);
        const croppedY = Math.round(drawY + spriteBounds.y * scaleY);
        const croppedW = Math.round(spriteBounds.w * scaleX);
        const croppedH = Math.round(spriteBounds.h * scaleY);

        ctx.save();
        ctx.imageSmoothingEnabled = false;
        spriteFrameCanvas.width = sprite.sw;
        spriteFrameCanvas.height = sprite.sh;
        spriteFrameCtx.clearRect(0, 0, sprite.sw, sprite.sh);
        spriteFrameCtx.drawImage(characterCanvas, sprite.sx, sprite.sy, sprite.sw, sprite.sh, 0, 0, sprite.sw, sprite.sh);
        const framePixels = spriteFrameCtx.getImageData(0, 0, sprite.sw, sprite.sh);
        spriteFrameCtx.putImageData(makeSpriteSheetBackdropTransparent(framePixels), 0, 0);

        ctx.fillStyle = "rgba(0,0,0,0.26)";
        ctx.beginPath();
        ctx.ellipse(screenX, screenY + 2, 14, 3.5, 0, 0, Math.PI * 2);
        ctx.fill();

        if (facing < 0) {
          ctx.translate(drawX + drawW, drawY);
          ctx.scale(-1, 1);
          ctx.drawImage(
            spriteFrameCanvas,
            spriteBounds.x,
            spriteBounds.y,
            spriteBounds.w,
            spriteBounds.h,
            Math.round(spriteBounds.x * scaleX),
            Math.round(spriteBounds.y * scaleY),
            croppedW,
            croppedH
          );
        } else {
          ctx.drawImage(
            spriteFrameCanvas,
            spriteBounds.x,
            spriteBounds.y,
            spriteBounds.w,
            spriteBounds.h,
            croppedX,
            croppedY,
            croppedW,
            croppedH
          );
        }

        ctx.restore();
        return;
      }

      const runAmount = Math.min(1, Math.abs(player.vx) / 5);
      const walk = Math.sin(frame * 0.32) * runAmount;
      const airborne = !player.grounded && !player.onRope;
      const climb = player.onRope ? Math.sin(frame * 0.34) : 0;
      const bob = player.grounded ? Math.abs(Math.sin(frame * 0.32)) * runAmount * 2 : 0;

      ctx.save();
      ctx.translate(Math.round(screenX), Math.round(screenY - bob));
      ctx.scale(facing, 1);

      ctx.fillStyle = "rgba(0,0,0,0.28)";
      ctx.beginPath();
      ctx.ellipse(0, 5, 24, 7, 0, 0, Math.PI * 2);
      ctx.fill();

      if (hasCharacterSprite) {
        const targetHeight = 86;
        const targetWidth = Math.round(characterSpriteBounds.w * targetHeight / characterSpriteBounds.h);
        ctx.drawImage(
          characterCanvas,
          characterSpriteBounds.x,
          characterSpriteBounds.y,
          characterSpriteBounds.w,
          characterSpriteBounds.h,
          Math.round(-targetWidth / 2),
          -targetHeight - 2,
          targetWidth,
          targetHeight
        );

        if (airborne) {
          ctx.strokeStyle = "rgba(255,255,255,0.35)";
          ctx.lineWidth = 2;
          ctx.beginPath();
          ctx.arc(-28, -30, 8, 0.2, Math.PI * 1.3);
          ctx.stroke();
        }

        ctx.restore();
        return;
      }

      const skin = "#ffd8a6";
      const skinDark = "#d99a66";
      const hair = "#1f1f24";
      const outfit = "#6fb8e8";
      const outfitDark = "#2b6f9b";
      const shoe = "#e5a13a";

      const armSwing = player.onRope ? climb * 8 : walk * 10;
      const legSwing = airborne ? 0.5 : walk;

      drawLimb(-8, -42, -18, -24 + armSwing, 6, skin);
      drawLimb(8, -42, 18, -24 - armSwing, 6, skin);
      drawLimb(-7, -18, -13, -2 + legSwing * 8, 7, skin);
      drawLimb(7, -18, 13, -2 - legSwing * 8, 7, skin);

      ctx.fillStyle = shoe;
      ctx.fillRect(-19, -3 + legSwing * 8, 16, 6);
      ctx.fillRect(5, -3 - legSwing * 8, 16, 6);

      ctx.fillStyle = outfitDark;
      ctx.fillRect(-12, -45, 24, 28);
      ctx.fillStyle = outfit;
      ctx.fillRect(-10, -48, 20, 20);
      ctx.fillStyle = "#eef9ff";
      ctx.fillRect(-5, -48, 4, 18);
      ctx.fillRect(3, -48, 4, 18);

      ctx.fillStyle = skin;
      ctx.beginPath();
      ctx.ellipse(0, -67, 22, 21, 0, 0, Math.PI * 2);
      ctx.fill();
      ctx.strokeStyle = skinDark;
      ctx.lineWidth = 2;
      ctx.stroke();

      ctx.fillStyle = hair;
      ctx.beginPath();
      ctx.ellipse(-5, -80, 18, 11, -0.35, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillRect(-22, -74, 15, 12);
      ctx.beginPath();
      ctx.ellipse(16, -83, 16, 10, 0.4, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillRect(17, -90, 16, 10);

      ctx.fillStyle = "#ffffff";
      ctx.fillRect(-14, -68, 8, 7);
      ctx.fillRect(6, -68, 8, 7);
      ctx.fillStyle = "#254c7d";
      ctx.fillRect(-12, -67, 4, 5);
      ctx.fillRect(8, -67, 4, 5);
      ctx.fillStyle = "#1b1512";
      ctx.fillRect(-13, -75, 10, 3);
      ctx.fillRect(4, -75, 11, 3);

      ctx.fillStyle = "#b85e5e";
      ctx.fillRect(-4, -55, 8, 2);

      if (airborne) {
        ctx.strokeStyle = "rgba(255,255,255,0.35)";
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.arc(-28, -30, 8, 0.2, Math.PI * 1.3);
        ctx.stroke();
      }

      ctx.restore();
    }

    function drawMiniMap(cameraY) {
      if (hasSuppliedBackground) return;

      ctx.fillStyle = "rgba(255,255,255,0.82)";
      ctx.fillRect(12, 12, 145, 98);
      ctx.strokeStyle = "#111";
      ctx.strokeRect(12, 12, 145, 98);
      ctx.fillStyle = "#111";
      ctx.font = "13px monospace";
      ctx.fillText("mini maf", 20, 29);
      ctx.fillText("인내? 숲", 20, 47);
      for (const p of platforms) {
        ctx.fillStyle = "#6d421b";
        ctx.fillRect(
          22 + p.x * 0.12,
          104 - (p.y / world.height) * 88,
          Math.max(4, p.w * 0.12),
          2
        );
      }
      ctx.fillStyle = "#e33232";
      ctx.fillRect(22 + player.x * 0.12, 104 - (player.y / world.height) * 88, 5, 5);
    }

    function getElapsedParts() {
      const elapsedMs = stageFinishElapsedMs ?? (performance.now() - stageStartedAt);
      const totalSeconds = Math.max(0, Math.floor(elapsedMs / 1000));
      return {
        minutes: Math.floor(totalSeconds / 60),
        seconds: totalSeconds % 60,
      };
    }

    function drawMapleTimePanel() {
      const { minutes, seconds } = getElapsedParts();
      const x = Math.round(canvas.width / 2 - 154);
      const y = 10;
      const w = 308;
      const h = 54;

      const panel = ctx.createLinearGradient(x, y, x, y + h);
      panel.addColorStop(0, "rgba(84, 63, 20, 0.94)");
      panel.addColorStop(0.48, "rgba(48, 32, 10, 0.96)");
      panel.addColorStop(1, "rgba(31, 20, 7, 0.98)");
      ctx.fillStyle = panel;
      ctx.fillRect(x, y, w, h);

      ctx.strokeStyle = "#f3d36b";
      ctx.lineWidth = 2;
      ctx.strokeRect(x + 1, y + 1, w - 2, h - 2);
      ctx.strokeStyle = "rgba(30, 17, 4, 0.9)";
      ctx.lineWidth = 3;
      ctx.strokeRect(x + 4, y + 4, w - 8, h - 8);

      ctx.fillStyle = "#e7d989";
      ctx.font = "bold 13px Arial";
      ctx.fillText("소요시간", x + 26, y + 22);
      ctx.beginPath();
      ctx.fillStyle = "#f6dc62";
      ctx.arc(x + 14, y + 17, 6, 0, Math.PI * 2);
      ctx.fill();
      ctx.strokeStyle = "#3a2608";
      ctx.lineWidth = 1.5;
      ctx.stroke();
      drawBadLine(x + 14, y + 17, x + 14, y + 13, "#3a2608", 1.5);
      drawBadLine(x + 14, y + 17, x + 18, y + 17, "#3a2608", 1.5);

      const minuteText = String(minutes).padStart(2, "0");
      const secondText = String(seconds).padStart(2, "0");
      ctx.textAlign = "right";
      ctx.shadowColor = "rgba(255, 246, 174, 0.7)";
      ctx.shadowBlur = 7;
      ctx.fillStyle = "#fff7b8";
      ctx.font = "bold 38px Consolas, 'Courier New', monospace";
      ctx.fillText(minuteText, x + 164, y + 44);
      ctx.fillText(secondText, x + 268, y + 44);
      ctx.shadowBlur = 0;

      ctx.textAlign = "left";
      ctx.fillStyle = "#fff0a0";
      ctx.font = "bold 15px Arial";
      ctx.fillText("분", x + 172, y + 42);
      ctx.fillText("초", x + 276, y + 42);
    }

    function render() {
      const targetCameraY = Math.max(0, Math.min(world.height - canvas.height, player.y - 360));
      cameraY += (targetCameraY - cameraY) * 0.12;
      drawBackground(cameraY);

      for (let i = 0; i < platforms.length; i++) drawPlatform(platforms[i], cameraY, i);
      for (const rope of ropes) drawRope(rope, cameraY);
      for (const spike of spikes) drawSpike(spike, cameraY);
      for (const c of checkpoints) drawCheckpoint(c, cameraY);
      for (const h of hazards) drawHazard(h, cameraY);
      drawGoal(cameraY);
      drawStartNpc(cameraY);
      drawPlayer(cameraY);
      drawMiniMap(cameraY);

      ctx.fillStyle = "#111";
      ctx.fillStyle = "rgba(9, 24, 14, 0.62)";
      ctx.fillRect(10, 10, 300, 44);
      ctx.strokeStyle = "rgba(219, 255, 181, 0.28)";
      ctx.strokeRect(10, 10, 300, 44);
      ctx.fillStyle = "#edffdc";
      ctx.font = "13px Arial";
      ctx.fillText(`${currentStage + 1}/${stages.length} ${stage.name}`, 18, 28);
      ctx.fillStyle = "#ccefb8";
      ctx.font = "13px Arial";
      ctx.fillText("Forest of Patience", 18, 47);

      ctx.fillStyle = "rgba(9, 24, 14, 0.62)";
      ctx.fillRect(805, 12, 138, 46);
      ctx.strokeStyle = "rgba(219, 255, 181, 0.28)";
      ctx.strokeRect(805, 12, 138, 46);
      ctx.fillStyle = "#edffdc";
      ctx.font = "15px Arial";
      ctx.fillText(`death: ${player.deaths}`, 815, 28);
      ctx.fillStyle = "#ccefb8";
      ctx.font = "13px Arial";
      ctx.fillText(`height: ${Math.max(0, Math.round(world.height - player.y))}`, 815, 48);
      drawMapleTimePanel();

      if (player.won) {
        ctx.fillStyle = "rgba(255,255,255,0.85)";
        ctx.fillRect(220, 210, 520, 130);
        ctx.strokeStyle = "#111";
        ctx.lineWidth = 4;
        ctx.strokeRect(220, 210, 520, 130);
        ctx.fillStyle = "#111";
        ctx.font = "24px Comic Sans MS";
        ctx.fillText("도착! 다음 숲으로 넘어감", 300, 270);
        ctx.font = "15px monospace";
        ctx.fillText("잠깐 뒤 자동으로 다음 스테이지", 340, 302);
      }
    }

    function loop() {
      update();
      render();
      requestAnimationFrame(loop);
    }

    window.addEventListener("keydown", (event) => {
      if (["ArrowLeft", "ArrowRight", "ArrowUp", " ", "a", "d", "w"].includes(event.key)) {
        event.preventDefault();
      }
      keys.add(event.key);
    });

    window.addEventListener("keyup", (event) => keys.delete(event.key));

    restartButton.addEventListener("click", () => {
      loadStage(currentStage);
      statusText.textContent = `${stage.name} 다시 시작`;
    });

    prevStageButton.addEventListener("click", () => loadStage(currentStage - 1));
    nextStageButton.addEventListener("click", () => loadStage(currentStage + 1));
    demoRunButton.addEventListener("click", () => {
      demoMode = true;
      demoIndex = 0;
      demoRoute = makeDemoRoute();
      player.deaths = 0;
      player.won = false;
      statusText.textContent = `${stage.name} 자동 시연 중`;
    });

    loadStage(0);
    loop();
    </script>
"""

components.html(
    game_html.replace("__BACKGROUND_DATA_URL__", background_data_url).replace(
        "__CHARACTER_DATA_URL__",
        character_data_url,
    ).replace(
        "__PORTAL_DATA_URL__",
        portal_data_url,
    ).replace(
        "__STAR_DATA_URL__",
        star_data_url,
    ).replace(
        "__NPC_DATA_URL__",
        npc_data_url,
    ),
    height=620,
    scrolling=False,
)
