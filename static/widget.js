(function() {
    'use strict';

    var API_BASE = window.WEBAI_CHAT_CONFIG ? (window.WEBAI_CHAT_CONFIG.apiBase || '/') : '/';

    var scripts = [
        'https://unpkg.com/react@18/umd/react.production.min.js',
        'https://unpkg.com/react-dom@18/umd/react-dom.production.min.js',
        'https://unpkg.com/@babel/standalone/babel.min.js'
    ];

    var loadPromises = scripts.map(function(src) {
        return new Promise(function(resolve) {
            var s = document.createElement('script');
            s.src = src;
            s.onload = resolve;
            s.onerror = resolve;
            document.head.appendChild(s);
        });
    });

    Promise.all(loadPromises).then(function() {
        setTimeout(function() {
            if (typeof React === 'undefined' || typeof ReactDOM === 'undefined') {
                console.error('React not loaded');
                return;
            }
            try { initWidget(); } catch(e) { console.error('Widget init error:', e); }
        }, 500);
    });

    function initWidget() {
        var R = React, ReactDOM = window.ReactDOM, h = R.createElement;
        var useState = R.useState, useEffect = R.useEffect, useRef = R.useRef, Fragment = R.Fragment;

        var PRESET_THEMES = {
            blue: { primary: '#1a73e8', secondary: '#4fc3f7', bg: '#ffffff', surface: '#f9fafb', messageBg: '#f3f4f6', text: '#111827', textSecondary: '#6b7280', border: '#e5e7eb', headerGrad: 'linear-gradient(135deg, #1a73e8 0%, #4fc3f7 100%)' },
            purple: { primary: '#7c3aed', secondary: '#c084fc', bg: '#ffffff', surface: '#f9fafb', messageBg: '#f3f4f6', text: '#111827', textSecondary: '#6b7280', border: '#e5e7eb', headerGrad: 'linear-gradient(135deg, #7c3aed 0%, #c084fc 100%)' },
            green: { primary: '#059669', secondary: '#34d399', bg: '#ffffff', surface: '#f9fafb', messageBg: '#f3f4f6', text: '#111827', textSecondary: '#6b7280', border: '#e5e7eb', headerGrad: 'linear-gradient(135deg, #059669 0%, #34d399 100%)' },
            red: { primary: '#dc2626', secondary: '#f87171', bg: '#ffffff', surface: '#f9fafb', messageBg: '#f3f4f6', text: '#111827', textSecondary: '#6b7280', border: '#e5e7eb', headerGrad: 'linear-gradient(135deg, #dc2626 0%, #f87171 100%)' },
            orange: { primary: '#ea580c', secondary: '#fb923c', bg: '#ffffff', surface: '#f9fafb', messageBg: '#f3f4f6', text: '#111827', textSecondary: '#6b7280', border: '#e5e7eb', headerGrad: 'linear-gradient(135deg, #ea580c 0%, #fb923c 100%)' },
            dark: { primary: '#818cf8', secondary: '#6366f1', bg: '#0f172a', surface: '#1e293b', messageBg: '#334155', text: '#f1f5f9', textSecondary: '#94a3b8', border: '#334155', headerGrad: 'linear-gradient(135deg, #1e1b4b 0%, #312e81 100%)' },
            gradient: { primary: '#764ba2', secondary: '#667eea', bg: '#ffffff', surface: '#f9fafb', messageBg: '#f3f4f6', text: '#111827', textSecondary: '#6b7280', border: '#e5e7eb', headerGrad: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }
        };

        var FONTS = { system: '-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif', inter: 'Inter,sans-serif', roboto: '"Roboto",sans-serif', poppins: '"Poppins",sans-serif' };

        var DEFAULTS = {
            position: 'bottom-right', theme: 'blue', color: '#1a73e8', customCSS: '', logo: '', greeting: 'Hi! How can I help you?',
            company_name: '', button_shape: 'circle', button_size: 'medium', show_quick_replies: true,
            quick_replies: ['What services do you offer?', 'Contact information', 'Pricing', 'FAQ'],
            show_emoji_picker: true, show_source_citations: true, typing_animation: 'dots', avatar_style: 'icon',
            unread_count: true, corner_radius: 16, animation_speed: 'normal', font_family: 'system',
            auto_open_delay: 0, minimize_to_icon: false, show_timestamps: false, show_status: true,
            status: 'online', keyboard_shortcut: true, show_admin_button: true
        };

        var EMOJIS = ['\ud83d\ude0a','\ud83d\ude02','\u2764\ufe0f','\ud83d\udc4d','\ud83d\udc4e','\ud83c\udf89','\ud83d\udd25','\ud83d\udca1','\u2705','\u274c','\u2b50','\ud83d\ude4f','\ud83e\udd14','\ud83d\udc4b','\ud83d\ude80','\ud83d\udcfa','\ud83c\udfaf','\ud83d\udccc','\ud83d\udce8','\ud83d\udcbb','\u2699\ufe0f','\ud83d\udcca','\ud83d\udcb0','\ud83c\udf01','\ud83d\udc4f','\ud83d\ude4c','\ud83d\udc8f','\u2728','\ud83c\udf1f','\ud83d\udd14','\ud83d\udcd1','\ud83d\udcda','\ud83d\udc7c','\ud83c\udf0d'];

        function loadConvs() { try { var d = localStorage.getItem('webai_convs'); return d ? JSON.parse(d) : []; } catch(e) { return []; } }
        function saveConvs(c) { try { localStorage.setItem('webai_convs', JSON.stringify(c)); } catch(e) {} }
        function loadMsgs(id) { try { var d = localStorage.getItem('webai_msgs_' + id); return d ? JSON.parse(d) : []; } catch(e) { return []; } }
        function saveMsgs(id, m) { try { localStorage.setItem('webai_msgs_' + id, JSON.stringify(m)); } catch(e) {} }

        function getTheme(cfg) {
            if (cfg.theme === 'custom' && cfg.color) {
                return { primary: cfg.color, secondary: cfg.color, bg: '#ffffff', surface: '#f9fafb', messageBg: '#f3f4f6', text: '#111827', textSecondary: '#6b7280', border: '#e5e7eb', headerGrad: 'linear-gradient(135deg, ' + cfg.color + ' 0%, ' + lightenColor(cfg.color, 30) + ' 100%)', isDark: false };
            }
            if (cfg.theme === 'dark') return { ...PRESET_THEMES.dark, isDark: true };
            return { ...PRESET_THEMES[cfg.theme], isDark: false };
        }

        function lightenColor(hex, percent) {
            hex = hex.replace('#', '');
            var r = Math.min(255, parseInt(hex.substr(0, 2), 16) + Math.round(255 * percent / 100));
            var g = Math.min(255, parseInt(hex.substr(2, 2), 16) + Math.round(255 * percent / 100));
            var b = Math.min(255, parseInt(hex.substr(4, 2), 16) + Math.round(255 * percent / 100));
            return '#' + [r, g, b].map(function(x) { return x.toString(16).padStart(2, '0'); }).join('');
        }

        function getAnimationDuration(speed) {
            switch(speed) { case 'slow': return '0.3s'; case 'fast': return '0.1s'; case 'off': return '0s'; default: return '0.2s'; }
        }

        function formatTime(ts) {
            var d = new Date(ts);
            return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        }

        function renderMarkdown(text, isDark) {
            if (!text) return '';
            var lines = text.split('\n'), html = '', inCode = false, codeLang = '', codeBuf = '';
            var inList = false, listType = '', listBuf = '';
            var inTable = false, tableBuf = [], tableSep = false;

            function esc(t) { return t.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
            function inline(t) {
                t = esc(t);
                t = t.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
                t = t.replace(/\*(.+?)\*/g, '<em>$1</em>');
                t = t.replace(/`(.+?)`/g, '<code style="background:' + (isDark ? '#374151' : '#e5e7eb') + ';padding:1px 5px;border-radius:3px;font-size:0.9em;font-family:monospace;">$1</code>');
                t = t.replace(/(https?:\/\/[^\s<]+)/g, '<a href="$1" target="_blank" style="color:inherit;text-decoration:underline;">$1</a>');
                t = t.replace(/&lt;br\s*\/&gt;/gi, '<br/>');
                return t;
            }
            function flushCode() {
                if (codeBuf) {
                    html += '<pre style="margin:8px 0;border-radius:8px;overflow:hidden;background:#1e1e2e;"><div style="display:flex;justify-content:space-between;align-items:center;padding:6px 12px;background:#2d2d3f;"><span style="font-size:11px;color:#a6adc8;font-family:monospace;">' + esc(codeLang) + '</span><button class="wc-copy-code" data-code="' + encodeURIComponent(esc(codeBuf)) + '" style="background:none;border:none;color:#a6adc8;cursor:pointer;font-size:11px;display:flex;align-items:center;gap:4px;padding:2px 6px;border-radius:3px;"><svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><path d="M16 1H4c-1.1 0-2 .9-2 2v14h2V3h12V1zm3 4H8c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h11c1.1 0 2-.9 2-2V7c0-1.1-.9-2-2-2zm0 16H8V7h11v14z"/></svg>Copy</button></div><code style="display:block;padding:12px 16px;overflow-x:auto;color:#cdd6f4;font-size:13px;line-height:1.5;font-family:monospace;">' + esc(codeBuf).replace(/\n/g, '<br/>') + '</code></pre>';
                    codeBuf = ''; codeLang = '';
                }
                inCode = false;
            }
            function flushList() {
                if (listBuf) { var tag = listType === 'number' ? 'ol' : 'ul'; html += '<' + tag + ' style="margin:4px 0;padding-left:20px;">' + listBuf + '</' + tag + '>'; listBuf = ''; inList = false; }
            }
            function flushTable() {
                if (tableBuf.length > 0) {
                    html += '<table style="width:100%;border-collapse:collapse;margin:8px 0;font-size:13px;"><tbody>';
                    tableBuf.forEach(function(row, i) {
                        html += '<tr' + (i === 0 ? ' style="background:' + (isDark ? '#313244' : '#f3f4f6') + ';"' : '') + '>';
                        row.forEach(function(cell, j) { var tag = (i === 0 && !tableSep) ? 'th' : 'td'; html += '<' + tag + ' style="padding:6px 10px;border:1px solid' + (isDark ? '#45475a' : '#e5e7eb') + ';' + (i === 0 ? 'font-weight:600;' : '') + '">' + cell + '</' + tag + '>'; });
                        html += '</tr>';
                    });
                    html += '</tbody></table>'; tableBuf = []; inTable = false; tableSep = false;
                }
            }
            for (var i = 0; i < lines.length; i++) {
                var line = lines[i], fenceMatch = line.match(/^```(\w*)/);
                if (fenceMatch) { flushList(); flushTable(); if (inCode) { flushCode(); } else { inCode = true; codeLang = fenceMatch[1]; codeBuf = ''; } continue; }
                if (inCode) { codeBuf += (codeBuf ? '\n' : '') + line; continue; }
                if (/^\|/.test(line.trim()) && /\|$/.test(line.trim())) {
                    flushList(); if (!inTable) { inTable = true; tableSep = false; tableBuf = []; }
                    var cells = line.trim().split('|').slice(1, -1).map(function(c) { return inline(c.trim()); });
                    if (!tableSep && cells.every(function(c) { return /^[-:]+$/.test(c); })) { tableSep = true; } else tableBuf.push(cells); continue;
                } else if (inTable) { flushTable(); }
                var bm = line.match(/^[\s]*[-*+]\s+(.*)/), nm = line.match(/^[\s]*\d+\.\s+(.*)/);
                if (bm || nm) {
                    flushTable(); var lt = bm ? 'bullet' : 'number', lc = inline((bm || nm)[1]);
                    if (!inList) { inList = true; listType = lt; } else if (listType !== lt) { flushList(); inList = true; listType = lt; }
                    listBuf += '<li>' + lc + '</li>'; continue;
                } else { flushList(); }
                if (line.trim() === '') { html += '<br/>'; continue; }
                html += inline(line) + '<br/>';
            }
            if (inCode) flushCode(); flushList(); flushTable(); return html;
        }

        function setupCopyHandlers() {
            document.querySelectorAll('.wc-copy-code').forEach(function(btn) {
                if (btn.dataset.setup) return; btn.dataset.setup = '1';
                btn.addEventListener('click', function() {
                    var text = decodeURIComponent(btn.dataset.code);
                    navigator.clipboard.writeText(text).then(function() {
                        btn.innerHTML = '<svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg>Done';
                        setTimeout(function() { btn.innerHTML = '<svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><path d="M16 1H4c-1.1 0-2 .9-2 2v14h2V3h12V1zm3 4H8c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h11c1.1 0 2-.9 2-2V7c0-1.1-.9-2-2-2zm0 16H8V7h11v14z"/></svg>Copy'; }, 2000);
                    });
                });
            });
        }

        function ChevronIcon(color) { return h('svg', { width: '28', height: '28', viewBox: '0 0 24 24', fill: 'none' }, h('path', { d: 'M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5', stroke: color || 'white', strokeWidth: '2', strokeLinecap: 'round', strokeLinejoin: 'round' })); }

   function BotIcon() { return h('svg', { width: '20', height: '20', viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', strokeWidth: '1.5', strokeLinecap: 'round', strokeLinejoin: 'round' }, h('path', { d: 'M12 2a2 2 0 0 1 2 2v2h4a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4V4a2 2 0 0 1 2-2z' }), h('circle', { cx: '9', cy: '10', r: '1', fill: 'currentColor' }), h('circle', { cx: '15', cy: '10', r: '1', fill: 'currentColor' }), h('path', { d: 'M9 14h6' }), h('path', { d: 'M10 17h4' }), h('path', { d: 'M12 2v2' })); }

        function UserIcon() { return h('svg', { width: '20', height: '20', viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', strokeWidth: '1.5', strokeLinecap: 'round', strokeLinejoin: 'round' }, h('circle', { cx: '12', cy: '8', r: '4' }), h('path', { d: 'M20 21a8 8 0 1 0-16 0' })); }

       function HtmlContent(props) {
            var contentRef = useRef(null);
            useEffect(function() {
                if (contentRef.current) contentRef.current.innerHTML = props.content || '';
            }, [props.content]);
            return h('div', { ref: contentRef, className: props.className });
        }

        function injectCSS(config, theme) {
            var id = 'wc-styles'; var existing = document.getElementById(id); if (existing) existing.remove();
            var dur = getAnimationDuration(config.animation_speed);
            var radius = config.corner_radius || 16;
            var btnSize = config.button_size === 'small' ? 48 : config.button_size === 'large' ? 72 : 60;
            var btnRadius = config.button_shape === 'square' ? '0' : config.button_shape === 'rounded-square' ? '16px' : '50%';
            var panelRadius = radius + 'px';
            var font = FONTS[config.font_family] || FONTS.system;
            var css = '.wc-panel{position:fixed;border-radius:' + panelRadius + ';box-shadow:0 12px 40px rgba(0,0,0,.2);display:flex;flex-direction:column;overflow:hidden;background:' + theme.bg + ';font-family:' + font + ';z-index:1000000;transition:all ' + dur + ' ease}.wc-panel.open{display:flex}.wc-resize{position:absolute;bottom:0;right:0;width:20px;height:20px;cursor:nwse-resize;z-index:10}.wc-resize::after{content:"";position:absolute;bottom:4px;right:4px;width:8px;height:8px;border-right:2px solid ' + theme.textSecondary + ';border-bottom:2px solid ' + theme.textSecondary + '}.wc-header{color:white;padding:14px 16px;display:flex;align-items:center;justify-content:space-between;min-height:56px;flex-shrink:0;background:' + theme.headerGrad + '}.wc-header-left{display:flex;align-items:center;gap:10px;flex:1;min-width:0}.wc-header-logo{width:32px;height:32px;border-radius:8px;object-fit:cover}.wc-header-info h3{margin:0;font-size:15px;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.wc-header-info span{font-size:11px;opacity:.85}.wc-header-btns{display:flex;gap:2px}.wc-hbtn{background:rgba(255,255,255,.15);border:none;color:white;cursor:pointer;padding:6px;border-radius:8px;display:flex;align-items:center;justify-content:center;transition:background ' + dur + '}.wc-hbtn:hover{background:rgba(255,255,255,.25)}.wc-hbtn svg{width:18px;height:18px;fill:white}.wc-dropdown{position:absolute;top:100%;right:0;background:' + theme.bg + ';border:1px solid ' + theme.border + ';border-radius:12px;box-shadow:0 8px 24px rgba(0,0,0,.12);min-width:220px;z-index:1000001;display:none;max-height:300px;overflow-y:auto}.wc-dropdown.open{display:block}.wc-dd-header{padding:10px 14px;font-size:11px;font-weight:600;color:' + theme.textSecondary + ';text-transform:uppercase;letter-spacing:.5px;border-bottom:1px solid ' + theme.surface + ';display:flex;justify-content:space-between;align-items:center;position:sticky;top:0;background:' + theme.bg + '}.wc-dd-new{background:' + theme.primary + ';color:white;border:none;border-radius:4px;padding:2px 8px;cursor:pointer;font-size:12px;font-weight:600}.wc-dd-item{padding:8px 14px;font-size:13px;color:' + theme.text + ';cursor:pointer;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;border-bottom:1px solid ' + theme.surface + '}.wc-dd-item:hover{background:' + theme.surface + '}.wc-dd-item.active{background:' + theme.primary + ';color:white}.wc-messages{flex:1;overflow-y:auto;padding:16px;display:flex;flex-direction:column;gap:12px}.wc-empty{display:flex;flex-direction:column;align-items:center;justify-content:center;height:100%;color:' + theme.textSecondary + ';text-align:center}.wc-empty .emoji{font-size:48px;margin-bottom:12px}.wc-empty h3{margin:0 0 4px;font-size:18px;color:' + theme.text + '}.wc-empty p{margin:0;font-size:14px}.wc-msg{display:flex;flex-direction:column;gap:8px;max-width:85%;animation:wcSlideIn ' + dur + ' ease}.wc-msg-user-row{align-self:flex-end;flex-direction:row-reverse}.wc-msg-bot-row{align-self:flex-start}.wc-msg-avatar{width:28px;height:28px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:12px;flex-shrink:0;background:' + theme.primary + ';color:white}.wc-msg-user-row .wc-msg-avatar{background:' + theme.secondary + '}.wc-msg-inner{padding:10px 14px;border-radius:16px;font-size:14px;line-height:1.5;word-wrap:break-word;white-space:pre-wrap}.wc-msg-user-row .wc-msg-inner{background:' + theme.primary + ';color:white;border-bottom-right-radius:4px}.wc-msg-bot-row .wc-msg-inner{background:' + theme.messageBg + ';color:' + theme.text + ';border-bottom-right-radius:4px}.wc-msg-inner pre{margin:8px 0;border-radius:8px;overflow:hidden;background:#1e1e2e}.wc-msg-inner pre code{display:block;padding:12px 16px;overflow-x:auto;color:#cdd6f4;font-size:13px;line-height:1.5;font-family:monospace}.wc-msg-inner code{background:' + (theme.isDark ? '#374151' : '#e5e7eb') + ';padding:1px 5px;border-radius:3px;font-size:0.9em;font-family:monospace}.wc-msg-inner a{color:' + theme.primary + ';text-decoration:underline}.wc-msg-actions{display:flex;gap:4px;margin-top:6px}.wc-mact{background:none;border:1px solid ' + theme.border + ';border-radius:4px;padding:2px 8px;font-size:11px;cursor:pointer;color:' + theme.textSecondary + '}.wc-mact:hover{background:' + theme.surface + '}.wc-mact.liked{background:#d1fae5;border-color:#22c55e;color:#15803d}.wc-mact.disliked{background:#fee2e2;border-color:#ef4444;color:#b91c1c}.wc-msg-delete{color:#ef4444!important}.wc-typing{display:flex;gap:4px;padding:12px 16px}.wc-typing span{width:8px;height:8px;background:' + theme.textSecondary + ';border-radius:50%;animation:wcBounce 1.4s infinite}.wc-typing span:nth-child(2){animation-delay:.2s}.wc-typing span:nth-child(3){animation-delay:.4s}.wc-input-area{display:flex;gap:8px;padding:12px;border-top:1px solid ' + theme.border + ';background:' + theme.surface + ';align-items:center;flex-shrink:0}.wc-input{flex:1;border:1px solid ' + theme.border + ';border-radius:24px;padding:10px 16px;font-size:14px;outline:none;font-family:' + font + ';background:' + theme.bg + ';color:' + theme.text + ';transition:border-color ' + dur + '}.wc-input:focus{border-color:' + theme.primary + '}.wc-send{width:40px;height:40px;border-radius:50%;border:none;color:white;cursor:pointer;display:flex;align-items:center;justify-content:center;transition:opacity ' + dur + '}.wc-send:disabled{opacity:.5;cursor:not-allowed}.wc-send svg{width:20px;height:20px;fill:white}.wc-emoji-btn{width:44px;height:44px;border-radius:50%;border:none;background:none;cursor:pointer;font-size:18px;transition:background ' + dur + '}.wc-emoji-btn:hover{background:' + theme.surface + '}.wc-mic-btn{width:24px;height:24px;border-radius:50%;border:none;background:none;cursor:pointer;display:flex;align-items:center;justify-content:center;color:' + theme.textSecondary + ';transition:all ' + dur + '}.wc-mic-btn:hover{background:' + theme.surface + ';color:' + theme.primary + '}.wc-mic-btn.recording{color:#ef4444;animation:wcPulse 1.5s infinite}.wc-emoji-picker{position:absolute;bottom:60px;left:12px;background:' + theme.bg + ';border:1px solid ' + theme.border + ';border-radius:12px;padding:12px;box-shadow:0 8px 24px rgba(0,0,0,.12);display:none;flex-wrap:wrap;gap:4px;max-width:280px;z-index:1000001}.wc-emoji-picker.open{display:flex}.wc-emoji-opt{width:32px;height:32px;display:flex;align-items:center;justify-content:center;font-size:18px;cursor:pointer;border-radius:6px;transition:background ' + dur + '}.wc-emoji-opt:hover{background:' + theme.surface + '}.wc-quick{padding:8px 12px;display:flex;flex-wrap:wrap;gap:6px;border-top:1px solid ' + theme.border + ';background:' + theme.surface + '}.wc-quick-btn{background:' + theme.surface + ';border:1px solid ' + theme.border + ';border-radius:16px;padding:6px 12px;font-size:12px;cursor:pointer;color:' + theme.text + ';transition:all ' + dur + '}.wc-quick-btn:hover{background:' + theme.primary + ';color:white;border-color:' + theme.primary + '}.wc-btn-wrap{position:fixed;z-index:999999;bottom:20px;right:20px;animation:wcBtnBounceIn 0.6s ease-out}.wc-btn{width:' + btnSize + 'px;height:' + btnSize + 'px;border-radius:' + btnRadius + ';border:none;color:white;cursor:pointer;box-shadow:0 4px 16px rgba(0,0,0,.2);display:flex;align-items:center;justify-content:center;transition:all ' + dur + ' ease;background:' + theme.headerGrad + ';overflow:hidden;animation:wcSpringBounce 2.5s ease-in-out infinite}.wc-btn:hover{transform:scale(1.05);box-shadow:0 6px 20px rgba(0,0,0,.3)}.wc-btn:hover svg{transform:rotate(360deg);transition:transform 0.6s cubic-bezier(0.34,1.56,0.64,1)}.wc-badge{position:absolute;top:-4px;right:-4px;background:#ef4444;color:white;font-size:11px;font-weight:700;min-width:18px;height:18px;border-radius:9px;display:flex;align-items:center;justify-content:center;padding:0 4px}.wc-status-dot{width:8px;height:8px;border-radius:50%;display:inline-block;margin-right:4px;animation:wcStatusPulse 2s infinite}.wc-status-dot.online{background:#22c55e}.wc-status-dot.busy{background:#ef4444}.wc-status-dot.offline{background:#ef4444}.wc-status-dot.away{background:#f59e0b}@keyframes wcStatusPulse{0%,100%{opacity:1;transform:scale(1)}50%{opacity:.5;transform:scale(1.3)}}@keyframes wcBtnBounceIn{0%{opacity:0;transform:scale(0.3)}50%{transform:scale(1.05)}70%{transform:scale(0.9)}100%{opacity:1;transform:scale(1)}}50%{box-shadow:0 4px 30px rgba(0,0,0,.4),0 0 0 8px rgba(255,255,255,.1)}100%{box-shadow:0 4px 16px rgba(0,0,0,.2)}}@keyframes wcStatusPulse{0%,100%{opacity:1;transform:scale(1)}50%{opacity:.5;transform:scale(1.3)}}@keyframes wcPulse{0%,100%{opacity:1}50%{opacity:.5}}.wc-recording{position:absolute;top:60px;left:50%;transform:translateX(-50%);background:#ef4444;color:white;padding:6px 16px;border-radius:16px;font-size:12px;display:flex;align-items:center;gap:6px;z-index:1000002;animation:wcPulse 1.5s infinite}.wc-recording-dot{width:8px;height:8px;background:white;border-radius:50%;animation:wcPulse 1s infinite}.wc-file-item{padding:6px 12px;background:' + theme.surface + ';border-bottom:1px solid ' + theme.border + ';display:flex;align-items:center;gap:8px;font-size:12px;color:' + theme.text + '}.wc-file-item button{background:none;border:none;color:' + theme.textSecondary + ';cursor:pointer;font-size:14px}.wc-file-drop{position:absolute;bottom:60px;left:12px;right:12px;height:60px;border:2px dashed ' + theme.primary + ';border-radius:12px;display:flex;align-items:center;justify-content:center;color:' + theme.primary + ';font-size:14px;z-index:1000001;background:' + theme.surface + '}.wc-file-drop.dragover{background:' + theme.primary + '20}.wc-sources{margin-top:6px}.wc-src-toggle{background:none;border:1px solid ' + theme.border + ';border-radius:4px;padding:2px 8px;font-size:11px;cursor:pointer;color:' + theme.textSecondary + '}.wc-src-items{display:none;margin-top:4px;padding:8px;background:' + theme.surface + ';border-radius:6px;font-size:12px}.wc-src-items.open{display:block}.wc-src-item{padding:4px 0;color:' + theme.textSecondary + '}.wc-src-item a{color:' + theme.primary + '}.wc-msg-timestamp{font-size:10px;color:' + theme.textSecondary + ';margin-top:4px;text-align:right}.@keyframes wcSlideIn{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:translateY(0)}}@keyframes wcBounce{0%,60%,100%{transform:translateY(0)}30%{transform:translateY(-8px)}}@keyframes wcBtnBounceIn{0%{opacity:0;transform:scale(0.3)}50%{transform:scale(1.05)}70%{transform:scale(0.9)}100%{opacity:1;transform:scale(1)}}50%{box-shadow:0 4px 30px rgba(0,0,0,.4),0 0 0 8px rgba(255,255,255,.1)}100%{box-shadow:0 4px 16px rgba(0,0,0,.2)}}@keyframes wcStatusPulse{0%,100%{opacity:1;transform:scale(1)}50%{opacity:.5;transform:scale(1.3)}}@keyframes wcPulse{0%,100%{opacity:1}50%{opacity:.5}}.wc-tooltip{padding:8px 14px;text-align:center;font-size:13px;color:' + theme.text + ';background:' + theme.bg + ';border-radius:12px;box-shadow:0 4px 12px rgba(0,0,0,.15);border:1px solid ' + theme.border + ';animation:wcTooltipFadeIn .8s ease-out .5s both;position:relative}.wc-tooltip-arrow{position:absolute;bottom:-6px;left:50%;transform:translateX(-50%);width:0;height:0;border-left:6px solid transparent;border-right:6px solid transparent;border-top:6px solid ' + theme.bg + '}@keyframes wcTooltipFadeIn{from{opacity:0;transform:translateX(-50%) translateY(8px)}to{opacity:1;transform:translateX(-50%) translateY(0)}}@keyframes wcSpringBounce{0%,100%{transform:translateY(0) scale(1)}40%{transform:translateY(-10px) scale(1.02)}60%{transform:translateY(-4px) scale(0.98)}80%{transform:translateY(-7px) scale(1.01)}}.wc-disclaimer{font-size:10px;color:' + theme.textSecondary + ';opacity:.6;text-align:center;padding:6px 8px;line-height:1.3}@media(max-width:768px){.wc-panel{border-radius:0!important;width:100vw!important;height:100vh!important}.wc-btn-wrap{bottom:12px!important;right:12px!important}.wc-panel .wc-input-area{padding:8px}.wc-panel .wc-messages{padding:8px}.wc-panel .wc-header{padding:10px 12px}.wc-disclaimer{font-size:9px;color:' + theme.textSecondary + ';opacity:.5;text-align:center;padding:4px 8px;line-height:1.2}';            if (config.customCSS) css += config.customCSS;
            var s = document.createElement('style'); s.id = id; s.textContent = css; document.head.appendChild(s);
        }

        // --- Main App ---
        function App(props) {
            var config = props.config;

            var _s1 = useState(false), open = _s1[0], setOpen = _s1[1];
            var _s2 = useState(null), sessionId = _s2[0], setSessionId = _s2[1];
            var _s3 = useState([]), messages = _s3[0], setMessages = _s3[1];
            var _s4 = useState(''), inputVal = _s4[0], setInputVal = _s4[1];
            var _s5 = useState(false), sending = _s5[0], setSending = _s5[1];
            var _s6 = useState(false), emojiOpen = _s6[0], setEmojiOpen = _s6[1];
            var _s7 = useState(false), dropdownOpen = _s7[0], setDropdownOpen = _s7[1];
            var _s8 = useState(false);
            var _s9 = useState(false), recording = _s9[0], setRecording = _s9[1];
            var _s10 = useState(loadConvs()), convs = _s10[0], setConvs = _s10[1];
            var _s11 = useState(false), quickHidden = _s11[0], setQuickHidden = _s11[1];
            var _s12 = useState(380), panelW = _s12[0], setPanelW = _s12[1];
            var _s13 = useState(600), panelH = _s13[0], setPanelH = _s13[1];
            var _s21 = useState(false), isMobile = _s21[0], setIsMobile = _s21[1];
            var _s14 = useState(0), unreadCount = _s14[0], setUnreadCount = _s14[1];
            var _s15 = useState(false), minimized = _s15[0], setMinimized = _s15[1];
            var _s16 = useState(null), dragFile = _s16[0], setDragFile = _s16[1];
            var _s17 = useState(config.status || 'online'), currentStatus = _s17[0], setWidgetStatus = _s17[1];
            var _s18 = useState(config), widgetConfig = _s18[0], setWidgetConfig = _s18[1];
            var _s19 = useState(getTheme(config)), theme = _s19[0], setTheme = _s19[1];
            var _s20 = useState({}), feedbackState = _s20[0], setFeedbackState = _s20[1];
            var _s22 = useState(true), tooltipVisible = _s22[0], setTooltipVisible = _s22[1];

            var messagesRef = useRef(null), inputRef = useRef(null), recognitionRef = useRef(null);
            var autoOpenTimer = useRef(null), fileInputRef = useRef(null);

            useEffect(function() {
                injectCSS(widgetConfig, theme);
            }, [widgetConfig, theme]);

            useEffect(function() {
                if (open && tooltipVisible) setTooltipVisible(false);
            }, [open]);

            useEffect(function() {
                setTimeout(function() { if (tooltipVisible) setTooltipVisible(false); }, 8000);
            }, []);

            useEffect(function() {
                setTheme(getTheme(widgetConfig));
            }, [widgetConfig]);

            useEffect(function() {
                if (open) {
                    fetch(API_BASE + 'api/widget/config')
                        .then(function(r) { return r.json(); })
                        .then(function(c) {
                            setWidgetConfig(c);
                        });
                }
            }, [open]);

            useEffect(function() {
                if (messagesRef.current) messagesRef.current.scrollTop = messagesRef.current.scrollHeight;
            }, [messages]);

            useEffect(function() {
                if (sessionId) { var loaded = loadMsgs(sessionId); if (loaded.length > 0) setMessages(loaded); }
            }, [sessionId]);

            useEffect(function() {
                var SR = window.SpeechRecognition || window.webkitSpeechRecognition;
                if (!SR) return;
                var rec = new SR(); rec.continuous = true; rec.interimResults = true;
                var fullTranscript = '';
                rec.onstart = function() { fullTranscript = ''; setRecording(true); };
                rec.onend = function() { setRecording(false); };
                rec.onresult = function(e) {
                    var transcript = '';
                    for (var i = e.resultIndex; i < e.results.length; i++) {
                        transcript += e.results[i][0].transcript;
                    }
                    fullTranscript = transcript;
                    setInputVal(fullTranscript);
                };
                rec.onerror = function() { setRecording(false); };
                recognitionRef.current = rec;
            }, []);

            useEffect(function() {
                if (widgetConfig.auto_open_delay && widgetConfig.auto_open_delay > 0 && !open) {
                    autoOpenTimer.current = setTimeout(function() { setOpen(true); }, widgetConfig.auto_open_delay * 1000);
                }
                return function() { if (autoOpenTimer.current) clearTimeout(autoOpenTimer.current); };
            }, []);

            useEffect(function() {
                function checkMobile() {
                    setIsMobile(window.innerWidth <= 768 || window.innerHeight <= 600);
                }
                checkMobile();
                window.addEventListener('resize', checkMobile);
                return function() { window.removeEventListener('resize', checkMobile); };
            }, []);

            useEffect(function() {
                if (widgetConfig.keyboard_shortcut) {
                    function handleKey(e) {
                        if (e.ctrlKey && e.shiftKey && e.key === 'K') { e.preventDefault(); setOpen(!open); }
                    }
                    document.addEventListener('keydown', handleKey);
                    return function() { document.removeEventListener('keydown', handleKey); };
                }
            }, [open, widgetConfig.keyboard_shortcut]);

            useEffect(function() {
                function fetchHealth() {
                    fetch(API_BASE + 'api/widget/health')
                        .then(function(r) { return r.json(); })
                        .then(function(data) {
                            setWidgetStatus(data.status || 'offline');
                        })
                        .catch(function() {
                            setWidgetStatus('offline');
                        });
                }
                fetchHealth();
                var healthInterval = setInterval(fetchHealth, 15000);
                return function() { clearInterval(healthInterval); };
            }, []);

            function newSession() {
                var id = 'sess_' + Date.now() + '_' + Math.random().toString(36).substr(2, 6);
                setSessionId(id); setMessages([]); setQuickHidden(false);
                setConvs(function(prev) { var updated = prev.filter(function(c) { return c.id !== id; }); saveConvs(updated); return updated; });
            }

            function switchSession(id) {
                setSessionId(id); setDropdownOpen(false);
                var loaded = loadMsgs(id); setMessages(loaded);
            }

            function createConv(id, firstMsg) {
                setConvs(function(prev) {
                    var updated = prev.filter(function(c) { return c.id !== id; });
                    updated.unshift({ id: id, first: firstMsg.substring(0, 50), ts: Date.now() });
                    if (updated.length > 20) updated = updated.slice(0, 20);
                    saveConvs(updated);
                    return updated;
                });
            }

            function exportConversation(id) {
                var msgs = loadMsgs(id);
                if (!msgs || msgs.length === 0) { alert('No messages to export'); return; }
                var text = msgs.map(function(m) { return (m.role === 'user' ? 'You' : 'Bot') + ': ' + m.text; }).join('\n\n');
                var blob = new Blob([text], { type: 'text/plain' });
                var url = URL.createObjectURL(blob);
                var a = document.createElement('a');
                a.href = url;
                a.download = 'conversation_' + new Date().toISOString().split('T')[0] + '.txt';
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
            }

            function sendMsg(text, file) {
                text = (text || '').trim();
                if (!text && !file) return;

                setInputVal(''); setEmojiOpen(false);
                if (!quickHidden) setQuickHidden(true);

                var displayText = text + (file ? ' \ud83d\udcce ' + file.name : '');
                var userMsg = { role: 'user', text: displayText, sources: null, file: file || null, ts: Date.now() };
                var newMsgs = messages.concat([userMsg]);
                setMessages(newMsgs); setSending(true);

                var sid = sessionId;
                if (!sid) {
                    sid = 'sess_' + Date.now() + '_' + Math.random().toString(36).substr(2, 6);
                    setSessionId(sid); createConv(sid, text || file.name);
                }
                saveMsgs(sid, newMsgs);
                setMessages(newMsgs.concat([{ role: 'typing', text: '', sources: null }]));

                var formData = new FormData();
                formData.append('message', text);
                formData.append('session_id', sid);
                if (file) formData.append('file', file);

               fetch(API_BASE + 'api/chat/stream', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ message: text, session_id: sid }) })
                .then(function(res) {
                    if (!res.ok) throw new Error('server error');
                    return res.text();
                }).then(function(text) {
                    var fullText = '';
                    var lines = text.split('\n');
                    for (var i = 0; i < lines.length; i++) {
                        var line = lines[i];
                        if (line.startsWith('data: ')) {
                            var data = line.slice(6);
                            if (data === '[DONE]') break;
                            try {
                                var parsed = JSON.parse(data);
                                if (parsed.token) {
                                    fullText += parsed.token;
                                }
                            } catch(e) {}
                        }
                    }
                    if (fullText) {
                        var finalMsgs = newMsgs.concat([{ role: 'bot', text: fullText, sources: null, ts: Date.now() }]);
                        setMessages(finalMsgs); saveMsgs(sid, finalMsgs); setSending(false);
                    } else {
                        throw new Error('no response');
                    }
                }).catch(function(e) {
                    console.log('Stream failed, using fallback:', e.message);
                    fetch(API_BASE + 'api/chat', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ message: text, session_id: sid }) })
                    .then(function(r) { return r.json(); }).then(function(data) {
                        var finalMsgs = newMsgs.concat([{ role: 'bot', text: data.response, sources: null, ts: Date.now() }]);
                        setMessages(finalMsgs); saveMsgs(sid, finalMsgs); setSending(false);
                    }).catch(function() {
                        var errMsgs = newMsgs.concat([{ role: 'bot', text: 'Sorry, I\'m having trouble connecting.', sources: null, ts: Date.now() }]);
                        setMessages(errMsgs); setSending(false);
                    });
                });
            }

            function handleFileDrop(e) {
                e.preventDefault(); setDragFile(e.dataTransfer.files[0]);
            }

            function toggleDropdown() { setDropdownOpen(!dropdownOpen); }

            function handleCopy(text, btn) {
                navigator.clipboard.writeText(text).then(function() { btn.textContent = 'Copied!'; setTimeout(function() { btn.textContent = 'Copy'; }, 2000); });
            }

            var headerStyle = { background: theme.headerGrad };
            var sendStyle = { background: theme.headerGrad };
            var btnSize = widgetConfig.button_size === 'small' ? 48 : widgetConfig.button_size === 'large' ? 72 : 60;
            var btnRadius = widgetConfig.button_shape === 'square' ? '0' : widgetConfig.button_shape === 'rounded-square' ? '16px' : '50%';
            var effectiveW, effectiveH;
            if (isMobile) {
                var vw = window.innerWidth, vh = window.innerHeight;
                effectiveW = Math.min(vw - 16, 420);
                effectiveH = Math.min(vh - 80, 936);
            } else {
                effectiveW = panelW;
                effectiveH = panelH;
            }
            var panelBottom = widgetConfig.position && widgetConfig.position.indexOf('top') !== -1 ? 'auto' : (isMobile ? '8px' : '72px');
            var panelTop = widgetConfig.position && widgetConfig.position.indexOf('top') !== -1 ? '8px' : 'auto';
            var panelRight = widgetConfig.position === 'bottom-left' || widgetConfig.position === 'top-left' ? 'auto' : (isMobile ? '8px' : '20px');
            var panelLeft = widgetConfig.position === 'bottom-left' || widgetConfig.position === 'top-left' ? '8px' : 'auto';
            var panelStyle = { width: effectiveW + 'px', height: effectiveH + 'px', display: (open && !minimized) ? 'flex' : 'none', position: 'fixed', bottom: panelBottom, top: panelTop, left: panelLeft, right: panelRight };

            var typingClass = 'wc-typing ' + (widgetConfig.typing_animation || 'dots');

            return h(Fragment, null,
                // Panel
                h('div', { style: panelStyle, className: 'wc-panel' },
                    !isMobile ? h('div', { className: 'wc-resize',
                        onMouseDown: function(e) {
                            var startX = e.clientX, startY = e.clientY, startW = panelW, startH = panelH;
                            function onMove(ev) { var dx = ev.clientX - startX, dy = ev.clientY - startY; setPanelW(Math.max(280, Math.min(600, startW - dx))); setPanelH(Math.max(300, startH + dy)); }
                            function onUp() { document.removeEventListener('mousemove', onMove); document.removeEventListener('mouseup', onUp); }
                            document.addEventListener('mousemove', onMove); document.addEventListener('mouseup', onUp);
                        }
                    }) : null,

                    // Header
                    h('div', { style: headerStyle, className: 'wc-header' },
                        h('div', { className: 'wc-header-left' },
                            widgetConfig.logo ? h('img', { src: widgetConfig.logo, className: 'wc-header-logo', alt: 'Logo' }) : null,
                            h('div', { className: 'wc-header-info' },
                                h('h3', null, (widgetConfig.company_name ? widgetConfig.company_name + ' - ' : '') + widgetConfig.greeting),
                                h('span', null, widgetConfig.show_status ? h(Fragment, null, h('span', { className: 'wc-status-dot ' + currentStatus }), currentStatus.charAt(0).toUpperCase() + currentStatus.slice(1)) : 'Online')
                            )
                        ),
                        h('div', { className: 'wc-header-btns' },
                            h('div', { style: { position: 'relative' } },
                                h('button', { className: 'wc-hbtn', onClick: toggleDropdown, title: 'Conversations' },
                                    h('svg', { viewBox: '0 0 24 24' }, h('path', { d: 'M3 13h2v-2H3v2zm0 4h2v-2H3v2zm0-8h2V7H3v2zm4 4h14v-2H7v2zm0 4h14v-2H7v2zM7 7v2h14V7H7z' }))
                                ),
                                dropdownOpen ? h('div', { className: 'wc-dropdown open' },
                                    h('div', { className: 'wc-dd-header' },
                                        h('span', null, 'Conversations'),
                                        h('button', { className: 'wc-dd-new', onClick: function() { newSession(); toggleDropdown(); }, title: 'New chat' }, '+')
                                    ),
                                    convs.slice(0, 15).map(function(c) {
                                        return h('div', { key: c.id, className: 'wc-dd-item' + (c.id === sessionId ? ' active' : ''), onClick: function() { switchSession(c.id); }, title: c.first },
                                            h('span', { style: { flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' } }, c.first || 'New chat'),
                                            h('button', { onClick: function(e) { e.stopPropagation(); exportConversation(c.id); }, style: { background: 'none', border: 'none', cursor: 'pointer', padding: '2px 4px', color: theme.textSecondary, marginLeft: '4px', fontSize: '14px' }, title: 'Export' }, h('svg', { width: '14', height: '14', viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', strokeWidth: '2', strokeLinecap: 'round', strokeLinejoin: 'round' }, h('path', { d: 'M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4' }), h('polyline', { points: '7 10 12 15 17 10' }), h('line', { x1: '12', y1: '15', x2: '12', y2: '3' })))
                                        );
                                    })
                                ) : null
                            ),
                            h('button', { className: 'wc-hbtn', onClick: function() { if (widgetConfig.minimize_to_icon) { setMinimized(true); setOpen(false); } else { setOpen(false); } }, title: 'Minimize/Close' },
                                h('svg', { viewBox: '0 0 24 24' }, h('path', { d: 'M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z' }))
                            ),
                            widgetConfig.show_admin_button !== false ? h('button', { className: 'wc-hbtn', onClick: function() { window.open(window.location.origin + '/admin', '_blank'); }, title: 'Open Admin Panel' },
                                h('svg', { viewBox: '0 0 24 24' }, h('path', { d: 'M14 2H6c-1.1 0-2 .9-2 2v16c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V8l-6-6zm4 18H6V4h12v16z M13 9V3.5L18.5 9H13z' }))
                            ) : null
                        )
                    ),

                    // Recording indicator
                    recording ? h('div', { className: 'wc-recording active' }, h('div', { className: 'wc-recording-dot' }), 'Listening...') : null,

                    // Messages
                    h('div', { ref: messagesRef, className: 'wc-messages',
                        onDragOver: function(e) { e.preventDefault(); setDragFile({ isDrag: true }); },
                        onDragLeave: function() { setDragFile(null); },
                        onDrop: function(e) { e.preventDefault(); setDragFile(e.dataTransfer.files[0]); }
                    },
                        messages.length === 0 ? h('div', { className: 'wc-empty' },
                            h('div', { className: 'emoji' }, '\ud83d\udc4b'),
                            h('h3', null, 'Welcome!'),
                            h('p', null, 'How can I help you today?')
                        ) : messages.map(function(msg, i) {
                            if (msg.role === 'typing') {
                                return h('div', { key: i, className: 'wc-msg' },
                                    h('div', { className: 'wc-msg-bot-row' },
                                        h('div', { className: 'wc-msg-avatar' }, widgetConfig.logo ? h('img', { src: widgetConfig.logo, style: { width: '100%', height: '100%', objectFit: 'cover', borderRadius: '8px' } }) : BotIcon()),
                                        h('div', { className: 'wc-msg-inner' }, h('div', { className: typingClass }, h('span', null), h('span', null), h('span', null)))
                                    )
                                );
                            }
                            if (msg.role === 'streaming') {
                                return h('div', { key: i, className: 'wc-msg' },
                                    h('div', { className: 'wc-msg-bot-row' },
                                        h('div', { className: 'wc-msg-avatar' }, widgetConfig.logo ? h('img', { src: widgetConfig.logo, style: { width: '100%', height: '100%', objectFit: 'cover', borderRadius: '8px' } }) : BotIcon()),
                                        h('div', { className: 'wc-msg-inner', dangerouslySetInnerHTML: { __html: renderMarkdown(msg.text, theme.isDark) } })
                                    )
                                );
                            }
                            var isUser = msg.role === 'user';
                            return h('div', { key: i, className: 'wc-msg' },
                                h('div', { className: 'wc-msg-' + (isUser ? 'user' : 'bot') + '-row' },
                                    h('div', { className: 'wc-msg-avatar' }, isUser ? UserIcon() : (widgetConfig.logo ? h('img', { src: widgetConfig.logo, style: { width: '100%', height: '100%', objectFit: 'cover', borderRadius: '8px' } }) : BotIcon())),
                                    h('div', null,
                                        h('div', { className: 'wc-msg-inner', dangerouslySetInnerHTML: { __html: isUser ? msg.text.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/\n/g,'<br/>') : renderMarkdown(msg.text, theme.isDark) } }),
                                        widgetConfig.show_timestamps && msg.ts ? h('div', { className: 'wc-msg-timestamp' }, formatTime(msg.ts)) : null,
                                        !isUser ? h(Fragment, null,
                                             widgetConfig.show_source_citations && msg.sources && msg.sources.length > 0 ?
                                                 h('div', { className: 'wc-sources' },
                                                     h('button', { className: 'wc-src-toggle', onClick: function() { var items = document.querySelector('.wc-src-items'); if (items) items.classList.toggle('open'); } }, 'Sources (' + msg.sources.length + ')'),
                                                     h('div', { className: 'wc-src-items' },
                                                         msg.sources.map(function(s, j) { var srcText = s.source || s.url || 'Document'; return h('div', { key: j, className: 'wc-src-item' }, srcText.indexOf('http') === 0 ? h('a', { href: srcText, target: '_blank' }, srcText) : srcText); })
                                                     )
                                                 ) : null,
                                             h('div', { className: 'wc-msg-actions' },
                                                 h('button', { className: 'wc-mact', onClick: function(e) { handleCopy(msg.text, e.target); } }, 'Copy'),
                                                 h('button', { className: 'wc-mact' + (feedbackState[i] === 'up' ? ' liked' : ''), onClick: function() { setFeedbackState(function(prev) { var n = Object.assign({}, prev); if (n[i] === 'up') { delete n[i]; } else { n[i] = 'up'; } return n; }); } }, '\ud83d\udc4d'),
                                                 h('button', { className: 'wc-mact' + (feedbackState[i] === 'down' ? ' disliked' : ''), onClick: function() { setFeedbackState(function(prev) { var n = Object.assign({}, prev); if (n[i] === 'down') { delete n[i]; } else { n[i] = 'down'; } return n; }); } }, '\ud83d\udc4e')
                                            )
                                        ) : null
                                    )
                                )
                            );
                        })
                    ),

                    // Quick replies
                    !quickHidden && widgetConfig.show_quick_replies ? h('div', { className: 'wc-quick' },
                        (widgetConfig.quick_replies || []).map(function(r) { return h('button', { key: r, className: 'wc-quick-btn', onClick: function() { sendMsg(r); } }, r); })
                    ) : null,

                    // File drop zone
                    dragFile && dragFile.isDrag ? h('div', { className: 'wc-file-drop dragover' }, 'Drop file here to upload') : null,
                    dragFile && !dragFile.isDrag ? h('div', { className: 'wc-file-item' },
                        h('span', null, '\ud83d\udcce ' + dragFile.name),
                        h('button', { onClick: function() { setDragFile(null); } }, '\u2715')
                    ) : null,

                    // Input area
                    h('div', { className: 'wc-input-area',
                        onDragOver: function(e) { e.preventDefault(); setDragFile({ isDrag: true }); },
                        onDrop: function(e) { e.preventDefault(); setDragFile(e.dataTransfer.files[0]); }
                    },
                        widgetConfig.show_emoji_picker ? h('button', { className: 'wc-emoji-btn', onClick: function() { setEmojiOpen(!emojiOpen); }, title: 'Emoji' }, '\ud83d\ude0a') : null,
                        h('button', { className: 'wc-mic-btn' + (recording ? ' recording' : ''), onClick: function() { var rec = recognitionRef.current; if (!rec) return; if (recording) rec.stop(); else rec.start(); }, title: 'Voice input' },
                            recording ? h('svg', { viewBox: '0 0 24 24', fill: 'currentColor' }, h('rect', { x: '6', y: '6', width: '12', height: '12', rx: '2' }))
                              : h('svg', { viewBox: '0 0 24 24', fill: 'currentColor' }, h('path', { d: 'M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z' }))
                        ),
                        h('input', { ref: inputRef, className: 'wc-input', placeholder: 'Type a message...', value: inputVal, onChange: function(e) { setInputVal(e.target.value); }, onKeyDown: function(e) { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMsg(inputVal); } }, disabled: sending }),
                        h('button', { className: 'wc-send', style: sendStyle, onClick: function() { sendMsg(inputVal, dragFile && !dragFile.isDrag ? dragFile : null); setDragFile(null); }, disabled: sending || (!inputVal.trim() && !dragFile) },
                            h('svg', { viewBox: '0 0 24 24' }, h('path', { d: 'M2.01 21L23 12 2.01 3 2 10l15 2-15 2z' }))
                        ),
                        emojiOpen ? h('div', { className: 'wc-emoji-picker open' },
                            EMOJIS.map(function(em) { return h('span', { key: em, className: 'wc-emoji-opt', onClick: function() { setInputVal(inputVal + em); if (inputRef.current) inputRef.current.focus(); } }, em); })
                        ) : null
                    ),

                    // Disclaimer
                    h('div', { className: 'wc-disclaimer' }, 'WebAI Chat can make mistakes. Double-check replies.')
                ),

                // Chat Button
                h('div', { className: 'wc-btn-wrap', style: { display: (open && !minimized) ? 'none' : 'block' } },
                    h('button', { className: 'wc-btn', onClick: function() { setOpen(!open); setMinimized(false); if (!open) setUnreadCount(0); }, title: 'Open chat' },
                        open ? h('svg', { viewBox: '0 0 24 24' }, h('path', { d: 'M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z' }))
                          : widgetConfig.logo ? h('img', { src: widgetConfig.logo, style: { width: '100%', height: '100%', objectFit: 'cover', borderRadius: btnRadius } }) : ChevronIcon(),
                        widgetConfig.unread_count && unreadCount > 0 ? h('div', { className: 'wc-badge' }, unreadCount > 9 ? '9+' : unreadCount) : null
                    )
                )
            );
        }

        // --- Mount ---
        function mountWidget(config) {
            var mountId = 'wc-widget-root'; var existing = document.getElementById(mountId); if (existing) existing.remove();
            var container = document.createElement('div'); container.id = mountId; document.body.appendChild(container);
            ReactDOM.render(h(App, { config: config }), container);

            document.addEventListener('keydown', function(e) {
                if (e.key === 'Escape') { var btn = document.querySelector('.wc-btn'); if (btn) btn.click(); }
            });

            window._webaiToggle = function() { var btn = document.querySelector('.wc-btn'); if (btn) btn.click(); };
            window._webaiQuickReply = function(text) { var btns = document.querySelectorAll('.wc-quick-btn'); btns.forEach(function(b) { if (b.textContent === text) b.click(); }); };
        }

        // --- Get config ---
        function getConfig() {
            return fetch(API_BASE + 'api/widget/config').then(function(r) { return r.json(); }).catch(function() { return DEFAULTS; });
        }

        function mergeConfig(serverConfig) {
            var merged = {};
            for (var key in DEFAULTS) { merged[key] = DEFAULTS[key]; }
            for (var key in serverConfig) { if (serverConfig[key] !== null && serverConfig[key] !== undefined && serverConfig[key] !== '') { merged[key] = serverConfig[key]; } }
            return merged;
        }

        getConfig().then(function(serverConfig) { mountWidget(mergeConfig(serverConfig)); });
    }

    })();
