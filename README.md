# 🛒 Amazon Product Image Automation

> Automatically download high-resolution product images from Amazon at scale — no manual saving, no quality loss.

Built with **Python + Selenium**, this script reads a list of Amazon products from an Excel file, navigates to each product page, interacts with the image gallery, and downloads every main image in its original high-resolution format.

---

## ✨ Features

- **Reads from Excel** — supply a simple `PRODUCT_LIST.xlsx` file with `PRODUCT_NAME` and `PRODUCT_URL` columns
- **Automated browser navigation** — opens each Amazon product page using Selenium 4 + local `chromedriver.exe`
- **Smart gallery interaction** — scrolls to the image gallery, hovers over thumbnails, and clicks to trigger lazy-loaded images
- **High-resolution image extraction** — parses `data-a-dynamic-image`, `data-old-hires`, and `src` attributes to find the best available image
- **Clean URL processing** — strips Amazon thumbnail modifiers (`_SX`, `_SY`, `_SS`, etc.) and preserves hi-res variants like `_SL1500_`
- **Up to 5 images per product** — downloads gallery images in order
- **Organized output** — saves each product's images in its own named folder

---

## 📁 Project Structure

```
amazon-image-automation/
├── main.py                      # Entry point
├── chromedriver.exe             # ChromeDriver (must match your Chrome version)
├── PRODUCT_LIST.xlsx            # Input file (you provide this)
├── venv/                        # Python virtual environment
├── output/                      # Downloaded images (auto-created)
│   ├── MEGAPHONE/
│   │   ├── image_1.jpg
│   │   └── image_2.jpg
│   ├── MINI_POPCORN_MAKER/
│   └── ...                      # One folder per product
├── .gitignore
└── requirements.txt
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- Google Chrome installed

> `chromedriver.exe` is already included in the project root. If it stops working after a Chrome update, download the matching version from [chromedriver.chromium.org](https://chromedriver.chromium.org/downloads) and replace it.

### Installation

```bash
git clone https://github.com/your-username/amazon-image-automation.git
cd amazon-image-automation
pip install -r requirements.txt
```

### Setup

Create a `PRODUCT_LIST.xlsx` file with the following columns:

| PRODUCT_NAME | PRODUCT_URL |
|---|---|
| My Product | https://www.amazon.com/dp/... |

### Run

```bash
python main.py
```

---

## 🛠️ Tech Stack

| Tool | Purpose |
|---|---|
| Python | Core language |
| Selenium 4 | Browser automation |
| ChromeDriver | Bundled `chromedriver.exe` — must match your Chrome version |
| openpyxl / pandas | Excel file reading |
| requests | Image downloading |

---

## ⚠️ Notes

- This tool is intended for personal or internal use. Make sure your usage complies with [Amazon's Terms of Service](https://www.amazon.com/gp/help/customer/display.html?nodeId=508088).
- Amazon's page structure may change over time, which could require selector updates.
- Add delays between requests to avoid rate limiting.

---

## 📄 License

MIT License — feel free to use and modify for your own projects.
