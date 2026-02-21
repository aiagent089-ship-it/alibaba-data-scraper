from DrissionPage import ChromiumPage, ChromiumOptions
import google.generativeai as genai
import time
import os
import json
import re
import html
from urllib.parse import urlparse

import requests

from dotenv import load_dotenv

load_dotenv()


def _dismiss_popups(page) -> None:
    """Try common close buttons to remove obstructive popups."""
    selectors = [
        "button[aria-label='Close']",
        ".close-icon",
        ".close",
        ".ui-dialog-close",
    ]
    for sel in selectors:
        try:
            btn = page.ele(sel, timeout=2)
            if btn:
                btn.click()
                time.sleep(1)
        except Exception:
            continue


def _open_message_center(page) -> None:
    """Open Alibaba message center after attempting popup cleanup."""
    _dismiss_popups(page)
    page.get("https://message.alibaba.com/message/messenger.htm")
    time.sleep(3)


def _read_unread_contacts(page) -> list[dict]:
    """Read contact cards and return only entries with unread messages."""
    contacts = []
    items = page.eles("@class:contact-item-container", timeout=15)
    for item in items:
        try:
            unread_raw = (item.attr("data-unread-count") or "0").strip()
            unread_count = int(unread_raw) if unread_raw.isdigit() else 0
            if unread_count <= 0:
                continue

            name = item.attr("data-name") or "Unknown"
            company_ele = item.ele("@class:contact-company", timeout=1)
            last_msg_ele = item.ele("@class:latest-msg", timeout=1)
            last_msg = last_msg_ele.text if last_msg_ele else ""
            company = company_ele.text if company_ele else ""

            contacts.append(
                {
                    "name": name,
                    "company": company,
                    "unread": unread_count,
                    "last_msg": last_msg,
                }
            )
        except Exception:
            continue
    return contacts


def _open_first_chat(page) -> dict:
    """Open the first available chat item and return basic chat metadata."""
    first_chat = page.ele("@class:contact-item-container", timeout=15)
    if not first_chat:
        return {"name": "", "opened": False}

    name = first_chat.attr("data-name") or "Unknown"
    first_chat.click()
    time.sleep(5)
    first_chat_new = page.ele("@class:contact-item-container", timeout=15)
    if first_chat_new:
        name = first_chat_new.attr("data-name") or name

    first_chat_new.click()
    time.sleep(2.5)
    return {"name": name, "opened": True}


def _extract_image_urls_from_raw_html(raw_html: str) -> list[str]:
    """Extract unique image src URLs from HTML fragments."""
    if not raw_html:
        return []

    decoded = html.unescape(raw_html)
    image_urls = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', decoded)

    seen = set()
    unique_urls = []
    for url in image_urls:
        clean = (url or "").strip()
        if not clean or clean in seen:
            continue
        seen.add(clean)
        unique_urls.append(clean)
    return unique_urls


def _get_recent_messages(
    page, limit: int = 5, include_images: bool = True, image_limit: int = 3
) -> list[dict]:
    """Collect latest chat messages and optional image URLs from the open thread."""
    containers = page.eles(
        "@class:scroll-box @class:message-item-wrapper", timeout=15
    ) or page.eles("@class:message-item-wrapper", timeout=5)

    messages = []
    for item in containers:
        role = "supplier"
        if "item-right" in (item.attr("class") or ""):
            role = "buyer"
        if "item-left" in (item.attr("class") or ""):
            role = "supplier"

        text_ele = item.ele("@class:session-rich-content.text", timeout=1)
        if not text_ele:
            text_ele = item.ele("@class:session-rich-content", timeout=1)
        if not text_ele:
            text_ele = item.ele("[data-original]", timeout=1)

        text = (text_ele.text if text_ele else "").strip()
        if not text and text_ele:
            text = (text_ele.attr("data-original") or "").strip()

        image_urls = []
        if include_images:
            rich_images = item.eles(".session-rich-content img", timeout=1) or []
            for img_ele in rich_images:
                src = (
                    img_ele.attr("src")
                    or img_ele.attr("data-src")
                    or img_ele.attr("data-original")
                    or ""
                ).strip()
                if src and src not in image_urls:
                    image_urls.append(src)

            raw_html = item.attr("data-original") or ""
            for url in _extract_image_urls_from_raw_html(raw_html):
                if url not in image_urls:
                    image_urls.append(url)

        if text or image_urls:
            messages.append({"role": role, "text": text, "images": image_urls})

    if len(messages) > limit:
        messages = messages[-limit:]

    if include_images and image_limit >= 0:
        remaining_images = image_limit
        for message in reversed(messages):
            imgs = message.get("images") or []
            if not imgs:
                continue
            if remaining_images <= 0:
                message["images"] = []
                continue
            if len(imgs) > remaining_images:
                message["images"] = imgs[-remaining_images:]
                remaining_images = 0
            else:
                remaining_images -= len(imgs)

    return messages


def _download_recent_images(
    page, messages: list[dict], max_images: int = 3, out_dir: str = "data/chat_images"
) -> list[str]:
    """Download recent image attachments to local storage using browser cookies."""
    image_urls = []
    for message in messages:
        for image_url in message.get("images", []):
            if image_url and image_url not in image_urls:
                image_urls.append(image_url)

    if not image_urls:
        return []

    image_urls = image_urls[-max_images:]
    os.makedirs(out_dir, exist_ok=True)

    cookie_jar = requests.cookies.RequestsCookieJar()
    try:
        all_cookies = page.cookies(all_domains=True)
        if isinstance(all_cookies, dict):
            for name, value in all_cookies.items():
                if name and value is not None:
                    cookie_jar.set(name, str(value))
        elif isinstance(all_cookies, (list, tuple)):
            for cookie in all_cookies:
                if isinstance(cookie, dict):
                    name = cookie.get("name")
                    value = cookie.get("value")
                    domain = cookie.get("domain")
                    path = cookie.get("path") or "/"
                    if name and value is not None:
                        cookie_jar.set(
                            name,
                            str(value),
                            domain=domain if domain else None,
                            path=path,
                        )
    except Exception as e:
        print(f"Warning: could not read browser cookies for image download: {e}")

    headers = {
        "Referer": "https://message.alibaba.com/",
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        ),
    }

    saved_paths = []
    timestamp_base = int(time.time())
    session = requests.Session()
    session.headers.update(headers)
    if len(cookie_jar):
        session.cookies.update(cookie_jar)

    for index, image_url in enumerate(image_urls, start=1):
        try:
            normalized_url = html.unescape((image_url or "").strip())
            if not normalized_url:
                continue

            response = session.get(normalized_url, timeout=20, allow_redirects=True)
            response.raise_for_status()

            content_type = (response.headers.get("Content-Type") or "").lower()
            if "image" not in content_type:
                print(
                    "Failed to download image: "
                    f"{normalized_url} | non-image response ({content_type or 'unknown'})"
                )
                continue

            parsed_path = urlparse(response.url).path
            ext = os.path.splitext(parsed_path)[1].lower()
            if ext not in {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp"}:
                if "png" in content_type:
                    ext = ".png"
                elif "webp" in content_type:
                    ext = ".webp"
                elif "gif" in content_type:
                    ext = ".gif"
                elif "jpeg" in content_type or "jpg" in content_type:
                    ext = ".jpg"
                elif "bmp" in content_type:
                    ext = ".bmp"
                else:
                    ext = ".jpg"

            file_name = f"chat_image_{timestamp_base}_{index}{ext}"
            file_path = os.path.join(out_dir, file_name)
            with open(file_path, "wb") as file:
                file.write(response.content)

            saved_paths.append(file_path)
        except Exception as e:
            print(f"Failed to download image: {image_url} | {e}")

    return saved_paths


def _generate_gemini_reply(contact_name: str, messages: list[dict]) -> str:
    """Generate a short negotiation-style reply using Gemini based on recent chat history."""
    api_key = os.getenv("GEMINI_API_KEY").strip()
    if not api_key:
        raise ValueError("Missing GEMINI_API_KEY env var")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.5-flash")

    history_text = "\n".join(
        [f"- {m['role']}: {m['text']}" for m in messages if m.get("text")]
    )
    prompt = (
        "You are a buyer talking to a supplier on Alibaba."
        "Write a concise, friendly, humanized reply that moves the conversation forward. Do not finalize the deal. Keep the reply short and concise and just go for negotiations if needed and never try to finalize the deal. Always ask for more details if needed. Always try to negotiate for a better price or better terms if possible."
        "Keep it 2-4 sentences and do not invent facts.\n\n"
        f"Contact: {contact_name}\n"
        f"Recent messages:\n{history_text}\n"
    )

    response = model.generate_content(prompt, image)
    return (response.text or "").strip()


def _send_message(page, text: str) -> bool:
    """Type text into the chat composer and click send."""
    textarea = page.ele("@class:send-textarea", timeout=10)
    if not textarea:
        return False
    textarea.clear()
    textarea.input(text)
    time.sleep(0.5)

    send_btn = page.ele("@class:send-tool-button", timeout=5)
    if not send_btn:
        return False
    send_btn.click()
    time.sleep(1)
    return True


def negotiation_chat(image_path: str):
    """Run end-to-end login, chat parsing, reply generation, and message sending."""
    co = ChromiumOptions()
    co.set_user_data_path(r"C:\Users\vinay\Downloads\Alibaba_UserProfile")
    page = ChromiumPage(co)

    print("Navigating to Login Page...")
    page.get("https://login.alibaba.com/")

    # Attempt login with saved credentials.
    try:
        email_input = page.ele("@name=account", timeout=10)
        if email_input:
            email_input.clear()
            email_input.input("10a.vinaykhedkar@gmail.com")
        pass_input = page.ele("@name=password", timeout=10)
        if pass_input:
            pass_input.clear()
            pass_input.input("Vinaymk@2005")
        login_btn = page.ele("text=Continue", timeout=5) or page.ele(
            "button[aria-label='Continue']"
        )
        if login_btn:
            login_btn.click()
        page.wait.url_change("login.alibaba.com", timeout=30)
        time.sleep(5)
    except Exception as e:
        print(f"Login process issue: {e}")

    _open_message_center(page)
    unread = _read_unread_contacts(page)
    print(f"Unread contacts: {len(unread)}")
    for entry in unread:
        print(
            f"- {entry['name']} | {entry['company']} | {entry['unread']} | {entry['last_msg']}"
        )

    first_chat = _open_first_chat(page)
    if not first_chat.get("opened"):
        print("No chat found to open.")
        return

    recent_messages = _get_recent_messages(page, limit=5)
    if not recent_messages:
        print("No recent messages found.")
        return

    for msg in recent_messages:
        print(f"{msg['role']}: {msg.get('text', '')}")
        for image_url in msg.get("images", []):
            print(f"  [image] {image_url}")

    # Save recent incoming images for downstream use/debugging.
    download_dir = os.path.join(os.path.dirname(__file__), "data", "chat_images")
    saved_images = _download_recent_images(
        page, recent_messages, max_images=3, out_dir=download_dir
    )
    if saved_images:
        print("\nSaved recent images:")
        for file_path in saved_images:
            print(f"- {file_path}")
    else:
        print("\nNo images were downloaded.")

    # Generate and optionally send AI-assisted negotiation response.
    reply = _generate_gemini_reply(first_chat.get("name", ""), recent_messages)
    print("\nSuggested reply:")
    print(reply)

    if reply:
        sent = _send_message(page, reply)
        print("Message sent." if sent else "Failed to send message.")


if __name__ == "__main__":
    img = os.path.join(
        os.path.dirname(__file__), "data", "uploaded_image_1771097717.png"
    )
    negotiation_chat(img)
