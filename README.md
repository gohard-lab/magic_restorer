🌐 **Read this in other languages:** [English](README.md) | [🇰🇷 한국어 (Korean)](README_ko.md)

# 🖼️ Magic Restore (Lite Ver.)

A lightweight and fast image restoration tool that bypasses heavy deep learning AI models in favor of traditional, powerful OpenCV inpainting algorithms. You can easily remove scratches or unwanted stains from damaged old photos through an intuitive UI.

<br>

## ⭐ Support the Developer!
💡 **유용하게 사용하셨나요? 소스코드만 날름 가져가는 분들이 많습니다. 개발자의 땀과 노력에 대한 최소한의 예의로 우측 상단의 깃허브 Star ⭐ 를 꾹 눌러주세요!**
*Did you find this project useful? Please show some basic courtesy for the developer's hard work by leaving a **GitHub Star ⭐**!*

<br>

## ✨ Key Features

* **Ultra-Lightweight & Standalone:** Runs instantly with a single `.exe` file, requiring no complex Python environment setup.
* **3 Custom Restoration Modes:**
  * **NS Mode (Navier-Stokes):** Optimized for restoring long scratches or linear damage.
  * **Telea Mode (Fast Marching):** Excellent for removing round mold, stains, and watermarks.
  * **Clone Stamp:** Precisely overwrite by copying repeating patterns or textures directly from the image.
* **Intuitive Controls:** Offers smooth zooming with the mouse wheel and screen panning via drag.

> **Notice:** This program collects minimal, anonymized usage statistics (e.g., feature click counts) to help improve the service and fix errors. (No personally identifiable information is collected.)

## 🚀 Download & Run (For General Users)

If you want to use the program immediately without installing Python or knowing how to code, please download the executable file from the link below.

* **[youtube]** [youtube](https://youtu.be/78EH925mXL0))

* **[Download .exe for Windows]** [magic_restore_lite.exe](https://github.com/gohard-lab/magic_restorer/releases/latest)

*(After downloading, simply double-click `magic_restore_lite.exe` to run it.)*

* **[Try it on Google Colab]** [Google Colab](https://colab.research.google.com/drive/1FES7fWwIV75bE8E59QDjE4-k8m6LSvoc?hl=ko#scrollTo=W_d7Dy5rORLi)


## ⌨️ Shortcuts & Controls

| Key / Mouse | Description |
| :--- | :--- |
| **`M`** | Change restoration mode (NS ↔ Telea ↔ Clone Stamp) |
| **`Z`** / **`X`** | Decrease / Increase brush size |
| **`Space Bar`** | Execute restoration on the selected area |
| **`S`** | Save the completed image |
| **`Right-Click`** | (Clone Stamp) Set the clean source area to copy from |
| **`Shift + Left-Click`** | Draw a straight line connecting two points |
| **`Ctrl + Z`** | Undo |

## 🛠 Development Setup & Running from Source (For Developers)

This project manages dependencies using the modern Python package management standard, `pyproject.toml` and `uv`, instead of the legacy `requirements.txt`.

### 1. Clone the Repository
```bash
git clone [https://github.com/gohard-lab/magic_restore.git](https://github.com/gohard-lab/magic_restore.git)
cd magic_restore
