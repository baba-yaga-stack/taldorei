/* Tal'Dorei Nights — tiny flaming donkey easter egg.
   Gallops across the viewport at random intervals and random angles. */
(function () {
  if (window.__fdonkey) return; window.__fdonkey = true;

  var css =
    '.fd-wrap{position:fixed;left:0;top:0;width:72px;height:48px;z-index:9998;' +
    'pointer-events:none;opacity:0;will-change:transform}' +
    '.fd-wrap svg{display:block;width:100%;height:100%;overflow:visible}' +
    '@keyframes fd-flick{0%,100%{transform:scaleY(1)}50%{transform:scaleY(.68)}}' +
    '.fd-flame{transform-origin:20px 26px;animation:fd-flick .16s infinite}' +
    '@media(prefers-reduced-motion:reduce){.fd-wrap{display:none}}';
  var st = document.createElement('style'); st.textContent = css;
  document.head.appendChild(st);

  var DONKEY =
    '<svg viewBox="0 0 72 48" aria-hidden="true">' +
    '<g class="fd-flame" fill="#c0303f"><path d="M20,34 Q6,32 2,20 Q9,30 14,27 Q6,20 11,10 Q11,24 22,24 Z"/></g>' +
    '<g class="fd-flame" fill="#e8781f"><path d="M20,33 Q9,31 6,22 Q12,29 16,26 Q10,20 14,13 Q14,25 23,25 Z"/>' +
    '<path d="M30,16 Q28,8 33,3 Q33,12 39,13 Z"/><path d="M40,15 Q39,8 44,4 Q44,12 49,14 Z"/></g>' +
    '<g class="fd-flame" fill="#f2c33a"><path d="M20,31 Q13,29 12,22 Q16,27 19,25 Q15,20 18,15 Q18,24 24,24 Z"/></g>' +
    '<g stroke="#5b606c" stroke-width="3" stroke-linecap="round">' +
    '<path d="M26,32 L21,45"/><path d="M32,33 L33,46"/><path d="M42,32 L47,45"/><path d="M47,31 L52,44"/></g>' +
    '<path d="M20,30 Q22,19 34,19 Q46,18 50,25 Q52,30 47,33 Q34,35 24,34 Q19,33 20,30 Z" fill="#9aa0ad" stroke="#5b606c" stroke-width="1.5"/>' +
    '<path d="M47,26 Q53,20 55,13 Q56,9 61,10 Q64,11 63,16 L61,22 Q59,28 51,30 Z" fill="#9aa0ad" stroke="#5b606c" stroke-width="1.5"/>' +
    '<ellipse cx="62" cy="17" rx="4" ry="4.5" fill="#b7bcc7" stroke="#5b606c" stroke-width="1.2"/>' +
    '<circle cx="63" cy="18" r="1" fill="#3a3e48"/>' +
    '<path d="M55,12 L52,2 L58,10 Z" fill="#9aa0ad" stroke="#5b606c" stroke-width="1.2"/>' +
    '<path d="M59,12 L61,1 L64,11 Z" fill="#9aa0ad" stroke="#5b606c" stroke-width="1.2"/>' +
    '<circle cx="57" cy="16" r="1.5" fill="#1c1c22"/>' +
    '<path d="M21,26 Q13,27 15,35" fill="none" stroke="#5b606c" stroke-width="2.4" stroke-linecap="round"/>' +
    '<path d="M15,35 l-2,5 l4,-2 Z" fill="#5b606c"/></svg>';

  var el = document.createElement('div'); el.className = 'fd-wrap';
  el.innerHTML = DONKEY; document.body.appendChild(el);

  function rand(a, b) { return a + Math.random() * (b - a); }

  function gallop() {
    var W = window.innerWidth, H = window.innerHeight, m = 140;
    var rightward = Math.random() < 0.5;
    var tilt = rand(-32, 32) * Math.PI / 180;          // random angle off horizontal
    var midY = rand(H * 0.15, H * 0.85);
    var startX, endX;
    if (rightward) { startX = -m; endX = W + m; }
    else { startX = W + m; endX = -m; }
    var dx = endX - startX;
    var startY = midY - dx * Math.tan(tilt) / 2;
    var endY = midY + dx * Math.tan(tilt) / 2;
    var ang = Math.atan2(endY - startY, endX - startX) * 180 / Math.PI;
    var flipY = Math.abs(ang) > 90 ? -1 : 1;           // keep legs down when running left
    var speed = rand(320, 520);                        // px/sec
    var dur = Math.hypot(endX - startX, endY - startY) / speed * 1000;

    el.style.transition = 'none';
    el.style.transform = 'translate(' + startX + 'px,' + startY + 'px) rotate(' + ang + 'deg) scale(1,' + flipY + ')';
    el.style.opacity = '1';
    el.getBoundingClientRect();                          // reflow
    el.style.transition = 'transform ' + dur + 'ms linear';
    el.style.transform = 'translate(' + endX + 'px,' + endY + 'px) rotate(' + ang + 'deg) scale(1,' + flipY + ')';
    setTimeout(function () { el.style.opacity = '0'; }, Math.max(0, dur - 250));
  }

  function loop() { gallop(); setTimeout(loop, rand(22000, 55000)); }  // random intervals
  setTimeout(loop, rand(5000, 12000));
})();
