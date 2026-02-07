"""
Interactive butterfly background: butterflies drift and gently move toward the cursor.
Uses streamlit.components.v1.html (HTML + CSS + JS). No external server; works on Streamlit Cloud.
Background layer is fixed, behind UI (pointer-events: none). Respects prefers-reduced-motion.
"""

import json
import streamlit.components.v1 as components


def butterfly_background(n: int = 10, opacity: float = 0.35, speed: float = 1.0) -> None:
    """
    Render a full-page animated background layer with butterflies that react to cursor movement.

    n: number of butterflies (default 10)
    opacity: layer opacity 0–1 (default 0.35)
    speed: animation speed multiplier (default 1.0; higher = faster)
    """
    butterfly_svg = (
        '<svg width="28" height="28" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">'
        '<path d="M32 30c-6-14-22-20-26-6-3 10 7 22 20 18 3-1 5-4 6-6Z" fill="rgba(255,255,255,0.85)"/>'
        '<path d="M32 30c6-14 22-20 26-6 3 10-7 22-20 18-3-1-5-4-6-6Z" fill="rgba(255,255,255,0.75)"/>'
        '<path d="M32 28c-2 3-2 10 0 14" stroke="rgba(255,255,255,0.9)" stroke-width="2" stroke-linecap="round"/>'
        '</svg>'
    )
    svg_js = json.dumps(butterfly_svg)

    script_body = f"""
        const butterflies = [];
        const svgStr = {svg_js};
        for (let i = 0; i < N; i++) {{
          const el = document.createElement("div");
          el.className = "butterfly";
          el.innerHTML = "<div class=\\"wing\\">" + svgStr + "</div>";
          bg.appendChild(el);
          butterflies.push({{
            el: el,
            x: Math.random() * W(),
            y: Math.random() * H(),
            vx: (Math.random() - 0.5) * 1.2,
            vy: (Math.random() - 0.5) * 1.0,
            rot: Math.random() * 360
          }});
        }}
    """

    html = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="margin:0;overflow:hidden;">
    <style>
      #cc-bg {{
        position: fixed;
        inset: 0;
        z-index: 0;
        pointer-events: none;
        overflow: hidden;
        opacity: {opacity};
      }}

      #cc-bg::before {{
        content: "";
        position: absolute;
        inset: -40%;
        background: radial-gradient(circle at 20% 30%, rgba(120,190,255,0.35), transparent 40%),
                    radial-gradient(circle at 75% 65%, rgba(200,120,255,0.28), transparent 45%),
                    radial-gradient(circle at 45% 90%, rgba(120,255,210,0.22), transparent 45%);
        filter: blur(30px);
        animation: driftGlow {20/speed:.2f}s ease-in-out infinite alternate;
      }}

      @keyframes driftGlow {{
        from {{ transform: translate3d(-1.5%, -1%, 0) scale(1.02); }}
        to   {{ transform: translate3d(1.5%, 1%, 0) scale(1.06); }}
      }}

      .butterfly {{
        position: absolute;
        width: 28px;
        height: 28px;
        will-change: transform;
        filter: drop-shadow(0 10px 20px rgba(0,0,0,0.12));
        transform: translate3d(0,0,0) rotate(0deg);
      }}

      .wing {{
        animation: flap {0.55/speed:.2f}s ease-in-out infinite;
        transform-origin: 50% 50%;
      }}

      @keyframes flap {{
        0% {{ transform: scale(1) rotate(0deg); }}
        50% {{ transform: scale(1.06) rotate(2deg); }}
        100% {{ transform: scale(1) rotate(0deg); }}
      }}

      @media (prefers-reduced-motion: reduce) {{
        #cc-bg::before, .wing {{
          animation: none !important;
        }}
      }}
    </style>

    <div id="cc-bg"></div>

    <script>
      (function() {{
        const bg = document.getElementById("cc-bg");
        const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

        const N = {n};
        const W = function() {{ return window.innerWidth; }};
        const H = function() {{ return window.innerHeight; }};

        let mouseX = W()/2, mouseY = H()/2;
        {script_body}

        window.addEventListener("mousemove", function(e) {{
          mouseX = e.clientX;
          mouseY = e.clientY;
        }}, {{ passive: true }});

        function tick() {{
          const w = W(), h = H();

          butterflies.forEach(function(b, idx) {{
            b.vx += (Math.random() - 0.5) * 0.02;
            b.vy += (Math.random() - 0.5) * 0.02;

            var dx = mouseX - b.x;
            var dy = mouseY - b.y;
            var dist = Math.sqrt(dx*dx + dy*dy) + 0.001;

            var strength = reducedMotion ? 0.0002 : 0.0011;
            b.vx += (dx / dist) * strength * Math.min(dist, 500);
            b.vy += (dy / dist) * strength * Math.min(dist, 500);

            var maxV = reducedMotion ? 0.35 : 1.25;
            b.vx = Math.max(-maxV, Math.min(maxV, b.vx));
            b.vy = Math.max(-maxV, Math.min(maxV, b.vy));

            b.x += b.vx;
            b.y += b.vy;

            if (b.x < -40) b.x = w + 40;
            if (b.x > w + 40) b.x = -40;
            if (b.y < -40) b.y = h + 40;
            if (b.y > h + 40) b.y = -40;

            var angle = Math.atan2(b.vy, b.vx) * 180 / Math.PI;
            var tilt = reducedMotion ? 0 : (Math.sin(Date.now()/800 + idx) * 4);
            b.el.style.transform = "translate3d(" + b.x + "px, " + b.y + "px, 0) rotate(" + (angle + tilt) + "deg)";
          }});

          requestAnimationFrame(tick);
        }}

        tick();
      }})();
    </script>
    </body>
    </html>
    """

    components.html(html, height=0)
