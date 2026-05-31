"""
Магазин плагинов из Telegram канала / GitHub.
Позволяет устанавливать плагины из указанного канала или по URL.
"""
import os
import asyncio
import logging
import json
import re
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

import medic_bot.app as app
from medic_bot.fsociety_lang.strings import Translations
from medic_bot.keyboards.menus import Keyboards
from medic_bot.plugins import PluginContext, PluginManager
from medic_bot.monitor import load_config as load_osnova_config

router = Router()
tr = Translations()
kb = Keyboards()
log = logging.getLogger("medic.plugin_store")

# Конфигурация магазина плагинов
PLUGIN_STORE_CHANNEL = "@fsociety_starvell"  # Канал для публикации плагинов
PLUGIN_STORE_REPO = "https://api.github.com/repos/me-dicament/Fsociety-Starvell-Plugins/releases"  # GitHub releases

# Кэш доступных плагинов
_available_plugins_cache: list[dict] = []
_last_cache_update: float = 0
_CACHE_TTL = 300  # 5 минут


async def fetch_available_plugins_from_github() -> list[dict]:
    """Получить список доступных плагинов из GitHub releases"""
    import requests
    from api.rate_limiter import throttle_sync

    try:
        throttle_sync()
        resp = requests.get(
            PLUGIN_STORE_REPO,
            headers={
                "accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            timeout=10,
        )
        if resp.status_code != 200:
            return []

        releases = resp.json() or []
        plugins: list[dict] = []

        for release in releases:
            tag = str((release or {}).get("tag_name") or "").strip()
            body = str((release or {}).get("body") or "").strip()
            assets = (release or {}).get("assets") or []

            for asset in assets:
                name = str((asset or {}).get("name") or "").strip()
                if not name.lower().endswith(".py"):
                    continue
                download_url = str((asset or {}).get("browser_download_url") or "").strip()
                if not download_url:
                    continue
                plugins.append({
                    "name": name,
                    "version": tag,
                    "url": download_url,
                    "description": body[:200] if body else f"Плагин {name}",
                    "size": (asset or {}).get("size", 0),
                })

        return plugins
    except Exception as exc:
        log.warning("fetch_plugins_from_github failed: %s", exc)
        return []


async def get_available_plugins(refresh: bool = False) -> list[dict]:
    """Получить кэшированный список доступных плагинов"""
    global _available_plugins_cache, _last_cache_update
    import time

    now = time.time()
    if refresh or (now - _last_cache_update > _CACHE_TTL) or not _available_plugins_cache:
        _available_plugins_cache = await fetch_available_plugins_from_github()
        _last_cache_update = now

    return _available_plugins_cache


async def install_plugin_from_url(url: str, dest_name: str | None = None) -> str | None:
    """Скачать и установить плагин по URL. Возвращает путь к файлу или None"""
    import aiohttp
    import tempfile

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                if resp.status != 200:
                    return None
                content = await resp.read()
    except Exception as exc:
        log.warning("download_plugin_failed url=%s error=%s", url, exc)
        return None

    if not dest_name:
        # Извлекаем имя из URL
        dest_name = os.path.basename(url.split("?")[0])
    if not dest_name.lower().endswith(".py"):
        dest_name += ".py"

    dest_path = os.path.join("plugins", dest_name)
    try:
        with open(dest_path, "wb") as f:
            f.write(content)
    except Exception as exc:
        log.warning("save_plugin_failed path=%s error=%s", dest_path, exc)
        return None

    return dest_path


@router.message(Command("plugin_store"))
async def cmd_plugin_store(message: Message):
    """Показать магазин плагинов"""
    db = app.app_context.db
    cfg = app.app_context.config
    user = await db.get_user(message.from_user.id)
    if not user.get("authorized"):
        return
    lang = user.get("language") or cfg.default_language

    status_msg = await message.answer("🔄 Загружаю список доступных плагинов…")

    plugins = await get_available_plugins()

    if not plugins:
        builder = InlineKeyboardBuilder()
        builder.button(text=tr.t(lang, "btn_back"), callback_data="menu:plugins")
        await status_msg.edit_text(
            "📭 Плагины пока не добавлены в магазин.\n"
            "Следите за обновлениями в @fsociety_starvell\n"
            "Или установите вручную: /plugin_install <url>",
            reply_markup=builder.as_markup(),
        )
        return

    lines = ["🧩 Магазин плагинов", "Выберите плагин для установки:", ""]
    builder = InlineKeyboardBuilder()

    for idx, plugin in enumerate(plugins, start=1):
        name = plugin.get("name", "unknown.py")
        version = plugin.get("version", "?")
        desc = plugin.get("description", "")[:50]
        lines.append(f"{idx}. <code>{name}</code> v{version}")
        if desc:
            lines[-1] += f" — {desc}"
        builder.button(
            text=f"#{idx} {name}",
            callback_data=f"plugin_store:install:{idx}",
        )

    builder.button(text=tr.t(lang, "btn_back"), callback_data="menu:plugins")
    builder.adjust(1)

    await status_msg.edit_text("\n".join(lines), reply_markup=builder.as_markup())


@router.message(Command("plugin_install"))
async def cmd_plugin_install(message: Message):
    """Установить плагин по URL"""
    db = app.app_context.db
    cfg = app.app_context.config
    user = await db.get_user(message.from_user.id)
    if not user.get("authorized"):
        return
    lang = user.get("language") or cfg.default_language

    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Использование: /plugin_install <url>\nПример: /plugin_install https://raw.githubusercontent.com/.../plugin.py")
        return

    url = parts[1].strip()
    if not url.startswith("http"):
        await message.answer("URL должен начинаться с http:// или https://")
        return

    status_msg = await message.answer("🔄 Скачиваю плагин…")

    dest_path = await install_plugin_from_url(url)

    if not dest_path:
        await status_msg.edit_text("❌ Не удалось скачать плагин. Проверьте URL.")
        return

    # Загружаем плагин
    try:
        pm = app.app_context.plugin_manager
        if pm is None:
            await status_msg.edit_text("❌ Менеджер плагинов не инициализирован.")
            return

        meta = pm.load_one(dest_path)
        pm.enable(meta.uuid)

        # Инициализация
        try:
            cfg2 = load_osnova_config()
        except Exception:
            cfg2 = {}
        ctx = PluginContext(
            session_cookie=(cfg2 or {}).get("SESSION_COOKIE", ""),
            db=app.app_context.db,
            config=cfg2 or {},
        )
        await pm.dispatch_init(ctx)

        # Обновляем список команд
        try:
            base_cmds = [
                BotCommand(command="start", description="Запуск"),
                BotCommand(command="restart", description="Перезапуск"),
                BotCommand(command="update", description="Обновление"),
            ]
            plugin_cmds: list[BotCommand] = []
            seen = {c.command for c in base_cmds}
            for name, meta_cmd in pm.commands.items():
                cmd = str(name or "").strip().lower()
                if not cmd or cmd in seen:
                    continue
                desc = str(meta_cmd.get("description") or "").strip()[:256]
                plugin_cmds.append(BotCommand(command=cmd, description=desc or "Plugin"))
                seen.add(cmd)
            await message.bot.set_my_commands(base_cmds + plugin_cmds)
        except Exception:
            pass

        await status_msg.edit_text(
            f"✅ Плагин установлен: <code>{meta.name}</code> v{meta.version}\n"
            f"UUID: <code>{meta.uuid}</code>"
        )
        log.info("plugin_installed_from_url name=%s url=%s", meta.name, url)

    except Exception as e:
        await status_msg.edit_text(f"❌ Не удалось установить плагин: {e}")


@router.message(Command("plugin_list"))
async def cmd_plugin_list(message: Message):
    """Показать список установленных плагинов"""
    db = app.app_context.db
    cfg = app.app_context.config
    user = await db.get_user(message.from_user.id)
    if not user.get("authorized"):
        return
    lang = user.get("language") or cfg.default_language

    pm = app.app_context.plugin_manager
    if not pm or not pm.plugins:
        await message.answer(tr.t(lang, "plugins_list_empty"))
        return

    lines = [tr.t(lang, "plugins_list_title")]
    for meta in sorted(pm.plugins.values(), key=lambda m: (m.name or "").lower()):
        status = "✅" if meta.enabled else "❌"
        load_status = ""
        if meta.module is None:
            load_status = " ⚠️ Ошибка"
        lines.append(f"{status} <code>{meta.name}</code> v{meta.version}{load_status}")

    builder = InlineKeyboardBuilder()
    builder.button(text=tr.t(lang, "btn_back"), callback_data="menu:plugins")
    await message.answer("\n".join(lines), reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("plugin_store:install:"))
async def plugin_store_install(callback: CallbackQuery):
    """Установить плагин из магазина"""
    db = app.app_context.db
    cfg = app.app_context.config
    user = await db.get_user(callback.from_user.id)
    if not user.get("authorized"):
        await callback.answer()
        return
    lang = user.get("language") or cfg.default_language

    parts = callback.data.split(":")
    if len(parts) < 3:
        await callback.answer()
        return
    try:
        idx = int(parts[2]) - 1
    except ValueError:
        await callback.answer()
        return

    plugins = await get_available_plugins()
    if idx < 0 or idx >= len(plugins):
        await callback.answer("Плагин не найден", show_alert=True)
        return

    plugin = plugins[idx]
    url = plugin.get("url", "")
    name = plugin.get("name", "plugin.py")

    await callback.message.edit_text(f"🔄 Устанавливаю <code>{name}</code>…")

    dest_name = _safe_file_name(name)
    dest_path = await install_plugin_from_url(url, dest_name)

    if not dest_path:
        await callback.message.edit_text(f"❌ Не удалось скачать плагин <code>{name}</code>")
        return

    try:
        pm = app.app_context.plugin_manager
        if pm is None:
            await callback.message.edit_text("❌ Менеджер плагинов не инициализирован.")
            return

        meta = pm.load_one(dest_path)
        pm.enable(meta.uuid)

        try:
            cfg2 = load_osnova_config()
        except Exception:
            cfg2 = {}
        ctx = PluginContext(
            session_cookie=(cfg2 or {}).get("SESSION_COOKIE", ""),
            db=app.app_context.db,
            config=cfg2 or {},
        )
        await pm.dispatch_init(ctx)

        # Обновляем команды
        try:
            base_cmds = [
                BotCommand(command="start", description="Запуск"),
                BotCommand(command="restart", description="Перезапуск"),
                BotCommand(command="update", description="Обновление"),
            ]
            plugin_cmds: list[BotCommand] = []
            seen = {c.command for c in base_cmds}
            for cmd_name, meta_cmd in pm.commands.items():
                cmd = str(cmd_name or "").strip().lower()
                if not cmd or cmd in seen:
                    continue
                desc = str(meta_cmd.get("description") or "").strip()[:256]
                plugin_cmds.append(BotCommand(command=cmd, description=desc or "Plugin"))
                seen.add(cmd)
            await callback.message.bot.set_my_commands(base_cmds + plugin_cmds)
        except Exception:
            pass

        await callback.message.edit_text(
            f"✅ Плагин установлен: <code>{meta.name}</code> v{meta.version}\n"
            f"UUID: <code>{meta.uuid}</code>",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[
                    InlineKeyboardButton(
                        text=tr.t(lang, "btn_back"),
                        callback_data="plugins:list",
                    )
                ]]
            ),
        )
        log.info("plugin_store_install name=%s url=%s", meta.name, url)

    except Exception as e:
        await callback.message.edit_text(f"❌ Не удалось установить плагин: {e}")


def _safe_file_name(name: str) -> str:
    """Безопасное имя файла для плагина"""
    base = os.path.basename(name).strip()
    allowed = []
    for ch in base:
        if ch.isalnum() or ch in ("-", "_", "."):
            allowed.append(ch)
    file = "".join(allowed) or "plugin.py"
    if not file.lower().endswith(".py"):
        file += ".py"
    return file
