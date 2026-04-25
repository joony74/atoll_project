from __future__ import annotations

import html

import streamlit as st
import streamlit.components.v1 as components


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


def render_message_content(content: str) -> str:
    return html.escape(content).replace("\n", "<br>")


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
        setTimeout(scrollToLatest, 0);
        setTimeout(scrollToLatest, 120);
        setTimeout(scrollToLatest, 320);
        setTimeout(scrollToLatest, 700);
        setTimeout(scrollToLatest, 1200);
        setTimeout(scrollToLatest, 1800);
        </script>
        """,
        height=0,
        width=0,
    )
