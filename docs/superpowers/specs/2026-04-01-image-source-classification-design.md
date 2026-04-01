# Image Source Classification — Design Spec

## Context

Social Agent hiện chỉ gen ảnh bằng AI (kie.ai) cho mọi content. Tuy nhiên, content về tin tức/sự kiện thực tế sẽ phù hợp hơn với ảnh thật từ internet. Cần upgrade `/generate-image` để tự phân biệt 2 loại content và chọn nguồn ảnh phù hợp.

## Hai loại content

| Loại | Ví dụ | Nguồn ảnh |
|------|-------|-----------|
| **Dự án / Sản phẩm** | "How our product uses RAG", "AI trends overview", tech tutorials | **AI-generated** (kie.ai) — visual concept, banner style |
| **Tin tức / Sự kiện thực** | "NASA Artemis II launch", "Trump addresses Iran war", "Earthquake in Japan" | **Web photo** — ảnh thật từ bài báo/tin tức |

## Logic phân loại

Claude đọc draft content và `./summary.md` (knowledge base summary), rồi quyết định:

1. **Đọc `./summary.md`** để hiểu dự án của user là gì
2. **So sánh draft content với knowledge:**
   - Nếu content liên quan trực tiếp đến dự án/sản phẩm trong knowledge → `image_source = "ai"`
   - Nếu content nhắc đến concept công nghệ trừu tượng, tutorial, tips → `image_source = "ai"`
3. **Kiểm tra dấu hiệu tin tức/sự kiện thực:**
   - Nhắc đến người thật (tên riêng chính trị gia, CEO, v.v.) → `image_source = "web"`
   - Nhắc đến sự kiện cụ thể có thời gian (launch, war, election, earthquake) → `image_source = "web"`
   - Nhắc đến tổ chức/địa điểm thực trong bối cảnh tin tức → `image_source = "web"`
4. **Rule ưu tiên:** Nếu content vừa liên quan dự án vừa nhắc sự kiện thực → dùng `"web"` (tin tức thường cần ảnh thật hơn)

## Phạm vi thay đổi

### 1. Tạo mới: `plugin/scripts/search_image.py`

Script download ảnh từ URL về local.

**Input:**
```bash
python3 search_image.py --url "https://example.com/photo.jpg" --output "./images/file.png"
```

**Output:**
```json
{"success": true, "path": "./images/file.png", "url": "https://example.com/photo.jpg", "source": "web"}
```

**Logic:**
- HTTP GET download ảnh từ URL
- Validate content-type là image (jpg, png, webp, gif)
- Save to output path, tạo parent dir nếu cần
- Return JSON với `path`, `url`, `source: "web"`

### 2. Sửa: `plugin/commands/generate-image.md`

Thêm bước phân loại trước khi tạo ảnh:

```
### Classify content type

1. Read the draft content.
2. If `./summary.md` exists, read it to understand the user's project/product.
3. Classify:
   - If the content is about the user's project/product (matches knowledge in summary.md),
     OR about abstract tech concepts, tutorials, tips → image_source = "ai"
   - If the content mentions real-world news events, real people in news context,
     specific incidents with dates, geopolitical events → image_source = "web"
   - When in doubt (content mixes both), prefer "web" for news-related content.

### If image_source = "web": Find real photo

1. Use WebSearch to find news articles related to the draft topic.
2. Use WebFetch on the most relevant article to extract image URLs.
3. Choose the highest quality, most relevant image URL.
4. Run the download script:
   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/search_image.py \
     --url "<selected image URL>" \
     --output "./images/YYYY-MM-DD_<topic-slug>_photo.png"
   ```
5. If download fails, fall back to AI generation.

### If image_source = "ai": Generate AI banner

(Keep existing flow — craft prompt, call generate_image.py)
```

### 3. Sửa: Draft frontmatter `images` — thêm `source` field

```yaml
images:
  - path: "images/2026-04-01_artemis-ii_photo.png"
    url: "https://nasa.gov/photo.jpg"
    description: "NASA Artemis II launch photo from CNN"
    source: "web"        # "web" hoặc "ai"
```

`source` field chỉ dùng để track nguồn gốc. Không ảnh hưởng logic posting.

### 4. Naming convention

- Ảnh AI: `YYYY-MM-DD_<topic-slug>_banner.png` (giữ nguyên)
- Ảnh web: `YYYY-MM-DD_<topic-slug>_photo.png` (mới — phân biệt bằng suffix)

## Files cần thay đổi

| File | Thay đổi |
|------|----------|
| `plugin/scripts/search_image.py` | **Tạo mới** — download ảnh từ URL |
| `plugin/commands/generate-image.md` | Thêm bước phân loại + branch tìm ảnh web |
| `tests/test_search_image.py` | **Tạo mới** — test download script |

**Không cần sửa:**
- `post.py`, platform modules — đã handle image dicts, `source` field không ảnh hưởng
- `draft.py` — `resolve_image_paths()` đã handle dict format, thêm field `source` không break

## Testing plan

### Phase 1: Test `search_image.py`
- Download ảnh từ URL hợp lệ → file tồn tại, JSON đúng format
- URL không hợp lệ / 404 → trả error JSON
- Content-type không phải image → trả error

### Phase 2: Test phân loại (manual)
Cho Claude phân loại các draft content:

| Content | Expected | Lý do |
|---------|----------|-------|
| "NASA Artemis II launches today" | `web` | Sự kiện thực, có ngày cụ thể |
| "Trump addresses Iran war" | `web` | Người thật, tin tức thời sự |
| "How our RAG pipeline works" | `ai` | Dự án/sản phẩm (match knowledge) |
| "AI trends to watch in 2026" | `ai` | Concept trừu tượng |
| "Earthquake hits Tokyo, 5.8 magnitude" | `web` | Sự kiện thực, địa điểm cụ thể |
| "5 tips for better social media content" | `ai` | Tutorial/tips trừu tượng |

### Phase 3: Test end-to-end
- Tạo content tin tức → `/generate-image` tìm ảnh thật → post lên platform
- Tạo content dự án → `/generate-image` gen ảnh AI → post lên platform
- Verify cả 2 flow hoạt động đúng

## Fallback

Nếu tìm ảnh web thất bại (không tìm được ảnh phù hợp, download lỗi), tự động fallback sang gen ảnh AI. Đảm bảo luôn có ảnh cho content.
