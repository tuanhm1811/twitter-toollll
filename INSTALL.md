# 🚀 Hướng dẫn cài đặt Social Agent

Plugin Claude Code (`social-agent` v2.0.0) để tạo & đăng nội dung mạng xã hội từ knowledge base — hỗ trợ **Twitter, Facebook, Threads, Reddit** và tạo ảnh AI (kie.ai).

Có 2 cách cài tùy môi trường bạn dùng:
- [Cách A — Claude Code (CLI / VS Code)](#cách-a--claude-code-cli--vs-code)
- [Cách B — Claude Desktop](#cách-b--claude-desktop)

---

## Yêu cầu chung (cả 2 cách đều cần)

- **Claude Code** đã cài đặt
- **Python 3** + pip

---

## Cách A — Claude Code (CLI / VS Code)

### 1. Tải mã nguồn

```bash
git clone https://github.com/tuanhm1811/twitter-toollll.git
cd twitter-toollll
```

### 2. Cài plugin vào Claude Code

```bash
# Chạy từ trong repo vừa clone
claude plugin add ./plugin
```

> Thư mục cần đăng ký là `plugin/` (chứa `.claude-plugin/plugin.json`), không phải thư mục gốc repo.

### 3. Cài thư viện Python (bắt buộc — script gọi API cần)

```bash
pip install -r plugin/scripts/requirements.txt
```

Gồm: `requests`, `tweepy` (Twitter), `praw` (Reddit), `pyyaml`.

### 4. Tạo project & cấu hình

```bash
mkdir my-social-project && cd my-social-project
```

Trong Claude Code chạy `/setup` để tự tạo `knowledges/`, `contents/`, `images/` và file `.social-agent.yaml`.
Sau đó điền API key (xem [phần Cấu hình API](#cấu-hình-api-social-agentyaml)).

### 5. Đăng bài

```
/post
```

Trên CLI, `/post` gọi API trực tiếp và đăng ngay.

---

## Cách B — Claude Desktop

Claude Desktop chạy script Python ở máy local nhưng **chặn kết nối mạng ra ngoài** trong sandbox, nên bước đăng thật phải chạy qua terminal.

### 1. Cài sẵn trên máy (làm 1 lần)

```bash
git clone https://github.com/tuanhm1811/twitter-toollll.git
cd twitter-toollll
pip install -r plugin/scripts/requirements.txt
```

### 2. Thêm marketplace & cài plugin (trong Claude Desktop)

Gõ trong khung chat:

```
/plugin marketplace add tuanhm1811/twitter-toollll
/plugin install social-agent@mtp-plugins
```

> Hoặc dùng menu `/plugin` → chọn marketplace `mtp-plugins` → cài `social-agent`. Restart Claude Desktop để nạp slash command.
>
> 💡 Cài thẳng từ thư mục đã clone (không qua GitHub):
> `/plugin marketplace add /đường-dẫn/tới/twitter-toollll`

### 3. Thiết lập project & API key

Mở/chuyển tới thư mục project rồi chạy `/setup`, sau đó điền key (xem [phần Cấu hình API](#cấu-hình-api-social-agentyaml)).

### 4. Đăng bài (qua sandbox fallback)

1. Gõ `/post` như bình thường.
2. Khi gặp lỗi mạng, Claude **tự sinh file `post_draft.sh`** trong project.
3. Mở **Terminal** và chạy:
   ```bash
   ./post_draft.sh
   ```
   Script sẽ đăng bài (terminal có mạng) và cập nhật draft tự động.
4. **Copy phần JSON output** từ terminal, dán lại vào Claude Desktop để xác nhận.

---

## Cấu hình API (`.social-agent.yaml`)

Điền key cho **những nền tảng muốn dùng** (để trống nền tảng không dùng):

```yaml
kie_api_key: ""            # key kie.ai — chỉ cần nếu tạo ảnh AI

twitter:
  api_key: ""
  api_secret: ""
  access_token: ""
  access_secret: ""

reddit:
  client_id: ""
  client_secret: ""
  username: ""
  password: ""

threads:
  access_token: ""

facebook:
  page_access_token: ""
  page_id: ""

auto_post: false           # true = đăng không hỏi xác nhận
```

> ⚠️ File `.social-agent.yaml` chứa khóa bí mật — **không commit lên git**.

### Lấy API key ở đâu

| Nền tảng | Lấy key tại |
|----------|-------------|
| **Twitter** | https://developer.twitter.com → tạo App → API key/secret + Access token/secret (cần quyền **Read & Write**) |
| **Facebook** | https://developers.facebook.com → tạo App → Graph API → `page_access_token` + `page_id` của Page |
| **Threads** | https://developers.facebook.com (Threads API) → OAuth lấy `access_token` (có script `plugin/scripts/threads_token.py` hỗ trợ) |
| **Reddit** | https://www.reddit.com/prefs/apps → tạo app loại *script* |
| **kie.ai** | https://kie.ai → API key (chỉ cần nếu dùng tạo ảnh) |

---

## Các slash command

| Lệnh | Chức năng |
|------|-----------|
| `/setup` | Khởi tạo project + config |
| `/import` | Nạp tài liệu vào `knowledges/` |
| `/summarize` | Tóm tắt knowledge base |
| `/plan-content` | Lập kế hoạch nội dung |
| `/generate-content` | Sinh bài đăng |
| `/generate-image` | Tạo ảnh (kie.ai) |
| `/post` | Đăng bài lên nền tảng |

### Kiểm tra credentials không đăng thật (dry-run)

```bash
python3 plugin/scripts/post.py --file contents/<draft>.md --config .social-agent.yaml --dry-run
```

---

## So sánh nhanh

| | Claude Code (CLI) | Claude Desktop |
|---|---|---|
| Cài plugin | `claude plugin add ./plugin` | `/plugin marketplace add ...` → `/plugin install ...` |
| Cài Python deps | `pip install -r ...` | `pip install -r ...` (vẫn cần) |
| Đăng bài | `/post` chạy trực tiếp | `/post` → chạy `post_draft.sh` ở terminal |

> **Lưu ý:** Đây là plugin dùng **slash command**, không phải "skill" kiểu Superpowers.
