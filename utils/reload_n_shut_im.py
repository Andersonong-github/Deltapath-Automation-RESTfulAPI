#utils/reload_n_shut_im.py

def reload_and_shutdown_im(page, log_func):
  """
  Module reload N close IM panel:Execute After Evert Task Finish
  1. reload Browser
  2. awaiting html loading
  3. IM Panel Pop-out
  4. Shut IM Panel
  """
  try:
      log_func("====================================================")
      log_func("🔄 reload + Shut IM Panel：Execute After Every Task Finish")
        log_func("==================================================")

        # 刷新
        page.reload()
        page.wait_for_load_state("networkidle", timeout=10000)
        page.wait_for_timeout(2000)

        # 等待IM延迟弹出（关键！）
        log_func("⏳ Awaiting IM Panel Loading...")
        page.wait_for_timeout(2000)

        # 暴力关闭所有窗口右上角 X
        log_func("🔨 Shut Instant Messaging Panel...")
        close_buttons = page.locator(".x-tool-close").all()

        for btn in close_buttons:
            try:
                if btn.is_visible(timeout=1000):
                    btn.click(force=True)
                    page.wait_for_timeout(300)
            except:
                continue

        log_func("✅ page reloaded ✅ IM Panel Shut ✅ Move to Next Task")
        log_func("==================================================\n")

    except Exception as e:
        log_func(f"⚠️ Task Progress adnormal，Continue execute Next Task: {str(e)}")
