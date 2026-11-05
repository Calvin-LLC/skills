# Accessibility Patterns

Reusable accessible code patterns for WCAG 2.2 Level A + AA. Copy and adapt.

---

## 1. Skip Link

```html
<a href="#main" class="skip-link">Skip to main content</a>
<!-- ... header, nav ... -->
<main id="main">...</main>

<style>
.skip-link {
    position: absolute;
    left: -9999px;
    top: 0;
    z-index: 9999;
    padding: 1rem;
    background: #000;
    color: #fff;
}
.skip-link:focus { left: 0; }
</style>
```

---

## 2. Page Template

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Page Title - Site Name</title>
</head>
<body>
    <a href="#main" class="skip-link">Skip to main content</a>
    <header>
        <nav aria-label="Main navigation">
            <ul>
                <li><a href="/">Home</a></li>
                <li><a href="/about">About</a></li>
            </ul>
        </nav>
    </header>
    <main id="main">
        <h1>Page Title</h1>
    </main>
    <footer>...</footer>
</body>
</html>
```

---

## 3. Accessible Form

```html
<form action="/submit" method="post">
    <div class="form-group">
        <label for="name">Full Name <span aria-hidden="true">*</span></label>
        <input type="text" id="name" name="name" required aria-required="true" autocomplete="name">
    </div>

    <div class="form-group">
        <label for="email">Email <span aria-hidden="true">*</span></label>
        <input type="email" id="email" name="email" required aria-required="true"
               aria-describedby="email-help" autocomplete="email">
        <p id="email-help" class="help-text">We'll never share your email.</p>
    </div>

    <div class="form-group">
        <label for="phone">Phone</label>
        <input type="tel" id="phone" name="phone"
               aria-invalid="true" aria-describedby="phone-error" autocomplete="tel">
        <p id="phone-error" class="error" role="alert">
            Please enter a valid phone number (e.g., 555-123-4567)
        </p>
    </div>

    <fieldset>
        <legend>Preferred Contact Method</legend>
        <input type="radio" id="c-email" name="contact" value="email">
        <label for="c-email">Email</label>
        <input type="radio" id="c-phone" name="contact" value="phone">
        <label for="c-phone">Phone</label>
    </fieldset>

    <button type="submit">Submit</button>
</form>
```

---

## 4. Modal/Dialog with Focus Trap

```html
<button type="button" id="open-modal">Open Dialog</button>

<div id="modal" role="dialog" aria-modal="true"
     aria-labelledby="modal-title" aria-describedby="modal-desc" hidden>
    <h2 id="modal-title">Confirm Action</h2>
    <p id="modal-desc">Are you sure you want to delete this item?</p>
    <button type="button" id="cancel-btn">Cancel</button>
    <button type="button" id="confirm-btn">Delete</button>
    <button type="button" class="close-btn" aria-label="Close dialog">&times;</button>
</div>

<script>
const modal = document.getElementById('modal');
const openBtn = document.getElementById('open-modal');
let previousFocus;

function openModal() {
    previousFocus = document.activeElement;
    modal.hidden = false;
    modal.querySelector('button').focus();
    document.body.style.overflow = 'hidden';
}

function closeModal() {
    modal.hidden = true;
    document.body.style.overflow = '';
    previousFocus?.focus();
}

modal.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') { closeModal(); return; }
    if (e.key !== 'Tab') return;

    const focusable = modal.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    const first = focusable[0];
    const last = focusable[focusable.length - 1];

    if (e.shiftKey && document.activeElement === first) {
        last.focus(); e.preventDefault();
    } else if (!e.shiftKey && document.activeElement === last) {
        first.focus(); e.preventDefault();
    }
});

openBtn.addEventListener('click', openModal);
modal.querySelector('.close-btn').addEventListener('click', closeModal);
document.getElementById('cancel-btn').addEventListener('click', closeModal);
</script>
```

---

## 5. Dropdown Menu with Arrow Keys

```html
<div class="dropdown">
    <button type="button" id="menu-btn" aria-haspopup="true"
            aria-expanded="false" aria-controls="menu">
        Menu <span aria-hidden="true">&#9660;</span>
    </button>
    <ul id="menu" role="menu" aria-labelledby="menu-btn" hidden>
        <li role="none"><a role="menuitem" href="/profile">Profile</a></li>
        <li role="none"><a role="menuitem" href="/settings">Settings</a></li>
        <li role="none"><button role="menuitem" type="button">Logout</button></li>
    </ul>
</div>

<script>
const btn = document.getElementById('menu-btn');
const menu = document.getElementById('menu');

btn.addEventListener('click', () => {
    const expanded = btn.getAttribute('aria-expanded') === 'true';
    btn.setAttribute('aria-expanded', !expanded);
    menu.hidden = expanded;
    if (!expanded) menu.querySelector('[role="menuitem"]').focus();
});

menu.addEventListener('keydown', (e) => {
    const items = [...menu.querySelectorAll('[role="menuitem"]')];
    const i = items.indexOf(document.activeElement);
    if (e.key === 'ArrowDown') { e.preventDefault(); items[(i + 1) % items.length].focus(); }
    if (e.key === 'ArrowUp') { e.preventDefault(); items[(i - 1 + items.length) % items.length].focus(); }
    if (e.key === 'Escape') { btn.setAttribute('aria-expanded', 'false'); menu.hidden = true; btn.focus(); }
});
</script>
```

---

## 6. Tabs

```html
<div class="tabs">
    <div role="tablist" aria-label="Product Info">
        <button role="tab" id="tab-1" aria-selected="true" aria-controls="panel-1">Description</button>
        <button role="tab" id="tab-2" aria-selected="false" aria-controls="panel-2" tabindex="-1">Specs</button>
        <button role="tab" id="tab-3" aria-selected="false" aria-controls="panel-3" tabindex="-1">Reviews</button>
    </div>
    <div role="tabpanel" id="panel-1" aria-labelledby="tab-1">...</div>
    <div role="tabpanel" id="panel-2" aria-labelledby="tab-2" hidden>...</div>
    <div role="tabpanel" id="panel-3" aria-labelledby="tab-3" hidden>...</div>
</div>

<script>
const tabs = document.querySelectorAll('[role="tab"]');
const panels = document.querySelectorAll('[role="tabpanel"]');

tabs.forEach(tab => {
    tab.addEventListener('click', () => {
        tabs.forEach(t => { t.setAttribute('aria-selected', 'false'); t.setAttribute('tabindex', '-1'); });
        panels.forEach(p => p.hidden = true);
        tab.setAttribute('aria-selected', 'true');
        tab.removeAttribute('tabindex');
        document.getElementById(tab.getAttribute('aria-controls')).hidden = false;
    });
    tab.addEventListener('keydown', (e) => {
        const i = [...tabs].indexOf(tab);
        let n;
        if (e.key === 'ArrowRight') n = (i + 1) % tabs.length;
        else if (e.key === 'ArrowLeft') n = (i - 1 + tabs.length) % tabs.length;
        else return;
        tabs[n].click();
        tabs[n].focus();
    });
});
</script>
```

---

## 7. Alert/Toast (Live Regions)

```html
<!-- Static alert -->
<div role="status" aria-live="polite">Settings saved successfully.</div>
<div role="alert" aria-live="assertive">Error: Connection lost.</div>

<!-- Dynamic toast -->
<div id="toast-container" aria-live="polite" aria-atomic="true"></div>

<script>
function showToast(message) {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 5000);
}
</script>
```

---

## 8. Data Table

```html
<table>
    <caption>Monthly Sensor Readings</caption>
    <thead>
        <tr>
            <th scope="col">Date</th>
            <th scope="col">Moisture (%)</th>
            <th scope="col">Temperature</th>
            <th scope="col">Status</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <th scope="row">Jan 1</th>
            <td>45</td>
            <td>22</td>
            <td><span aria-label="Status: OK">[OK] Normal</span></td>
        </tr>
    </tbody>
</table>
```

---

## 9. Tooltip/Popover (1.4.13 Compliant)

Three requirements: **dismissible** (Escape), **hoverable** (pointer can reach it), **persistent** (stays until dismissed).

```html
<div class="tooltip-container">
    <button type="button" aria-describedby="tip-1" class="tooltip-trigger">Help</button>
    <div id="tip-1" role="tooltip" class="tooltip">
        This controls notification frequency.
    </div>
</div>

<style>
.tooltip { display: none; position: absolute; background: #333; color: #fff; padding: 0.5rem 1rem; }
.tooltip-trigger:hover + .tooltip:not(.dismissed),
.tooltip-trigger:focus + .tooltip:not(.dismissed),
.tooltip:hover:not(.dismissed) { display: block; }
</style>

<script>
// Dismiss on Escape by removing the show class
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        document.querySelectorAll('.tooltip').forEach(t => t.classList.add('dismissed'));
    }
});
// Re-show on next hover/focus cycle
document.querySelectorAll('.tooltip-trigger').forEach(trigger => {
    ['mouseenter', 'focus'].forEach(evt =>
        trigger.addEventListener(evt, () => {
            trigger.nextElementSibling.classList.remove('dismissed');
        })
    );
});
</script>
```

---

## 10. Drag-and-Drop with Alternative (2.5.7)

```html
<ul class="sortable" role="listbox" aria-label="Reorder tasks">
    <li role="option" draggable="true">
        <span>Task 1: Design mockups</span>
        <button aria-label="Move Task 1 up" onclick="moveItem(this.closest('li'), -1)">Up</button>
        <button aria-label="Move Task 1 down" onclick="moveItem(this.closest('li'), 1)">Down</button>
    </li>
    <li role="option" draggable="true">
        <span>Task 2: Write tests</span>
        <button aria-label="Move Task 2 up" onclick="moveItem(this.closest('li'), -1)">Up</button>
        <button aria-label="Move Task 2 down" onclick="moveItem(this.closest('li'), 1)">Down</button>
    </li>
</ul>
<div id="sort-status" role="status" aria-live="polite" class="visually-hidden"></div>

<script>
function moveItem(item, dir) {
    const list = item.parentNode;
    const items = [...list.children];
    const i = items.indexOf(item);
    const target = i + dir;
    if (target < 0 || target >= items.length) return;
    dir === -1 ? list.insertBefore(item, items[target]) : list.insertBefore(item, items[target].nextSibling);
    document.getElementById('sort-status').textContent =
        `${item.querySelector('span').textContent} moved to position ${target + 1}`;
    item.querySelector(`[aria-label*="${dir === -1 ? 'up' : 'down'}"]`).focus();
}
</script>
```

---

## 11. Authentication (3.3.8)

```html
<form action="/login" method="post">
    <label for="login-email">Email</label>
    <input type="email" id="login-email" autocomplete="username" required>

    <label for="login-pass">Password</label>
    <input type="password" id="login-pass" autocomplete="current-password" required>

    <button type="submit">Sign In</button>
</form>

<!-- Alternatives -->
<button type="button" onclick="startWebAuthn()">Sign in with passkey</button>
```

Key rules: allow paste in password fields, use proper `autocomplete`, no text CAPTCHAs, provide passkey/magic-link alternatives.

---

## 12. Consistent Help (3.2.6)

Place help mechanism in the same relative position on every page:

```html
<header>
    <nav aria-label="Main">...</nav>
    <a href="/help">Help</a>
</header>
<!-- OR -->
<footer>
    <a href="/faq">FAQ</a>
    <a href="/contact">Contact</a>
    <a href="tel:+18005551234">1-800-555-1234</a>
</footer>
```

---

## 13. Focus Styles

```css
:focus-visible {
    outline: 2px solid #0d6efd;
    outline-offset: 2px;
}
button:focus-visible {
    outline: 2px solid #0d6efd;
    box-shadow: 0 0 0 4px rgba(13, 110, 253, 0.25);
}
input:focus-visible, select:focus-visible, textarea:focus-visible {
    outline: none;
    border-color: #0d6efd;
    box-shadow: 0 0 0 3px rgba(13, 110, 253, 0.25);
}
```

---

## 14. Reduced Motion

```css
.toast { animation: toast-in 300ms cubic-bezier(0.16, 1, 0.3, 1); }
@media (prefers-reduced-motion: reduce) {
    .toast { animation: toast-fade 150ms linear; }
}
@keyframes toast-in { from { opacity: 0; transform: translateY(12px); } }
@keyframes toast-fade { from { opacity: 0; } }
```

Drop movement, keep the fade so the state change stays visible.

---

## 15. Touch Targets

```css
/* WCAG 2.2 minimum: 24x24 CSS px. Recommended: 48px */
button, a, [role="button"] {
    min-width: 48px;
    min-height: 48px;
}
.icon-btn {
    padding: 12px;
    min-width: 48px;
    min-height: 48px;
}
/* 8px minimum spacing */
.btn-group > * + * { margin-left: 8px; }

@media (pointer: coarse) {
    .btn { min-height: 48px; padding: 12px 24px; }
}
```

---

## 16. Reflow Layout (1.4.10)

```css
.container { max-width: 100%; padding: 1rem; overflow-wrap: break-word; }
.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 20rem), 1fr)); gap: 1rem; }
img { max-width: 100%; height: auto; }
```

Content must work at 320 CSS px without horizontal scroll. Exception: data tables, maps, toolbars.

---

## Visually Hidden Utility

```css
.visually-hidden {
    position: absolute;
    width: 1px; height: 1px;
    padding: 0; margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    white-space: nowrap; border: 0;
}
```
