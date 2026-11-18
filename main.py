import discord
from discord.ext import commands
import os
import json
import time
import asyncio
import re
import aiohttp
from datetime import datetime

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True
bot = commands.Bot(command_prefix="!", intents=intents)

DATA_FILE = "mipi_data.json"
VOUCH_CHANNEL_ID = 1571783490297528420
ORDER_LOGS_CHANNEL_ID = 1571783908058730547
TESTIMONI_CHANNEL_ID = 1571784387438055515

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    return {"order_count": 0, "reviews": [], "orders": []}

def save_data(data):
    try:
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except:
        pass

DATA = load_data()
PENDING = {}
COOLDOWN = {}

@bot.event
async def on_ready():
    print(f"Bot Online: {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands")
    except Exception as e:
        print(e)

CATEGORIES = {
    "bot": {
        "kategori": "Jasa Buat Bot",
        "rate": "Mulai Rp 25.000",
        "list": "• SIMPLE\n  └ 🏷️ Rp 25.000\n• MEDIUM\n  └ 🏷️ Rp 50.000\n• FULL\n  └ 🏷️ Rp 100.000\n• PREMIUM\n  └ 🏷️ Rp 150.000\n• SULTAN\n  └ 🏷️ Rp 250.000\n• GOD\n  └ 🏷️ Rp 500.000\n• BOT MUSIC\n  └ 🏷️ Rp 30.000",
        "products": [
            ("💎 SIMPLE - Rp 25.000", "simple"),
            ("🛡️ MEDIUM - Rp 50.000", "medium"),
            ("⭐ FULL - Rp 100.000", "full"),
            ("👑 PREMIUM - Rp 150.000", "premium"),
            ("🔥 SULTAN - Rp 250.000", "sultan"),
            ("🧊 GOD - Rp 500.000", "god"),
            ("🎵 BOT MUSIC - Rp 30.000", "music"),
        ]
    },
    "setup": {
        "kategori": "Jasa Setup DC",
        "rate": "Mulai Rp 25.000",
        "list": "• SETUP SIMPLE\n  └ 🏷️ Rp 25.000\n• SETUP MEDIUM\n  └ 🏷️ Rp 50.000\n• SETUP FULL\n  └ 🏷️ Rp 100.000\n• SETUP PREMIUM\n  └ 🏷️ Rp 150.000\n• SETUP SULTAN\n  └ 🏷️ Rp 250.000",
        "products": [
            ("🛠️ SETUP SIMPLE - Rp 25.000", "setup_simple"),
            ("🛠️ SETUP MEDIUM - Rp 50.000", "setup_medium"),
            ("🛠️ SETUP FULL - Rp 100.000", "setup_full"),
            ("🛠️ SETUP PREMIUM - Rp 150.000", "setup_premium"),
            ("🛠️ SETUP SULTAN - Rp 250.000", "setup_sultan"),
        ]
    },
}

PRODUCTS_DETAIL = {
    "simple": ("💎 SIMPLE", "Rp 25.000", "Ticket + QRIS + Status + Close"),
    "medium": ("🛡️ MEDIUM", "Rp 50.000", "Simple + Saldo + Leaderboard + Vouch + Giveaway"),
    "full": ("⭐ FULL", "Rp 100.000", "Medium + Promo + Anti Jualan + History + 7 Produk + Custom + Diajarin Sampai Bisa"),
    "premium": ("👑 PREMIUM", "Rp 150.000", "Semua Full + 7 Fitur Custom + Setup Hosting + Support Lifetime"),
    "sultan": ("🔥 SULTAN", "Rp 250.000", "Semua Premium + 5 Fitur Custom + 2 Bot + Banner Gratis + VIP"),
    "god": ("🧊 GOD", "Rp 500.000", "Semua Sultan + Unlimited + Source Code + Partner MIPI"),
    "music": ("🎵 BOT MUSIC", "Rp 30.000", "Music 24/7 + Play / Skip / Queue + Spotify & Youtube"),
    "setup_simple": ("🛠️ SETUP SIMPLE", "Rp 25.000", "Channel + Role + Kategori + Rules"),
    "setup_medium": ("🛠️ SETUP MEDIUM", "Rp 50.000", "Simple + Ticket + Welcome + Vouch + Pricelist"),
    "setup_full": ("🛠️ SETUP FULL", "Rp 100.000", "Medium + Bot Ticket + Leaderboard + Banner + Catalog"),
    "setup_premium": ("🛠️ SETUP PREMIUM", "Rp 150.000", "Semua Full + Custom Design + Setup Hosting + Support 7 Hari"),
    "setup_sultan": ("🛠️ SETUP SULTAN", "Rp 250.000", "Semua Premium + 2 Bot + Banner Gratis + VIP + Support Lifetime"),
}

def find_channel(guild, name_part):
    if "vouch" in name_part.lower():
        ch = guild.get_channel(VOUCH_CHANNEL_ID)
        if ch:
            return ch
    if "order-logs" in name_part.lower():
        ch = guild.get_channel(ORDER_LOGS_CHANNEL_ID)
        if ch:
            return ch
    if "testimoni" in name_part.lower():
        ch = guild.get_channel(TESTIMONI_CHANNEL_ID)
        if ch:
            return ch
    for ch in guild.text_channels:
        if name_part in ch.name.lower():
            return ch
    return None

def get_vouch_embed(review):
    embed = discord.Embed(title="⭐ TESTIMONI PEMBELI — Mipi Store", color=0xFFD700)
    embed.add_field(name="👤 Pembeli:", value=review["customer_mention"], inline=False)
    embed.add_field(name="📦 Produk:", value=review["produk"], inline=False)
    embed.add_field(name="⭐ Rating:", value=f"{'⭐' * review['rating']} ({review['rating']}/5)", inline=False)
    embed.add_field(name="📅 Tanggal:", value=review["tanggal"], inline=False)
    embed.add_field(name="💬 Ulasan & Review:", value=f"\"{review['ulasan']}\"", inline=False)
    if review.get("avatar"):
        embed.set_thumbnail(url=review["avatar"])
    return embed

def get_order_log_embed(order):
    embed = discord.Embed(title=f"🧾 ORDER LOG — {order['order_id']}", color=0x2B2D31)
    embed.add_field(name="👤 Customer:", value=order["customer_mention"], inline=False)
    embed.add_field(name="🎮 Nama Server:", value=order.get("roblox_user", "-"), inline=False)
    embed.add_field(name="📦 Produk:", value=order["produk"], inline=False)
    embed.add_field(name="📦 Jumlah:", value=order.get("jumlah", "1 Unit"), inline=False)
    embed.add_field(name="💰 Total Bayar:", value=order["harga"], inline=False)
    embed.add_field(name="💳 Metode:", value="QRIS (All Payment)", inline=False)
    embed.add_field(name="📅 Tanggal:", value=order["tanggal"], inline=False)
    embed.add_field(name="📊 Status:", value="🟢 DONE / PAID", inline=False)
    if order.get("avatar"):
        embed.set_thumbnail(url=order["avatar"])
    return embed

def get_testimoni_embed():
    reviews = DATA.get("reviews", [])
    total = len(reviews)
    avg = sum(r["rating"] for r in reviews) / total if total > 0 else 0.0
    counts = {5:0, 4:0, 3:0, 2:0, 1:0}
    for r in reviews:
        counts[r["rating"]] = counts.get(r["rating"], 0) + 1
    stars = "⭐" * round(avg) if avg > 0 else "⭐"
    desc = f"Rangkuman kepuasan dan ulasan pelanggan dari transaksi terverifikasi di Mipi Store:\n\n"
    desc += f"📊 **STATISTIK REPUTASI TOKO:**\n"
    desc += f"⭐ **Rating Kepuasan:** {avg:.1f} / 5.0 {stars}\n"
    desc += f"⭐ **Total Ulasan Selesai:** {total} Pembeli\n\n"
    desc += f"📝 **RINCIAN RATING BINTANG:**\n"
    desc += f"⭐⭐⭐⭐⭐ (5 Bintang): {counts[5]} ulasan\n"
    desc += f"⭐⭐⭐⭐ (4 Bintang): {counts[4]} ulasan\n"
    desc += f"⭐⭐⭐ (3 Bintang): {counts[3]} ulasan\n"
    desc += f"⭐⭐ (2 Bintang): {counts[2]} ulasan\n"
    desc += f"⭐ (1 Bintang): {counts[1]} ulasan\n\n"
    desc += f"🔒 *Reputasi Terverifikasi Otomatis: Setiap ulasan di bawah berasal langsung dari tiket pesanan yang telah selesai (DONE).*"
    embed = discord.Embed(title="⭐ REPUTASI & STATISTIK TOKO — Mipi Store", description=desc, color=0xFFD700)
    return embed

async def update_testimoni_channel(guild):
    ch = find_channel(guild, "testimoni")
    if not ch:
        return
    try:
        async for msg in ch.history(limit=20):
            if msg.author == guild.me:
                try:
                    await msg.delete()
                except:
                    pass
    except:
        pass
    await ch.send(embed=get_testimoni_embed())

async def create_ticket_filled(interaction, paket_nama, harga, filled_text, extra_data=None):
    guild = interaction.guild
    category = None
    for cat in guild.categories:
        if "ticket" in cat.name.lower():
            category = cat
            break
    existing = discord.utils.get(guild.text_channels, name=f"ticket-{interaction.user.name.lower()}")
    if existing:
        return existing
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_messages=True),
        guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_messages=True),
    }
    channel = await guild.create_text_channel(name=f"ticket-{interaction.user.name}", category=category, overwrites=overwrites)
    embed = discord.Embed(title="🎫 TICKET MIPI STORE", description=f"Halo {interaction.user.mention}!\n\nKamu order **{paket_nama}** 💖\n\n{filled_text}\n\nPembayaran via **QRIS** ya! Scan di bawah ini, terus kirim bukti TF di sini 👇", color=0xFF69B4)
    embed.set_image(url="https://raw.githubusercontent.com/mipistore/mipi-store/main/IMG_5210.jpeg")
    await channel.send(embed=embed, view=TicketActionView())
    PENDING[channel.id] = {
        "customer_id": interaction.user.id,
        "customer_mention": interaction.user.mention,
        "customer_name": str(interaction.user),
        "avatar": str(interaction.user.display_avatar.url) if interaction.user.display_avatar else None,
        "produk": paket_nama,
        "harga": harga,
        "roblox_user": (extra_data or {}).get("roblox_user", "-"),
        "nama": (extra_data or {}).get("nama", "-"),
        "jumlah": (extra_data or {}).get("jumlah", "1 Unit"),
    }
    return channel

class TicketActionView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    def is_allowed(self, interaction, channel_id):
        if interaction.user.guild_permissions.manage_channels or interaction.user.guild_permissions.administrator:
            return True
        data = PENDING.get(channel_id, {})
        if data.get("customer_id") == interaction.user.id:
            return True
        ch_name = interaction.channel.name.lower() if interaction.channel else ""
        if ch_name.startswith("ticket-"):
            owner_name = ch_name.replace("ticket-", "").strip()
            if interaction.user.name.lower() == owner_name:
                return True
        return False
    @discord.ui.button(label="✅ Tandai Selesai / DONE", style=discord.ButtonStyle.green, custom_id="ticket_done")
    async def ticket_done(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.is_allowed(interaction, interaction.channel.id):
            await interaction.response.send_message("❌ Ehh, ini bukan ticket kamu! Cuma pemilik ticket + admin yang bisa pencet DONE!", ephemeral=True)
            return
        await interaction.response.send_modal(ReviewModal(interaction.channel.id))
    @discord.ui.button(label="🔒 Close Ticket", style=discord.ButtonStyle.red, custom_id="close_ticket")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.is_allowed(interaction, interaction.channel.id):
            await interaction.response.send_message("❌ Ehh, ini bukan ticket kamu! Cuma pemilik ticket + admin yang bisa Close!", ephemeral=True)
            return
        await interaction.response.send_message("Ticket akan ditutup dalam 5 detik...")
        await interaction.channel.delete()

class CloseTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="🔒 Close Ticket", style=discord.ButtonStyle.red, custom_id="close_ticket2")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Ticket akan ditutup dalam 5 detik...")
        await interaction.channel.delete()

class ReviewModal(discord.ui.Modal):
    def __init__(self, channel_id):
        super().__init__(title="Kasih Rating & Ulasan")
        self.channel_id = channel_id
        self.rating_input = discord.ui.TextInput(label="Rating (1-5)", placeholder="Contoh: 5", required=True, max_length=1)
        self.ulasan_input = discord.ui.TextInput(label="Ulasan / Review", placeholder="Contoh: great store, fast respon!", required=True, style=discord.TextStyle.paragraph)
        self.add_item(self.rating_input)
        self.add_item(self.ulasan_input)
    async def on_submit(self, interaction: discord.Interaction):
        try:
            rating = int(self.rating_input.value.strip())
            if rating < 1: rating = 1
            if rating > 5: rating = 5
        except:
            rating = 5
        ulasan = self.ulasan_input.value.strip()
        tanggal = datetime.now().strftime("%d %b %Y").upper()
        data = PENDING.get(self.channel_id, {})
        customer_mention = data.get("customer_mention", interaction.user.mention)
        avatar = data.get("avatar", str(interaction.user.display_avatar.url))
        produk = data.get("produk", "Produk Mipi Store")
        harga = data.get("harga", "-")
        roblox_user = data.get("roblox_user", "-")
        jumlah = data.get("jumlah", "1 Unit")
        DATA["order_count"] = DATA.get("order_count", 0) + 1
        order_id = f"ORDER-{DATA['order_count']:06d}"
        order = {
            "order_id": order_id,
            "customer_mention": customer_mention,
            "avatar": avatar,
            "produk": produk,
            "harga": harga,
            "roblox_user": roblox_user,
            "jumlah": jumlah,
            "tanggal": tanggal,
        }
        review = {
            "customer_mention": customer_mention,
            "avatar": avatar,
            "produk": produk,
            "rating": rating,
            "tanggal": tanggal,
            "ulasan": ulasan,
        }
        DATA.setdefault("orders", []).append(order)
        DATA.setdefault("reviews", []).append(review)
        save_data(DATA)
        guild = interaction.guild
        log_ch = find_channel(guild, "order-logs")
        if log_ch:
            await log_ch.send(embed=get_order_log_embed(order))
        vouch_ch = find_channel(guild, "vouch")
        if vouch_ch:
            await vouch_ch.send(embed=get_vouch_embed(review))
        await update_testimoni_channel(guild)
        await interaction.response.send_message(f"✅ Makasih! Order **{order_id}** DONE!\nUlasan kamu udah masuk ke #⭐・vouch, #🧾・order-logs, dan rating toko ke-update di #⭐・testimoni! 💖\nTicket akan ditutup dalam 5 detik...", ephemeral=False)
        if self.channel_id in PENDING:
            del PENDING[self.channel_id]
        async def close_later():
            await asyncio.sleep(5)
            try:
                ch = guild.get_channel(self.channel_id)
                if ch:
                    await ch.delete()
            except:
                pass
        asyncio.create_task(close_later())

class OrderBotModal(discord.ui.Modal):
    def __init__(self, key):
        super().__init__(title="Order Bot - Isi Data")
        self.key = key
        self.nama_input = discord.ui.TextInput(label="Nama Kamu", placeholder="Contoh: Rafix", required=True, max_length=30)
        self.jenis_input = discord.ui.TextInput(label="Jenis Bot", placeholder="Contoh: Bot Store", required=True, max_length=50)
        self.fitur_input = discord.ui.TextInput(label="Fitur Yang Mau", placeholder="Contoh: Welcome, Ticket, QRIS, dll", required=True, style=discord.TextStyle.paragraph)
        self.deadline_input = discord.ui.TextInput(label="Deadline", placeholder="Contoh: Besok / 3 Hari", required=False)
        self.add_item(self.nama_input)
        self.add_item(self.jenis_input)
        self.add_item(self.fitur_input)
        self.add_item(self.deadline_input)
    async def on_submit(self, interaction: discord.Interaction):
        nama, harga, desc = PRODUCTS_DETAIL[self.key]
        filled = f"**FORMAT ORDER BOT (UDAH KEISI ✅):**\n```\nNama : {self.nama_input.value}\nJenis Bot : {self.jenis_input.value}\nPaket : {nama} - {harga}\nFitur Yang Mau : {self.fitur_input.value}\nBudget : {harga}\nDeadline : {self.deadline_input.value or '-'}\n```"
        channel = await create_ticket_filled(interaction, f"{nama} - {harga}", harga, filled, extra_data={"nama": self.nama_input.value, "roblox_user": "-", "jumlah": "1 Unit"})
        await interaction.response.send_message(f"Order kamu dibuat & udah keisi! 👉 {channel.mention}", ephemeral=True)

class OrderSetupModal(discord.ui.Modal):
    def __init__(self, key):
        super().__init__(title="Order Setup DC - Isi Data")
        self.key = key
        self.nama_input = discord.ui.TextInput(label="Nama Kamu", placeholder="Contoh: Rafix", required=True, max_length=30)
        self.server_input = discord.ui.TextInput(label="Nama Server Discord Kamu", placeholder="Contoh: MIPI STORE", required=True, max_length=30)
        self.tema_input = discord.ui.TextInput(label="Tema / Mau Setup Apa Aja?", placeholder="Contoh: Store Robux, tema pink, mau ada ticket + vouch", required=True, style=discord.TextStyle.paragraph)
        self.deadline_input = discord.ui.TextInput(label="Deadline", placeholder="Contoh: Besok / 3 Hari", required=False)
        self.add_item(self.nama_input)
        self.add_item(self.server_input)
        self.add_item(self.tema_input)
        self.add_item(self.deadline_input)
    async def on_submit(self, interaction: discord.Interaction):
        nama, harga, desc = PRODUCTS_DETAIL[self.key]
        filled = f"**FORMAT ORDER SETUP DC (UDAH KEISI ✅):**\n```\nNama : {self.nama_input.value}\nNama Server : {self.server_input.value}\nPaket : {nama} - {harga}\nTema / Request : {self.tema_input.value}\nDeadline : {self.deadline_input.value or '-'}\nBukti TF : -\n```"
        channel = await create_ticket_filled(interaction, f"{nama} - {harga}", harga, filled, extra_data={"nama": self.nama_input.value, "roblox_user": self.server_input.value, "jumlah": "1 Unit"})
        await interaction.response.send_message(f"Order kamu dibuat & udah keisi! 👉 {channel.mention}", ephemeral=True)

class OrderButton(discord.ui.View):
    def __init__(self, key):
        super().__init__(timeout=None)
        self.key = key
    @discord.ui.button(label="🛒 Order / Beli Sekarang", style=discord.ButtonStyle.green, custom_id="order_now")
    async def order_now(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = interaction.user.id
        now = time.time()
        existing = discord.utils.get(interaction.guild.text_channels, name=f"ticket-{interaction.user.name.lower()}")
        if existing:
            await interaction.response.send_message(f"❌ Kamu udah punya ticket aktif! Selesaikan dulu 👉 {existing.mention}\nGa bisa bikin ticket baru sebelum yang lama di-close!", ephemeral=True)
            return
        last = COOLDOWN.get(user_id, 0)
        sisa = 60 - (now - last)
        if sisa > 0:
            await interaction.response.send_message(f"⏳ Ehh sabar! Tunggu {int(sisa)} detik lagi baru bisa order lagi! Biar ga spam!", ephemeral=True)
            return
        COOLDOWN[user_id] = now
        if self.key.startswith("setup_"):
            await interaction.response.send_modal(OrderSetupModal(self.key))
        else:
            await interaction.response.send_modal(OrderBotModal(self.key))

class CategorySelect(discord.ui.Select):
    def __init__(self, current="bot"):
        options = [
            discord.SelectOption(label="🤖 Jasa Buat Bot", description="Lihat produk di kategori ini", value="bot", emoji="🤖"),
            discord.SelectOption(label="🛠️ Jasa Setup DC", description="Lihat produk di kategori ini", value="setup", emoji="🛠️"),
        ]
        placeholder = "🤖 Jasa Buat Bot" if current == "bot" else "🛠️ Jasa Setup DC"
        super().__init__(placeholder=placeholder, options=options, custom_id="cat_select")
    async def callback(self, interaction: discord.Interaction):
        cat_key = self.values[0]
        await interaction.response.edit_message(view=CatalogLayout(cat_key))

class ProductSelect(discord.ui.Select):
    def __init__(self, cat_key):
        c = CATEGORIES[cat_key]
        options = [discord.SelectOption(label=label, value=val) for label, val in c["products"]]
        super().__init__(placeholder="🛒 Pilih Produk untuk Order / Beli...", options=options, custom_id="prod_select")
    async def callback(self, interaction: discord.Interaction):
        key = self.values[0]
        nama, harga, desc = PRODUCTS_DETAIL[key]
        embed = discord.Embed(title="Mipi Store CATALOG", description=f"**{nama}**\n\n**Harga :** `{harga}`\n\n**Detail :**\n• {desc}", color=0x2B2D31)
        await interaction.response.send_message(embed=embed, view=OrderButton(key), ephemeral=True)

class CatalogLayout(discord.ui.LayoutView):
    def __init__(self, cat_key="bot"):
        super().__init__(timeout=None)
        self.cat_key = cat_key
        c = CATEGORIES[cat_key]
        keys = list(CATEGORIES.keys())
        idx = keys.index(cat_key)
        page_text = f"{idx+1}/{len(keys)}"
        container = discord.ui.Container()
        container.add_item(discord.ui.TextDisplay("## Mipi Store CATALOG"))
        container.add_item(discord.ui.ActionRow(CategorySelect(cat_key)))
        container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))
        container.add_item(discord.ui.TextDisplay(f"**Kategori :** {c['kategori']}\n**⚡ Rate Kategori :** `{c['rate']}`\n\n**List Product :**\n{c['list']}"))
        container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))
        container.add_item(discord.ui.ActionRow(ProductSelect(cat_key)))
        row = discord.ui.ActionRow()
        prev_btn = discord.ui.Button(label="PREV", style=discord.ButtonStyle.secondary, custom_id=f"prev_{cat_key}")
        page_btn = discord.ui.Button(label=page_text, style=discord.ButtonStyle.secondary, custom_id="page_btn", disabled=True)
        next_btn = discord.ui.Button(label="Next", style=discord.ButtonStyle.secondary, custom_id=f"next_{cat_key}")
        async def prev_cb(interaction: discord.Interaction, _cat=cat_key):
            keys2 = list(CATEGORIES.keys())
            idx2 = keys2.index(_cat)
            new_key = keys2[(idx2 - 1) % len(keys2)]
            await interaction.response.edit_message(view=CatalogLayout(new_key))
        async def next_cb(interaction: discord.Interaction, _cat=cat_key):
            keys2 = list(CATEGORIES.keys())
            idx2 = keys2.index(_cat)
            new_key = keys2[(idx2 + 1) % len(keys2)]
            await interaction.response.edit_message(view=CatalogLayout(new_key))
        prev_btn.callback = prev_cb
        next_btn.callback = next_cb
        row.add_item(prev_btn)
        row.add_item(page_btn)
        row.add_item(next_btn)
        container.add_item(row)
        self.add_item(container)

@bot.tree.command(name="product", description="Lihat katalog produk Mipi Store")
async def product(interaction: discord.Interaction):
    await interaction.response.send_message(view=CatalogLayout("bot"))

class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="🎫 Open Ticket", style=discord.ButtonStyle.blurple, custom_id="open_ticket")
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Pilih produk di #🛍️・product dulu ya!", ephemeral=True)

@bot.tree.command(name="ticket", description="Kirim panel open ticket")
async def ticket(interaction: discord.Interaction):
    embed = discord.Embed(title="MIPI STORE - OPEN!", description="**List Bisa Dibuat / Dibeli:**\n> 🤖 Jasa Buat Bot - Mulai 25K\n> 🛠️ Jasa Setup DC - Mulai 25K\n\n**Cara Order:**\n1. Ke channel `#🛍️・product` pilih produk\n2. Pencet Order -> Isi Form -> Ticket langsung keisi!\n\n*Pembayaran QRIS 💖*", color=0x2B2D31)
    await interaction.response.send_message(embed=embed, view=TicketView())

@bot.tree.command(name="pricelist", description="Lihat pricelist")
async def pricelist(interaction: discord.Interaction):
    embed = discord.Embed(title="💖 PRICELIST - MIPI STORE", description="**🤖 JASA BUAT BOT**\n> SIMPLE - 25K\n> MEDIUM - 50K\n> FULL - 100K\n> PREMIUM - 150K\n> SULTAN - 250K\n> GOD - 500K\n> BOT MUSIC - 30K\n\n**🛠️ JASA SETUP DC**\n> SETUP SIMPLE - 25K\n> SETUP MEDIUM - 50K\n> SETUP FULL - 100K\n> SETUP PREMIUM - 150K\n> SETUP SULTAN - 250K\n\n*Pembayaran QRIS 💖*", color=0x2B2D31)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="setup_store", description="Buat channel vouch, order-logs, testimoni kaya Issa")
async def setup_store(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    guild = interaction.guild
    cat = None
    for c in guild.categories:
        if "catalog" in c.name.lower():
            cat = c
            break
    if not cat:
        cat = await guild.create_category("🛍️ — CATALOG —")
    for name in ["🛍️・product", "⭐・vouch", "🧾・order-logs", "⭐・testimoni"]:
        if not find_channel(guild, name.split("・")[-1] if "・" in name else name):
            try:
                await guild.create_text_channel(name=name, category=cat)
            except:
                pass
    await update_testimoni_channel(guild)
    await interaction.followup.send("✅ Berhasil! Channel #🛍️・product, #⭐・vouch, #🧾・order-logs, #⭐・testimoni udah dibuat!\nSekarang ketik `/product` di #🛍️・product!", ephemeral=True)

# ========== CHECKAVATAR V6 - TETEP ADA, SEMUA BISA DIPENCET ==========
@bot.tree.command(name="checkavatar", description="Mengecek detail profil dan avatar akun Roblox dengan username")
async def checkavatar(interaction: discord.Interaction, username: str):
    await interaction.response.defer()
    try:
        headers = {"User-Agent": "Mozilla/5.0 MIPI-STORE-Bot"}
        async with aiohttp.ClientSession(headers=headers) as s:
            async with s.post("https://users.roproxy.com/v1/usernames/users", json={"usernames": [username], "excludeBannedUsers": True}) as r:
                data = await r.json()
            if not data.get("data"):
                await interaction.followup.send(f"❌ Username `{username}` tidak ditemukan!")
                return
            user = data["data"][0]
            user_id = user["id"]
            display = user.get("displayName", username)
            uname = user.get("name", username)
            async with s.get(f"https://users.roproxy.com/v1/users/{user_id}") as r:
                info = await r.json()
            created = info.get("created", "")
            try: tgl = datetime.fromisoformat(created.replace("Z", "+00:00")).strftime("%d %B %Y")
            except: tgl = created
            async with s.get(f"https://avatar.roproxy.com/v1/users/{user_id}/avatar") as r:
                av = await r.json()
            tipe = av.get("playerAvatarType", "R15")
            assets = av.get("assets", [])
            names = {}
            sem = asyncio.Semaphore(8)
            async def get_nama(aid):
                async with sem:
                    try:
                        async with s.get(f"https://economy.roproxy.com/v2/assets/{aid}/details") as r:
                            if r.status == 200:
                                d = await r.json()
                                if d.get("Name"):
                                    return aid, d["Name"]
                    except: pass
                    try:
                        async with s.get(f"https://api.roproxy.com/marketplace/productinfo?assetId={aid}") as r:
                            if r.status == 200:
                                d = await r.json()
                                if d.get("Name"):
                                    return aid, d["Name"]
                    except: pass
                    try:
                        async with s.post("https://catalog.roproxy.com/v1/catalog/items/details", json={"items": [{"id": aid, "itemType": "Asset"}]}) as r:
                            if r.status == 200:
                                d = await r.json()
                                if d.get("data") and d["data"][0].get("name"):
                                    return aid, d["data"][0]["name"]
                    except: pass
                    return aid, None
            hasil = await asyncio.gather(*[get_nama(a["id"]) for a in assets])
            for aid, nm in hasil:
                if nm: names[aid] = nm
            def link(nama, aid):
                slug = re.sub(r'[^a-zA-Z0-9\- ]', '', nama).strip().replace(' ', '-')
                nama_bersih = nama.replace('[', '').replace(']', '').replace('(', '').replace(')', '')
                return f"[{nama_bersih}](https://www.roblox.com/catalog/{aid}/{slug})"
            aksesoris, pakaian, tubuh, animasi = [], [], [], []
            for a in assets:
                aid = a["id"]
                nama_asli = names.get(aid, f"Asset {aid}")
                nama = link(nama_asli, aid)
                t = a.get("assetType", {}).get("name", "")
                tid = a.get("assetType", {}).get("id", 0)
                low = nama_asli.lower()
                if any(x in low for x in ["skirt", "dress", "top ", "top and", "shirt", "tshirt", "t-shirt", "pants", "shorts", "jeans", "jacket", "hoodie", "sweater", "cardigan", "blouse", "outfit", "uniform", "pajama", "bikini", "swimsuit", "leggings", "vest"]):
                    pakaian.append(nama)
                elif any(x in low for x in ["doll", "torso", "- right arm", "- left arm", "- right leg", "- left leg", "dynamic head"]) and "hair" not in low and "hat" not in low and "glasses" not in low:
                    tubuh.append(nama)
                elif any(x in low for x in ["run", "walk", "jump", "fall", "swim", "climb", "idle", "mood", "animation", "emote", "dance", "pack"]):
                    animasi.append(nama)
                elif tid in [11, 12, 2]:
                    pakaian.append(nama)
                elif tid in [17, 18, 27, 28, 29, 30, 31]:
                    tubuh.append(nama)
                elif tid in [61, 62, 63, 64]:
                    animasi.append(nama)
                elif t in ["Hat", "HairAccessory", "FaceAccessory", "NeckAccessory", "ShoulderAccessory", "FrontAccessory", "BackAccessory", "WaistAccessory", "Gear", "Hair", "Face"]:
                    aksesoris.append(nama)
                elif t in ["Shirt", "Pants", "TShirt", "Jacket", "Sweater", "Shorts", "DressSkirt", "Skirt", "ShirtGraphic"]:
                    pakaian.append(nama)
                elif t in ["Head", "Torso", "RightArm", "LeftArm", "RightLeg", "LeftLeg", "DynamicHead"]:
                    tubuh.append(nama)
                elif "Animation" in t or "Emote" in t or t in ["Run", "Walk", "Jump", "Fall", "Swim", "Climb", "Idle", "Mood", "Animation"]:
                    animasi.append(nama)
                else:
                    aksesoris.append(nama)
            async with s.get(f"https://thumbnails.roproxy.com/v1/users/avatar?userIds={user_id}&size=720x720&format=Png&isCircular=false") as r:
                thumb = await r.json()
            avatar_url = thumb["data"][0]["imageUrl"] if thumb.get("data") else None
            profil_url = f"https://www.roblox.com/users/{user_id}/profile"
            profil_link = f"[{uname}]({profil_url})"
            desc = f"🔍 **Profil Roblox:** {profil_link}\n"
            desc += f"👤 **Display Name**\n{display}\n"
            desc += f"🆔 **User ID**\n{user_id}\n"
            desc += f"📅 **Tanggal Dibuat**\n{tgl}\n"
            desc += f"🏃 **Tipe Avatar**\n{tipe}\n\n"
            desc += f"🎩 **Aksesoris**\n" + ("".join([f"• {x}\n" for x in aksesoris]) if aksesoris else "• -\n")
            desc += f"\n👕 **Pakaian**\n" + ("".join([f"• {x}\n" for x in pakaian]) if pakaian else "• -\n")
            desc += f"\n👤 **Tubuh & Wajah**\n" + ("".join([f"• {x}\n" for x in tubuh]) if tubuh else "• -\n")
            desc += f"\n🎬 **Animasi & Bundel**\n" + ("".join([f"• {x}\n" for x in animasi]) if animasi else "• -\n")
            if len(desc) > 4000:
                desc = desc[:3950] + "\n... (terlalu banyak item)"
            e = discord.Embed(title=f"Profil Roblox: {uname}", description=desc, color=0xFF69B4)
            e.url = profil_url
            if avatar_url: e.set_image(url=avatar_url)
            e.set_footer(text="MIPI STORE • /checkavatar • Klik nama item / profil buat buka di Roblox")
            view = discord.ui.View()
            view.add_item(discord.ui.Button(label="👤 Buka Profil Roblox", style=discord.ButtonStyle.link, url=profil_url, emoji="🔍"))
            view.add_item(discord.ui.Button(label="🎮 Lihat Avatar 3D", style=discord.ButtonStyle.link, url=profil_url))
            await interaction.followup.send(embed=e, view=view)
    except Exception as ex:
        await interaction.followup.send(f"❌ Gagal cek avatar: {ex}")

# ========== CHECKAVATAR GAMPANG - TINGGAL PENCET ==========
class CheckAvatarModal(discord.ui.Modal, title="🔍 Cek Avatar Roblox"):
    username_input = discord.ui.TextInput(label="Username Roblox", placeholder="Contoh: DENCOW2505", required=True, max_length=20)
    async def on_submit(self, interaction: discord.Interaction):
        username = self.username_input.value.strip()
        await checkavatar.callback(interaction, username)

class CheckAvatarButtonView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="🔍 CEK AVATAR ROBLOX", style=discord.ButtonStyle.blurple, custom_id="cek_avatar_pencet", emoji="🔍")
    async def cek_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(CheckAvatarModal())
    @discord.ui.button(label="💰 CEK RBX / GAMEPASS", style=discord.ButtonStyle.green, custom_id="cek_rbx_pencet", emoji="💰")
    async def cek_rbx_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Ketik ini di channel ini:\n```\n/cekrbx username: usernameKamu\n```", ephemeral=True)

@bot.tree.command(name="checkavatar-panel", description="Kirim panel pencet cek avatar (Owner only)")
async def checkavatar_panel(interaction: discord.Interaction):
    if interaction.user.id != interaction.guild.owner_id:
        await interaction.response.send_message("❌ Hanya Owner!", ephemeral=True); return
    e = discord.Embed(color=0xff69b4)
    e.description = (
        "## 🌸・CHECK AVATAR ROBLOX\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "Mau cek avatar temen / akun kamu?\n"
        "**Ga usah ketik command!** ✨\n\n"
        "### 👇 CARANYA GAMPANG BANGET:\n"
        "1. Pencet tombol **🔍 CEK AVATAR ROBLOX** dibawah\n"
        "2. Ketik username Roblox kamu\n"
        "3. Pencet Kirim / Enter\n"
        "4. Langsung muncul avatar + semua itemnya!\n\n"
        "Semua item bisa dipencet -> langsung ke Catalog Roblox! 💖\n\n"
        "💗 *MIPI STORE • Aman, Cepat, Terpercaya*"
    )
    e.set_image(url="https://raw.githubusercontent.com/mipistore/mipi-store/main/----563dc75098ea.jpeg")
    e.set_footer(text="MIPI STORE • Tinggal Pencet Aja!")
    await interaction.response.send_message(embed=e, view=CheckAvatarButtonView())

@bot.tree.command(name="cekrbx", description="Link untuk mengecek riwayat transaksi Robux Gamepass")
async def cekrbx(interaction: discord.Interaction, username: str = None, link_gamepass: str = None):
    await interaction.response.defer(ephemeral=True)
    e = discord.Embed(title="🔍 CEK RIWAYAT TRANSAKSI ROBUX - MIPI STORE", description="Cek sendiri Robux kamu udah masuk / belum, tanpa nunggu admin! 💗", color=0xFF69B4)
    if username:
        try:
            async with aiohttp.ClientSession() as s:
                async with s.post("https://users.roblox.com/v1/usernames/users", json={"usernames": [username], "excludeBannedUsers": True}) as r:
                    data = await r.json()
                if not data.get("data"):
                    await interaction.followup.send(f"❌ Username `{username}` tidak ditemukan!", ephemeral=True); return
                user_id = data["data"][0]["id"]
                display = data["data"][0].get("displayName", username)
                gamepasses = []
                async with s.get(f"https://games.roblox.com/v2/users/{user_id}/games?limit=50&sortOrder=Asc") as r:
                    games = await r.json()
                for g in games.get("data", [])[:5]:
                    async with s.get(f"https://games.roblox.com/v1/games/{g.get('id')}/game-passes?limit=50&sortOrder=Asc") as r2:
                        gp = await r2.json()
                    for p in gp.get("data", []):
                        gamepasses.append(f"• **{p['name']}** - {p.get('price', 0)} R$ | ID: `{p['id']}`")
                e.add_field(name=f"👤 Akun: {username} ({display})", value=f"🆔 User ID: `{user_id}`\n\n**🎫 Gamepass:**\n" + ("\n".join(gamepasses[:10]) if gamepasses else "• Tidak ada / Private"), inline=False)
        except Exception as ex:
            e.add_field(name="⚠️ Info", value=f"Gagal ambil gamepass: {ex}", inline=False)
    if link_gamepass:
        m = re.search(r'(\d+)', link_gamepass)
        if m:
            gp_id = m.group(1)
            e.add_field(name="🎫 Gamepass yang dicek", value=f"ID: `{gp_id}`\nLink: https://www.roblox.com/game-pass/{gp_id}", inline=False)
            try:
                async with aiohttp.ClientSession() as s:
                    async with s.get(f"https://economy.roblox.com/v1/game-pass/{gp_id}/details") as r:
                        d = await r.json()
                    e.add_field(name="📊 Detail Gamepass", value=f"Nama: **{d.get('Name', '-')}**\nHarga: **{d.get('PriceInRobux', 0)} R$**\nPenjual: **{d.get('SellerName', '-')}**\nTerjual: **{d.get('Sales', 0)}x**", inline=False)
            except: pass
    e.add_field(name="🔗 LINK CEK RESMI ROBLOX", value="1. **Cek Transaksi:**\nhttps://www.roblox.com/transactions\n\n2. **Cek Pending Robux:**\nhttps://www.roblox.com/transactions#pending-robux\n\n3. **Cek Saldo:**\nhttps://www.roblox.com/my/account#!/info", inline=False)
    e.add_field(name="📖 CARA CEK", value="1. Login Roblox di browser\n2. Buka link Transaksi di atas\n3. Pilih Penjualan / Pembelian\n4. Kalau Pending, tunggu 3-7 hari (Hold Roblox)\n5. Kalau udah masuk, cek di pojok kanan atas", inline=False)
    e.set_footer(text="MIPI STORE • Kalau belum masuk 3 hari, buka tiket di #open-ticket")
    await interaction.followup.send(embed=e, ephemeral=True)

@bot.tree.command(name="setup-cek", description="Buatin channel cek yang estetik otomatis (Owner only)")
async def setup_cek(interaction: discord.Interaction):
    if interaction.user.id != interaction.guild.owner_id:
        await interaction.response.send_message("❌ Hanya Owner!", ephemeral=True); return
    await interaction.response.defer(ephemeral=True)
    guild = interaction.guild
    cat = None
    for c in guild.categories:
        if "MIPI" in c.name.upper() and "CEK" in c.name.upper():
            cat = c; break
    if not cat:
        cat = await guild.create_category("🌸・MIPI — CEK ROBLOX")
    ch1 = await guild.create_text_channel("🔍┆・check-avatar", category=cat, topic="✨ Cek avatar Roblox kamu disini | /checkavatar")
    ch2 = await guild.create_text_channel("💰┆・cek-rbx", category=cat, topic="✨ Cek riwayat Robux / Gamepass disini | /cekrbx")
    e1 = discord.Embed(color=0xff69b4)
    e1.description = (
        "## 🌸・CHECK AVATAR ROBLOX\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "Mau liat avatar temen? Atau mau cek akun kamu sendiri sebelum order?\n"
        "Cek disini aja, **gratis & instan!** ✨\n\n"
        "### 👇 CARANYA GAMPANG BANGET:\n"
        "1. Pencet tombol **🔍 CEK AVATAR ROBLOX** dibawah\n"
        "2. Ketik username Roblox kamu\n"
        "3. Pencet Kirim\n\n"
        "### 💡 ATAU KETIK MANUAL:\n"
        "```\n/checkavatar username: 1mrafii\n```\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "### 🎁 YANG AKAN MUNCUL\n"
        "👤 Profil • 🆔 User ID • 📅 Tanggal Dibuat\n"
        "🎩 Aksesoris • 👕 Pakaian • 🦵 Tubuh & Wajah\n"
        "🎬 Animasi • 🖼️ Foto Avatar HD\n\n"
        "💗 *MIPI STORE • Aman, Cepat, Terpercaya*"
    )
    e1.set_image(url="https://raw.githubusercontent.com/mipistore/mipi-store/main/----563dc75098ea.jpeg")
    e1.set_footer(text="MIPI STORE • /checkavatar • Check Avatar Roblox")
    e2 = discord.Embed(color=0xff69b4)
    e2.description = (
        "## 💰・CEK RIWAYAT ROBUX\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "Robux belum masuk? Jangan panik dulu Wal! 😭\n"
        "Cek sendiri disini, **tanpa nunggu admin!** ✨\n\n"
        "### 📝 CARA PAKAI\n"
        "Ketik di channel ini:\n"
        "```\n/cekrbx username: usernameRobloxKamu\n```\n"
        "### 💡 CEK GAMEPASS\n"
        "```\n/cekrbx link_gamepass: linkGamepassKamu\n```\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "### 🔗 LINK RESMI ROBLOX\n"
        "[📦 Cek Transaksi](https://www.roblox.com/transactions)\n"
        "[⏳ Cek Pending Robux](https://www.roblox.com/transactions#pending-robux)\n"
        "[💳 Cek Saldo](https://www.roblox.com/my/account#!/info)\n\n"
        "### 📖 KENAPA PENDING?\n"
        "Roblox hold Robux **3 - 7 hari** ya Wal, itu normal!\n"
        "Kalau udah 7 hari belum masuk, buka tiket di <#open-ticket>\n\n"
        "💗 *MIPI STORE • Aman, Cepat, Terpercaya*"
    )
    e2.set_image(url="https://raw.githubusercontent.com/mipistore/mipi-store/main/IMG_5210.jpeg")
    e2.set_footer(text="MIPI STORE • /cekrbx • Cek Robux & Gamepass")
    await ch1.send(embed=e1, view=CheckAvatarButtonView())
    await ch2.send(embed=e2)
    done = discord.Embed(color=0x57f287)
    done.description = (
        "## ✅ BERHASIL DIBUAT! 🎉\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📂 Kategori: **{cat.name}**\n"
        f"🔍 Channel: {ch1.mention}\n"
        f"💰 Channel: {ch2.mention}\n\n"
        "Udah estetik banget, tinggal suruh member cobain! 🌸"
    )
    await interaction.followup.send(embed=done, ephemeral=True)

bot.run(os.getenv("DISCORD_TOKEN"))
