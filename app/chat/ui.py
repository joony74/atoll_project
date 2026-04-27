from __future__ import annotations

import base64
import html
import mimetypes
import re
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

try:
    from PIL import Image
except Exception:
    Image = None


def queue_prompt_submission() -> None:
    prompt = str(st.session_state.get("prompt_input", ""))
    if not prompt.strip():
        st.session_state["prompt_submit_requested"] = False
        st.session_state["prompt_submit_value"] = ""
        st.session_state["prompt_input"] = ""
        return

    submit_seq = int(st.session_state.get("prompt_submit_seq", 0) or 0) + 1
    st.session_state["prompt_submit_requested"] = True
    st.session_state["prompt_submit_value"] = prompt
    st.session_state["prompt_submit_seq"] = submit_seq
    st.session_state["prompt_input"] = ""
    st.session_state["_clear_prompt_on_render"] = True
    st.rerun()


_INTERNAL_LINK_RE = re.compile(r"\[([^\]\n]{1,120})\]\((\?(?:chat=main|doc=[^)]+))\)")


def render_message_content(content: str) -> str:
    raw = str(content or "")
    pieces: list[str] = []
    cursor = 0
    for match in _INTERNAL_LINK_RE.finditer(raw):
        pieces.append(html.escape(raw[cursor : match.start()]))
        label = html.escape(match.group(1).strip())
        href = html.escape(match.group(2).strip(), quote=True)
        pieces.append(f'<a class="coco-chat-link" href="{href}">{label}</a>')
        cursor = match.end()
    pieces.append(html.escape(raw[cursor:]))
    return "".join(pieces).replace("\n", "<br>")


def _image_preview_payload(image_path: str) -> dict[str, str | int]:
    path = Path(str(image_path or "")).expanduser()
    if not path.exists() or not path.is_file():
        return {}
    mime_type = mimetypes.guess_type(path.name)[0] or "image/png"
    try:
        data = path.read_bytes()
    except Exception:
        return {}
    width = 0
    height = 0
    if Image is not None:
        try:
            with Image.open(path) as image:
                width, height = image.size
        except Exception:
            width = 0
            height = 0
    encoded = base64.b64encode(data).decode("ascii")
    return {
        "uri": f"data:{mime_type};base64,{encoded}",
        "width": width,
        "height": height,
        "name": path.name,
    }


def render_conversation(messages: list[dict], mode: str = "main") -> str:
    if not messages:
        empty_text = (
            "안녕 전 코코입니다 일상적인 대화를 진행 할 수 있어요"
            if mode == "main"
            else "학습리스트를 선택하거나 문제 이미지를 올리면 수학 풀이 대화를 이어갈 수 있어요"
        )
        return (
            '<div class="chat-shell empty-state"><div class="empty-chat">'
            f"{html.escape(empty_text)}"
            "</div></div>"
        )

    rendered = []
    for index, message in enumerate(reversed(messages)):
        role = str(message.get("role") or "assistant")
        pending = bool(message.get("pending"))
        content = render_message_content(str(message.get("content") or ""))
        preview = _image_preview_payload(str(message.get("preview_image_path") or ""))
        preview_uri = str(preview.get("uri") or "")
        preview_width = int(preview.get("width") or 0)
        preview_height = int(preview.get("height") or 0)
        preview_label_prefix = str(message.get("preview_image_label") or "").strip()
        if preview_label_prefix and preview_width and preview_height:
            preview_label = f"{preview_label_prefix} {preview_width} x {preview_height}px"
        elif preview_label_prefix:
            preview_label = preview_label_prefix
        else:
            preview_label = f"원본 {preview_width} x {preview_height}px" if preview_width and preview_height else "원본 이미지"
        preview_style = (
            f"--preview-original-width:{preview_width}px;--preview-original-height:{preview_height}px;"
            if preview_width and preview_height
            else ""
        )
        latest_attr = ' data-latest-message="true"' if index == 0 else ""
        if role == "user":
            rendered.append(
                f'<div class="chat-row user"{latest_attr}><div class="user-bubble">{content}</div></div>'
            )
        elif pending:
            rendered.append(
                f'<div class="chat-row assistant"{latest_attr}>'
                '<div class="assistant-card pending-card">'
                '<div class="typing-dots" aria-label="생각 중">'
                '<span></span><span></span><span></span>'
                '</div>'
                '</div></div>'
            )
        else:
            if preview_uri:
                rendered.append(
                    f'<div class="chat-row assistant"{latest_attr}>'
                    '<div class="assistant-card with-preview">'
                    f'<div class="assistant-card-body">{content}</div>'
                    f'<figure class="assistant-card-preview" style="{preview_style}">'
                    '<div class="assistant-card-preview-frame">'
                    f'<img src="{preview_uri}" alt="원본 문제 이미지">'
                    '</div>'
                    '<div class="assistant-image-popover" aria-hidden="true">'
                    '<div class="assistant-image-pan-frame">'
                    f'<img src="{preview_uri}" alt="">'
                    '</div>'
                    f'<span>{html.escape(preview_label)}</span>'
                    '</div>'
                    '</figure>'
                    '</div></div>'
                )
                continue
            rendered.append(
                f'<div class="chat-row assistant"{latest_attr}><div class="assistant-card">{content}</div></div>'
            )
    return f'<div class="chat-shell">{"".join(rendered)}<div class="chat-end-anchor"></div></div>'


def scroll_chat_to_latest() -> None:
    components.html(
        """
        <script>
        const findScrollParent = (root, node) => {
          const shell = node ? node.closest('.chat-shell') : null;
          if (shell) return shell;
          let current = node ? node.parentElement : null;
          while (current && current !== root.body) {
            const style = window.parent.getComputedStyle(current);
            const overflowY = style.overflowY || '';
            const canScroll = /(auto|scroll|overlay)/.test(overflowY) && current.scrollHeight > current.clientHeight + 4;
            if (canScroll) return current;
            current = current.parentElement;
          }
          return root.scrollingElement || root.documentElement || root.body;
        };

        const scrollToLatest = () => {
          const root = window.parent.document;
          const anchors = root.querySelectorAll('.chat-end-anchor');
          const target = anchors[anchors.length - 1];
          if (!target) return;
          const latestRows = root.querySelectorAll('.chat-row[data-latest-message="true"]');
          const latestRow = latestRows[latestRows.length - 1] || target.previousElementSibling || target;
          const promptBar = root.querySelector('div[data-testid="stChatInput"]')
            || root.querySelector('div[data-testid="stTextInput"]');
          const bottomBlock = root.querySelector('[data-testid="stBottomBlockContainer"]');
          const scrollParent = findScrollParent(root, latestRow);
          const computed = scrollParent ? window.parent.getComputedStyle(scrollParent) : null;
          const clearance = computed
            ? parseFloat(computed.getPropertyValue('--coco-chat-scroll-clearance')) || 84
            : 84;
          const extraBottom = Math.max(clearance, 84);
          if (scrollParent) {
            if (computed && (computed.flexDirection || '').includes('reverse')) {
              scrollParent.scrollTop = 0;
              return;
            }
            if (latestRow && latestRow.offsetParent) {
              const parentRect = scrollParent.getBoundingClientRect();
              const rowRect = latestRow.getBoundingClientRect();
              const rowTop = rowRect.top - parentRect.top + scrollParent.scrollTop;
              const desiredTop = rowTop + latestRow.offsetHeight - scrollParent.clientHeight + extraBottom;
              scrollParent.scrollTop = Math.max(0, desiredTop);
            } else {
              scrollParent.scrollTop = scrollParent.scrollHeight;
            }
            const safeEdge = promptBar || bottomBlock;
            if (safeEdge && typeof scrollParent.scrollBy === 'function') {
              const latestRect = latestRow.getBoundingClientRect();
              const edgeRect = safeEdge.getBoundingClientRect();
              const overflow = latestRect.bottom - (edgeRect.top - 18);
              if (overflow > 0) {
                scrollParent.scrollBy({top: overflow + 8, left: 0, behavior: 'auto'});
              }
            }
            return;
          }
          const docHeight = Math.max(root.body.scrollHeight, root.documentElement.scrollHeight);
          if (window.parent && typeof window.parent.scrollTo === 'function') {
            window.parent.scrollTo({top: docHeight + extraBottom, left: 0, behavior: 'auto'});
          }
        };

        const wireImagePanners = () => {
          const root = window.parent.document;
          const previews = root.querySelectorAll('.assistant-card-preview');
          previews.forEach((preview) => {
            if (preview.dataset.cocoPanReady === '1') return;
            const thumbFrame = preview.querySelector('.assistant-card-preview-frame');
            const panFrame = preview.querySelector('.assistant-image-pan-frame');
            const img = panFrame ? panFrame.querySelector('img') : null;
            if (!thumbFrame || !panFrame || !img) return;
            preview.dataset.cocoPanReady = '1';

            const updatePan = (event) => {
              const frameRect = thumbFrame.getBoundingClientRect();
              const maxX = Math.max(0, img.offsetWidth - panFrame.clientWidth);
              const maxY = Math.max(0, img.offsetHeight - panFrame.clientHeight);
              const ratioX = frameRect.width ? Math.min(1, Math.max(0, (event.clientX - frameRect.left) / frameRect.width)) : 0;
              const ratioY = frameRect.height ? Math.min(1, Math.max(0, (event.clientY - frameRect.top) / frameRect.height)) : 0;
              img.style.setProperty('--pan-x', `${-maxX * ratioX}px`);
              img.style.setProperty('--pan-y', `${-maxY * ratioY}px`);
            };

            preview.addEventListener('mousemove', updatePan);
            preview.addEventListener('mouseenter', updatePan);
            preview.addEventListener('mouseleave', () => {
              img.style.setProperty('--pan-x', '0px');
              img.style.setProperty('--pan-y', '0px');
            });
          });
        };

        wireImagePanners();
        setTimeout(scrollToLatest, 0);
        setTimeout(scrollToLatest, 120);
        setTimeout(scrollToLatest, 320);
        setTimeout(scrollToLatest, 700);
        setTimeout(scrollToLatest, 1200);
        setTimeout(scrollToLatest, 1800);
        setTimeout(wireImagePanners, 120);
        setTimeout(wireImagePanners, 700);
        </script>
        """,
        height=0,
        width=0,
    )
