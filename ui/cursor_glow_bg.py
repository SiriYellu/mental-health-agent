"""
Cursor-following soft glow background. A gentle radial gradient follows the mouse.
Calm, low-distraction; respects prefers-reduced-motion (static glow when reduced).
Uses streamlit.components.v1.html. No butterflies; smooth cursor-reactive light.
"""

import streamlit.components.v1 as components


def cursor_glow_background(opacity: float = 0.4, size_px: int = 420) -> None:
    """
    Full-page fixed layer with a soft glow that follows the cursor.
    opacity: glow strength 0–1 (default 0.4)
    size_px: radius of the glow circle in px (default 420)
    """
    html = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="margin:0;overflow:hidden;">
    <style>
      #cc-cursor-glow {{
        position: fixed;
        inset: 0;
        z-index: 0;
        pointer-events: none;
        overflow: hidden;
      }}
      #cc-cursor-glow .glow {{
        position: absolute;
        width: {size_px * 2}px;
        height: {size_px * 2}px;
        margin-left: -{size_px}px;
        margin-top: -{size_px}px;
        border-radius: 50%;
        background: radial-gradient(
          circle,
          rgba(45, 212, 191, 0.12) 0%,
          rgba(14, 165, 233, 0.06) 35%,
          transparent 60%
        );
        opacity: {opacity};
        transition: left 0.2s ease-out, top 0.2s ease-out;
      }}
      @media (prefers-reduced-motion: reduce) {{
        #cc-cursor-glow .glow {{
          left: 50% !important;
          top: 40% !important;
          transform: translate(-50%, -50%);
          transition: none;
        }}
      }}
    </style>
    <div id="cc-cursor-glow">
      <div class="glow" id="cc-glow"></div>
    </div>
    <script>
      (function() {{
        var glow = document.getElementById('cc-glow');
        if (!glow) return;
        function move(e) {{
          glow.style.left = e.clientX + 'px';
          glow.style.top = e.clientY + 'px';
        }}
        document.addEventListener('mousemove', move, {{ passive: true }});
        document.addEventListener('touchmove', function(e) {{
          if (e.touches.length) move(e.touches[0]);
        }}, {{ passive: true }});
      }})();
    </script>
    </body>
    </html>
    """
    components.html(html, height=0, scrolling=False)

