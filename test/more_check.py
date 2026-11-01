# More page check (Oct 31 2026): category buttons, one h1 per page, focus to the heading on open, Back and Escape return
# focus to the category, Admin only for the owner and moderators, the Mode line, blocked people in Privacy & safety.
# Usage: python3 test/more_check.py <home> <seed json from test/seed-min.mjs plus "tag"> <outdir>

import sys, json
from playwright.sync_api import sync_playwright
home, seedf, outdir = sys.argv[1:4]
seed = json.load(open(seedf))
res = []
def ok(c, m): res.append(('PASS' if c else 'FAIL') + ' ' + m)
def active(pg): return pg.evaluate("(() => { const e = document.activeElement; return (e.id||'') + '|' + (e.tagName) + '|' + (e.textContent||'').trim().slice(0,60); })()")
with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={'width': 390, 'height': 844}, bypass_csp=True)
    pg = ctx.new_page()
    errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(home + '/'); pg.wait_for_selector('#in-key')
    pg.fill('#in-key', seed['owner_nsec']); pg.click('button:has-text("Sign in")')
    pg.wait_for_function("location.hash === '#dreamline'", timeout=15000)
    navs = pg.eval_on_selector_all('#nav a', 'els => els.map(e => e.firstChild.textContent)')
    ok(navs == ['Dreamline','Discover','Search','Chats','Inbox','More'], 'nav is ' + ', '.join(navs))
    pg.click('#nav a[href="#more"]'); pg.wait_for_selector('button.cat')
    ok(pg.locator('h1').count() == 1 and pg.inner_text('h1') == 'More', 'More h1')
    ok('More' in active(pg), 'focus on More heading: ' + active(pg))
    ok(pg.get_attribute('#nav a[href="#more"]', 'aria-current') == 'page', 'More is current page')
    mode = pg.inner_text('.mode'); ok('Mode: Looscid server' in mode and '@2three1y' in mode, 'mode line: ' + mode)
    cats = pg.eval_on_selector_all('button.cat', "els => els.map(e => e.querySelector('.cat-name').textContent + ' -- ' + document.getElementById(e.getAttribute('aria-describedby')).textContent)")
    for c in cats: res.append('  owner cat: ' + c)
    ok(any(c.startswith('Admin') for c in cats), 'owner sees Admin')
    snap = pg.accessibility.snapshot() if hasattr(pg, 'accessibility') else None
    pg.screenshot(path=outdir + '/more-owner.png', full_page=True)
    for cid, h1 in [('looscidid','LooscidID'),('server','Server'),('privacy','Privacy & safety'),('admin','Admin'),('look','App settings'),('help','Help & about')]:
        pg.click('#cat-' + cid); pg.wait_for_function("document.querySelector('h1').textContent === %s" % json.dumps(h1))
        pg.wait_for_timeout(500)
        ok(pg.locator('h1').count() == 1, h1 + ': one h1')
        ok(h1 in active(pg), h1 + ': focus on heading (' + active(pg) + ')')
        ok(pg.locator('button.back').count() == 1, h1 + ': Back button')
        pg.screenshot(path=outdir + '/sub-' + cid + '.png', full_page=True)
        if cid in ('looscidid', 'admin', 'look'):
            pg.keyboard.press('Escape')
        else:
            pg.click('button.back')
        pg.wait_for_function("location.hash === '#more'"); pg.wait_for_timeout(300)
        ok(active(pg).startswith('cat-' + cid), h1 + ': back focuses its category (' + active(pg) + ')')
    pg.goto(home + '/#mod'); pg.wait_for_timeout(1200); ok(pg.evaluate('location.hash') == '#more/admin' and 'Open reports' in pg.inner_text('#view'), 'old #mod goes to Admin')
    pg.goto(home + '/#settings'); pg.wait_for_timeout(1200); ok(pg.evaluate('location.hash') == '#more/looscidid', 'old #settings goes to Looscid account')
    # Escape inside a text field does not leave
    pg.click('#s-name'); pg.keyboard.press('Escape'); pg.wait_for_timeout(300); ok(pg.evaluate('location.hash') == '#more/looscidid', 'Escape in a text field stays')
    # member
    ctx2 = b.new_context(viewport={'width': 390, 'height': 844}, bypass_csp=True); m = ctx2.new_page(); m.on('pageerror', lambda e: errs.append('member: ' + str(e)))
    m.goto(home + '/#join=' + seed['invites'][seed.get('inv',0)]); m.wait_for_selector('#j-handle')
    m.fill('#j-handle', 'menutest' + seed['tag']); m.fill('#j-name', 'Menu Test'); m.check('#j-age'); m.click('button:has-text("Join")')
    m.wait_for_function("location.hash === '#more/looscidid'", timeout=20000); m.wait_for_selector('#s-name')
    ok(m.inner_text('h1') == 'LooscidID', 'new member lands on Looscid account')
    m.click('button.back'); m.wait_for_selector('button.cat')
    mc = m.eval_on_selector_all('button.cat .cat-name', 'els => els.map(e => e.textContent)')
    ok('Admin' not in mc, 'member does not see Admin: ' + ', '.join(mc))
    m.goto(home + '/#more/admin'); m.wait_for_timeout(1200); ok(m.evaluate('location.hash') == '#more', 'member #more/admin goes to More')
    # block owner, see in privacy, unblock
    m.goto(home + '/#@2three1y'); m.wait_for_selector('button:has-text("Block")')
    m.once('dialog', lambda d: d.accept()); m.click('button:has-text("Block")'); m.wait_for_timeout(1200)
    m.goto(home + '/#more/privacy'); m.wait_for_selector('button:has-text("Unblock")', timeout=10000)
    ok(True, 'blocked person shows in Privacy & safety')
    m.click('button:has-text("Unblock")'); m.wait_for_selector("text=You have not blocked anyone.", timeout=10000); ok(True, 'Unblock works from Privacy & safety')
    m.goto(home + '/#more'); m.wait_for_selector('.mode'); ok('@menutest' in m.inner_text('.mode'), 'member mode line names their handle')
    m.screenshot(path=outdir + '/more-member.png', full_page=True)
    ok(not errs, 'no page errors ' + '; '.join(errs))
    b.close()
print('\n'.join(res))
